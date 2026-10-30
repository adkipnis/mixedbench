"""The handoff between Python and R, offline (#65).
`Handoff.write` gives the R script a level's table and model.
`Handoff.read` and `Handoff.diagnostics` read what R left, from RDS files of recorded runs (#63)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
from mixedbench.contract import Problem
from mixedbench.references import LEVELS
from mixedbench.references.handoff import Handoff
from mixedbench.registry.row import SlopeTerm

from .conftest import (
    ROW,
    binomialTrials,
    fixtureProblem,
    gaussianSlopes,
    manyGroups,
    nestedProblem,
    ordinalProblem,
)


def writtenModel(problem: Problem, dir: Path, settings: dict = LEVELS[0]) -> dict:
    """`input.json` as `Handoff.write` leaves it for R."""
    Handoff(problem).write(dir, settings)
    return json.loads((dir / 'input.json').read_text())


# ==============================================================================================
# write
# ==============================================================================================


def test_the_table_reaches_r_standardized_under_aliases_without_the_intercept(
    tmp_path: Path,
) -> None:
    """brms would read the interaction `x:sex` as its own term, so R sees aliases.
    A group's value is its code, so brms's label names the code.
    The CSV round-trips every float."""
    row = replace(ROW, interactions=('x:sex',), formula='y ~ x * sex + (1 | block)')
    problem = fixtureProblem(row)
    Handoff(problem).write(tmp_path, LEVELS[0])
    table = pd.read_csv(tmp_path / 'table.csv')
    aliases = {'y': 'y', 'x1': 'x', 'x2': 'sex', 'x3': 'x:sex', 'g1': 'block'}
    expected = problem.standardized('full')[list(aliases.values())]
    expected.columns = list(aliases)
    pd.testing.assert_frame_equal(table, expected.reset_index(drop=True), check_dtype=False)
    assert table['g1'].dtype == 'int64'


def test_the_model_reaches_r_as_formula_family_prior_settings_and_seed(tmp_path: Path) -> None:
    """The seed is the first 4 bytes of sha256 of `fixture/trial/1`, modulo 2³¹."""
    assert writtenModel(fixtureProblem(), tmp_path) == {
        'formula': 'y ~ x1 + x2 + (1 | g1)',
        'family': 'gaussian',
        'link': 'identity',
        'prior': {
            'Intercept': 'normal(0, 2.5)',
            'b': 'normal(0, 2.5)',
            'sd': 'student_t(3, 0, 2.5)',
            'sigma': 'student_t(3, 0, 2.5)',
        },
        'settings': LEVELS[0],
        'seed': 75704431,
        'summarized': [],
    }


def test_each_level_of_the_ladder_reaches_r_with_its_settings_and_the_same_seed(
    tmp_path: Path,
) -> None:
    """ADR 0004's ladder runs four chains in parallel at every level.
    Level 1 warms up longer at a higher adapt_delta.
    Level 2 also deepens the trees and samples 2,000 draws per chain, thinned by 2.
    So every level stores 4,000 draws.
    Level 3 is level 2 with the dense metric."""
    settings = {}
    seeds = set()
    for level, ladder in LEVELS.items():
        model = writtenModel(fixtureProblem(), tmp_path, ladder)
        settings[level] = model['settings']
        seeds.add(model['seed'])
    assert settings == {
        0: {
            'chains': 4,
            'cores': 4,
            'warmup': 1000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.8,
            'max_treedepth': 10,
            'metric': 'diag_e',
        },
        1: {
            'chains': 4,
            'cores': 4,
            'warmup': 2000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.9,
            'max_treedepth': 10,
            'metric': 'diag_e',
        },
        2: {
            'chains': 4,
            'cores': 4,
            'warmup': 4000,
            'draws': 2000,
            'thin': 2,
            'adapt_delta': 0.99,
            'max_treedepth': 12,
            'metric': 'diag_e',
        },
        3: {
            'chains': 4,
            'cores': 4,
            'warmup': 4000,
            'draws': 2000,
            'thin': 2,
            'adapt_delta': 0.99,
            'max_treedepth': 12,
            'metric': 'dense_e',
        },
    }
    assert seeds == {75704431}


def test_a_binomial_response_reaches_r_with_its_trials(tmp_path: Path) -> None:
    """brms reads a binomial's trials from the formula, `y | trials(n)`, with `n` aliased."""
    handoff = Handoff(binomialTrials())
    handoff.write(tmp_path, LEVELS[0])
    model = json.loads((tmp_path / 'input.json').read_text())
    table = pd.read_csv(tmp_path / 'table.csv')
    assert model['formula'] == 'y | trials(n) ~ x1 + (x1 | g1)'
    assert handoff.aliases == {'y': 'deaths', 'n': 'animals', 'x1': 'dose', 'g1': 'farm'}
    assert list(table.columns) == ['y', 'n', 'x1', 'g1']


