"""Measure one loaded table against its registry row: the dimension survey's numbers that no
agent types (spec #14, ticket #18). `Measurer(df, row).dimensions()` gives one row per grouping
factor, `.columns()` one row per covariate column; the merge script writes them to
`dimensions.csv` and `columns.csv`.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

# =====================================================================================
# globals
# =====================================================================================
IDENTITY = ('source', 'object', 'model_index', 'tier')
DIMENSION_COLUMNS = (
    *IDENTITY, 'factor', 'n_factors', 'relation', 'd_doc', 'd_all', 'n_obs', 'n_groups',
    'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max',
    'singleton_share', 'cv', 'alpha',
)  # fmt: skip
COLUMN_COLUMNS = (*IDENTITY, 'column', 'type', 'K', 'level', 'constant_within', 'missing_share', 'in_model')  # fmt: skip
# A string or integer column with at most this many distinct values is a categorical (spec #14).
MAX_INTEGER_LEVELS = 10


def splitList(text: str) -> list[str]:
    return [t.strip() for t in text.split(';') if t.strip()]


def withComposites(df: pd.DataFrame, factors: list[str]) -> pd.DataFrame:
    """A grouping factor `a:b` names no column (lme4's `(1|a:b)`, the whole plots of a
    split-plot): the combination of its parts is added under that name, one level per pair of
    levels present; a row missing a part has no level (the ARM radon survey's rows without a
    county). Built here once, so the merge's checks and the measures see a plain column."""
    composites = {}
    for factor in factors:
        if ':' in factor:
            parts = factor.split(':')
            composite = df[parts[0]].astype(str)
            for part in parts[1:]:
                composite = composite + ':' + df[part].astype(str)  # missing stays missing
            composites[factor] = composite
    return df.assign(**composites)


def fitAlpha(sizes: pd.Series) -> float:
    """Concentration of a symmetric Dirichlet fitted by moment matching to the group-size
    proportions: Var(p) = (1 − 1/G) / (G (G α + 1)) solved for α; the variance is around the
    known mean 1/G. A balanced allocation has zero variance, hence infinite α (spec #14)."""
    g = len(sizes)
    p = sizes / sizes.sum()
    variance = float(((p - 1 / g) ** 2).mean())
    if variance == 0:
        return float('inf')
    return ((1 - 1 / g) / (g * variance) - 1) / g


def parseTypes(text: str) -> dict[str, str]:
    """`col=categorical;col2=continuous` -> {col: kind}."""
    pairs = [entry.partition('=') for entry in splitList(text)]
    return {col.strip(): kind.strip() for col, _, kind in pairs}


def observed(values: pd.Series, q: float) -> int | float:
    """The observed value at or below the level under p50, at or above from p50 on."""
    v = values.quantile(q, interpolation='higher' if q >= 0.5 else 'lower')
    return int(v) if float(v).is_integer() else float(v)


# =====================================================================================
# pipeline: registry row -> relation -> group sizes per factor -> covariate columns -> d
# =====================================================================================
class Measurer:
    def __init__(self, df: pd.DataFrame, row: dict) -> None:
        self.row = row
        self.factors = splitList(row['grouping_factors'])
        measured = df[df[row['response']].notna()]  # a PK table's dosing rows carry no response
        self.df = withComposites(measured, self.factors)
        self.identity = {k: row[k] for k in IDENTITY}
        self.declared = parseTypes(row['types'])
        self.covariates = splitList(row['covariates'])
        taken = {row['response'], row['trials'], *self.factors, *splitList(row['ignore'])}
        self.columnNames = [c for c in df.columns if c not in taken]

    def columns(self) -> list[dict]:
        return [self.identity | {'column': c} | self.describe(c) for c in self.columnNames]

    def dimensions(self) -> list[dict]:
        shared = {'n_factors': len(self.factors), 'relation': self.relation()} | self.design()
        return [self.identity | {'factor': f} | shared | self.groupSizes(f) for f in self.factors]  # fmt: skip

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
        levels = self.df[[a, b]].drop_duplicates()
        return self.oneParentEach(levels, a, b) or self.oneParentEach(levels, b, a)

    @staticmethod
    def oneParentEach(levels: pd.DataFrame, child: str, parent: str) -> bool:
        parents = levels.groupby(child, observed=True)[parent].nunique()
        return bool(parents.max() == 1)

    # ---------------------------------------------------------------------------------
    # group sizes
    # ---------------------------------------------------------------------------------
    def groupSizes(self, factor: str) -> dict:
        sizes = self.df[factor].value_counts()
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
    def describe(self, column: str) -> dict:
        values = self.df[column]
        kind, levels = self.columnType(values, self.declared.get(column, ''))
        constantWithin = [f for f in self.factors if self.constantWithin(column, f)]
        return {
            'type': kind,
            'K': levels,
            'level': 'group' if constantWithin else 'within',
            'constant_within': ';'.join(constantWithin),
            'missing_share': round(float(values.isna().mean()), 4),
            'in_model': 'yes' if column in self.covariates else 'no',
        }

    @staticmethod
    def columnType(values: pd.Series, declared: str) -> tuple[str, int | str]:
        """The one typing rule, in order: ordered categorical; exactly two distinct values is
        binary; a declared or typed categorical, a string, or an integer with few distinct values
        is categorical with K levels; otherwise continuous. K is blank for a continuous column."""
        distinct = values.dropna().nunique()
        dtype = values.dtype
        if isinstance(dtype, pd.CategoricalDtype) and dtype.ordered:
            return 'ordered', distinct
        if distinct == 2:
            return 'binary', 2
        if declared == 'continuous':
            return 'continuous', ''
        if isinstance(dtype, pd.CategoricalDtype) or pd.api.types.is_string_dtype(dtype):
            return 'categorical', distinct
        if pd.api.types.is_integer_dtype(dtype) and distinct <= MAX_INTEGER_LEVELS:
            return 'categorical', distinct
        return 'continuous', ''

    def constantWithin(self, column: str, factor: str) -> bool:
        distinct = self.df.groupby(factor, observed=True)[column].nunique()
        return bool(distinct.max() <= 1)

    # ---------------------------------------------------------------------------------
    # design columns
    # ---------------------------------------------------------------------------------
    def design(self) -> dict:
        """d_doc expands the documented model, d_all every covariate column plus the documented
        interactions, so that d_all is never below d_doc (envelope rule 4): continuous and
        binary count 1, categorical K − 1, an interaction the product."""
        width = {c['column']: self.width(c) for c in self.columns()}
        interactions = splitList(self.row['interactions'])
        dInteractions = sum(np.prod([width[c] for c in term.split(':')]) for term in interactions)
        dDoc = sum(width[c] for c in self.covariates) + dInteractions
        dAll = sum(width.values()) + dInteractions
        return {'d_doc': int(dDoc), 'd_all': int(dAll)}

    @staticmethod
    def width(column: dict) -> int:
        if column['type'] in ('categorical', 'ordered'):
            return column['K'] - 1
        return 1
