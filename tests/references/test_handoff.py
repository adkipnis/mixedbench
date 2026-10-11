"""The handoff between Python and R (#65), offline: what `Handoff.write` gives the R script for a
level, and what `Handoff.read` makes of the RDS files brms's run left, recorded by #63."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
from mixedbench.contract import Problem
from mixedbench.references.handoff import Handoff
from mixedbench.registry.row import SlopeTerm

from .conftest import (
    ROW,
    binomialTrials,
    gaussianMixed,
    manyGroups,
    nestedProblem,
    ordinalProblem,
)


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
        'summarised': [],
    }


def test_each_level_reaches_r_with_its_settings_and_the_same_seed(
    problem: Problem, tmp_path: Path
) -> None:
    """ADR 0004's ladder: level 1 warms up longer at a higher adapt_delta, and level 2 also
    deepens the trees and samples 2,000 draws per chain thinned by 2, so every level stores
    4,000 draws."""
    settings = {}
    seeds = set()
    for level in (1, 2):
        Handoff(problem).write(tmp_path, level=level)
        model = json.loads((tmp_path / 'input.json').read_text())
        settings[level] = model['settings']
        seeds.add(model['seed'])
    assert settings == {
        1: {
            'chains': 4,
            'cores': 4,
            'warmup': 2000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.9,
            'max_treedepth': 10,
        },
        2: {
            'chains': 4,
            'cores': 4,
            'warmup': 4000,
            'draws': 2000,
            'thin': 2,
            'adapt_delta': 0.99,
            'max_treedepth': 12,
        },
    }
    assert seeds == {75704431}


def test_a_binomial_response_reaches_r_with_its_trials(tmp_path: Path) -> None:
    """brms reads a binomial's trials from the formula, `y | trials(n)`, with `n` aliased."""
    handoff = Handoff(binomialTrials())
    handoff.write(tmp_path, level=0)
    model = json.loads((tmp_path / 'input.json').read_text())
    table = pd.read_csv(tmp_path / 'table.csv')
    assert model['formula'] == 'y | trials(n) ~ 1 + x1 + (1 + x1 | g1)'
    assert handoff.aliases == {'y': 'deaths', 'n': 'animals', 'x1': 'dose', 'g1': 'farm'}
    assert list(table.columns) == ['y', 'n', 'x1', 'g1']


def test_uncorrelated_slopes_take_their_own_term_beside_the_correlated_ones(
    tmp_path: Path,
) -> None:
    """`||` keeps `age`'s slope independent of the intercept and of the other slopes on
    `school`; the correlated ones share the intercept's term."""
    Handoff(gaussianMixed()).write(tmp_path, level=0)
    model = json.loads((tmp_path / 'input.json').read_text())
    assert model['formula'] == 'y ~ 1 + x1 + x2 + x3 + (1 + x1 + x2 | g1) + (0 + x3 || g1)'


def test_a_slope_on_a_categorical_covariate_takes_all_its_contrast_columns(
    tmp_path: Path,
) -> None:
    """`diet` of three levels is coded `diet[b]` and `diet[c]`, aliased `x1` and `x2`."""
    table = pd.DataFrame(
        {'block': ['A', 'B'] * 6, 'diet': ['a', 'b', 'c'] * 4, 'y': np.arange(12.0)}
    )
    for bars, term in (('|', '(1 + x1 + x2 | g1)'), ('||', '(1 | g1) + (0 + x1 + x2 || g1)')):
        row = replace(
            ROW,
            covariates=('diet',),
            random_slopes=(SlopeTerm.parse(f'diet{bars}block'),),
            formula=f'y ~ diet + (1 + diet {bars} block)',
        )
        Handoff(Problem.build(row, table)).write(tmp_path, level=0)
        model = json.loads((tmp_path / 'input.json').read_text())
        assert model['formula'] == f'y ~ 1 + x1 + x2 + {term}'


def test_an_ordinal_models_thresholds_take_brms_default_prior(tmp_path: Path) -> None:
    """The contract states no threshold prior, so no `Intercept` class reaches brms."""
    Handoff(ordinalProblem()).write(tmp_path, level=0)
    model = json.loads((tmp_path / 'input.json').read_text())
    assert model['formula'] == 'y ~ 1 + x1 + (1 | g1)'
    assert (model['family'], model['link']) == ('cumulative', 'logit')
    assert list(model['prior']) == ['b', 'sd']


def test_r_summarises_the_random_effects_of_a_factor_above_1000_groups(tmp_path: Path) -> None:
    """Full draws of 20,000 groups would be a file of gigabytes, so R keeps per-effect
    summaries of such a factor instead; 1,000 groups still keep their draws."""
    for groups, summarised in ((1000, []), (1001, ['g1'])):
        Handoff(manyGroups(groups)).write(tmp_path, level=0)
        model = json.loads((tmp_path / 'input.json').read_text())
        assert model['summarised'] == summarised


# ==============================================================================================
# read
# ==============================================================================================

