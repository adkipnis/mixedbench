"""measure.py runs the measurement pass: the dimension survey's numbers that no agent types,
measured on each registry row's loaded table and written to the five measured files.
The Measurer holds what the five share: the loaded rows, those with a response,
the covariate columns with their types, each grouping factor's group-level columns,
two factors' holders and the empty cells of two columns' levels.

pipeline:
---------
registry.csv and each row's loaded table
-> one row's table and what the measured files share  Measurer
-> a row per grouping factor                         dimensions.measure
-> a row per covariate column                        columns.measure
-> a row per covariate column and grouping factor    groups.measure
-> a row per pair of grouping factors                pairs.measure
-> a row per registry row's response                 responses.measure
-> the row's records in a file of its own            Measurement.run
-> the five measured files, in registry order        Measurement.collect

A merge measures nothing, so the pass and the summary after it run as a job of their own
before a release. A cluster array task measures one row, named by its index in registry.csv, so
that a crash costs one row; the collect writes the measured files and the summary. Run from the
repo root:

    uv run python survey/measure.py run 17
    uv run python survey/measure.py collect
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import columns
import dimensions
import groups
import pairs
import pandas as pd
import responses
from mixedbench import registry
from mixedbench.contract import columnKind, withComposites
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
        self.loaded = table  # the response's missing share counts every loaded row
        measured = table[table[row.response].notna()]  # a PK table's dosing rows carry no response
        self.table = withComposites(measured, self.grouping_factors)
        self.identity = {k: getattr(row, k) for k in IDENTITY}
        taken = {row.response, row.trials, *self.grouping_factors, *row.ignore}
        self.column_names = [c for c in table.columns if c not in taken]
        self.column_types = {c: columnKind(self.table[c]) for c in self.column_names}
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
# pass: a registry row -> its measurements -> the five measured files
# =====================================================================================
MEASURED_COLUMNS = {
    'dimensions': dimensions.DIMENSION_COLUMNS,
    'columns': columns.COLUMN_COLUMNS,
    'column_factors': groups.COLUMN_FACTOR_COLUMNS,
    'factor_pairs': pairs.FACTOR_PAIR_COLUMNS,
    'responses': responses.RESPONSE_COLUMNS,
}


class Measurement:
    """The measurement of a registry's rows, a records file each under `dir`."""

    def __init__(self, root: Path, loader: Loader, dir: Path) -> None:
        self.root = root
        self.loader = loader
        self.dir = dir
        self.sources = readFrame(root).sources
        self.rows = registry.rows(root / 'registry.csv')

    def run(self, index: int) -> None:
        """Measures the row at `index` in registry order, replacing an earlier run of it."""
        row = self.rows[index]
        table = self.loader.load(self.sources[row.source], row.object, row.types)
        measurer = Measurer(table, row)
        measured = {
            'dimensions': dimensions.measure(measurer),
            'columns': columns.measure(measurer),
            'column_factors': groups.measure(measurer),
            'factor_pairs': pairs.measure(measurer),
            'responses': [responses.measure(measurer)],
        }
        self.dir.mkdir(parents=True, exist_ok=True)
        self.findRecords(row).write_text(json.dumps(measured, indent=2))

    def collect(self) -> None:
        """Writes every row's records into the five measured files in registry order."""
        measured = {name: [] for name in MEASURED_COLUMNS}
        for row in self.rows:
            records = json.loads(self.findRecords(row).read_text())
            for name in MEASURED_COLUMNS:
                measured[name] += records[name]
        for name, header in MEASURED_COLUMNS.items():
            writeCsv(pd.DataFrame(measured[name], columns=header), self.root / f'{name}.csv')

    def findRecords(self, row: Row) -> Path:
        return self.dir / f'{digestId(row.id)}.json'


def digestId(id: str) -> str:
    """A run is named by its row's hash, since an id may hold `/`, `!` and spaces."""
    return hashlib.sha256(id.encode()).hexdigest()[:16]


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    from summarize import Summarizer  # imported here: summarize imports the measured modules

    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('run', 'collect'), help='measure one row, or collect every row into the measured files and the summary')
    parser.add_argument('index', type=int, nargs='?', help='the row to measure, by its 0-based index in registry.csv')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding the duplicates and dropped tables')
    parser.add_argument('--dir', type=Path, default=HERE.parent / 'measure', help='folder of the rows\' records')
    args = parser.parse_args()
    # fmt: on
    measurement = Measurement(args.registry, Loader(args.registry / 'cache'), args.dir)
    if args.command == 'run':
        measurement.run(args.index)
    else:
        measurement.collect()
        Summarizer(args.registry, args.survey).flush()
