"""`runner.run` with real R (#65): a problem and a directory in, the problem's reference run
out, its global draws under the contract's names. Most tests fit a model, about ten seconds each."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, fields
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
import pytest
from mixedbench.contract import Problem, contractHash
from mixedbench.references import runner
from mixedbench.references.handoff import Handoff

from .conftest import binomialTrials, fixtureProblem, gaussianSlopes, nestedProblem, ordinalProblem

FOUR_CHAINS = {chain: list(range(1000)) for chain in range(4)}  # 1,000 draws each, from 0


def problemDir(dir: Path, problem: Problem) -> Path:
    return dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]


def record(dir: Path) -> dict:
    return json.loads((dir / 'run.json').read_text())


def drawsPerChain(file: Path) -> dict[int, list[int]]:
    return pd.read_parquet(file).groupby('chain')['draw'].apply(list).to_dict()


@pytest.fixture(scope='module')
def ran(tmp_path_factory: pytest.TempPathFactory) -> tuple[Problem, runner.Outcome, Path]:
    """One fit shared by the tests that read a passing run."""
    problem = fixtureProblem()
    dir = tmp_path_factory.mktemp('references')
    outcome = runner.run(problem, dir)
    return problem, outcome, problemDir(dir, problem)


@pytest.mark.brms
def test_a_passing_run_writes_4000_global_draws_over_4_chains(ran) -> None:
    problem, outcome, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    assert outcome.outcome == 'passed'
    assert list(draws.columns) == ['chain', 'draw', *problem.globalDraws()]
    assert drawsPerChain(dir / 'globals.parquet') == FOUR_CHAINS
    assert (draws.dtypes.iloc[2:] == 'float64').all()


@pytest.mark.brms
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


@pytest.mark.brms
def test_a_run_records_each_level_with_its_settings_time_and_diagnostics(ran) -> None:
    """The bar gates on R-hat, ESS and divergences, the random effects' too,
    so a passing level shows them within it; tree depth and E-BFMI per chain are recorded for a
    reviewer."""
    _, _, dir = ran
    [level] = record(dir)['levels']
    assert (level['level'], level['outcome']) == (0, 'passed')
    assert level['settings'] == runner.LEVELS[0]
    assert level['seconds'] > 0
    assert level['rhat'] < 1.01
    assert min(level['ess_bulk'], level['ess_tail']) >= 400
    assert level['divergences'] == 0
    assert level['treedepth_hits'] == 0
    assert len(level['ebfmi']) == 4
    assert min(level['ebfmi']) > 0.3  # a healthy fit, above the usual warning threshold
    assert 1 <= level['rhat_locals'] < 1.05
    assert min(level['ess_bulk_locals'], level['ess_tail_locals']) >= 400


@pytest.mark.brms
def test_a_level_records_each_chains_sampler_and_each_global_parameters_rhat_and_ess(ran) -> None:
    """Counting `bar` endings by their slowest parameters,
    and the difficulty of a problem for NUTS, read these later without a rerun (#93).
    Every iteration takes at least one leapfrog step, and the chains run within the level's time.
    brms's labels of a real fit reach the record under every global parameter's contract name."""
    problem, _, dir = ran
    [level] = record(dir)['levels']
    assert len(level['step_size']) == 4
    assert min(level['step_size']) > 0
    assert min(level['leapfrog_steps']) >= 1000
    assert 0 < min(level['acceptance']) <= max(level['acceptance']) <= 1
    seconds = np.add(level['warmup_seconds'], level['sampling_seconds'])  # per chain
    assert 0 < seconds.min() <= seconds.max() < level['seconds']
    assert list(level['by_parameter']) == list(problem.globalDraws())


@pytest.mark.brms
def test_the_outcome_is_the_last_levels_references_row_and_the_record_holds_it(ran) -> None:
    """The driver's collect step reads `references.csv`'s row back from the record."""
    problem, outcome, dir = ran
    written = record(dir)
    [level] = written['levels']
    assert outcome == runner.Outcome(
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
    assert {field.name: written[field.name] for field in fields(outcome)} == asdict(outcome)


@pytest.mark.brms
def test_the_intercept_is_the_uncentered_one(ran) -> None:
    """brms samples a centered intercept and reports the uncentered `b_Intercept`. Every group of
    the fixture holds the same design rows, so least squares gives the mixed model's fixed
    effects at any variances, and the posterior mean sits on it within Monte Carlo error
    (4 standard errors at the bar's smallest bulk ESS, 400). The centered intercept is about 0,
    since `y` is z-scored, and lies far outside that."""
    problem, _, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    table = problem.standardized('full')
    design = table[['Intercept', 'x', 'sex']].to_numpy()  # (n, d)
    leastSquares = np.linalg.lstsq(design, table['y'].to_numpy(), rcond=None)[0][0]
    tolerance = 4 * draws['Intercept'].std() / np.sqrt(400)
    assert abs(draws['Intercept'].mean() - leastSquares) < tolerance
    assert abs(leastSquares) > 10 * tolerance


@pytest.mark.brms
def test_a_pin_mismatch_raises_before_any_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No reference is made on an unpinned stack, and the refusal records nothing."""
    monkeypatch.setattr(runner, 'CMDSTAN', '2.39.0')
    with pytest.raises(RuntimeError, match="'cmdstan': '2.39.0'"):
        runner.run(fixtureProblem(), tmp_path)
    assert list(tmp_path.iterdir()) == []


# ==============================================================================================
# the ladder and the ends of a run
# ==============================================================================================

PASSING = {  # at the edge
    'rhat': 1.009,
    'ess_bulk': 400.0,
    'ess_tail': 400.0,
    'divergences': 0,
    'rhat_locals': 1.049,
    'ess_bulk_locals': 400.0,
    'ess_tail_locals': 400.0,
}


@pytest.mark.parametrize(
    'diagnostic, value',
    [
        ('rhat', 1.01),
        ('rhat', math.nan),
        ('ess_bulk', 399.0),
        ('ess_bulk', math.nan),
        ('ess_tail', 399.0),
        ('ess_tail', math.nan),
        ('divergences', 1),
        ('rhat_locals', 1.05),
        ('rhat_locals', math.nan),
        ('ess_bulk_locals', 399.0),
        ('ess_bulk_locals', math.nan),
        ('ess_tail_locals', 399.0),
        ('ess_tail_locals', math.nan),
    ],
)
def test_the_bar_fails_past_a_threshold_and_on_nan(diagnostic: str, value: float) -> None:
    """Without R. posterior gives NaN for an R-hat or ESS it could not compute,
    and a NaN that passed would make a reference of an unchecked fit."""
    assert runner._Runner._passes(PASSING)
    assert not runner._Runner._passes({**PASSING, diagnostic: value})


def tinyLevels() -> dict[int, dict]:
    """The ladder at 10 draws per chain: 40 draws hold no bulk ESS of 400, so every level
    fails the bar, quickly."""
    levels = {}
    for level, settings in runner.LEVELS.items():
        levels[level] = {**settings, 'warmup': 20, 'draws': 10 * settings['thin']}
    return levels


@pytest.mark.brms
def test_a_failed_bar_climbs_the_ladder_and_ends_as_bar_at_level_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every level gets its chance; what failed keeps its record and R's log, and no draws.
    So each level's record names its slowest parameters."""
    monkeypatch.setattr(runner, 'LEVELS', tinyLevels())
    problem = fixtureProblem()
    outcome = runner.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    levels = record(dir)['levels']
    assert (outcome.outcome, outcome.level) == ('bar', 3)
    assert [level['outcome'] for level in levels] == ['bar', 'bar', 'bar', 'bar']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']
    for level in levels:
        assert list(level['by_parameter']) == list(problem.globalDraws())


@pytest.mark.brms
def test_each_level_records_the_metric_its_chains_ran_with(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The metric is read back from the fit, not copied from the settings, so the record
    shows that the last level ran the dense one."""
    monkeypatch.setattr(runner, 'LEVELS', tinyLevels())
    problem = fixtureProblem()
    runner.run(problem, tmp_path)
    levels = record(problemDir(tmp_path, problem))['levels']
    diagonal = ['diag_e'] * 4
    dense = ['dense_e'] * 4
    assert [level['metric'] for level in levels] == [diagonal, diagonal, diagonal, dense]


@pytest.mark.brms
def test_a_diagnostic_r_could_not_compute_is_null_in_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record is published, and strict JSON readers (JavaScript, jq) reject a bare NaN.
    No small fit reliably leaves posterior without an R-hat, so the NaN is set on a real fit's."""
    diagnostics = Handoff.diagnostics

    def withoutRhat(handoff: Handoff, dir: Path) -> dict:
        reported = diagnostics(handoff, dir)
        reported['rhat'] = math.nan
        reported['by_parameter']['sigma']['rhat'] = math.nan
        return reported

    monkeypatch.setattr(Handoff, 'diagnostics', withoutRhat)
    monkeypatch.setattr(runner, 'LEVELS', {0: tinyLevels()[0]})
    problem = fixtureProblem()
    runner.run(problem, tmp_path)
    text = (problemDir(tmp_path, problem) / 'run.json').read_text()
    written = json.loads(text)
    [level] = written['levels']
    assert 'NaN' not in text
    assert written['rhat'] is None
    assert level['rhat'] is None
    assert level['by_parameter']['sigma']['rhat'] is None


@pytest.mark.brms
def test_thinning_hides_no_divergence_from_the_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nested problem at 6 blocks diverges at level 0's settings. Thinned by 2 or not, the
    same seed samples the same chains, so the bar counts the same divergences: it sees every
    iteration, not only the stored ones."""
    problem = nestedProblem()
    divergences = {}
    for thin in (1, 2):
        settings = {**runner.LEVELS[0], 'draws': 2000, 'thin': thin}
        monkeypatch.setattr(runner, 'LEVELS', {0: settings})
        divergences[thin] = runner.run(problem, tmp_path / str(thin)).divergences
    assert divergences[1] > 1
    assert divergences[2] == divergences[1]


@pytest.mark.brms
def test_a_thinned_level_stores_4000_draws_numbered_within_their_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Level 2 samples 2,000 draws per chain and keeps every second; the fixture passes at
    level 0's settings, so level 0 thinned the same way stands in for it."""
    settings = {**runner.LEVELS[0], 'draws': 2000, 'thin': 2}
    monkeypatch.setattr(runner, 'LEVELS', {0: settings})
    problem = fixtureProblem()
    assert runner.run(problem, tmp_path).outcome == 'passed'
    assert drawsPerChain(problemDir(tmp_path, problem) / 'globals.parquet') == FOUR_CHAINS


@pytest.mark.brms
def test_a_run_out_of_time_ends_as_cap_with_its_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three seconds do not cover loading brms, so level 0 times out; the record is written
    before the scheduler's limit would kill the job."""
    monkeypatch.setattr(runner, 'CAP', 3)
    problem = fixtureProblem()
    outcome = runner.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    assert (outcome.outcome, outcome.level) == ('cap', 0)
    assert [level['outcome'] for level in record(dir)['levels']] == ['cap']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']


@pytest.mark.brms
def test_a_rerun_leaves_no_file_of_the_earlier_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run whose contract hash moved may have passed: its draws must not sit beside the
    record of a rerun that ends otherwise, here at the cap."""
    monkeypatch.setattr(runner, 'CAP', 3)
    problem = fixtureProblem()
    dir = problemDir(tmp_path, problem)
    dir.mkdir()
    (dir / 'globals.parquet').write_text('an earlier run')
    runner.run(problem, tmp_path)
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']


@pytest.mark.brms
def test_an_r_error_ends_the_run_as_error_and_keeps_r_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An adapt_delta above 1 makes cmdstanr stop, as a broken model would: the ladder stops at
    the level that failed, since the next would fail the same way and burn the cap.
    R.log still names the R session, which run.R prints before it fits."""
    levels = {level: {**settings, 'adapt_delta': 2} for level, settings in runner.LEVELS.items()}
    monkeypatch.setattr(runner, 'LEVELS', levels)
    problem = fixtureProblem()
    outcome = runner.run(problem, tmp_path)
    dir = problemDir(tmp_path, problem)
    assert (outcome.outcome, outcome.level) == ('error', 0)
    assert [level['outcome'] for level in record(dir)['levels']] == ['error']
    assert sorted(path.name for path in dir.iterdir()) == ['R.log', 'run.json']
    log = (dir / 'R.log').read_text()
    assert 'brms_2.23.0' in log
    assert 'adapt_delta' in log


# ==============================================================================================
# every model shape
# ==============================================================================================


@pytest.mark.brms
@pytest.mark.parametrize(
    'shape', [partial(gaussianSlopes, correlated=False), binomialTrials, ordinalProblem]
)
def test_each_model_shape_writes_its_draws_stan_program_and_data(shape, tmp_path: Path) -> None:
    """Uncorrelated slopes, a binomial with trials and an ordinal model: every factor has
    at most 1,000 groups, so the random effects are kept in full and no summary is written.
    brms names the parameters of `(x1 + x2 + x3 || g1)` as the contract does, with no `cor`."""
    problem = shape()
    outcome = runner.run(problem, tmp_path)
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


@pytest.mark.brms
def test_a_summarized_factor_reaches_locals_summary_and_stays_out_of_draws_rds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the threshold lowered to 10 groups, `block`'s 6 groups keep their draws and
    `block:plot`'s 18 are summarized. `draws.rds` holds no draw of a summarized factor, which
    would run to gigabytes at tens of thousands of groups. run.R runs on its own here, so the
    test reads its raw file."""
    monkeypatch.setattr(Handoff, 'FULL_GROUPS', 10)
    handoff = Handoff(nestedProblem())
    handoff.write(tmp_path, tinyLevels()[0])
    run_r = Path(runner.__file__).with_name('run.R')
    fitted = subprocess.run(['Rscript', run_r, tmp_path], capture_output=True, text=True)
    assert fitted.returncode == 0, fitted.stderr
    raw = pyreadr.read_r(tmp_path / 'draws.rds')[None]
    files = handoff.read(tmp_path)
    assert [column for column in raw.columns if column.startswith('r_g2[')] == []
    assert list(files['locals'].columns) == ['chain', 'draw', *[f'r[block][{j}]' for j in range(6)]]
    summary = files['locals_summary']
    assert list(summary.columns) == ['name', 'mean', 'sd', 'q5', 'q25', 'q50', 'q75', 'q95']
    assert summary['name'].tolist() == [f'r[block:plot][{j}]' for j in range(18)]