FIXTURES = Path(__file__).parent / 'fixtures'


def test_brms_draws_read_back_under_the_contracts_global_names_in_order() -> None:
    """Renamed by brms's label, never by position: `sd_g2__Intercept` is the composite's `sd`.
    `chain` and `draw` count from 0, `draw` within its chain."""
    draws = Handoff(nestedProblem()).read(FIXTURES / 'nested')['globals']
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


def test_slopes_and_correlation_pairs_read_back_by_brms_label() -> None:
    """`sd_g1__x3` is `age`'s uncorrelated slope, and `cor_g1__x1__x2` the pair of `dose` and
    `sex`, wherever brms puts them; `age` has no correlation."""
    draws = Handoff(gaussianMixed()).read(FIXTURES / 'gaussian_mixed')['globals']
    raw = pyreadr.read_r(FIXTURES / 'gaussian_mixed' / 'draws.rds')[None]
    assert list(draws.columns) == [
        'chain',
        'draw',
        'Intercept',
        'dose',
        'sex',
        'age',
        'sd[school]',
        'sd[dose|school]',
        'sd[sex|school]',
        'sd[age|school]',
        'cor[school][Intercept,dose]',
        'cor[school][Intercept,sex]',
        'cor[school][dose,sex]',
        'sigma',
    ]
    assert draws['sd[age|school]'].tolist() == raw['sd_g1__x3'].tolist()
    assert draws['cor[school][Intercept,sex]'].tolist() == raw['cor_g1__Intercept__x2'].tolist()
    assert draws['cor[school][dose,sex]'].tolist() == raw['cor_g1__x1__x2'].tolist()


def test_ordinal_thresholds_read_back_as_intercept_k() -> None:
    """brms names a threshold `b_Intercept[k]`; the contract drops the `b_` as for every fixed
    effect, so the thresholds lead the global draws in `k`'s order."""
    draws = Handoff(ordinalProblem()).read(FIXTURES / 'ordinal')['globals']
    raw = pyreadr.read_r(FIXTURES / 'ordinal' / 'draws.rds')[None]
    assert list(draws.columns) == [
        'chain',
        'draw',
        'Intercept[1]',
        'Intercept[2]',
        'Intercept[3]',
        'x',
        'sd[judge]',
    ]
    assert draws['Intercept[2]'].tolist() == raw['b_Intercept[2]'].tolist()


def test_random_effects_read_back_by_brms_label_in_factor_slope_and_group_order() -> None:
    """`r_g1[7,x3]` is the seventh school's `age` slope; a factor of at most 1,000 groups keeps
    its full draws, so `locals` holds every factor and no summary is written."""
    files = Handoff(gaussianMixed()).read(FIXTURES / 'gaussian_mixed')
    raw = pyreadr.read_r(FIXTURES / 'gaussian_mixed' / 'draws.rds')[None]
    effects = ['school', 'dose|school', 'sex|school', 'age|school']
    assert list(files) == ['globals', 'locals']
    assert list(files['locals'].columns) == [
        'chain',
        'draw',
        *[f'r[{effect}][{j}]' for effect in effects for j in range(12)],
    ]
    assert files['locals']['r[age|school][7]'].tolist() == raw['r_g1[7,x3]'].tolist()
    assert files['locals']['chain'].tolist() == files['globals']['chain'].tolist()


def test_the_random_effects_of_nested_factors_follow_factor_order() -> None:
    """The composite `block:plot` is aliased `g2`, so `r_g2[10,Intercept]` is its group 10."""
    draws = Handoff(nestedProblem()).read(FIXTURES / 'nested')['locals']
    raw = pyreadr.read_r(FIXTURES / 'nested' / 'draws.rds')[None]
    assert list(draws.columns) == [
        'chain',
        'draw',
        *[f'r[block][{j}]' for j in range(6)],
        *[f'r[block:plot][{j}]' for j in range(18)],
    ]
    assert draws['r[block:plot][10]'].tolist() == raw['r_g2[10,Intercept]'].tolist()


def test_a_factor_above_1000_groups_reads_back_as_summaries_without_draws() -> None:
    """Recorded by `run.R` from `Handoff.write` of `manyGroups()`, at 100 warmup and 10 draws
    per chain: `subject`'s 1,001 groups reach Python as summaries only, so no `locals` file."""
    files = Handoff(manyGroups()).read(FIXTURES / 'many_groups')
    raw = pyreadr.read_r(FIXTURES / 'many_groups' / 'locals_summary.rds')[None]
    summary = files['locals_summary']
    assert list(files) == ['globals', 'locals_summary']
    assert list(summary.columns) == ['name', 'mean', 'sd', 'q5', 'q25', 'q50', 'q75', 'q95']
    assert summary['name'].tolist() == [f'r[subject][{j}]' for j in range(1001)]
    row = raw.set_index('variable').loc['r_g1[1000,Intercept]']
    assert summary.iloc[1000, 1:].tolist() == row.tolist()
