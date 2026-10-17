"""__init__.py defines a problem's reference run: a problem and a directory in, its outcome out.

The run climbs the ladder.
At each level, `run.R` fits the problem with brms through cmdstanr, and Python checks the bar on
the fit's diagnostics.
The first level that passes ends the run, and its draws are kept under the contract's names.
The run refuses to start on an R stack other than the pinned one: brms, cmdstanr and posterior as
`renv.lock` pins them, CmdStan at `CMDSTAN`.

pipeline:
---------
a Problem and a directory
-> the R stack, checked against the pins                        _Runner._checkStack
-> each level fitted by run.R                                   _climbLadder, _attemptLevel, _fit
-> its outcome, judged by the bar                               _passes
-> the draws as parquet, Stan's program and data, the record    _keep, _Runner.run
-> the outcome                                                  run
"""

from __future__ import annotations

import hashlib
import json
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

__all__ = ['CAP', 'CMDSTAN', 'ESS', 'LEVELS', 'RHAT', 'Ending', 'Outcome', 'run']

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
# the bar: R-hat and both ESS on the stored draws of the global parameters, and no divergence
# in any iteration
RHAT = 1.01
ESS = 400
CMDSTAN = '2.40.0'
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
    """Climbs the ladder on `problem` and returns its outcome.
    The ladder stops at the first level that passes, at an R error, or when `CAP` seconds are spent.
    The run writes into `dir/<the first 16 hex characters of sha256 of the id>`
    and replaces an earlier run there.
    It always leaves `run.json` and R's output, `R.log`.
    Where the bar passed, it adds the draws as `Handoff.read` gives them
    (`globals.parquet`, `locals.parquet`, `locals_summary.parquet`),
    and brms's Stan program and data (`model.stan`, `standata.json`).
    Raises before any level on an unpinned R stack."""
    return _Runner(problem, dir).run()


# =====================================================================================
# the run
# =====================================================================================


class _Runner:
    def __init__(self, problem: Problem, dir: Path) -> None:
        self.problem = problem
        self.handoff = Handoff(problem)
        # an id may hold `/`, `!` and spaces, and the record carries the id itself
        self.dir = dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]

    def run(self) -> Outcome:
        versions = self._checkStack()
        if self.dir.exists():  # no file of an earlier run stays beside this run's record
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True)
        with tempfile.TemporaryDirectory() as tmp, open(self.dir / 'R.log', 'w') as log:
            work = Path(tmp)
            levels = self._climbLadder(work, log)
            last = levels[-1]
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
            'levels': levels,
            'versions': versions,
        }
        (self.dir / 'run.json').write_text(json.dumps(record, indent=2))
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
        report = (
            'cat(as.character(packageVersion("brms")), as.character(packageVersion("cmdstanr")), '
            'as.character(packageVersion("posterior")), cmdstanr::cmdstan_version())'
        )
        found = subprocess.run(
            ['Rscript', '-e', report], capture_output=True, text=True, check=True
        )
        installed = dict(zip(pins, found.stdout.split()))
        if installed != pins:
            raise RuntimeError(f'the R stack {installed} differs from the pins {pins}')
        return installed

    def _climbLadder(self, work: Path, log: TextIO) -> list[dict]:
        """Each level's attempt, up to the first that does not end at the bar."""
        levels = []
        start = time.monotonic()
        for level in LEVELS:
            timeout = CAP - (time.monotonic() - start)
            levels.append(self._attemptLevel(work, level, log, timeout))
            if levels[-1]['outcome'] != 'bar':
                break
        return levels

    def _attemptLevel(self, work: Path, level: int, log: TextIO, timeout: float) -> dict:
        """The level's settings, seconds and outcome, and its diagnostics where R ran to the end."""
        began = time.monotonic()
        ended = self._fit(work, level, log, timeout)
        attempt = {'level': level, 'settings': LEVELS[level], 'seconds': time.monotonic() - began}
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
            and diagnostics['divergences'] == 0
        )

    def _keep(self, work: Path) -> None:
        """The passing level's draws as parquet, and brms's Stan program and data."""
        for name, draws in self.handoff.read(work).items():
            draws.to_parquet(self.dir / f'{name}.parquet', index=False)
        for name in ('model.stan', 'standata.json'):
            shutil.copy(work / name, self.dir / name)
