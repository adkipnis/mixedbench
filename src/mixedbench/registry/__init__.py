"""The registry files (ADR 0002): the only way the package and metabeta read them."""

from __future__ import annotations

from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

import yaml
from mixedbench.datasets import Manifest, ManifestRow, Source
from mixedbench.registry.row import Row, readCsv

RegistryFile = Literal[
    'sources.yaml',
    'registry.csv',
    'excluded.csv',
    'dimensions.csv',
    'columns.csv',
    'quantiles.yaml',
    'SUMMARY.md',
    'manifest.csv',
]


def path(name: RegistryFile | None = None) -> Path:
    """A registry file, or their directory without a name. Located through the installed
    distribution, not importlib.resources: the editable install keeps its copies in
    site-packages, outside src/ (pyproject's force-include)."""
    dir = Path(distribution('mixedbench').locate_file('mixedbench/registry/files'))
    return dir if name is None else dir / name


def sources(file: Path | None = None) -> dict[str, Source]:
    """Every pinned source by its label; `file` is a `sources.yaml` other than the installed
    one (the survey's scratch registries)."""
    frame = yaml.safe_load((file or path('sources.yaml')).read_text())
    pinned = {}
    for entries in frame['tiers'].values():
        for label, entry in (entries or {}).items():
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
    """The file every registry object loads from, for `Loader(cache, manifest=manifest())`."""
    pinned = sources()
    rows = readCsv(path('manifest.csv'))
    entries = {}
    for row in rows.itertuples(index=False):
        entries[pinned[row.source], row.object] = ManifestRow(row.file, row.sha256)
    return entries


def rows(file: Path | None = None) -> list[Row]:
    """Every row of `registry.csv`, typed; `file` is a `registry.csv` other than the installed
    one."""
    cells = readCsv(file or path('registry.csv'))
    return [Row.parse(record) for record in cells.to_dict('records')]
