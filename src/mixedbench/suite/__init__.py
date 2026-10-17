"""__init__.py defines mixedbench's suites: a problem by its id, from one call.

A suite's list holds the contract hash of each of its problems.
On first use a problem is built from its pinned source and materialized into the cache,
where later calls find it; files written by another contract are rebuilt the same way.
A problem that builds to a hash off the list raises: its source or the code moved.

pipeline:
---------
a problem id
-> its contract hash on the suite's list                  _Suite.hashes
-> its files in the cache, built where stale or missing   _Suite._build
-> the problem read from them                             load
-> every problem of a suite, one at a time in list order  problems
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

from mixedbench import contract, registry
from mixedbench.contract import Problem, contractHash, materialize, storedHash
from mixedbench.registry.row import Row, readCsv

__all__ = ['Version', 'load', 'path', 'problems']

Version = Literal['1.1']


def path(version: Version) -> Path:
    # through the installed distribution, as the registry files (pyproject's force-include)
    return Path(distribution('mixedbench').locate_file(f'mixedbench/suite/files/{version}'))


def load(id: str, cache: Path) -> Problem:
    return _Suite('1.1', cache).load(id)


def problems(version: Version, cache: Path) -> Iterator[tuple[str, Problem]]:
    """Each problem is built on first use, so a first pass fetches every source."""
    suite = _Suite(version, cache)
    for id in suite.hashes:
        yield id, suite.load(id)


class _Suite:
    def __init__(self, version: Version, cache: Path) -> None:
        self.version = version
        self.cache = Path(cache)

    def load(self, id: str) -> Problem:
        if id not in self.hashes:
            raise KeyError(f'{id} is not in suite {self.version}')
        if storedHash(id, self.cache) != self.hashes[id]:
            self._build(id)
        return contract.load(id, self.cache)

    @cached_property
    def hashes(self) -> dict[str, str]:
        listed = readCsv(path(self.version) / 'candidates.csv')
        return dict(zip(listed['id'], listed['contract_hash']))

    # ------------------------------------------------------------------------------------------
    # id -> row -> table -> problem -> files
    # ------------------------------------------------------------------------------------------

    @cached_property
    def _rows(self) -> dict[str, Row]:
        return {row.id: row for row in registry.rows()}

    @cached_property
    def _tables(self) -> registry.Tables:
        # one loader for the whole suite: it parses each source once
        return registry.Tables(self.cache)

    def _build(self, id: str) -> None:
        """Checked before it is written, so the cache never holds a problem off the list."""
        row = self._rows[id]
        problem = Problem.build(row, self._tables.load(row))
        built = contractHash(problem)
        if built != self.hashes[id]:
            raise ValueError(
                f'{id} builds to contract hash {built}, suite {self.version} lists '
                f'{self.hashes[id]}: its source or the code moved'
            )
        materialize(problem, self.cache)
