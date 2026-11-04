"""installed.py reads the registry files that the wheel installs.

The suite, the survey and metabeta read them only through it.

pipeline:
---------
the installed files                                   path
-> sources.yaml as a pinned Source per label          sources
-> manifest.csv as the file each object loads from    manifest
-> registry.csv as typed Rows                         rows
-> fits.csv as lme4's status per fitted row           fits
-> fits_preparation.csv as the rows each fit read     Preparations
-> a row's typed table                                Tables.load
-> the rows its fit read                              Tables.loadFitted
"""

from __future__ import annotations

from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from mixedbench.datasets import Loader, Manifest, ManifestRow, Source
from mixedbench.registry.row import Row, readCsv

RegistryFile = Literal[
    'sources.yaml',
    'registry.csv',
    'excluded.csv',
    'dimensions.csv',
    'columns.csv',
    'column_factors.csv',
    'factor_pairs.csv',
    'fits.csv',
    'fits_preparation.csv',
    'responses.csv',
    'flat.csv',
    'flat_columns.csv',
    'flat_response_statistics.csv',
    'quantiles.yaml',
    'SUMMARY.md',
    'manifest.csv',
]


def path(name: RegistryFile | None = None) -> Path:
    # through the installed distribution, not importlib.resources: the editable install keeps
    # the files in site-packages, outside src/ (pyproject's force-include)
    dir = Path(distribution('mixedbench').locate_file('mixedbench/registry/files'))
    return dir if name is None else dir / name


def sources() -> dict[str, Source]:
    tiers = yaml.safe_load(path('sources.yaml').read_text())['tiers']
    pinned = {}
    for entries in tiers.values():
        for label, entry in entries.items():
            pinned[label] = source(label, entry)
    return pinned


def source(label: str, entry: dict) -> Source:
    """One entry of `sources.yaml` as a pinned source."""
    checksum = entry.get('checksum')
    if entry['kind'] == 'url':  # a URL has no version: the file's sha256 is its pin
        checksum = str(entry['pin'])
    layout = tuple(entry['layout']) if 'layout' in entry else None  # headerless text
    return Source(
        kind=entry['kind'],
        name=entry.get('name', label),
        pin=str(entry['pin']),
        checksum=checksum,
        path=entry.get('path'),
        file=entry.get('file'),
        layout=layout,
        mirror=entry.get('mirror'),
    )


def manifest() -> Manifest:
    """The file every registry object loads from."""
    pinned = sources()
    rows = readCsv(path('manifest.csv'))
    entries = {}
    for row in rows.itertuples(index=False):
        entries[pinned[row.source], row.object] = ManifestRow(row.file, row.sha256)
    return entries


def rows(file: Path | None = None) -> list[Row]:
    cells = readCsv(file or path('registry.csv'))
    return [Row.parse(record) for record in cells.to_dict('records')]


def fits() -> dict[str, str]:
    """lme4's status per fitted row id. fits.csv repeats a row's status on each of its factors."""
    statuses = {}
    for fit in readCsv(path('fits.csv')).to_dict('records'):
        statuses[_joinId(fit)] = fit['status']
    return statuses


def _joinId(cells: dict[str, str]) -> str:
    """A row's id from its key cells, as `Row.id` writes it."""
    return f'{cells["source"]}/{cells["object"]}/{cells["model_index"]}'


class Preparations:
    """fits_preparation.csv: the registry fits that read other rows than the whole table."""

    # a row whose source fits a subset (a pandas query) or repeats each row by a frequency
    # weight (its column), the factor whose groups a weight counts, and why
    COLUMNS = (
        'source', 'object', 'model_index', 'subset', 'frequency', 'frequency_factor', 'reason',
    )  # fmt: skip

    def __init__(self, file: Path | None = None) -> None:
        self.listed = {}
        for preparation in readCsv(file or path('fits_preparation.csv')).to_dict('records'):
            self.listed[_joinId(preparation)] = preparation

    def prepare(self, row: Row, table: pd.DataFrame) -> pd.DataFrame:
        """The rows the source fitted: its subset, each row repeated by its frequency weight.
        A weight that counts a factor's groups makes each copy of a group a group of its own."""
        preparation = self.listed.get(row.id)
        if preparation is None:
            return table
        if preparation['subset']:
            table = table.query(preparation['subset'])
        if preparation['frequency']:
            repeats = table[preparation['frequency']].astype(int)
            table = table.loc[table.index.repeat(repeats)]
        if preparation['frequency_factor']:
            factor = preparation['frequency_factor']
            copies = table.groupby(level=0).cumcount()  # per row of the table, 0 to its weight - 1
            labels = table[factor].astype(str) + ':' + copies.astype(str)
            table = table.assign(**{factor: labels})
        return table.reset_index(drop=True)


class Tables:
    def __init__(self, cache: Path) -> None:
        self.sources = sources()
        self.loader = Loader(cache, manifest=manifest())
        self.preparations = Preparations()

    def load(self, row: Row) -> pd.DataFrame:
        return self.loader.load(self.sources[row.source], row.object, row.types)

    def loadFitted(self, row: Row) -> pd.DataFrame:
        """The rows the row's fit in fits.csv read. A problem builds from `load`'s whole table."""
        return self.preparations.prepare(row, self.load(row))