def test_a_1_stands_only_where_no_covariate_or_slope_does(tmp_path: Path) -> None:
    """brms implies both intercepts, as in `y ~ x + (x | g)`.
    So the formula writes a `1` only for a model without covariates or a factor without slopes."""
    row = replace(ROW, covariates=(), formula='y ~ 1 + (1 | block)')
    model = writtenModel(fixtureProblem(row), tmp_path)
    assert model['formula'] == 'y ~ 1 + (1 | g1)'


def test_a_slope_on_a_categorical_covariate_takes_all_its_contrast_columns(
    tmp_path: Path,
) -> None:
    """`diet` of three levels is coded `diet[b]` and `diet[c]`, aliased `x1` and `x2`."""
    table = pd.DataFrame(
        {'block': ['A', 'B'] * 6, 'diet': ['a', 'b', 'c'] * 4, 'y': np.arange(12.0)}
    )
    for bars, term in (('|', '(x1 + x2 | g1)'), ('||', '(x1 + x2 || g1)')):
        row = replace(
            ROW,
            covariates=('diet',),
            random_slopes=(SlopeTerm.parse(f'diet{bars}block'),),
            formula=f'y ~ diet + (1 + diet {bars} block)',
        )
        model = writtenModel(Problem.build(row, table), tmp_path)
        assert model['formula'] == f'y ~ x1 + x2 + {term}'


def test_an_ordinal_models_thresholds_take_brms_default_prior(tmp_path: Path) -> None:
    """The contract states no threshold prior, so no `Intercept` class reaches brms."""
    model = writtenModel(ordinalProblem(), tmp_path)
    assert model['formula'] == 'y ~ x1 + (1 | g1)'
    assert (model['family'], model['link']) == ('cumulative', 'logit')
    assert list(model['prior']) == ['b', 'sd']


def test_r_summarizes_the_random_effects_of_a_factor_above_1000_groups(tmp_path: Path) -> None:
    """Full draws of 20,000 groups would be a file of gigabytes.
    So R keeps per-effect summaries of such a factor instead.
    1,000 groups still keep their draws."""
    for groups, summarized in ((1000, []), (1001, ['g1'])):
        model = writtenModel(manyGroups(groups), tmp_path)
        assert model['summarized'] == summarized


# ==============================================================================================
# read
# ==============================================================================================

FIXTURES = Path(__file__).parent / 'fixtures'


def rawDraws(fixture: str) -> pd.DataFrame:
    """`draws.rds` of a recorded fixture, as brms named it."""
    return pyreadr.read_r(FIXTURES / fixture / 'draws.rds')[None]


def test_brms_draws_read_back_under_the_contracts_global_names_in_order() -> None:
    """Renamed by brms's label, never by position: `sd_g2__Intercept` is the composite's `sd`.
    `chain` and `draw` count from 0, `draw` within its chain."""
    draws = Handoff(nestedProblem()).read(FIXTURES / 'nested')['globals']
    raw = rawDraws('nested')
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
    """brms orders `school`'s six pairs column by column, the contract row by row.
    So `cor[school][Intercept,age]` is read from `cor_g1__Intercept__x3`, brms's fourth pair."""
    problem = gaussianSlopes(correlated=True)
    draws = Handoff(problem).read(FIXTURES / 'gaussian_correlated')['globals']
    raw = rawDraws('gaussian_correlated')
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
        'cor[school][Intercept,age]',
        'cor[school][dose,sex]',
        'cor[school][dose,age]',
        'cor[school][sex,age]',
        'sigma',
    ]
    assert draws['sd[age|school]'].tolist() == raw['sd_g1__x3'].tolist()
    assert draws['cor[school][Intercept,age]'].tolist() == raw['cor_g1__Intercept__x3'].tolist()
    assert draws['cor[school][dose,sex]'].tolist() == raw['cor_g1__x1__x2'].tolist()


