"""runner.py defines a problem's reference run: a problem and a directory in, its outcome out.

The run climbs the NUTS ladder (each level allocates more resources):
`run.R` fits the problem with brms through cmdstanr,
and Python checks the convergence bar on the fit's diagnostics.
The first passing level ends the run, and its draws are kept under the contract's names.
brms, cmdstanr and posterior are pinned by `renv.lock`, CmdStan at `CMDSTAN`.

pipeline:
---------
a Problem and a directory
-> the R stack, checked against the pins                        _Runner._checkStack
-> each level fitted by run.R                                   _climbLadder, _attemptLevel, _fit
-> its outcome, judged by the bar                               _passes
-> the draws as parquet, Stan's program and data                _keep
-> the record, with null for a diagnostic R could not compute   _Runner.run, _nullifyNonFinite
-> the outcome                                                  run
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, TextIO

from mixedbench.contract import Problem, contractHash
from mixedbench.references.handoff import Handoff

CMDSTAN = '2.40.0'
# the ladder: the settings of `brm()` per level.
# four chains run in parallel at every level, one core each
LEVELS = {
    0: {
        'chains': 4,
        'cores': 4,
        'warmup': 1000,
        'draws': 1000,
        'thin': 1,
        'adapt_delta': 0.8,
        'max_treedepth': 10,
    },
    1: {
        'chains': 4,
        'cores': 4,
        'warmup': 2000,
        'draws': 1000,
        'thin': 1,
        'adapt_delta': 0.9,
        'max_treedepth': 10,
    },
    # 2,000 draws per chain, thinned by 2: 4,000 stored, as at the other levels.
    # the divergences count every iteration, before thinning
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
CAP = 12 * 60 * 60  # seconds over the whole ladder
# the bar: R-hat and both ESS on the stored draws of every parameter, and no divergence
# in any iteration.
# the random effects' R-hat is rstan's warning threshold, since the largest of thousands
# crosses 1.01 by chance more often than one does
RHAT = 1.01
RHAT_LOCALS = 1.05
ESS = 400
_HERE = Path(__file__).parent

Ending = Literal['passed', 'bar', 'cap', 'error']


@dataclass(frozen=True)
class Outcome:
    """A row of `references.csv`.
    The diagnostics are the last level's, and `None` where it ended as `cap` or `error`."""

    id: str
    contract_hash: str
    level: int  # the last level attempted
    outcome: Ending
    rhat: float | None  # the largest over the global parameters
    ess_bulk: float | None  # the smallest
    ess_tail: float | None  # the smallest
    divergences: int | None
    brms: str
    cmdstan: str


def run(problem: Problem, dir: Path) -> Outcome:
    """Writes the run's files into a directory of `dir` named by the id's hash,
    replacing an earlier run there.
    Raises before any level where the R stack differs from its pins."""
    return _Runner(problem, dir).run()


# =====================================================================================
# the run
# =====================================================================================


