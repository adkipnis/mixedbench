"""__init__.py defines a problem's reference run: a problem and a directory in, its outcome out.

The run hands the problem to `run.R`, which fits it with brms through cmdstanr and checks the
bar, and keeps what passed under the contract's names, in a directory per problem.
It refuses to start on an R stack other than the pinned one: brms and cmdstanr as `renv.lock`
pins them, CmdStan at `CMDSTAN`.

pipeline:
---------
a Problem and a directory
-> the R stack, checked against the pins                        _Run._versions
-> the handoff fitted by run.R at level 0                       _Run._fit
-> the draws as parquet, Stan's program and data, the record    _Run.outcome
-> the outcome                                                  run
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
import pyreadr
from mixedbench.contract import Problem, contractHash
from mixedbench.references.handoff import Handoff

__all__ = ['CMDSTAN', 'Outcome', 'run']

CMDSTAN = '2.40.0'
_HERE = Path(__file__).parent


@dataclass(frozen=True)
class Outcome:
    id: str
    contract_hash: str
    level: int  # the last level attempted
    outcome: Literal['passed', 'bar']


def run(problem: Problem, dir: Path) -> Outcome:
    """Writes into `dir/<the first 16 hex characters of sha256 of the id>`: where the bar passed,
    `globals.parquet`, `locals.parquet` and `locals_summary.parquet` as `Handoff.read` gives
    them, `model.stan` and `standata.json`; and `run.json` always.
    Raises before any level on an unpinned R stack."""
    return _Run(problem, Path(dir)).outcome()


# =====================================================================================
# the run
# =====================================================================================


class _Run:
    def __init__(self, problem: Problem, dir: Path) -> None:
        self.problem = problem
        self.handoff = Handoff(problem)
        # named as the cache names a problem's directory: an id may hold `/`, `!` and spaces
        self.dir = dir / hashlib.sha256(problem.id.encode()).hexdigest()[:16]

    def outcome(self) -> Outcome:
        versions = self._versions()
        self.dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as work:
            meta = self._fit(Path(work), level=0)
            passed = bool(meta['passed'][0])
            if passed:
                for name, draws in self.handoff.read(Path(work)).items():
                    draws.to_parquet(self.dir / f'{name}.parquet', index=False)
                for name in ('model.stan', 'standata.json'):  # brms's Stan program and data
                    shutil.copy(Path(work) / name, self.dir / name)
        outcome = Outcome(
            id=self.problem.id,
            contract_hash=contractHash(self.problem),
            level=0,
            outcome='passed' if passed else 'bar',
        )
        record = {
            'id': outcome.id,
            'contract_hash': outcome.contract_hash,
            'seed': self.handoff.seed,
            'aliases': self.handoff.aliases,
            'outcome': outcome.outcome,
            'levels': [{'level': 0, 'settings': Handoff.LEVELS[0]}],
            'versions': versions,
            'session': meta['session'][0],
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

    def _fit(self, work: Path, level: int) -> pd.DataFrame:
        """The level's `meta.rds` as a table; the draws and summaries stay in `work`."""
        self.handoff.write(work, level)
        subprocess.run([shutil.which('Rscript'), _HERE / 'run.R', work], check=True)
        return pyreadr.read_r(work / 'meta.rds')[None]
