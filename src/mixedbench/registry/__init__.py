"""The registry files (ADR 0002): the only way the package and metabeta read them."""

from __future__ import annotations

from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

RegistryFile = Literal[
    'sources.yaml',
    'registry.csv',
    'excluded.csv',
    'dimensions.csv',
    'columns.csv',
    'quantiles.yaml',
    'SUMMARY.md',
]


def path(name: RegistryFile | None = None) -> Path:
    """A registry file, or their directory without a name. Located through the installed
    distribution, not importlib.resources: the editable install keeps its copies in
    site-packages, outside src/ (pyproject's force-include)."""
    dir = Path(distribution('mixedbench').locate_file('mixedbench/registry/files'))
    return dir if name is None else dir / name
