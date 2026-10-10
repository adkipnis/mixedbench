"""The committed candidate list rebuilds from the pins (ADR 0003): a seeded subset of
`suite/1.1/candidates.csv`, fetched afresh, materialises to the hashes the list records. It runs
on every pull request in the three operating systems' matrix, so it is marked network."""

from __future__ import annotations

from pathlib import Path

import pytest
from mixedbench import registry
from mixedbench.contract import Problem, materialise
from mixedbench.registry.row import Row, readCsv

CANDIDATES = Path(__file__).parents[1] / 'suite' / '1.1' / 'candidates.csv'
SEED = 0
SUBSET = 20


def rowsById() -> dict[str, Row]:
    return {row.id: row for row in registry.rows()}


@pytest.mark.network
def test_a_seeded_subset_of_the_candidates_rebuilds_to_its_hashes(tmp_path: Path) -> None:
    rows = rowsById()
    subset = readCsv(CANDIDATES).sample(SUBSET, random_state=SEED)
    tables = registry.Tables(tmp_path)
    rebuilt = {}
    for id in subset['id']:
        row = rows[id]
        rebuilt[id] = materialise(Problem.build(row, tables.load(row)), tmp_path)
    committed = dict(zip(subset['id'], subset['contract_hash']))
    assert rebuilt == committed
