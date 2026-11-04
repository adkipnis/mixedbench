"""The registry's tests read a row of the installed registry by its id."""

from __future__ import annotations

from mixedbench import registry
from mixedbench.registry.row import Row


def installedRow(id: str) -> Row:
    [row] = [row for row in registry.rows() if row.id == id]
    return row