class _Runner:
    """A problem's reference run, in a directory of its own."""

    def __init__(self, problem: Problem, dir: Path) -> None:
        self.problem = problem
        self.handoff = Handoff(problem)
        # an id may hold `/`, `!` and spaces, and the record carries the id itself
        digest = hashlib.sha256(problem.id.encode()).hexdigest()
        self.dir = dir / digest[:16]

    def run(self) -> Outcome:
        versions = self._checkStack()
        if self.dir.exists():  # no file of an earlier run stays beside this run's record
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True)
        with tempfile.TemporaryDirectory() as tmp, open(self.dir / 'R.log', 'w') as log:
            work = Path(tmp)
            attempts = self._climbLadder(work, log)
            last = attempts[-1]
            if last['outcome'] == 'passed':
                self._keep(work)
        outcome = Outcome(
            id=self.problem.id,
            contract_hash=contractHash(self.problem),
            level=last['level'],
            outcome=last['outcome'],
            rhat=last.get('rhat'),
            ess_bulk=last.get('ess_bulk'),
            ess_tail=last.get('ess_tail'),
            divergences=last.get('divergences'),
            brms=versions['brms'],
            cmdstan=versions['cmdstan'],
        )
        record = asdict(outcome) | {
            'seed': self.handoff.seed,
            'aliases': self.handoff.aliases,
            'levels': attempts,
            'versions': versions,
        }
        strict = _nullifyNonFinite(record)
        (self.dir / 'run.json').write_text(json.dumps(strict, indent=2))
        return outcome

    # ---------------------------------------------------------------------------------
    # pins -> ladder -> level -> fit -> bar -> draws kept
    # ---------------------------------------------------------------------------------

    @staticmethod
    def _checkStack() -> dict[str, str]:
        """Returns the installed versions of brms, cmdstanr, posterior and CmdStan,
        and raises where one differs from its pin."""
        lock = json.loads((_HERE / 'renv.lock').read_text())['Packages']
        pins = {
            'brms': lock['brms']['Version'],
            'cmdstanr': lock['cmdstanr']['Version'],
            'posterior': lock['posterior']['Version'],
            'cmdstan': CMDSTAN,
        }
        # R prints the installed versions in the order of `pins`
        script = (
            'cat(as.character(packageVersion("brms")), as.character(packageVersion("cmdstanr")), '
            'as.character(packageVersion("posterior")), cmdstanr::cmdstan_version())'
        )
        process = subprocess.run(
            ['Rscript', '-e', script], capture_output=True, text=True, check=True
        )
        installed = dict(zip(pins, process.stdout.split()))
        if installed != pins:
            raise RuntimeError(f'the R stack {installed} differs from the pins {pins}')
        return installed

    def _climbLadder(self, work: Path, log: TextIO) -> list[dict]:
        """Each level's attempt, up to the first that does not end at the bar."""
        attempts = []
        start = time.monotonic()
        for level in LEVELS:
            spent = time.monotonic() - start
            timeout = CAP - spent
            attempt = self._attemptLevel(work, level, log, timeout)
            attempts.append(attempt)
            if attempt['outcome'] != 'bar':
                break
        return attempts

    def _attemptLevel(self, work: Path, level: int, log: TextIO, timeout: float) -> dict:
        """The level's settings, seconds and outcome, and its diagnostics where R ran to the end."""
        start = time.monotonic()
        ended = self._fit(work, level, log, timeout)
        seconds = time.monotonic() - start
        attempt = {'level': level, 'settings': LEVELS[level], 'seconds': seconds}
        if ended == 'ran':
            diagnostics = self.handoff.diagnostics(work)
            attempt['outcome'] = 'passed' if self._passes(diagnostics) else 'bar'
            attempt.update(diagnostics)
        else:
            attempt['outcome'] = ended
        return attempt

    def _fit(
        self, work: Path, level: int, log: TextIO, timeout: float
    ) -> Literal['ran', 'cap', 'error']:
        """How R's run of the level ended. Its outputs stay in `work`."""
        self.handoff.write(work, LEVELS[level])
        log.write(f'# level {level}\n')
        log.flush()
        process = subprocess.Popen(
            ['Rscript', _HERE / 'run.R', work], stdout=log, stderr=subprocess.STDOUT
        )
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # an interrupt, not a kill: cmdstanr starts the chains in sessions of their own,
            # and only R's own exit stops them
            process.send_signal(signal.SIGINT)
            process.wait()
            return 'cap'
        return 'ran' if process.returncode == 0 else 'error'

    @staticmethod
    def _passes(diagnostics: dict) -> bool:
        """A NaN fails every comparison, so a diagnostic R could not compute fails the bar."""
        return (
            diagnostics['rhat'] < RHAT
            and diagnostics['ess_bulk'] >= ESS
            and diagnostics['ess_tail'] >= ESS
            and diagnostics['rhat_locals'] < RHAT_LOCALS
            and diagnostics['ess_bulk_locals'] >= ESS
            and diagnostics['ess_tail_locals'] >= ESS
            and diagnostics['divergences'] == 0
        )

    def _keep(self, work: Path) -> None:
        """The passing level's draws as parquet, and brms's Stan program and data."""
        for name, draws in self.handoff.read(work).items():
            draws.to_parquet(self.dir / f'{name}.parquet', index=False)
        for name in ('model.stan', 'standata.json'):
            shutil.copy(work / name, self.dir / name)


# =====================================================================================
# the record as strict JSON
# =====================================================================================
# the record is published, and strict JSON readers reject a bare NaN


def _nullifyNonFinite(value: object) -> object:
    """Returns `value` with each NaN or infinity as `None`, which JSON writes as null,
    as JavaScript's `JSON.stringify` does."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _nullifyNonFinite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_nullifyNonFinite(item) for item in value]
    return value
