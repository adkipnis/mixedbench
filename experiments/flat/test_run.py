"""Checks run.py's U test against scipy, whose values are hard-coded since scipy is no dependency,
and which flat tables the response's tests take. Run by hand from the repo root:

    uv run pytest experiments/flat/test_run.py
"""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent))  # run.py is a script, not a package module

from run import RESPONSE_STATISTICS, STATISTICS, _testMannWhitney, compareSamples


@pytest.mark.parametrize(
    ('x', 'y', 'u', 'p'),
    [
        pytest.param(
            [1.0, 2.0, 2.0, 3.0, 5.0, 8.0],
            [2.0, 3.0, 3.0, 4.0, 6.0, 7.0, 9.0],
            13.0,
            0.2786308216420915,
            id='ties within and across the samples',
        ),
        pytest.param(
            [1.0, 2.0, math.inf, math.inf],
            [0.5, 2.0, 3.0, 4.0, 4.0],
            12.5,
            0.619796388494133,
            id='inf ranks above every finite value',
        ),
    ],
)
def test_the_u_test_is_scipys_asymptotic_one(x, y, u, p):
    """The values are scipy 1.16.2's `mannwhitneyu(x, y, method='asymptotic')`, two-sided with
    the continuity correction."""
    tested = _testMannWhitney(pd.Series(x), pd.Series(y))
    assert tested['U'] == u
    assert tested['p'] == pytest.approx(p, rel=1e-12)


def summary(offset: float, **columns: list) -> pd.DataFrame:
    """A summary table, one row per value of `columns`, whose every statistic counts up from
    `offset`, so that no test sees only ties."""
    n = len(next(iter(columns.values())))
    counted = {s: [offset + i for i in range(n)] for s in (*STATISTICS, *RESPONSE_STATISTICS)}
    return pd.DataFrame(counted | columns)


def test_the_response_is_compared_only_against_the_flat_tables_that_name_one():
    """A flat table without a response has no response statistics or type, so the response's
    tests run on the `response` side alone. For a 0/1 type indicator, the rank-biserial r is
    the registry's share minus the flat one's: 1/6 binary against 1/2."""
    types = ['continuous', 'binary', 'count', 'binomial', 'ordinal', 'categorical']
    registry = summary(0.0, response_type=types)
    flat = summary(0.5, response=['y', 'z', 'none'], response_type=['binary', 'count', ''])
    flat.loc[2, list(RESPONSE_STATISTICS)] = math.nan

    tests = compareSamples(registry, flat)

    responses = tests[tests['statistic'].str.startswith('response_')]
    assert set(responses['flat']) == {'response'}
    binary = responses[responses['statistic'] == 'response_binary_share'].iloc[0]
    assert (binary['n_registry'], binary['n_flat']) == (6, 2)
    assert binary['rank_biserial'] == pytest.approx(1 / 6 - 1 / 2)
