"""`references.run` with real R (#65): a problem and a directory in, the problem's reference run
out, its global draws under the contract's names. Each test fits a model, about a minute."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from mixedbench import references
from mixedbench.contract import Problem, contractHash
from mixedbench.references.handoff import Handoff

from .conftest import binomialTrials, fixtureProblem, gaussianMixed, nestedProblem, ordinalProblem

pytestmark = [pytest.mark.brms, pytest.mark.usefixtures('rstack')]

FOUR_CHAINS = {chain: list(range(1000)) for chain in range(4)}  # 1,000 draws each, from 0


def problemDir(dir: Path, problem: Problem) -> Path:
    return dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]


def record(dir: Path) -> dict:
    return json.loads((dir / 'run.json').read_text())


def drawsPerChain(file: Path) -> dict[int, list[int]]:
    return pd.read_parquet(file).groupby('chain')['draw'].apply(list).to_dict()


@pytest.fixture(scope='module')
def ran(tmp_path_factory: pytest.TempPathFactory) -> tuple[Problem, references.Outcome, Path]:
    """One fit shared by the tests that read a passing run."""
    problem = fixtureProblem()
    dir = tmp_path_factory.mktemp('references')
    outcome = references.run(problem, dir)
    return problem, outcome, problemDir(dir, problem)


def test_a_passing_run_writes_4000_global_draws_over_4_chains(ran) -> None:
    problem, outcome, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    assert outcome.outcome == 'passed'
    assert list(draws.columns) == ['chain', 'draw', *problem.globalDraws()]
    assert len(draws) == 4000
    assert drawsPerChain(dir / 'globals.parquet') == FOUR_CHAINS
    assert (draws.dtypes.iloc[2:] == 'float64').all()


def test_a_run_records_its_seed_aliases_and_r_stack(ran) -> None:
    _, _, dir = ran
    written = record(dir)
    assert written['seed'] == 75704431
    assert written['aliases'] == {'y': 'y', 'x1': 'x', 'x2': 'sex', 'g1': 'block'}
    assert written['versions'] == {
        'brms': '2.23.0',
        'cmdstanr': '0.9.0',
        'posterior': '1.7.0',
        'cmdstan': '2.40.0',
    }


def test_a_run_records_its_outcome_row(ran) -> None:
    """The driver's collect step reads `references.csv`'s row back from the record."""
    _, outcome, dir = ran
    written = record(dir)
    assert {field.name: written[field.name] for field in fields(outcome)} == asdict(outcome)


def test_a_run_records_each_level_with_its_settings_time_and_diagnostics(ran) -> None:
    """The bar gates on R-hat, ESS and divergences, so a passing level shows them within it;
    tree depth, E-BFMI per chain and the random effects' R-hat are recorded for a reviewer."""
    _, _, dir = ran
    [level] = record(dir)['levels']
    assert (level['level'], level['outcome']) == (0, 'passed')
    assert level['settings'] == references.LEVELS[0]
    assert level['seconds'] > 0
    assert level['rhat'] < 1.01
    assert min(level['ess_bulk'], level['ess_tail']) >= 400
    assert level['divergences'] == 0
    assert level['treedepth_hits'] == 0
    assert len(level['ebfmi']) == 4
    assert min(level['ebfmi']) > 0.3  # a healthy fit, above the usual warning threshold
    assert 1 <= level['rhat_locals'] < 1.05


def test_the_outcome_is_the_references_row_of_the_last_level(ran) -> None:
    problem, outcome, dir = ran
    [level] = record(dir)['levels']
    assert outcome == references.Outcome(
        id='fixture/trial/1',
        contract_hash=contractHash(problem),
        level=0,
        outcome='passed',
        rhat=level['rhat'],
        ess_bulk=level['ess_bulk'],
        ess_tail=level['ess_tail'],
        divergences=0,
        brms='2.23.0',
        cmdstan='2.40.0',
    )


def test_the_intercept_is_the_uncentered_one(ran) -> None:
    """brms samples a centered intercept and reports the uncentered `b_Intercept`. Every group of
    the fixture holds the same design rows, so least squares gives the mixed model's fixed
    effects at any variances, and the posterior mean sits on it within Monte Carlo error
    (4 standard errors at the bar's smallest bulk ESS, 400). The centered intercept is about 0,
    since `y` is z-scored, and lies far outside that."""
    problem, _, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    table = problem.standardized('full')
    design = table[['Intercept', 'x', 'sex']].to_numpy()  # (N, 3)
    leastSquares = np.linalg.lstsq(design, table['y'].to_numpy(), rcond=None)[0][0]
    tolerance = 4 * draws['Intercept'].std() / np.sqrt(400)
    assert abs(draws['Intercept'].mean() - leastSquares) < tolerance
    assert abs(leastSquares) > 10 * tolerance


def test_a_pin_mismatch_raises_before_any_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No reference is made on an unpinned stack, and the refusal records nothing."""
    monkeypatch.setattr(references, 'CMDSTAN', '2.39.0')
    with pytest.raises(RuntimeError, match="'cmdstan': '2.39.0'"):
        references.run(fixtureProblem(), tmp_path)
    assert list(tmp_path.iterdir()) == []


# ==============================================================================================
# the ladder and the ends of a run
# ==============================================================================================


def tinyLevels() -> dict[int, dict]:
    """The ladder at 10 draws per chain: 40 draws hold no bulk ESS of 400, so every level
    fails the bar, quickly."""
    levels = {}
    for level, settings in references.LEVELS.items():
        levels[level] = {**settings, 'warmup': 20, 'draws': 10 * settings['thin']}
    return levels


def test_a_failed_bar_climbs_the_ladder_and_ends_as_bar_at_level_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every level gets its chance; what failed keeps its record and R's log, and no draws."""
    monkeypatch.setattr(references, 'LEVELS', tinyLevels())
    problem = fixtureProblem()
    outcome = references.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    assert (outcome.outcome, outcome.level) == ('bar', 2)
    assert [level['outcome'] for level in record(dir)['levels']] == ['bar', 'bar', 'bar']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']


