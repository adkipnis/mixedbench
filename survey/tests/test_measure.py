"""The Measurer: the rows a registry row measures, its composite grouping factors and the codes
of a column's present levels, each through the measured file that shows it. The pass: a run per
registry row, collected into the measured files."""

import subprocess
import sys

import columns
import dimensions
import pandas as pd
import pytest
from conftest import (
    FIXTURES,
    MEASURED,
    SURVEY,
    asOrdered,
    measuredColumnFactors,
    mergeShard,
    parsed,
    readRows,
    runMeasure,
)
from measure import Measurement, Measurer
from mixedbench.registry.row import readCsv, writeCsv


def test_rows_without_a_measured_response_are_not_observations(herds, rows):
    """A pharmacokinetic table carries dosing rows with no concentration (the pilot's Phenobarb:
    744 rows, 155 measured); only rows with a response count, here 13 of 14 once the first
    weight is missing, so north holds 4 and h1 2."""
    unmeasured = herds.copy()
    unmeasured.loc[0, 'weight'] = float('nan')
    region, herd = dimensions.measure(Measurer(unmeasured, parsed(rows[0])))
    assert (region['n_obs'], herd['n_obs']) == (13, 13)
    assert (region['group_size_min'], herd['group_size_min']) == (4, 1)
    assert herd['group_size_p50'] == 2


def test_a_composite_grouping_factor_is_built_from_its_parts(herds, rows):
    """`region:breed` names no column: the measurer combines the two, a group per pair of
    levels present. Twelve pairs, north:angus and south:jersey hold two rows, the ten others
    one; the composite lies in region, so the relation is nested. breed and herd, no longer
    a factor, are covariate columns; the composite does not appear in columns.csv."""
    row = rows[0] | {'grouping_factors': 'region;region:breed'}
    measurer = Measurer(herds, parsed(row))
    region, pairs = dimensions.measure(measurer)
    assert pairs['factor'] == 'region:breed'
    assert (pairs['n_groups'], pairs['group_size_min'], pairs['group_size_max']) == (12, 1, 2)
    assert pairs['singleton_share'] == pytest.approx(10 / 12, abs=1e-4)
    assert (region['relation'], pairs['relation']) == ('nested', 'nested')
    assert [c['column'] for c in columns.measure(measurer)] == ['herd', 'breed', 'feed', 'parity', 'sick']  # fmt: skip


def test_a_level_no_measured_row_holds_leaves_no_gap_in_the_codes(herds, rows):
    """Parity's third level is held only by rows without a weight, so the measured rows code
    their three levels 0, 1 and 2 in loaded order, as if the unused level were removed. Codes
    0, 1 and 3 would move every numeric statistic of parity against herd."""
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    unmeasured = numbered.assign(weight=numbered['weight'].where(numbered['parity'] != 3))
    measured = unmeasured[unmeasured['weight'].notna()]
    compact = measured.assign(parity=measured['parity'].cat.remove_unused_categories())
    gapped = measuredColumnFactors(unmeasured, rows[0]).loc['parity']
    pd.testing.assert_frame_equal(gapped, measuredColumnFactors(compact, rows[0]).loc['parity'])


