"""run.py's U test against scipy's, whose values are hard-coded, since scipy is no dependency.
Run by hand from the repo root:

    uv run pytest experiments/flat/test_run.py
"""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent))  # run.py is a script, not a package module

from run import _testMannWhitney


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