def test_thinning_hides_no_divergence_from_the_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nested problem at 6 blocks diverges at level 0's settings. Thinned by 2 or not, the
    same seed samples the same chains, so the bar counts the same divergences: it sees every
    iteration, not only the stored ones."""
    problem = nestedProblem()
    divergences = {}
    for thin in (1, 2):
        settings = {**references.LEVELS[0], 'draws': 2000, 'thin': thin}
        monkeypatch.setattr(references, 'LEVELS', {0: settings})
        divergences[thin] = references.run(problem, tmp_path / str(thin)).divergences
    assert divergences[1] > 1
    assert divergences[2] == divergences[1]


def test_a_thinned_level_stores_4000_draws_numbered_within_their_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Level 2 samples 2,000 draws per chain and keeps every second; the fixture passes at
    level 0's settings, so level 0 thinned the same way stands in for it."""
    settings = {**references.LEVELS[0], 'draws': 2000, 'thin': 2}
    monkeypatch.setattr(references, 'LEVELS', {0: settings})
    problem = fixtureProblem()
    assert references.run(problem, tmp_path).outcome == 'passed'
    assert drawsPerChain(problemDir(tmp_path, problem) / 'globals.parquet') == FOUR_CHAINS


def test_a_run_out_of_time_ends_as_cap_with_its_record(tmp_path: Path) -> None:
    """Three seconds do not cover loading brms, so level 0 times out; the record is written
    before the scheduler's limit would kill the job."""
    problem = fixtureProblem()
    outcome = references.run(problem, tmp_path, cap=3)
    dir = problemDir(tmp_path, problem)
    assert (outcome.outcome, outcome.level) == ('cap', 0)
    assert [level['outcome'] for level in record(dir)['levels']] == ['cap']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']


def test_a_rerun_leaves_no_file_of_the_earlier_run(tmp_path: Path) -> None:
    """A run whose contract hash moved may have passed: its draws must not sit beside the
    record of a rerun that ends otherwise, here at the cap."""
    problem = fixtureProblem()
    dir = problemDir(tmp_path, problem)
    dir.mkdir()
    (dir / 'globals.parquet').write_text('an earlier run')
    references.run(problem, tmp_path, cap=3)
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']


def test_an_r_error_ends_the_run_as_error_and_keeps_r_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adapt_delta above 1 makes cmdstanr stop, as a broken model would: the ladder stops at
    the level that failed, since the next would fail the same way and burn the cap."""
    levels = {
        level: {**settings, 'adapt_delta': 2} for level, settings in references.LEVELS.items()
    }
    monkeypatch.setattr(references, 'LEVELS', levels)
    problem = fixtureProblem()
    outcome = references.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    assert (outcome.outcome, outcome.level) == ('error', 0)
    assert [level['outcome'] for level in record(dir)['levels']] == ['error']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']
    assert 'adapt_delta' in (dir / 'R.log').read_text()


# ==============================================================================================
# every model shape
# ==============================================================================================


@pytest.mark.parametrize('shape', [gaussianMixed, binomialTrials, ordinalProblem])
def test_each_model_shape_writes_its_draws_stan_program_and_data(shape, tmp_path: Path) -> None:
    """Mixed `|` and `||` slopes, a binomial with trials and an ordinal model: every factor has
    at most 1,000 groups, so the random effects are kept in full and no summary is written."""
    problem = shape()
    outcome = references.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    assert outcome.outcome == 'passed'
    assert sorted(path.name for path in dir.iterdir()) == [
        'R.log',
        'globals.parquet',
        'locals.parquet',
        'model.stan',
        'run.json',
        'standata.json',
    ]
    local = [name for names in problem.localDraws().values() for name in names]
    effects = pd.read_parquet(dir / 'locals.parquet')
    assert list(effects.columns) == ['chain', 'draw', *local]
    assert len(effects) == 4000
    assert list(pd.read_parquet(dir / 'globals.parquet').columns)[2:] == [*problem.globalDraws()]
    assert (dir / 'model.stan').read_text().startswith('// generated with brms 2.23.0')
    assert json.loads((dir / 'standata.json').read_text())['N'] == len(problem.table)


def test_nested_factors_split_between_full_draws_and_summaries_at_the_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the threshold lowered to 20 groups, `block`'s 12 groups keep their draws and
    `block:plot`'s 36 reach `locals_summary.parquet`, so one small fit covers both files.
    12 blocks, not the 6 of the offline fixture, so level 0 fits without a divergence."""
    monkeypatch.setattr(Handoff, 'FULL_GROUPS', 20)
    problem = nestedProblem(blocks=12)
    assert references.run(problem, tmp_path).outcome == 'passed'
    dir = problemDir(tmp_path, problem)
    effects = pd.read_parquet(dir / 'locals.parquet')
    summary = pd.read_parquet(dir / 'locals_summary.parquet')
    assert list(effects.columns) == ['chain', 'draw', *[f'r[block][{j}]' for j in range(12)]]
    assert list(summary.columns) == ['name', 'mean', 'sd', 'q5', 'q25', 'q50', 'q75', 'q95']
    assert summary['name'].tolist() == [f'r[block:plot][{j}]' for j in range(36)]