def test_the_measure_pass_writes_a_dimension_row_per_factor_and_a_column_row_per_column(merger):
    """No measured number is typed: the measure pass loads every registry row's table and
    writes one dimension row per grouping factor and one column row per covariate column
    (#18)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    runMeasure(merger)
    dimensions = readRows(merger.registry / 'dimensions.csv')
    assert [(r['model_index'], r['factor'], r['n_groups'], r['relation']) for r in dimensions] == [
        ('1', 'region', '3', 'nested'),
        ('1', 'herd', '5', 'nested'),
        ('2', 'herd', '5', 'single'),
    ]
    assert dimensions[0]['tier'] == 'D' and dimensions[0]['alpha'] == '65.0'
    columns = readRows(merger.registry / 'columns.csv')
    assert [(r['model_index'], r['column'], r['type']) for r in columns][:5] == [
        ('1', 'breed', 'categorical'),
        ('1', 'feed', 'categorical'),
        ('1', 'parity', 'ordered'),  # declared in the shard: pyreadr drops R's ordering
        ('1', 'sick', 'binary'),
        ('2', 'region', 'categorical'),
    ]
    assert len(columns) == 10


def test_the_measure_pass_writes_the_released_headers_and_a_left_out_statistic_as_blank(merger):
    """column_factors.csv and factor_pairs.csv carry their released headers, and dimensions.csv
    the two condition numbers after d_all. The nested region and herd pair has no empty-cell
    share, written as a blank cell (#99, #100)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    runMeasure(merger)
    column_factors = readRows(merger.registry / 'column_factors.csv')
    assert list(column_factors[0]) == [
        'source', 'object', 'model_index', 'tier', 'column', 'factor', 'between_group_share',
        'group_level_r2', 'absent_level_share', 'size_rho', 'within_sd_cv',
    ]  # fmt: skip
    pairs = readRows(merger.registry / 'factor_pairs.csv')
    assert list(pairs[0]) == [
        'source', 'object', 'model_index', 'tier', 'factor_a', 'factor_b', 'relation', 'superior',
        'empty_cell_share',
    ]  # fmt: skip
    assert pairs[0]['empty_cell_share'] == ''
    columns = list(readRows(merger.registry / 'dimensions.csv')[0])
    after = columns.index('d_all') + 1
    assert columns[after : after + 2] == ['condition_doc', 'condition_all']


def mergedHerds(merger) -> Measurement:
    """The pass over the scratch registry of the two herds rows."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    return Measurement(merger.registry, merger.loader, merger.survey / 'measure')


def test_the_collect_writes_every_rows_measurements_in_registry_order(merger):
    """Array tasks end in any order: the collect follows the registry. responses.csv is keyed
    like dimensions.csv, one row per registry row and its response."""
    measurement = mergedHerds(merger)

    measurement.run(1)
    measurement.run(0)
    measurement.collect()

    responses = readRows(merger.registry / 'responses.csv')
    keys = [
        (r['source'], r['object'], r['model_index'], r['tier'], r['response']) for r in responses
    ]
    assert keys == [
        ('herds', 'herds.csv', '1', 'D', 'weight'),
        ('herds', 'herds.csv', '2', 'D', 'cases'),
    ]


def test_the_collect_refuses_a_row_never_run(merger):
    """A task that crashed or was preempted is no row to leave out of the measured files."""
    measurement = mergedHerds(merger)

    measurement.run(0)

    with pytest.raises(FileNotFoundError):
        measurement.collect()


def test_a_failed_run_leaves_no_record_of_an_earlier_one(merger, monkeypatch):
    """A task killed for memory writes nothing, so a record of the row's last run would pass
    for this one in the collect."""
    measurement = mergedHerds(merger)
    measurement.run(0)
    measurement.run(1)

    monkeypatch.setattr(measurement.loader, 'load', raiseMemoryError)
    with pytest.raises(MemoryError):
        measurement.run(0)

    with pytest.raises(FileNotFoundError):
        measurement.collect()


def raiseMemoryError(*args) -> None:
    raise MemoryError


def test_the_collect_refuses_a_record_of_other_registry_cells(merger):
    """A shard merged after a row's run changes what the row measures, here a column it ignores,
    so its record no longer measures the registry's row."""
    measurement = mergedHerds(merger)
    measurement.run(0)
    measurement.run(1)
    cells = readCsv(merger.registry / 'registry.csv')
    cells.loc[0, 'ignore'] = 'sick'
    writeCsv(cells, merger.registry / 'registry.csv')

    edited = Measurement(merger.registry, merger.loader, merger.survey / 'measure')

    with pytest.raises(ValueError, match='herds/herds.csv/1.*ignore'):
        edited.collect()


def test_the_measure_script_writes_the_measured_files_and_the_summary(merger):
    """`measure.py run` measures one registry row, as a cluster array task, and `collect` writes
    the measured files and the summary (#98, #172, #182). It loads from the cache the merge
    filled, so the run is offline."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    runMeasure(merger)
    measured = {name: (merger.registry / name).read_bytes() for name in MEASURED}
    for name in MEASURED:
        (merger.registry / name).unlink()
    folders = ['--registry', merger.registry, '--survey', merger.survey, '--dir', merger.survey / 'measure']  # fmt: skip
    for command in (['run', '0'], ['run', '1'], ['collect']):
        subprocess.run([sys.executable, SURVEY / 'measure.py', *command, *folders], check=True)
    assert {name: (merger.registry / name).read_bytes() for name in MEASURED} == measured
