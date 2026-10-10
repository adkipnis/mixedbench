"""The handoff between Python and R (#65), offline: what `Handoff.write` gives the R script for a
level, and what `Handoff.read` makes of the RDS files brms's run left, recorded by #63."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pyreadr
from mixedbench.contract import Problem
from mixedbench.references.handoff import Handoff

from .conftest import ROW


def test_the_table_reaches_r_standardised_under_aliases_without_the_intercept(
    problem: Problem, tmp_path: Path
) -> None:
    """brms rewrites names such as `x[level]` or `a:b`, so R sees only safe aliases; group
    values are the codes, so a brms label names its code. The CSV round-trips every float."""
    Handoff(problem).write(tmp_path, level=0)
    table = pd.read_csv(tmp_path / 'table.csv')
    aliases = {'y': 'y', 'x1': 'x', 'x2': 'sex', 'g1': 'block'}
    expected = problem.standardised('full')[list(aliases.values())]
    expected.columns = list(aliases)
    pd.testing.assert_frame_equal(table, expected.reset_index(drop=True), check_dtype=False)
    assert table['g1'].dtype == 'int64'


def test_the_model_reaches_r_as_formula_family_prior_settings_and_seed(
    problem: Problem, tmp_path: Path
) -> None:
    """Level 0 of the ladder, four chains in parallel; the seed is the first 4 bytes of sha256
    of `fixture/trial/1`, modulo 2³¹."""
    Handoff(problem).write(tmp_path, level=0)
    model = json.loads((tmp_path / 'input.json').read_text())
    assert model == {
        'formula': 'y ~ 1 + x1 + x2 + (1 | g1)',
        'family': 'gaussian',
        'link': 'identity',
        'prior': {
            'Intercept': 'normal(0, 2.5)',
            'b': 'normal(0, 2.5)',
            'sd': 'student_t(3, 0, 2.5)',
            'sigma': 'student_t(3, 0, 2.5)',
        },
        'settings': {
            'chains': 4,
            'cores': 4,
            'warmup': 1000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.8,
            'max_treedepth': 10,
        },
        'seed': 75704431,
    }


# ==============================================================================================
# read
# ==============================================================================================

FIXTURES = Path(__file__).parent / 'fixtures'


def nestedProblem() -> Problem:
    """The problem behind #63's `nested` fixture: a poisson count, `x`, and the factors `block`
    and the composite `block:plot`, aliased `x1`, `g1` and `g2`."""
    row = replace(
        ROW,
        response_type='count',
        grouping_factors=('block', 'block:plot'),
        covariates=('x',),
        formula='y ~ x + (1 | block) + (1 | block:plot)',
    )
    table = pd.DataFrame(
        {
            'block': ['A'] * 4 + ['B'] * 4,
            'plot': ['p1', 'p1', 'p2', 'p2'] * 2,
            'x': [0.5, 1.0, -1.0, 2.0, 0.0, 1.5, -0.5, 1.0],
            'y': [1, 0, 3, 2, 4, 1, 0, 2],
        }
    )
    return Problem.build(row, table)


def test_brms_draws_read_back_under_the_contracts_global_names_in_order() -> None:
    """Renamed by brms's label, never by position: `sd_g2__Intercept` is the composite's `sd`.
    `chain` and `draw` count from 0, `draw` within its chain."""
    draws = Handoff(nestedProblem()).read(FIXTURES / 'nested')
    raw = pyreadr.read_r(FIXTURES / 'nested' / 'draws.rds')[None]
    assert list(draws.columns) == [
        'chain',
        'draw',
        'Intercept',
        'x',
        'sd[block]',
        'sd[block:plot]',
    ]
    assert draws['chain'].tolist() == (raw['chain'] - 1).tolist()
    assert draws['draw'].tolist() == (raw['iteration'] - 1).tolist()
    assert sorted(set(draws['chain'])) == [0, 1, 2, 3]
    assert draws['Intercept'].tolist() == raw['b_Intercept'].tolist()
    assert draws['sd[block:plot]'].tolist() == raw['sd_g2__Intercept'].tolist()
    assert (draws.dtypes.iloc[2:] == 'float64').all()
