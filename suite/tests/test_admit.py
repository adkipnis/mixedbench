"""The admission script (#32): over a scratch registry it writes the suite's candidate list,
one row per admissible registry row in registry order, and reports what it refused and the top
of the dropped-share distribution (ADR 0002). Run by hand: `uv run pytest suite/tests`.

The scratch registry is a `registry.csv` written in the package's dialect and read back through
`registry.rows`; every row loads one small grouped table, held in memory by object name.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from mixedbench import registry
from mixedbench.contract import contractHash, load
from mixedbench.registry.row import COLUMNS, Row, readCsv, writeCsv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the suite's scripts

from admit import Admission

CELLS = {column: '' for column in COLUMNS} | {
    'source': 'fixture', 'tier': 'R', 'reader': 'pandas', 'licence': 'MIT', 'model_index': '1',
    'response': 'y', 'response_type': 'continuous', 'grouping_factors': 'g', 'covariates': 'x',
    'formula': 'y ~ x + (1 | g)', 'published_model': 'yes', 'domain': 'test',
    'confidence': 'high', 'verified': 'high',
}  # fmt: skip


def groupedTable(missing: int = 0) -> pd.DataFrame:
    """Twelve rows over four groups; the first `missing` rows lack their response."""
    y = [float(i % 5) for i in range(12)]
    y[:missing] = [float('nan')] * missing
    return pd.DataFrame({'g': [f'g{i % 4}' for i in range(12)], 'x': range(12), 'y': y})


def scratchRegistry(dir: Path, objects: list[str], **overrides: str) -> list[Row]:
    """A `registry.csv` with one row per object, in the given order, read back typed."""
    file = dir / 'registry.csv'
    cells = [CELLS | {'object': name, 'sources': f'fixture:{name}'} | overrides for name in objects]
    writeCsv(pd.DataFrame(cells, columns=COLUMNS), file)
    return registry.rows(file)


class Tables:
    """The loaded table per object name, as the loader would give it."""

    def __init__(self, tables: dict[str, pd.DataFrame]) -> None:
        self.tables = tables

    def __call__(self, row: Row) -> pd.DataFrame:
        return self.tables[row.object]


# =====================================================================================
# the candidate list
# =====================================================================================
def test_the_list_has_one_row_per_admissible_row_in_registry_order_with_its_hash(tmp_path):
    """The list item 5 runs references on: registry order, not sorted by id, and each hash the
    one the materialized files verify against, so the list and the cache agree."""
    objects = ['zeta', 'alpha', 'mid']
    rows = scratchRegistry(tmp_path, objects)
    tables = Tables(
        {'zeta': groupedTable(), 'alpha': groupedTable(missing=3), 'mid': groupedTable()}
    )
    admission = Admission(rows, tables, tmp_path / 'cache')
    admitted = admission.admit()
    candidates = admitted.candidates
    assert list(candidates['id']) == [f'fixture/{name}/1' for name in objects]
    assert list(candidates.columns) == [
        'id',
        'contract_hash',
        'verified',
        'dropped_share',
        'fidelity',
    ]
    assert list(candidates['dropped_share']) == [0, 0.25, 0]
    for id, hash in zip(candidates['id'], candidates['contract_hash']):
        assert hash == contractHash(load(id, tmp_path / 'cache'))


def test_a_refused_row_leaves_the_list_and_keeps_its_reason(tmp_path):
    """Three ways a row is refused, each with the reason the report prints: the family rule
    (a categorical response), a hand decision (a nonlinear model, #27), and a table with no
    complete row, which only `Problem.build` can see (Phenobarb, #29)."""
    rows = [
        *scratchRegistry(tmp_path, ['kept']),
        *scratchRegistry(tmp_path, ['colours'], response_type='categorical'),
        *scratchRegistry(tmp_path, ['curve']),
        *scratchRegistry(tmp_path, ['empty']),
    ]
    tables = Tables({name: groupedTable() for name in ['kept', 'colours', 'curve']})
    tables.tables['empty'] = groupedTable(missing=12)
    refused = {'fixture/curve/1': 'nonlinear_parameter_model: random effects on curve parameters'}
    admission = Admission(rows, tables, tmp_path / 'cache', refused=refused)
    admitted = admission.admit()
    assert list(admitted.candidates['id']) == ['fixture/kept/1']
    assert set(admitted.refused) == {'fixture/colours/1', 'fixture/curve/1', 'fixture/empty/1'}
    assert 'categorical response' in admitted.refused['fixture/colours/1']
    assert admitted.refused['fixture/curve/1'].startswith('nonlinear_parameter_model')
    assert 'no row has every model value' in admitted.refused['fixture/empty/1']


def test_a_row_whose_random_effects_were_changed_carries_its_fidelity(tmp_path):
    """The slope decisions of #27 and the dropped terms of #45 travel with the problem into the
    list; a row the parser filled unchanged has none."""
    rows = scratchRegistry(tmp_path, ['changed', 'same'])
    tables = Tables({'changed': groupedTable(), 'same': groupedTable()})
    fidelity = {'fixture/changed/1': 'approximate'}
    admission = Admission(rows, tables, tmp_path / 'cache', fidelity=fidelity)
    candidates = admission.admit().candidates
    assert list(candidates['fidelity']) == ['approximate', '']


class FailingTables(Tables):
    """The loader's verdict on a rotted source: a checksum mismatch."""

    def __call__(self, row: Row) -> pd.DataFrame:
        if row.object == 'rotted':
            raise ValueError('rotted.csv: checksum mismatch')
        return super().__call__(row)


def test_a_row_that_fails_to_load_is_reported_with_its_error_not_refused(tmp_path):
    """A row the cache cannot give is never dropped silently: it is a failure, kept apart from
    the refusals, since a failure is fixed by fetching and a refusal by the contract."""
    rows = scratchRegistry(tmp_path, ['kept', 'rotted'])
    admission = Admission(rows, FailingTables({'kept': groupedTable()}), tmp_path / 'cache')
    admitted = admission.admit()
    assert list(admitted.candidates['id']) == ['fixture/kept/1']
    assert admitted.refused == {}
    assert admitted.failed == {'fixture/rotted/1': 'ValueError: rotted.csv: checksum mismatch'}


def test_the_report_names_the_refused_rows_and_the_top_dropped_shares(tmp_path):
    """What Alex reads before a reference is run: every refusal with its reason, and the rows
    losing most to missing values, largest first, since ADR 0002 caps no dropped share."""
    rows = [
        *scratchRegistry(tmp_path, ['none', 'most', 'some']),
        *scratchRegistry(tmp_path, ['colours'], response_type='categorical'),
    ]
    tables = Tables(
        {
            'none': groupedTable(),
            'most': groupedTable(6),
            'some': groupedTable(3),
            'colours': groupedTable(),
        }
    )
    admission = Admission(rows, tables, tmp_path / 'cache')
    report = admission.admit().report(top=2)
    assert 'fixture/colours/1' in report
    assert 'categorical response' in report
    assert report.index('fixture/most/1') < report.index('fixture/some/1')
    assert '0.5' in report
    assert 'fixture/none/1' not in report


def test_the_list_and_the_refusals_are_written_beside_each_other(tmp_path):
    """A suite version records why a registry row is out as well as which are in, since the
    registry keeps every row (ADR 0002): both files in registry order, in the package's dialect."""
    rows = [
        *scratchRegistry(tmp_path, ['kept']),
        *scratchRegistry(tmp_path, ['colours'], response_type='categorical'),
        *scratchRegistry(tmp_path, ['curve']),
    ]
    tables = Tables({name: groupedTable() for name in ['kept', 'colours', 'curve']})
    refused = {'fixture/curve/1': 'nonlinear_parameter_model: a curve (#27)'}
    admission = Admission(rows, tables, tmp_path / 'cache', refused=refused)
    admission.admit().write(tmp_path / 'suite')
    candidates = readCsv(tmp_path / 'suite' / 'candidates.csv')
    written = readCsv(tmp_path / 'suite' / 'refused.csv')
    assert list(candidates['id']) == ['fixture/kept/1']
    assert list(written.columns) == ['id', 'reason']
    assert list(written['id']) == ['fixture/colours/1', 'fixture/curve/1']
    assert written['reason'].iloc[1] == 'nonlinear_parameter_model: a curve (#27)'
