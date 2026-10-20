"""Measure every registry row against its loaded table: the dimension survey's numbers that no
agent types (spec #14, ticket #18). `Measurer(table, row).dimensions()` gives one row per grouping
factor, `.columns()` one row per covariate column; `measureRegistry` writes them to
`dimensions.csv` and `columns.csv`. Every merge runs the pass; run it alone, and the summary
after it, from the repo root:

    uv run python survey/measure.py
"""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from mixedbench.contract import columnType, withComposites
from mixedbench.datasets import Loader
from mixedbench.registry.row import Row, parts, readCsv, writeCsv
from sources import readFrame

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
IDENTITY = ('source', 'object', 'model_index', 'tier')
DIMENSION_COLUMNS = (
    *IDENTITY, 'factor', 'n_factors', 'relation', 'd_doc', 'd_all', 'n_obs', 'n_groups',
    'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max',
    'singleton_share', 'cv', 'alpha',
)  # fmt: skip
COLUMN_COLUMNS = (*IDENTITY, 'column', 'type', 'K', 'level', 'constant_within', 'missing_share', 'in_model')  # fmt: skip


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
# pass: registry.csv -> each row's loaded table -> dimensions.csv, columns.csv
# =====================================================================================
def measureRegistry(registry: Path, loader: Loader) -> None:
    frame = readFrame(registry)
    dimensions, columns = [], []
    for cells in readCsv(registry / 'registry.csv').to_dict('records'):
        row = Row.parse(cells)
        table = loader.load(frame.sources[row.source], row.object, row.types)
        measurer = Measurer(table, row)
        dimensions += measurer.dimensions()
        columns += measurer.columns()
    writeCsv(pd.DataFrame(dimensions, columns=DIMENSION_COLUMNS), registry / 'dimensions.csv')
    writeCsv(pd.DataFrame(columns, columns=COLUMN_COLUMNS), registry / 'columns.csv')


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
        levels = self.table[[a, b]].drop_duplicates()
        return self.oneParentEach(levels, a, b) or self.oneParentEach(levels, b, a)

    @staticmethod
    def oneParentEach(levels: pd.DataFrame, child: str, parent: str) -> bool:
        parents = levels.groupby(child, observed=True)[parent].nunique()
        return bool(parents.max() == 1)

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
    def describe(self, column: str) -> dict:
        values = self.table[column]
        kind, levels = columnType(values, self.row.types.get(column, ''))
        constantWithin = [f for f in self.factors if self.constantWithin(column, f)]
        return {
            'type': kind,
            'K': levels,
            'level': 'group' if constantWithin else 'within',
            'constant_within': ';'.join(constantWithin),
            'missing_share': round(float(values.isna().mean()), 4),
            'in_model': 'yes' if column in self.row.covariates else 'no',
        }

    def constantWithin(self, column: str, factor: str) -> bool:
        distinct = self.table.groupby(factor, observed=True)[column].nunique()
        return bool(distinct.max() <= 1)

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
