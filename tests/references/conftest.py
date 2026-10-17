"""The fixture problem of the references tests: gaussian, one random intercept on `block`, a
continuous `x` and a binary `sex`. Every group holds the same ten design rows, so least squares
and the mixed model's generalized least squares give the same fixed effects."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from mixedbench.contract import Problem
from mixedbench.registry.row import Row, SlopeTerm

GROUPS = 20
X = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SEX = [0, 0, 1, 0, 1, 0, 0, 1, 0, 1]  # f = 0, m = 1, a share of 0.4
ROW = Row(
    source='fixture', tier='R', sources=('fixture:trial',), object='trial', reader='pandas',
    license='MIT', model_index=1, response='y', response_type='continuous', trials='', family='',
    grouping_factors=('block',), covariates=('x', 'sex'), interactions=(), random_slopes=(),
    ignore=(), types={}, formula='y ~ x + sex + (1 | block)', documented_prior='',
    published_model='yes', domain='test', confidence='high', verified='hand', notes='',
)  # fmt: skip


def fixtureProblem(row: Row = ROW) -> Problem:
    rng = np.random.default_rng(1)
    block = np.repeat([f'b{j:02d}' for j in range(GROUPS)], len(X))
    x = np.tile(X, GROUPS)
    sex = np.tile(SEX, GROUPS)
    intercepts = rng.normal(0, 0.5, GROUPS).repeat(len(X))
    y = 1 + 0.5 * x + 2 * sex + intercepts + rng.normal(0, 1, len(x))
    table = pd.DataFrame({'block': block, 'x': x, 'sex': np.array(['f', 'm'])[sex], 'y': y})
    return Problem.build(row, table)


@pytest.fixture(scope='session')
def rstack() -> None:
    """Skips a `brms` test where R or CmdStan is absent (CI's runners have R, not cmdstanr)."""
    rscript = shutil.which('Rscript')
    if rscript is None:
        pytest.skip('no Rscript')
    probe = subprocess.run([rscript, '-e', 'cmdstanr::cmdstan_version()'], capture_output=True)
    if probe.returncode != 0:
        pytest.skip('no cmdstanr or CmdStan')


# ==============================================================================================
# the shapes of #63's fixtures
# ==============================================================================================
# a problem per model shape, which the real-R tests fit.
# `fixtures/` holds brms's draws of each but `binomialTrials`.
# a problem keeps its fixture's columns, factors and group counts, so brms's labels name its aliases


def gaussianMixed() -> Problem:
    """Two correlated slopes and an uncorrelated one on `school`, 12 groups of 15 rows:
    `dose`, `sex` and `age` are aliased `x1`, `x2` and `x3`, `school` is `g1`."""
    rng = np.random.default_rng(1)
    school = np.repeat(np.arange(12), 15)
    dose = rng.normal(2, 1, len(school))
    sex = rng.binomial(1, 0.3, len(school))
    age = rng.normal(-1, 1, len(school))
    u = rng.normal(0, 1, (12, 4))[school]  # (N, 4)
    y = 1 + u[:, 0] + (0.5 + u[:, 1]) * dose + (-0.3 + u[:, 2]) * sex + (0.2 + u[:, 3]) * age
    table = pd.DataFrame({
        'school': [f's{j:02d}' for j in school], 'dose': dose, 'sex': np.array(['f', 'm'])[sex],
        'age': age, 'y': y + rng.normal(0, 1, len(school)),
    })  # fmt: skip
    slopes = (
        SlopeTerm('dose', 'school', correlated=True),
        SlopeTerm('sex', 'school', correlated=True),
        SlopeTerm('age', 'school', correlated=False),
    )
    row = replace(
        ROW, object='gaussian_mixed', grouping_factors=('school',),
        covariates=('dose', 'sex', 'age'), random_slopes=slopes,
        formula='y ~ dose + sex + age + (1 + dose + sex | school) + (0 + age || school)',
    )  # fmt: skip
    return Problem.build(row, table)


def binomialTrials() -> Problem:
    """`deaths` of `animals` with a correlated slope on `dose` per `farm`, 8 groups of 12 rows."""
    rng = np.random.default_rng(3)
    farm = np.repeat(np.arange(8), 12)
    dose = rng.normal(0, 1, len(farm))
    animals = rng.integers(5, 21, len(farm))
    eta = -0.5 + 0.6 * dose + rng.normal(0, 0.5, 8)[farm]
    deaths = rng.binomial(animals, 1 / (1 + np.exp(-eta)))
    table = pd.DataFrame({
        'farm': [f'f{j}' for j in farm], 'dose': dose, 'animals': animals, 'deaths': deaths,
    })  # fmt: skip
    row = replace(
        ROW, object='binomial_trials', response='deaths', response_type='binomial',
        trials='animals', grouping_factors=('farm',), covariates=('dose',),
        random_slopes=(SlopeTerm('dose', 'farm', correlated=True),),
        formula='deaths | trials(animals) ~ dose + (1 + dose | farm)',
    )  # fmt: skip
    return Problem.build(row, table)


def ordinalProblem() -> Problem:
    """A `rating` of 4 categories per `judge`, 10 groups of 20 rows: thresholds `Intercept[1]`
    to `Intercept[3]`."""
    rng = np.random.default_rng(2)
    judge = np.repeat(np.arange(10), 20)
    x = rng.normal(0, 1, len(judge))
    eta = 0.8 * x + rng.normal(0, 0.7, 10)[judge] + rng.logistic(0, 1, len(judge))
    rating = np.digitize(eta, [-1, 0, 1.2]) + 1
    table = pd.DataFrame({'judge': [f'j{j}' for j in judge], 'x': x, 'rating': rating})
    row = replace(
        ROW, object='ordinal', response='rating', response_type='ordinal',
        grouping_factors=('judge',), covariates=('x',), formula='rating ~ x + (1 | judge)',
    )  # fmt: skip
    return Problem.build(row, table)


def nestedProblem(blocks: int = 6) -> Problem:
    """A poisson count with the factors `block` and the composite `block:plot` of 3 plots per
    block (6 and 18 groups by default), aliased `g1` and `g2`."""
    rng = np.random.default_rng(4)
    block = np.repeat(np.arange(blocks), 18)
    plot = np.tile(np.repeat(np.arange(3), 6), blocks)
    x = rng.normal(0, 1, len(block))
    effects = rng.normal(0, 0.8, blocks)[block] + rng.normal(0, 0.5, 3 * blocks)[3 * block + plot]
    eta = 0.5 + 0.3 * x + effects
    table = pd.DataFrame({
        'block': [f'b{j}' for j in block], 'plot': [f'p{k}' for k in plot], 'x': x,
        'y': rng.poisson(np.exp(eta)),
    })  # fmt: skip
    row = replace(
        ROW, object='nested', response_type='count', grouping_factors=('block', 'block:plot'),
        covariates=('x',), formula='y ~ x + (1 | block) + (1 | block:plot)',
    )  # fmt: skip
    return Problem.build(row, table)


def manyGroups(groups: int = 1001) -> Problem:
    """A binary response per `subject`, 3 rows each: above 1,000 groups by default."""
    rng = np.random.default_rng(6)
    subject = np.repeat(np.arange(groups), 3)
    x = rng.normal(0, 1, len(subject))
    eta = 0.2 + 0.5 * x + rng.normal(0, 0.5, groups)[subject]
    table = pd.DataFrame({
        'subject': [f'{j:04d}' for j in subject], 'x': x,
        'y': rng.binomial(1, 1 / (1 + np.exp(-eta))),
    })  # fmt: skip
    row = replace(
        ROW, object='many_groups', response_type='binary', grouping_factors=('subject',),
        covariates=('x',), formula='y ~ x + (1 | subject)',
    )  # fmt: skip
    return Problem.build(row, table)
