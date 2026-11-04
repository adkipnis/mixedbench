"""members.py defines a suite's members: a problem by its id, from one call.

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
-> the candidates whose axes match                        select
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property
from importlib.metadata import distribution
from pathlib import Path
from typing import Literal, get_args

import pandas as pd
from mixedbench import contract, registry
from mixedbench.contract import FAMILY, Grouping, Problem, contractHash, materialize, storedHash
from mixedbench.registry.row import Row, readCsv, splitList

Version = Literal['1.1']
Tier = Literal['R', 'E', 'T', 'D', 'O']
Fitter = Literal['lme4']  # brms joins once suite 1.1's references freeze
Range = int | tuple[int | None, int | None]


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


def select(
    tier: Tier | list[Tier] | None = None,
    family: str | list[str] | None = None,
    grouping: Grouping | list[Grouping] | None = None,
    q: Range | None = None,
    n: Range | None = None,
    m: Range | None = None,
    d: Range | None = None,
    n_i: Range | None = None,
    fit: Fitter | list[Fitter] | None = None,
) -> pd.DataFrame:
    """Returns the candidates of suite 1.1 whose axes match, one row each, in list order.
    An axis left out matches every candidate.
    - tier: `R` CRAN packages, `E` ecosystem examples, `T` textbook companions,
      `D` data deposits of published papers, `O` open tabular repositories.
    - family: `gaussian`, `bernoulli`, `poisson`, `binomial` or `cumulative`.
    - grouping: how the factors relate, `single`, `nested`, `crossed` or `mixed`.
    - n, d: the rows and the design columns, `Intercept` included.
    - m, q: the groups and the random effects per group, of every factor.
    - n_i: the rows of every group of every factor.
    - fit: `lme4`, whose fit of the documented model ended `ok` or `singular`.
    A count takes an int, matched exactly, or an inclusive `(low, high)` with `None` for an
    open end. A categorical axis takes one value or a list."""
    categories = {'tier': tier, 'family': family, 'grouping': grouping, 'fit': fit}
    listed = {}
    for axis, wanted in categories.items():
        if wanted is not None:
            listed[axis] = _checkValues(axis, wanted)
    candidates = _listCandidates()
    for axis, values in listed.items():
        candidates = [c for c in candidates if _holdsValue(c, axis, values)]
    counts = {'n': n, 'd': d, 'm': m, 'q': q, 'n_i': n_i}
    for axis, wanted in counts.items():
        if wanted is not None:
            candidates = [c for c in candidates if _holdsRange(_listCounts(c, axis), wanted)]
    return pd.DataFrame(candidates, columns=list(AXES))


# ----------------------------------------------------------------------------------------------
# list -> axes -> matches
# ----------------------------------------------------------------------------------------------
AXES = (
    'id', 'tier', 'family', 'grouping', 'n', 'd', 'factors', 'm', 'q', 'n_i_min', 'n_i_max', 'fit',
)  # fmt: skip
VALUES = {
    'tier': get_args(Tier),
    'family': tuple(family for family, _ in FAMILY.values()),
    'grouping': get_args(Grouping),
    'fit': get_args(Fitter),
}
PASSED = ('ok', 'singular')  # lme4's statuses of a converged fit, a singular one at the boundary


def _listCandidates() -> list[dict]:
    """Returns each candidate's axes: its dimensions from the list, its tier and family from its
    registry row, and the fitters that passed."""
    rows = {row.id: row for row in registry.rows()}
    fits = readCsv(registry.path('fits.csv'))
    passed = fits[fits['status'].isin(PASSED)]
    lme4 = set(passed['source'] + '/' + passed['object'] + '/' + passed['model_index'])
    candidates = []
    for listed in readCsv(path('1.1') / 'candidates.csv').to_dict('records'):
        id = listed['id']
        row = rows[id]
        family, _ = FAMILY[row.response_type]
        candidates.append({
            'id': id,
            'tier': row.tier,
            'family': family,
            'grouping': listed['grouping'],
            'n': int(listed['n']),
            'd': int(listed['d']),
            'factors': splitList(listed['factors']),
            'm': _splitCounts(listed['m']),
            'q': _splitCounts(listed['q']),
            'n_i_min': _splitCounts(listed['n_i_min']),
            'n_i_max': _splitCounts(listed['n_i_max']),
            'fit': ('lme4',) if id in lme4 else (),
        })  # fmt: skip
    return candidates


def _splitCounts(cell: str) -> tuple[int, ...]:
    return tuple(int(value) for value in splitList(cell))


def _checkValues(axis: str, wanted: str | list[str]) -> list[str]:
    """Returns the wanted values as a list. Raises on a value the axis does not take."""
    listed = [wanted] if isinstance(wanted, str) else list(wanted)
    for value in listed:
        if value not in VALUES[axis]:
            raise ValueError(f'{axis} {value!r} is none of {", ".join(VALUES[axis])}')
    return listed


def _holdsValue(candidate: dict, axis: str, values: list[str]) -> bool:
    held = candidate[axis] if axis == 'fit' else (candidate[axis],)  # each fitter that passed
    return any(value in values for value in held)


def _listCounts(candidate: dict, axis: str) -> tuple[int, ...]:
    """Returns the values a range must hold: the problem's, each factor's, or the smallest and
    largest group of each factor, between which every group lies."""
    match axis:
        case 'n' | 'd':
            return (candidate[axis],)
        case 'm' | 'q':
            return candidate[axis]
        case 'n_i':
            return candidate['n_i_min'] + candidate['n_i_max']


def _holdsRange(values: tuple[int, ...], wanted: Range) -> bool:
    low, high = (wanted, wanted) if isinstance(wanted, int) else wanted
    above = low is None or min(values) >= low
    below = high is None or max(values) <= high
    return above and below


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
