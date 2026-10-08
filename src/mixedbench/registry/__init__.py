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
            pinned[label] = Source(
                kind=entry['kind'],
                name=entry.get('name', label),
                pin=str(entry['pin']),
                checksum=entry.get('checksum'),
                path=entry.get('path'),
                file=entry.get('file'),
                layout=_layout(entry),
            )
    return pinned


def _layout(entry: dict) -> tuple[str, ...] | None:
    """The columns of a headerless text file, as the frame lists them."""
    if 'layout' not in entry:
        return None
    return tuple(entry['layout'])


def manifest() -> Manifest:
    """The file every registry object loads from, for `Loader(cache, manifest=manifest())`."""
    pinned = sources()
    rows = pd.read_csv(path('manifest.csv'), dtype=str, keep_default_na=False)
    entries = {}
    for row in rows.itertuples(index=False):
        sha256 = row.sha256 or None  # empty for base R's objects, which R dumps
        size = int(row.size) if row.size else None
        entries[pinned[row.source], row.object] = ManifestRow(row.file, sha256, size)
    return entries
