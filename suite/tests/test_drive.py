"""The driver (#68): one candidate's reference run by id or index, and the per-problem records
collected into `references.csv`. Run by hand: `uv run pytest suite/tests`.

The records are written as `references.run` writes `run.json`, under directories named apart
from the ids, since collect finds a record by the id inside it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest
from mixedbench.registry.row import readCsv, writeCsv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the suite's scripts

from drive import Driver

CANDIDATES = {'zeta/a/1': 'hash-z', 'alpha/b/1': 'hash-a', 'mid/c/1': 'hash-m'}


def candidateList(dir: Path) -> Path:
    file = dir / 'candidates.csv'
    table = pd.DataFrame(CANDIDATES.items(), columns=['id', 'contract_hash'])
    writeCsv(table, file)
    return file


def writeRecord(
    dir: Path, name: str, id: str, outcome: str = 'passed', level: int = 0, hash: str = ''
) -> None:
    """A `run.json` with the outcome row and a trimmed rest of the record;
    its contract hash the listed one unless `hash` is given."""
    passed = outcome == 'passed'
    record = {
        'id': id,
        'contract_hash': hash or CANDIDATES[id],
        'level': level,
        'outcome': outcome,
        'rhat': 1.002 if passed else None,
        'ess_bulk': 1200.0 if passed else None,
        'ess_tail': 900.0 if passed else None,
        'divergences': 0 if passed else None,
        'brms': '2.23.0',
        'cmdstan': '2.40.0',
        'seed': 1,
        'levels': [],
    }
    (dir / name).mkdir(parents=True)
    (dir / name / 'run.json').write_text(json.dumps(record))


# =====================================================================================
# collect
# =====================================================================================
def test_collect_writes_one_row_per_candidate_in_candidate_order(tmp_path):
    """`references.csv` is read beside the candidate list, so it keeps the list's order,
    whatever order the records lie in on disk; a failed run is a row too."""
    references = tmp_path / 'references'
    writeRecord(references, '0a', 'mid/c/1', outcome='cap', level=2)
    writeRecord(references, '0b', 'alpha/b/1', outcome='passed', level=1)
    writeRecord(references, '0c', 'zeta/a/1', outcome='passed')
    driver = Driver(candidateList(tmp_path), references)
    driver.collect(tmp_path / 'references.csv')
    written = readCsv(tmp_path / 'references.csv')
    assert list(written.columns) == [
        'id',
        'contract_hash',
        'level',
        'outcome',
        'rhat',
        'ess_bulk',
        'ess_tail',
        'divergences',
        'brms',
        'cmdstan',
    ]
    assert list(written['id']) == ['zeta/a/1', 'alpha/b/1', 'mid/c/1']
    assert list(written['outcome']) == ['passed', 'passed', 'cap']
    assert list(written['level'].astype(int)) == [0, 1, 2]


def test_collect_refuses_while_a_candidate_has_no_record(tmp_path):
    """A missing row would read as a problem never run, so nothing is written until every
    candidate has its record."""
    references = tmp_path / 'references'
    writeRecord(references, '0a', 'zeta/a/1')
    writeRecord(references, '0b', 'mid/c/1')
    driver = Driver(candidateList(tmp_path), references)
    with pytest.raises(ValueError, match='alpha/b/1'):
        driver.collect(tmp_path / 'references.csv')
    assert not (tmp_path / 'references.csv').exists()


def test_collect_takes_a_record_of_another_contract_hash_for_no_record(tmp_path):
    """A run made before the problem's hash moved is not a reference of the listed problem."""
    references = tmp_path / 'references'
    writeRecord(references, '0a', 'zeta/a/1')
    writeRecord(references, '0b', 'alpha/b/1', hash='hash-old')
    writeRecord(references, '0c', 'mid/c/1')
    driver = Driver(candidateList(tmp_path), references)
    with pytest.raises(ValueError, match='alpha/b/1'):
        driver.collect(tmp_path / 'references.csv')
    assert not (tmp_path / 'references.csv').exists()


# =====================================================================================
# run
# =====================================================================================
def test_an_index_names_the_candidate_at_that_position_and_an_id_names_itself(tmp_path):
    """A scheduler array task knows only its 0-based index; a rerun by hand names the id."""
    driver = Driver(candidateList(tmp_path), tmp_path / 'references')
    assert driver.id('1') == 'alpha/b/1'
    assert driver.id('0') == 'zeta/a/1'
    assert driver.id('mid/c/1') == 'mid/c/1'
