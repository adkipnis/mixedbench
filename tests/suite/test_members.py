"""A suite's problems by id (#55): `suite.load` builds a problem from its pinned source on first
use, materializes it into the cache and checks its contract hash against the suite's list;
later calls load it from the cache. Every test that loads a problem but the first fetches a
source, so it is marked network.
`suite.select` (#193) picks candidates by their axes from the installed files alone."""

from __future__ import annotations

import socket
from itertools import islice
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from mixedbench import registry, suite
from mixedbench.contract import Problem, contractHash, materialize, storedHash
from mixedbench.registry.row import writeCsv
from mixedbench.suite import members

# suite 1.1's list, copied by hand
SLEEPSTUDY = '78bda46ff3996060104d7ce61de055373415213e38190b5dcc01ffbfd23a4146'
FIRST_TWO = {
    'lme4/Arabidopsis/1': 'fe9e8df45535a2cc32657c4e766e5e5612a86f72efdb28a415940bd49071b428',
    'lme4/Dyestuff/1': '3ca838e00f298712176f7c865ec94a9ef18ad638fc37c251495d2845d0ddb0b7',
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


# ==============================================================================================
# select
# ==============================================================================================
# each row's axes from its source's documentation (lme4's and ordinal's help pages): the rows,
# the design columns with `Intercept` and per factor the groups and their sizes
DYESTUFF = 'lme4/Dyestuff/1'
SLEEPSTUDY_ID = 'lme4/sleepstudy/1'
ARABIDOPSIS = 'lme4/Arabidopsis/1'
WINE = 'ordinal/wine/1'
KNOWN = (DYESTUFF, SLEEPSTUDY_ID, ARABIDOPSIS, WINE)


@pytest.mark.parametrize(
    'id, axes',
    [
        pytest.param(
            DYESTUFF,
            {'tier': 'R', 'family': 'gaussian', 'grouping': 'single', 'n': 30, 'd': 1, 'factors': ('Batch',), 'm': (6,), 'q': (1,), 'n_i_min': (5,), 'n_i_max': (5,), 'fit': ('lme4',)},
            id='Dyestuff: six batches of five yields, intercepts only',
        ),
        pytest.param(
            SLEEPSTUDY_ID,
            {'tier': 'R', 'family': 'gaussian', 'grouping': 'single', 'n': 180, 'd': 2, 'factors': ('Subject',), 'm': (18,), 'q': (2,), 'n_i_min': (10,), 'n_i_max': (10,), 'fit': ('lme4',)},
            id='sleepstudy: ten days of 18 subjects, a slope on Days',
        ),
        pytest.param(
            ARABIDOPSIS,
            {'tier': 'R', 'family': 'poisson', 'grouping': 'nested', 'n': 625, 'd': 7, 'factors': ('popu', 'gen'), 'm': (9, 24), 'q': (1, 1), 'n_i_min': (32, 11), 'n_i_max': (137, 47), 'fit': ('lme4',)},
            id='Arabidopsis: 24 genotypes within 9 populations',
        ),
        pytest.param(
            WINE,
            {'tier': 'R', 'family': 'cumulative', 'grouping': 'single', 'n': 72, 'd': 4, 'factors': ('judge',), 'm': (9,), 'q': (1,), 'n_i_min': (8,), 'n_i_max': (8,), 'fit': ()},
            id='wine: nine judges, an ordinal rating lme4 does not fit',
        ),
    ],
)  # fmt: skip
def test_select_without_axes_lists_each_candidate_with_its_axes(id: str, axes: dict) -> None:
    selected = suite.select()
    [row] = selected[selected['id'] == id].to_dict('records')
    assert row == {'id': id} | axes


@pytest.mark.parametrize(
    'axes, kept',
    [
        pytest.param({'q': 1}, {DYESTUFF, ARABIDOPSIS, WINE}, id='an int matches exactly'),
        pytest.param({'n': np.int64(30)}, {DYESTUFF}, id='a numpy int matches as an int'),
        pytest.param({'n': (100, None)}, {SLEEPSTUDY_ID, ARABIDOPSIS}, id='a range with an open end'),
        pytest.param({'d': (2, 4)}, {SLEEPSTUDY_ID, WINE}, id='a range includes both ends'),
        pytest.param({'family': ['gaussian', 'cumulative']}, {DYESTUFF, SLEEPSTUDY_ID, WINE}, id='a list of values'),
        pytest.param({'m': (10, None)}, {SLEEPSTUDY_ID}, id='every factor: popu has 9 groups, gen 24'),
        pytest.param({'n_i': (None, 8)}, {DYESTUFF, WINE}, id='every group: none of sleepstudy has fewer than 10'),
        pytest.param({'grouping': 'nested', 'tier': 'R'}, {ARABIDOPSIS}, id='two axes together'),
        pytest.param({'fit': 'lme4'}, {DYESTUFF, SLEEPSTUDY_ID, ARABIDOPSIS}, id='lme4 fits no ordinal model'),
    ],
)  # fmt: skip
def test_select_keeps_the_known_rows_whose_axes_match(axes: dict, kept: set[str]) -> None:
    selected = suite.select(**axes)
    assert set(selected['id']) & set(KNOWN) == kept


@pytest.mark.parametrize(
    'axes, message',
    [
        pytest.param({'grouping': 'simple'}, "grouping 'simple' is none of single, nested, crossed, mixed", id='a misspelled value, named with the values'),
        pytest.param({'n': (100, 10)}, r'n \(100, 10\) is a reversed range', id='a reversed range'),
    ],
)  # fmt: skip
def test_select_raises_where_it_would_select_nothing_without_a_word(
    axes: dict, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        suite.select(**axes)


def test_select_takes_its_axes_by_name_only() -> None:
    """By position, `select('R', 'gaussian', 'single', 1)` would set `n` to 1, not `q`."""
    with pytest.raises(TypeError):
        suite.select('R')
