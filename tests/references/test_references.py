"""`references.run` with real R (#65): a problem and a directory in, the problem's reference run
out, its global draws under the contract's names. Each test fits a model, about a minute."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from mixedbench import references
from mixedbench.contract import Problem, contractHash

from .conftest import fixtureProblem

pytestmark = [pytest.mark.brms, pytest.mark.usefixtures('rstack')]


@pytest.fixture(scope='module')
def ran(tmp_path_factory: pytest.TempPathFactory) -> tuple[Problem, references.Outcome, Path]:
    """One fit shared by the tests that read a passing run."""
    problem = fixtureProblem()
    dir = tmp_path_factory.mktemp('references')
    outcome = references.run(problem, dir)
    return problem, outcome, dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]


def test_a_passing_run_writes_4000_global_draws_over_4_chains(ran) -> None:
    problem, outcome, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    assert outcome.outcome == 'passed'
    assert list(draws.columns) == ['chain', 'draw', *problem.globalDraws()]
    assert len(draws) == 4000
    assert draws.groupby('chain')['draw'].apply(list).to_dict() == {
        chain: list(range(1000)) for chain in range(4)
    }
    assert (draws.dtypes.iloc[2:] == 'float64').all()


def test_a_run_records_its_problem_seed_and_aliases(ran) -> None:
    problem, outcome, dir = ran
    record = json.loads((dir / 'run.json').read_text())
    assert record['id'] == 'fixture/trial/1'
    assert record['contract_hash'] == contractHash(problem) == outcome.contract_hash
    assert record['seed'] == 75704431
    assert record['aliases'] == {'y': 'y', 'x1': 'x', 'x2': 'sex', 'g1': 'block'}
    assert record['outcome'] == 'passed'
    assert record['versions'] == {'brms': '2.23.0', 'cmdstanr': '0.9.0', 'cmdstan': '2.40.0'}


def test_the_intercept_is_the_uncentred_one(ran) -> None:
    """brms samples a centred intercept and reports the uncentred `b_Intercept`. Every group of
    the fixture holds the same design rows, so least squares gives the mixed model's fixed
    effects at any variances, and the posterior mean sits on it within Monte Carlo error
    (4 standard errors at the bar's smallest bulk ESS, 400). The centred intercept is about 0,
    since `y` is z-scored, and lies far outside that."""
    problem, _, dir = ran
    draws = pd.read_parquet(dir / 'globals.parquet')
    table = problem.standardised('full')
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
