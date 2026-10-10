"""The fixture problem of the references tests: gaussian, one random intercept on `block`, a
continuous `x` and a binary `sex`. Every group holds the same ten design rows, so least squares
and the mixed model's generalised least squares give the same fixed effects."""

from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest
from mixedbench.contract import Problem
from mixedbench.registry.row import Row

GROUPS = 20
X = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SEX = [0, 0, 1, 0, 1, 0, 0, 1, 0, 1]  # f = 0, m = 1, a share of 0.4
ROW = Row(
    source='fixture', tier='R', sources=('fixture:trial',), object='trial', reader='pandas',
    licence='MIT', model_index=1, response='y', response_type='continuous', trials='', family='',
    grouping_factors=('block',), covariates=('x', 'sex'), interactions=(), random_slopes=(),
    ignore=(), types={}, formula='y ~ x + sex + (1 | block)', documented_prior='',
    published_model='yes', domain='test', confidence='high', verified='hand', notes='',
)  # fmt: skip


@pytest.fixture
def problem() -> Problem:
    return fixtureProblem()


def fixtureProblem() -> Problem:
    rng = np.random.default_rng(1)
    block = np.repeat([f'b{j:02d}' for j in range(GROUPS)], len(X))
    x = np.tile(X, GROUPS)
    sex = np.tile(SEX, GROUPS)
    intercepts = rng.normal(0, 0.5, GROUPS).repeat(len(X))
    y = 1 + 0.5 * x + 2 * sex + intercepts + rng.normal(0, 1, len(x))
    table = pd.DataFrame({'block': block, 'x': x, 'sex': np.array(['f', 'm'])[sex], 'y': y})
    return Problem.build(ROW, table)


@pytest.fixture(scope='session')
def rstack() -> None:
    """Skips a `brms` test where R or CmdStan is absent (CI's runners have R, not cmdstanr)."""
    rscript = shutil.which('Rscript')
    if rscript is None:
        pytest.skip('no Rscript')
    probe = subprocess.run([rscript, '-e', 'cmdstanr::cmdstan_version()'], capture_output=True)
    if probe.returncode != 0:
        pytest.skip('no cmdstanr or CmdStan')
