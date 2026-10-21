"""Measure every registry row against its loaded table: the dimension survey's numbers that no
agent types (spec #14, ticket #18). `Measurer(table, row).dimensions()` gives one row per grouping
factor, `.columns()` one row per covariate column, `.columnFactors()` one row per covariate
column and grouping factor, `.factorPairs()` one row per pair of grouping factors;
`measureRegistry` writes them to `dimensions.csv`, `columns.csv`, `column_factors.csv` and
`factor_pairs.csv`. Every merge runs the pass; run it alone, and the summary
after it, from the repo root:

    uv run python survey/measure.py
"""

from __future__ import annotations

import argparse
import dataclasses
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from mixedbench.contract import Problem, Refused, columnType, withComposites
from mixedbench.datasets import Loader
from mixedbench.registry.row import Row, parts, readCsv, writeCsv
from sources import readFrame

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
IDENTITY = ('source', 'object', 'model_index', 'tier')
DIMENSION_COLUMNS = (
    *IDENTITY, 'factor', 'n_factors', 'relation', 'd_doc', 'd_all', 'condition_doc',
    'condition_all', 'n_obs', 'n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50',
    'group_size_p90', 'group_size_max', 'singleton_share', 'cv', 'alpha',
)  # fmt: skip
COLUMN_COLUMNS = (
    *IDENTITY, 'column', 'type', 'K', 'level', 'constant_within', 'missing_share', 'in_model',
    'skewness', 'excess_kurtosis', 'outlier_share', 'zero_share', 'min_share', 'max_share',
    'unique_share', 'rare_level_share', 'max_abs_rho',
)  # fmt: skip
COLUMN_FACTOR_COLUMNS = (
    *IDENTITY, 'column', 'factor', 'between_group_share', 'group_level_r2', 'absent_level_share',
    'size_rho', 'within_sd_cv',
)  # fmt: skip
FACTOR_PAIR_COLUMNS = (
    *IDENTITY,
    'factor_a',
    'factor_b',
    'relation',
    'superior',
    'empty_cell_share',
)


def fitAlpha(sizes: pd.Series) -> float:
    """Concentration of a symmetric Dirichlet fitted by moment matching to the group-size
    proportions: Var(p) = (1 − 1/m) / (m (m α + 1)) solved for α; the variance is around the
    known mean 1/m. A balanced allocation has zero variance, hence infinite α (spec #14)."""
    m = len(sizes)
    p = sizes / sizes.sum()
    variance = float(((p - 1 / m) ** 2).mean())
    if variance == 0:
        return float('inf')
    return ((1 - 1 / m) / (m * variance) - 1) / m


def observed(values: pd.Series, q: float) -> int | float:
    """The observed value at or below the level under p50, at or above from p50 on."""
    v = values.quantile(q, interpolation='higher' if q >= 0.5 else 'lower')
    return int(v) if float(v).is_integer() else float(v)


# =====================================================================================
# pass: registry.csv -> each row's loaded table -> the four measured files
# =====================================================================================
def measureRegistry(registry: Path, loader: Loader) -> None:
    frame = readFrame(registry)
    dimensions, columns, pairs, factorPairs = [], [], [], []
    for cells in readCsv(registry / 'registry.csv').to_dict('records'):
        row = Row.parse(cells)
        table = loader.load(frame.sources[row.source], row.object, row.types)
        measurer = Measurer(table, row)
        dimensions += measurer.dimensions()
        columns += measurer.columns()
        pairs += measurer.columnFactors()
        factorPairs += measurer.factorPairs()
    writeCsv(pd.DataFrame(dimensions, columns=DIMENSION_COLUMNS), registry / 'dimensions.csv')
    writeCsv(pd.DataFrame(columns, columns=COLUMN_COLUMNS), registry / 'columns.csv')
    writeCsv(pd.DataFrame(pairs, columns=COLUMN_FACTOR_COLUMNS), registry / 'column_factors.csv')
    writeCsv(pd.DataFrame(factorPairs, columns=FACTOR_PAIR_COLUMNS), registry / 'factor_pairs.csv')