def test_ordinal_thresholds_read_back_as_intercept_k() -> None:
    """brms names a threshold `b_Intercept[k]`.
    The contract drops the `b_`, as for every fixed effect.
    The thresholds lead the global draws in `k`'s order."""
    draws = Handoff(ordinalProblem()).read(FIXTURES / 'ordinal')['globals']
    assert list(draws.columns) == [
        'chain',
        'draw',
        'Intercept[1]',
        'Intercept[2]',
        'Intercept[3]',
        'x',
        'sd[judge]',
    ]
    assert draws['Intercept[2]'].tolist() == rawDraws('ordinal')['b_Intercept[2]'].tolist()


def test_random_effects_read_back_by_brms_label_in_factor_slope_and_group_order() -> None:
    """`r_g1[7,x3]` is the `age` slope of school 7.
    A factor of at most 1,000 groups keeps its full draws.
    So `locals` holds every factor, and no summary is written."""
    files = Handoff(gaussianSlopes(correlated=True)).read(FIXTURES / 'gaussian_correlated')
    effects = ['school', 'dose|school', 'sex|school', 'age|school']
    assert list(files) == ['globals', 'locals']
    assert list(files['locals'].columns) == [
        'chain',
        'draw',
        *[f'r[{effect}][{j}]' for effect in effects for j in range(12)],
    ]
    raw = rawDraws('gaussian_correlated')
    assert files['locals']['r[age|school][7]'].tolist() == raw['r_g1[7,x3]'].tolist()
    assert files['locals']['chain'].tolist() == files['globals']['chain'].tolist()


def test_the_random_effects_of_nested_factors_follow_factor_order() -> None:
    """The composite `block:plot` is aliased `g2`, so `r_g2[10,Intercept]` is its group 10."""
    draws = Handoff(nestedProblem()).read(FIXTURES / 'nested')['locals']
    assert list(draws.columns) == [
        'chain',
        'draw',
        *[f'r[block][{j}]' for j in range(6)],
        *[f'r[block:plot][{j}]' for j in range(18)],
    ]
    assert draws['r[block:plot][10]'].tolist() == rawDraws('nested')['r_g2[10,Intercept]'].tolist()


def test_a_factor_above_1000_groups_reads_back_as_summaries_without_draws() -> None:
    """Recorded by `run.R` from `Handoff.write` of `manyGroups()`,
    at 100 warmup and 10 draws per chain.
    `subject`'s 1,001 groups reach Python as summaries only, so there is no `locals` file."""
    files = Handoff(manyGroups()).read(FIXTURES / 'many_groups')
    raw = pyreadr.read_r(FIXTURES / 'many_groups' / 'locals_summary.rds')[None]
    summary = files['locals_summary']
    assert list(files) == ['globals', 'locals_summary']
    assert list(summary.columns) == ['name', 'mean', 'sd', 'q5', 'q25', 'q50', 'q75', 'q95']
    assert summary['name'].tolist() == [f'r[subject][{j}]' for j in range(1001)]
    row = raw.set_index('variable').loc['r_g1[1000,Intercept]']
    assert summary.iloc[1000, 1:].tolist() == row.tolist()


CHAINS = pd.DataFrame({
    'chain': [1, 2], 'metric': ['diag_e', 'diag_e'], 'divergences': [0, 3], 'treedepth_hits': [2, 0], 'ebfmi': [0.9, 1.1],
    'step_size': [0.31, 0.27], 'leapfrog_steps': [7012.0, 6890.0], 'acceptance': [0.86, 0.91],
    'warmup_seconds': [4.2, 3.9], 'sampling_seconds': [3.1, 3.4],
})  # fmt: skip
SUMMARY = pd.DataFrame({
    'variable': ['sigma', 'sd_g1__Intercept', 'b_x2', 'b_x1', 'b_Intercept'],
    'rhat': [1.0, 1.02, 1.001, 1.002, 1.003], 'ess_bulk': [1200.0, 320.0, 900.0, 800.0, 700.0],
    'ess_tail': [1100.0, 410.0, 950.0, 850.0, 750.0],
})  # fmt: skip


def recordedDiagnostics(dir: Path, summary: pd.DataFrame) -> dict:
    """`Handoff.diagnostics` of the fixture problem, from files written as run.R writes them."""
    pyreadr.write_rds(dir / 'summary.rds', summary)
    pyreadr.write_rds(dir / 'chains.rds', CHAINS)
    meta = pd.DataFrame(
        {'rhat_locals': [1.003], 'ess_bulk_locals': [450.0], 'ess_tail_locals': [520.0]}
    )
    pyreadr.write_rds(dir / 'meta.rds', meta)
    return Handoff(fixtureProblem()).diagnostics(dir)


def picked(diagnostics: dict, keys: tuple[str, ...]) -> dict:
    return {key: diagnostics[key] for key in keys}


