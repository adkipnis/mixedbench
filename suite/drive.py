"""drive.py defines suite 1.1's reference runs: one candidate's run, and every record collected.

A cluster job runs one candidate, named by its 0-based index in the list as a scheduler array
task knows it, or by its id. The draws stay under `references/`, never committed;
`references.csv` is the suite's record of every run, failures included.

pipeline:
---------
a candidate id or its index in the list           id
-> its reference run, a directory with run.json   run
-> the record of each run, by its id and hash     _records
-> one row per candidate, in list order           collect

Run from the repo root, with the references extra:

    uv run --extra references python suite/drive.py run 17
    uv run python suite/drive.py collect
"""

from __future__ import annotations

import argparse
import json
from dataclasses import fields
from functools import cached_property
from pathlib import Path

import pandas as pd
from mixedbench import references, suite
from mixedbench.references import Outcome
from mixedbench.registry.row import readCsv, writeCsv


class Driver:
    def __init__(self, candidates: Path, dir: Path) -> None:
        """`candidates` is the suite's candidate list, `dir` holds a directory per run."""
        self.candidates = readCsv(candidates)
        self.dir = dir

    def id(self, name: str) -> str:
        """An all-digit name is an index; no id is all digits."""
        if name.isdigit():
            return self.candidates['id'].iloc[int(name)]
        return name

    def run(self, name: str, cache: Path) -> Outcome:
        problem = suite.load(self.id(name), cache)
        return references.run(problem, self.dir)

    def collect(self, file: Path) -> None:
        """`references.csv`: the outcome row of every candidate's record, in list order.
        Refuses while a candidate has no record of its listed contract hash."""
        listed = list(zip(self.candidates['id'], self.candidates['contract_hash']))
        missing = [id for id, hash in listed if (id, hash) not in self._records]
        if missing:
            first = ', '.join(missing[:5])
            raise ValueError(
                f'{len(missing)} of {len(listed)} candidates have no record of their listed '
                f'contract hash, among them {first}'
            )
        columns = [field.name for field in fields(Outcome)]
        rows = [self._records[candidate] for candidate in listed]
        writeCsv(pd.DataFrame(rows, columns=columns), file)

    # ---------------------------------------------------------------------------------
    # id -> record -> row
    # ---------------------------------------------------------------------------------

    @cached_property
    def _records(self) -> dict[tuple[str, str], dict]:
        """Keyed by id and contract hash: a run made before its problem's hash moved is
        no record of the listed problem."""
        records = [json.loads(file.read_text()) for file in self.dir.glob('*/run.json')]
        return {(record['id'], record['contract_hash']): record for record in records}


# =====================================================================================
# main
# =====================================================================================
# a candidate's run, or every record collected into the suite's references.csv
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'registry' / 'cache'
SUITE = ROOT / 'suite' / '1.1'
REFERENCES = ROOT / 'references' / '1.1'

if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description='The reference runs of suite 1.1.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('run', help='one candidate').add_argument('name', help='an id or a 0-based index')
    commands.add_parser('collect', help='every record into references.csv')
    args = parser.parse_args()
    # fmt: on
    driver = Driver(SUITE / 'candidates.csv', REFERENCES)
    if args.command == 'run':
        print(driver.run(args.name, CACHE))
    else:
        driver.collect(SUITE / 'references.csv')
