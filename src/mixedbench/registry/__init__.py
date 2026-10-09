"""The registry files (ADR 0002): the only way the package and metabeta read them."""

from __future__ import annotations

from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from mixedbench.datasets import Manifest, ManifestRow, Source

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
            checksum = entry.get('checksum')
            if entry['kind'] == 'url':  # a URL has no version: the file's sha256 is its pin
                checksum = str(entry['pin'])
            layout = tuple(entry['layout']) if 'layout' in entry else None  # headerless text
            pinned[label] = Source(
                kind=entry['kind'],
                name=entry.get('name', label),
                pin=str(entry['pin']),
                checksum=checksum,
                path=entry.get('path'),
                file=entry.get('file'),
                layout=layout,
                mirror=entry.get('mirror'),
            )
    return pinned


def manifest() -> Manifest:
    """The file every registry object loads from, for `Loader(cache, manifest=manifest())`."""
    pinned = sources()
    rows = pd.read_csv(path('manifest.csv'), dtype=str, keep_default_na=False)
    entries = {}
    for row in rows.itertuples(index=False):
        entries[pinned[row.source], row.object] = ManifestRow(row.file, row.sha256, int(row.size))
    return entries
