"""measure.py runs the measurement pass: the dimension survey's numbers that no agent types,
measured on each registry row's loaded table and written to the four measured files.
The Measurer holds what the four share: the rows with a response, the covariate columns
with their types, each grouping factor's group-level columns, a column's codes, two factors' holders
and the empty cells of two columns' levels.

pipeline:
---------
registry.csv and each row's loaded table
-> one row's table and what the measured files share  Measurer
-> a row per grouping factor                         dimensions.measure
-> a row per covariate column                        columns.measure
-> a row per covariate column and grouping factor    groups.measure
-> a row per pair of grouping factors                pairs.measure
-> the four measured files                           measureRegistry

Every merge runs the pass; run it alone, and the summary after it, from the repo root:

    uv run python survey/measure.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import columns
import dimensions
import groups
import pairs
import pandas as pd
from mixedbench import registry
from mixedbench.contract import columnType, withComposites
from mixedbench.datasets import Loader
from mixedbench.registry.row import Row, writeCsv
from schema import IDENTITY
from sources import readFrame

HERE = Path(__file__).parent


# =====================================================================================
# measurer: one registry row's table and what the measured files share
# =====================================================================================
class Measurer:
    def __init__(self, table: pd.DataFrame, row: Row) -> None:
        self.row = row
        self.grouping_factors = row.grouping_factors
        measured = table[table[row.response].notna()]  # a PK table's dosing rows carry no response
        self.table = withComposites(measured, self.grouping_factors)
        self.identity = {k: getattr(row, k) for k in IDENTITY}
        taken = {row.response, row.trials, *self.grouping_factors, *row.ignore}
        self.column_names = [c for c in table.columns if c not in taken]
        self.column_types = {c: columnType(self.table[c]) for c in self.column_names}
        self.group_level = self.findGroupLevel()

    def findGroupLevel(self) -> dict[str, list[str]]:
        """Each grouping factor's group-level columns, those constant within its groups."""
        group_level = {}
        for grouping_factor in self.grouping_factors:
            grouped = self.table.groupby(grouping_factor, observed=True)
            group_level[grouping_factor] = [
                c for c in self.column_names if grouped[c].nunique().max() <= 1
            ]
        return group_level

    def codeColumn(self, column: str, kind: str) -> pd.Series:
        """A continuous column as loaded, a binary or ordered one by the codes of its present
        levels. A missing value stays missing."""
        values = self.table[column]
        if kind == 'continuous':
            return values.astype(float)
        levels = pd.Categorical(values).remove_unused_categories()
        codes = pd.Series(levels.codes, index=values.index)
        return codes.where(codes >= 0)  # -1 codes a missing value

    def findHolders(self, a: str, b: str) -> list[str]:
        """The factors whose groups hold whole groups of the other: none when the two cross,
        both when they partition the rows alike."""
        levels = self.table[[a, b]].drop_duplicates()
        holders = []
        if self.hasOneParent(levels, b, a):
            holders.append(a)
        if self.hasOneParent(levels, a, b):
            holders.append(b)
        return holders

    @staticmethod
    def hasOneParent(levels: pd.DataFrame, child: str, parent: str) -> bool:
        parents = levels.groupby(child, observed=True)[parent].nunique()
        return bool(parents.max() == 1)

    @staticmethod
    def measureEmptyCells(pairs: pd.DataFrame) -> float:
        """The share of the two columns' level × level cells that hold no row."""
        cells = pairs.dropna().drop_duplicates()
        first, second = cells.columns
        m, k = cells[first].nunique(), cells[second].nunique()
        return round(1 - len(cells) / (m * k), 4)


# =====================================================================================
# pass: registry.csv -> each row's loaded table -> the four measured files
# =====================================================================================
def measureRegistry(root: Path, loader: Loader) -> None:
    frame = readFrame(root)
    measured = {'dimensions': [], 'columns': [], 'column_factors': [], 'factor_pairs': []}
    for row in registry.rows(root / 'registry.csv'):
        table = loader.load(frame.sources[row.source], row.object, row.types)
        measurer = Measurer(table, row)
        measured['dimensions'] += dimensions.measure(measurer)
        measured['columns'] += columns.measure(measurer)
        measured['column_factors'] += groups.measure(measurer)
        measured['factor_pairs'] += pairs.measure(measurer)
    headers = {
        'dimensions': dimensions.DIMENSION_COLUMNS,
        'columns': columns.COLUMN_COLUMNS,
        'column_factors': groups.COLUMN_FACTOR_COLUMNS,
        'factor_pairs': pairs.FACTOR_PAIR_COLUMNS,
    }
    for name, rows in measured.items():
        writeCsv(pd.DataFrame(rows, columns=headers[name]), root / f'{name}.csv')


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    from summarize import Summarizer  # imported here: summarize imports the measured modules

    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding the duplicates and dropped tables')
    args = parser.parse_args()
    # fmt: on
    measureRegistry(args.registry, Loader(args.registry / 'cache'))
    Summarizer(args.registry, args.survey).flush()
