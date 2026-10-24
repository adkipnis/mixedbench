"""installed.py reads the registry files that the wheel installs.

The suite, the survey and metabeta read them only through it.

pipeline:
---------
the installed files                                   path
-> sources.yaml as a pinned Source per label          sources
-> manifest.csv as the file each object loads from    manifest
-> registry.csv as typed Rows                         rows
-> a row's typed table                                Tables.load
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


class Tables:
    def __init__(self, cache: Path) -> None:
        self.sources = sources()
        self.loader = Loader(cache, manifest=manifest())

    def load(self, row: Row) -> pd.DataFrame:
        return self.loader.load(self.sources[row.source], row.object, row.types)
