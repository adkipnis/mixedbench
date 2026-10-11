"""__init__.py defines a problem's reference run: a problem and a directory in, its outcome out.

The run hands the problem to `run.R`, which fits it with brms through cmdstanr and checks the
bar, and keeps what passed under the contract's names, in a directory per problem.
It refuses to start on an R stack other than the pinned one: brms and cmdstanr as `renv.lock`
pins them, CmdStan at `CMDSTAN`.

pipeline:
---------
a Problem and a directory
-> the R stack, checked against the pins                        _Run._versions
-> the handoff fitted by run.R, level by level within the cap   _Run._fit
-> the draws as parquet, Stan's program and data, the record    _Run.outcome
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
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TextIO

import pyreadr
from mixedbench.contract import Problem, contractHash
from mixedbench.references.handoff import Handoff

__all__ = ['CAP', 'CMDSTAN', 'Outcome', 'run']

CAP = 12 * 60 * 60  # seconds over the whole ladder
CMDSTAN = '2.40.0'
_HERE = Path(__file__).parent


@dataclass(frozen=True)
class Outcome:
    """A row of `references.csv`. The diagnostics are the last level's, and `None` where it
    ended as `cap` or `error`."""

    id: str
    contract_hash: str
    level: int  # the last level attempted
    outcome: Literal['passed', 'bar', 'cap', 'error']
    rhat: float | None  # the largest over the global parameters
    ess_bulk: float | None  # the smallest
    ess_tail: float | None  # the smallest
    divergences: int | None
    brms: str
    cmdstan: str


def run(problem: Problem, dir: Path, cap: float = CAP) -> Outcome:
    """Writes into `dir/<the first 16 hex characters of sha256 of the id>`: where the bar passed,
    `globals.parquet`, `locals.parquet` and `locals_summary.parquet` as `Handoff.read` gives
    them, `model.stan` and `standata.json`; and `run.json` and R's output, `R.log`, always.
    The ladder stops at the first level that passes, at an R error, or when `cap` seconds
    are spent. Raises before any level on an unpinned R stack."""
    return _Run(problem, Path(dir), cap).outcome()


# =====================================================================================
# the run
# =====================================================================================


class _Run:
    def __init__(self, problem: Problem, dir: Path, cap: float) -> None:
        self.problem = problem
        self.cap = cap
        self.handoff = Handoff(problem)
        # named as the cache names a problem's directory: an id may hold `/`, `!` and spaces
        self.dir = dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]

    def outcome(self) -> Outcome:
        versions = self._versions()
        self.dir.mkdir(parents=True, exist_ok=True)
        levels = []
        start = time.monotonic()
        with tempfile.TemporaryDirectory() as tmp, open(self.dir / 'R.log', 'w') as log:
            work = Path(tmp)
            for level in Handoff.LEVELS:
                began = time.monotonic()
                end = self._fit(work, level, log, timeout=self.cap - (began - start))
                attempt = {
                    'level': level,
                    'settings': Handoff.LEVELS[level],
                    'seconds': time.monotonic() - began,
                }
                if end in ('passed', 'bar'):
                    attempt.update(self._diagnostics(work))
                levels.append(attempt)
                if end != 'bar':
                    break
            if end == 'passed':
                self._keep(work)
            session = None
            if end in ('passed', 'bar'):
                session = pyreadr.read_r(work / 'meta.rds')[None]['session'][0]
        outcome = Outcome(
            id=self.problem.id,
            contract_hash=contractHash(self.problem),
            level=level,
            outcome=end,
            rhat=attempt.get('rhat'),
            ess_bulk=attempt.get('ess_bulk'),
            ess_tail=attempt.get('ess_tail'),
            divergences=attempt.get('divergences'),
            brms=versions['brms'],
            cmdstan=versions['cmdstan'],
        )
        record = {
            'id': outcome.id,
            'contract_hash': outcome.contract_hash,
            'seed': self.handoff.seed,
            'aliases': self.handoff.aliases,
            'outcome': outcome.outcome,
            'levels': levels,
            'versions': versions,
            'session': session,
        }
        (self.dir / 'run.json').write_text(json.dumps(record, indent=2))
        return outcome

    # ---------------------------------------------------------------------------------
    # pins -> handoff -> fit
    # ---------------------------------------------------------------------------------

    @staticmethod
    def _versions() -> dict[str, str]:
        """Raises where the installed brms, cmdstanr or CmdStan differs from its pin."""
        lock = json.loads((_HERE / 'renv.lock').read_text())['Packages']
        pins = {
            'brms': lock['brms']['Version'],
            'cmdstanr': lock['cmdstanr']['Version'],
            'cmdstan': CMDSTAN,
        }
        report = (
            'cat(as.character(packageVersion("brms")), '
            'as.character(packageVersion("cmdstanr")), cmdstanr::cmdstan_version())'
        )
        found = subprocess.run(
            [shutil.which('Rscript'), '-e', report], capture_output=True, text=True, check=True
        )
        installed = dict(zip(pins, found.stdout.split()))
        if installed != pins:
            raise RuntimeError(f'the R stack {installed} differs from the pins {pins}')
        return installed

    def _fit(
        self, work: Path, level: int, log: TextIO, timeout: float
    ) -> Literal['passed', 'bar', 'cap', 'error']:
        """How the level ended; R's outputs stay in `work`."""
        self.handoff.write(work, level)
        log.write(f'# level {level}\n')
        log.flush()
        process = subprocess.Popen(
            [shutil.which('Rscript'), _HERE / 'run.R', work], stdout=log, stderr=subprocess.STDOUT
        )
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # an interrupt, not a kill: R halts and its exit stops the chains, which cmdstanr
            # started in sessions of their own
            process.send_signal(signal.SIGINT)
            process.wait()
            return 'cap'
        if process.returncode != 0:
            return 'error'
        return 'passed' if pyreadr.read_r(work / 'meta.rds')[None]['passed'][0] else 'bar'

    @staticmethod
    def _diagnostics(work: Path) -> dict:
        """What R reported of a level that ran to its end; only the bar gates."""
        summary = pyreadr.read_r(work / 'summary.rds')[None]  # the global parameters
        chains = pyreadr.read_r(work / 'chains.rds')[None]
        meta = pyreadr.read_r(work / 'meta.rds')[None]
        return {
            'rhat': float(summary['rhat'].max()),
            'ess_bulk': float(summary['ess_bulk'].min()),
            'ess_tail': float(summary['ess_tail'].min()),
            'divergences': int(chains['divergences'].sum()),
            'treedepth_hits': int(chains['treedepth_hits'].sum()),
            'ebfmi': chains['ebfmi'].tolist(),
            'rhat_locals': float(meta['rhat_locals'][0]),
        }

    def _keep(self, work: Path) -> None:
        """The passing level's draws as parquet, and brms's Stan program and data."""
        for name, draws in self.handoff.read(work).items():
            draws.to_parquet(self.dir / f'{name}.parquet', index=False)
        for name in ('model.stan', 'standata.json'):
            shutil.copy(work / name, self.dir / name)