# =====================================================================================
# pipeline: registry row -> relation -> group sizes per factor -> covariate columns -> d
# =====================================================================================
class Measurer:
    def __init__(self, table: pd.DataFrame, row: Row) -> None:
        self.row = row
        self.factors = row.grouping_factors
        measured = table[table[row.response].notna()]  # a PK table's dosing rows carry no response
        self.table = withComposites(measured, self.factors)
        self.identity = {k: getattr(row, k) for k in IDENTITY}
        taken = {row.response, row.trials, *self.factors, *row.ignore}
        self.columnNames = [c for c in table.columns if c not in taken]
        self.groupLevel = self.findGroupLevel()

    def columns(self) -> list[dict]:
        rho = self.maxAbsRho()
        return [self.identity | {'column': c} | self.describe(c) | {'max_abs_rho': rho[c]} for c in self.columnNames]  # fmt: skip

    def dimensions(self) -> list[dict]:
        shared = {'n_factors': len(self.factors), 'relation': self.relation()}
        shared |= self.design() | self.measureConditions()
        return [self.identity | {'factor': f} | shared | self.groupSizes(f) for f in self.factors]  # fmt: skip

    def columnFactors(self) -> list[dict]:
        pairs = []
        for column in self.columnNames:
            for factor in self.factors:
                key = {'column': column, 'factor': factor}
                pairs.append(self.identity | key | self.relate(column, factor))
        return pairs

    def factorPairs(self) -> list[dict]:
        pairs = []
        for a, b in combinations(self.factors, 2):
            key = {'factor_a': a, 'factor_b': b}
            pairs.append(self.identity | key | self.relateFactors(a, b))
        return pairs

    # ---------------------------------------------------------------------------------
    # relation
    # ---------------------------------------------------------------------------------
    def relation(self) -> str:
        """The practice survey's single / nested / crossed / mixed, computed from the data:
        a pair is nested when every level of one factor lies in one level of the other."""
        if len(self.factors) == 1:
            return 'single'
        nested = {self.nested(a, b) for a, b in combinations(self.factors, 2)}
        if nested == {True}:
            return 'nested'
        if nested == {False}:
            return 'crossed'
        return 'mixed'

    def nested(self, a: str, b: str) -> bool:
        levels = self.table[[a, b]].drop_duplicates()
        return self.oneParentEach(levels, a, b) or self.oneParentEach(levels, b, a)

    @staticmethod
    def oneParentEach(levels: pd.DataFrame, child: str, parent: str) -> bool:
        parents = levels.groupby(child, observed=True)[parent].nunique()
        return bool(parents.max() == 1)

    def relateFactors(self, a: str, b: str) -> dict:
        if self.nested(a, b):
            return {'relation': 'nested'} | self.findSuperior(a, b)
        return {'relation': 'crossed'} | self.emptyCellShare(a, b)

    def findSuperior(self, a: str, b: str) -> dict:
        """The factor whose groups each hold whole groups of the other; blank when each holds
        the other's, as the two partitions coincide."""
        levels = self.table[[a, b]].drop_duplicates()
        pairs = ((a, b), (b, a))  # (parent, child)
        holders = [parent for parent, child in pairs if self.oneParentEach(levels, child, parent)]
        if len(holders) == 2:
            return {}
        return {'superior': holders[0]}

    def emptyCellShare(self, a: str, b: str) -> dict:
        """The share of the m_a × m_b group × group cells that hold no row."""
        cells = self.table[[a, b]].dropna().drop_duplicates()
        m_a, m_b = cells[a].nunique(), cells[b].nunique()
        return {'empty_cell_share': round(1 - len(cells) / (m_a * m_b), 4)}

    # ---------------------------------------------------------------------------------
    # group sizes
    # ---------------------------------------------------------------------------------
    def groupSizes(self, factor: str) -> dict:
        sizes = self.table[factor].value_counts()
        sizes = sizes[sizes > 0]  # a categorical may carry unused levels
        return {
            'n_obs': int(sizes.sum()),
            'n_groups': len(sizes),
            'group_size_min': int(sizes.min()),
            'group_size_p10': observed(sizes, 0.1),
            'group_size_p50': observed(sizes, 0.5),
            'group_size_p90': observed(sizes, 0.9),
            'group_size_max': int(sizes.max()),
            'singleton_share': round(float((sizes == 1).mean()), 4),
            'cv': round(float(np.std(sizes) / np.mean(sizes)), 4),
            'alpha': round(fitAlpha(sizes), 4),
        }

    # ---------------------------------------------------------------------------------
    # covariate columns
    # ---------------------------------------------------------------------------------
    def typeOf(self, column: str) -> tuple[str, int | str]:
        return columnType(self.table[column], self.row.types.get(column, ''))

    def describe(self, column: str) -> dict:
        values = self.table[column]
        kind, levels = self.typeOf(column)
        constantWithin = [f for f in self.factors if self.constantWithin(column, f)]
        return {
            'type': kind,
            'K': levels,
            'level': 'group' if constantWithin else 'within',
            'constant_within': ';'.join(constantWithin),
            'missing_share': round(float(values.isna().mean()), 4),
            'in_model': 'yes' if column in self.row.covariates else 'no',
        } | self.shape(values.dropna(), kind)

    def constantWithin(self, column: str, factor: str) -> bool:
        distinct = self.table.groupby(factor, observed=True)[column].nunique()
        return bool(distinct.max() <= 1)

    def findGroupLevel(self) -> dict[str, list[str]]:
        """Each factor's group-level columns, found once: every column × factor pair asks."""
        groupLevel = {}
        for factor in self.factors:
            groupLevel[factor] = [c for c in self.columnNames if self.constantWithin(c, factor)]
        return groupLevel

    def shape(self, values: pd.Series, kind: str) -> dict:
        """The quirk statistics that the column's kind defines, over its non-missing values;
        a statistic left out is blank in columns.csv."""
        if values.empty:
            return {}
        shape = {'unique_share': round(values.nunique() / len(values), 4)}
        if kind == 'continuous':
            shape |= self.moments(values)
        if kind in ('continuous', 'ordered'):
            shape |= self.bounds(values, kind)
        if kind != 'continuous':
            counts = values.value_counts()
            present = counts[counts > 0]  # a categorical may carry unused levels
            shape['rare_level_share'] = round(float(present.min() / present.sum()), 4)
        return shape

    @staticmethod
    def moments(values: pd.Series) -> dict:
        """Fisher's G1 and G2 as pandas computes them, and the share beyond four sample
        standard deviations; none for a constant column."""
        if values.nunique() < 2:
            return {}
        z = (values - values.mean()) / values.std()
        return {
            'skewness': round(float(values.skew()), 4),  # blank under three values
            'excess_kurtosis': round(float(values.kurt()), 4),  # blank under four
            'outlier_share': round(float((z.abs() > 4).mean()), 4),
        }

    @staticmethod
    def bounds(values: pd.Series, kind: str) -> dict:
        """The shares at the lowest value, at the highest and at zero: an ordered column's values
        are its levels in order, its zero a level loaded as the number zero."""
        ranks = values.cat.codes if kind == 'ordered' else values
        bounds = {
            'min_share': round(float((ranks == ranks.min()).mean()), 4),
            'max_share': round(float((ranks == ranks.max()).mean()), 4),
        }
        loaded = values.cat.categories if kind == 'ordered' else values
        if pd.api.types.is_numeric_dtype(loaded):
            bounds['zero_share'] = round(float((values == 0).mean()), 4)
        return bounds

    # ---------------------------------------------------------------------------------
    # dependence between covariate columns
    # ---------------------------------------------------------------------------------
    def maxAbsRho(self) -> pd.Series:
        """Each column's largest |Spearman| with another, over the rows where both are observed:
        continuous columns as loaded, binary and ordered ones by their levels in loaded order.
        Blank with no partner, or when every partner or the column is constant on those rows."""
        ranked = {}
        for column in self.columnNames:
            kind, _ = self.typeOf(column)
            if kind != 'categorical':
                ranked[column] = self.codeColumn(column, kind)
        rho = pd.DataFrame(ranked, index=self.table.index).corr(method='spearman').abs()
        partners = rho.where(~np.eye(len(rho), dtype=bool))
        return partners.max().round(4).reindex(self.columnNames)

    def codeColumn(self, column: str, kind: str) -> pd.Series:
        """A continuous column as loaded, a binary or ordered one by its levels' codes in loaded
        order; a missing value stays missing."""
        values = self.table[column]
        if kind == 'continuous':
            return values.astype(float)
        codes = pd.Series(pd.Categorical(values).codes, index=values.index)
        return codes.where(codes >= 0)  # -1 codes a missing value

    # ---------------------------------------------------------------------------------
    # columns against grouping factors
    # ---------------------------------------------------------------------------------
    def relate(self, column: str, factor: str) -> dict:
        """The quirk statistics of a column against a factor's groups, over the rows that observe
        both; a statistic left out is blank in column_factors.csv."""
        observed = self.table[column].notna() & self.table[factor].notna()
        if not observed.any():
            return {}
        kind, _ = self.typeOf(column)
        groups = self.table.loc[observed, factor]
        statistics = {}
        if kind != 'continuous':
            statistics |= self.absentLevelShare(self.table.loc[observed, column], groups)
        if kind != 'categorical':
            values = self.codeColumn(column, kind)[observed]
            statistics |= self.betweenGroupShare(values, groups) | self.sizeRho(values, groups)
            statistics |= self.withinSdCv(values, groups) | self.groupLevelR2(column, factor, kind)
        return statistics

    @staticmethod
    def absentLevelShare(values: pd.Series, groups: pd.Series) -> dict:
        """The share of the m × k group × level cells that hold no row."""
        cells = pd.DataFrame({'group': groups, 'level': values}).drop_duplicates()
        m, k = groups.nunique(), values.nunique()
        return {'absent_level_share': round(1 - len(cells) / (m * k), 4)}

    @staticmethod
    def betweenGroupShare(values: pd.Series, groups: pd.Series) -> dict:
        """The adjusted ICC(1) of a one-way analysis of variance,
        (MSB − MSW) / (MSB + (k₀ − 1) MSW) with k₀ = (n − Σ nⱼ² / n) / (m − 1)
        (Snijders & Bosker 2012, section 3.3.1).
        None with one group, when every group is a singleton or the column is constant."""
        grouped = values.groupby(groups, observed=True)
        sizes = grouped.size()
        n, m = int(sizes.sum()), len(sizes)
        if m < 2 or n == m:
            return {}
        between = float((sizes * (grouped.mean() - values.mean()) ** 2).sum())
        within = float(((values - grouped.transform('mean')) ** 2).sum())
        if between + within == 0:  # a constant column has no variance to share
            return {}
        msb, msw = between / (m - 1), within / (n - m)
        k0 = (n - float((sizes**2).sum()) / n) / (m - 1)
        return {'between_group_share': round((msb - msw) / (msb + (k0 - 1) * msw), 4)}

    @staticmethod
    def sizeRho(values: pd.Series, groups: pd.Series) -> dict:
        """Spearman's ρ of the groups' sizes with their means; blank when either is constant."""
        grouped = values.groupby(groups, observed=True)
        sizes, means = grouped.size(), grouped.mean()
        if sizes.nunique() < 2 or means.nunique() < 2:
            return {}
        rho = sizes.rank().corr(means.rank())  # Pearson's r of the ranks
        return {'size_rho': round(float(rho), 4)}

    @staticmethod
    def withinSdCv(values: pd.Series, groups: pd.Series) -> dict:
        """The population coefficient of variation of the groups' sample standard deviations,
        over the groups of two or more rows; blank with fewer than two or a zero mean."""
        grouped = values.groupby(groups, observed=True)
        sds = grouped.std()[grouped.size() >= 2]
        if len(sds) < 2 or sds.mean() == 0:
            return {}
        return {'within_sd_cv': round(float(sds.std(ddof=0) / sds.mean()), 4)}

    def groupLevelR2(self, column: str, factor: str, kind: str) -> dict:
        """The row-level R² of the column on the factor's other group-level columns, adjusted by
        the group count m and the design's rank p, 1 − (1 − R²)(m − 1) / (m − p − 1), over the
        rows that observe them all. Blank when the partners span nothing beyond the intercept,
        leave no degree of freedom, or the column is constant."""
        partners = [c for c in self.groupLevel[factor] if c != column]
        complete = self.table[[column, factor, *partners]].dropna().index
        y = self.codeColumn(column, kind)[complete].to_numpy(float)
        design = self.codeDesign(partners, complete)
        m = self.table.loc[complete, factor].nunique()
        p = np.linalg.matrix_rank(design) - 1
        if p == 0 or m - p - 1 <= 0:
            return {}
        total = float(((y - y.mean()) ** 2).sum())
        if total == 0:  # a constant column has no variance to explain
            return {}
        fitted = design @ np.linalg.lstsq(design, y)[0]
        r2 = 1 - float(((y - fitted) ** 2).sum()) / total
        return {'group_level_r2': round(float(1 - (1 - r2) * (m - 1) / (m - p - 1)), 4)}

    def codeDesign(self, columns: list[str], rows: pd.Index) -> np.ndarray:
        """An intercept, then each column as the contract's design spans it: a continuous one
        raw, any other by its levels' indicators but the first. R² and rank depend only on the
        span, not on which level is the reference."""
        coded = [pd.DataFrame({'intercept': 1.0}, index=rows)]
        for column in columns:
            values = self.table.loc[rows, column]
            kind, _ = self.typeOf(column)
            if kind == 'continuous':
                coded.append(values.astype(float).to_frame())
            else:
                coded.append(pd.get_dummies(values, drop_first=True, dtype=float))
        return pd.concat(coded, axis=1).to_numpy()

    # ---------------------------------------------------------------------------------
    # design columns
    # ---------------------------------------------------------------------------------
    def design(self) -> dict:
        """d_doc expands the documented model, d_all every covariate column plus the documented
        interactions, so that d_all is never below d_doc (envelope rule 4): continuous and
        binary count 1, categorical k − 1, an interaction the product."""
        width = {c['column']: self.width(c) for c in self.columns()}
        interactions = self.row.interactions
        dInteractions = sum(np.prod([width[c] for c in parts(term)]) for term in interactions)
        dDoc = sum(width[c] for c in self.row.covariates) + dInteractions
        dAll = sum(width.values()) + dInteractions
        return {'d_doc': int(dDoc), 'd_all': int(dAll)}

    @staticmethod
    def width(column: dict) -> int:
        if column['type'] in ('categorical', 'ordered'):
            return column['K'] - 1
        return 1

    def measureConditions(self) -> dict:
        """The condition index of the contract's design, of the documented model and of every
        measured column with the documented interactions; the contract codes, types and drops
        incomplete rows alike for both. Blank where the contract builds no problem."""
        try:
            documented = Problem.build(self.row, self.table)
        except Refused:
            return {}
        conditions = {'condition_doc': self.computeConditionIndex(documented)}
        everything = dataclasses.replace(self.row, covariates=tuple(self.columnNames))
        try:
            measured = Problem.build(everything, self.table)
        except (Refused, TypeError):  # no complete row, or a column of strings and numbers (#105)
            return conditions
        return conditions | {'condition_all': self.computeConditionIndex(measured)}

    @staticmethod
    def computeConditionIndex(problem: Problem) -> float:
        """Belsley, Kuh and Welsch's (1980) σ_max / σ_min of the standardized full-regime design,
        intercept included, each column scaled to unit length; inf when rank-deficient."""
        design = problem.standardized()[list(problem.design)]
        scaled = (design / np.sqrt((design**2).sum())).to_numpy()
        # a constant continuous column standardizes to 0/0, and an interaction's empty cell
        # gives a column of zeros, which scales to 0/0: both leave the design rank-deficient
        if not np.isfinite(scaled).all():
            return float('inf')
        if np.linalg.matrix_rank(scaled) < scaled.shape[1]:
            return float('inf')
        singular = np.linalg.svd(scaled, compute_uv=False)
        return round(float(singular[0] / singular[-1]), 4)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    from summarize import Summarizer  # imported here: summarize imports this module

    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding the duplicates and dropped tables')
    args = parser.parse_args()
    # fmt: on
    measureRegistry(args.registry, Loader(args.registry / 'cache'))
    Summarizer(args.registry, args.survey).flush()