def test_diagnostics_read_back_as_the_worst_over_parameters_with_nan_kept(tmp_path: Path) -> None:
    """posterior gives NA for the R-hat and ESS of constant draws, and for the tail ESS of
    non-finite ones.
    Skipped by the largest or smallest, an NA would let the bar pass.
    Divergences and tree-depth hits add up over the chains."""
    nan = float('nan')
    summary = pd.DataFrame({
        'variable': ['b_Intercept', 'b_x1', 'b_x2', 'sd_g1__Intercept', 'sigma'],
        'rhat': [1.001, nan, 1.0, 1.002, 1.0], 'ess_bulk': [900.0, 500.0, 1000.0, 700.0, 1200.0],
        'ess_tail': [800.0, 600.0, 1000.0, nan, 1100.0],
    })  # fmt: skip
    diagnostics = recordedDiagnostics(tmp_path, summary)
    assert np.isnan(diagnostics['rhat'])
    assert np.isnan(diagnostics['ess_tail'])
    keys = (
        'ess_bulk', 'divergences', 'treedepth_hits', 'ebfmi', 'rhat_locals', 'ess_bulk_locals',
        'ess_tail_locals',
    )  # fmt: skip
    assert picked(diagnostics, keys) == {
        'ess_bulk': 500.0,
        'divergences': 3,
        'treedepth_hits': 2,
        'ebfmi': [0.9, 1.1],
        'rhat_locals': 1.003,
        'ess_bulk_locals': 450.0,
        'ess_tail_locals': 520.0,
    }


def test_diagnostics_name_each_global_parameters_rhat_and_ess_by_the_contract(
    tmp_path: Path,
) -> None:
    """A run that ends at the bar keeps no draws, so its record names the slowest parameters.
    Renamed by brms's label, never by position: `SUMMARY` lists them in reverse,
    and they come back in the contract's order."""
    parameters = recordedDiagnostics(tmp_path, SUMMARY)['by_parameter']
    assert list(parameters) == ['Intercept', 'x', 'sex', 'sd[block]', 'sigma']
    assert parameters == {
        'Intercept': {'rhat': 1.003, 'ess_bulk': 700.0, 'ess_tail': 750.0},
        'x': {'rhat': 1.002, 'ess_bulk': 800.0, 'ess_tail': 850.0},
        'sex': {'rhat': 1.001, 'ess_bulk': 900.0, 'ess_tail': 950.0},
        'sd[block]': {'rhat': 1.02, 'ess_bulk': 320.0, 'ess_tail': 410.0},
        'sigma': {'rhat': 1.0, 'ess_bulk': 1200.0, 'ess_tail': 1100.0},
    }


def test_a_brms_global_the_contract_does_not_name_still_counts_toward_the_bar(
    tmp_path: Path,
) -> None:
    """The bar reads every global R summarized, as before the record named them.
    Only the record of each parameter keeps to the contract's names."""
    unnamed = pd.DataFrame(
        {'variable': ['b_x3'], 'rhat': [1.2], 'ess_bulk': [40.0], 'ess_tail': [30.0]}
    )
    diagnostics = recordedDiagnostics(tmp_path, pd.concat([SUMMARY, unnamed]))
    assert picked(diagnostics, ('rhat', 'ess_bulk', 'ess_tail')) == {
        'rhat': 1.2,
        'ess_bulk': 40.0,
        'ess_tail': 30.0,
    }
    assert list(diagnostics['by_parameter']) == ['Intercept', 'x', 'sex', 'sd[block]', 'sigma']


def test_diagnostics_keep_each_chains_step_size_leapfrog_steps_acceptance_and_seconds(
    tmp_path: Path,
) -> None:
    """Leapfrog steps per effective draw measure how hard a problem is for NUTS without wall-clock.
    A leapfrog step is one gradient evaluation (Hoffman & Gelman 2014, §4).
    R sums the steps as doubles, and they reach the record as integers."""
    diagnostics = recordedDiagnostics(tmp_path, SUMMARY)
    kept = ('step_size', 'leapfrog_steps', 'acceptance', 'warmup_seconds', 'sampling_seconds')
    assert picked(diagnostics, kept) == {
        'step_size': [0.31, 0.27],
        'leapfrog_steps': [7012, 6890],
        'acceptance': [0.86, 0.91],
        'warmup_seconds': [4.2, 3.9],
        'sampling_seconds': [3.1, 3.4],
    }
    assert {type(steps) for steps in diagnostics['leapfrog_steps']} == {int}
