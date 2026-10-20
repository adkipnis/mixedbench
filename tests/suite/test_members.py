"""A suite's problems by id (#55): `suite.load` builds a problem from its pinned source on first
use, materializes it into the cache and checks its contract hash against the suite's list;
later calls load it from the cache. Every test but the first fetches a source, so it is marked
network."""

from __future__ import annotations

import socket
from itertools import islice
from pathlib import Path

import pandas as pd
import pytest
from mixedbench import registry, suite
from mixedbench.contract import Problem, contractHash, materialize, storedHash
from mixedbench.registry.row import writeCsv
from mixedbench.suite import members

# suite 1.1's list, copied by hand
SLEEPSTUDY = '7c77c1a9c2623025fad02d74c1f5748965c5985b6e97b269954ce486e2eac839'
FIRST_TWO = {
    'lme4/Arabidopsis/1': 'e4b739ba7c610a3449b827cfc3d57eb0f2f4e68810bf7bcbacacae39ee8d87bd',
    'lme4/Dyestuff/1': 'b0d0cdcf43ab380b83c3de47ac195cf7e65df8c948ba0b757467d9ef23025ce0',
}


def refuseNetwork(*args: object, **kwargs: object) -> socket.socket:
    raise AssertionError('load opened a socket')


def test_an_id_outside_the_suite_raises_naming_it(tmp_path: Path) -> None:
    with pytest.raises(KeyError, match='lme4/sleepstudy/9'):
        suite.load('lme4/sleepstudy/9', tmp_path)


@pytest.mark.network
def test_a_problem_builds_to_its_listed_hash_then_loads_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first call fetches lme4 and builds; the second needs the cache alone."""
    built = suite.load('lme4/sleepstudy/1', tmp_path)
    monkeypatch.setattr(socket, 'socket', refuseNetwork)
    cached = suite.load('lme4/sleepstudy/1', tmp_path)
    assert contractHash(built) == contractHash(cached) == SLEEPSTUDY


@pytest.mark.network
def test_files_written_with_another_hash_are_rebuilt(tmp_path: Path) -> None:
    """Files an older contract wrote under the same id, here from a table one row short,
    are rebuilt from the pin rather than refused."""
    [row] = [row for row in registry.rows() if row.id == 'lme4/sleepstudy/1']
    table = registry.Tables(tmp_path).load(row)
    materialize(Problem.build(row, table.iloc[:-1]), tmp_path)
    assert storedHash('lme4/sleepstudy/1', tmp_path) != SLEEPSTUDY
    problem = suite.load('lme4/sleepstudy/1', tmp_path)
    assert contractHash(problem) == SLEEPSTUDY


@pytest.mark.network
def test_a_suites_problems_come_one_at_a_time_in_list_order(tmp_path: Path) -> None:
    """Lazily: taking the first two fetches lme4 alone, not the suite's few GB."""
    problems = suite.problems('1.1', tmp_path)
    first = {id: contractHash(problem) for id, problem in islice(problems, 2)}
    assert list(first.items()) == list(FIRST_TWO.items())


@pytest.mark.network
def test_a_problem_that_builds_off_its_listed_hash_raises_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where the source or the code moved: here the list moves instead, to a hash no build gives."""
    listed = tmp_path / 'list'
    listed.mkdir()
    moved = pd.DataFrame({'id': ['lme4/sleepstudy/1'], 'contract_hash': ['0' * 64]})
    writeCsv(moved, listed / 'candidates.csv')

    def movedList(version: suite.Version) -> Path:
        return listed

    monkeypatch.setattr(members, 'path', movedList)
    with pytest.raises(ValueError, match='lme4/sleepstudy/1 builds to contract hash'):
        suite.load('lme4/sleepstudy/1', tmp_path)
    assert storedHash('lme4/sleepstudy/1', tmp_path) is None
