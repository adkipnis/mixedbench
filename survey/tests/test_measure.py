"""The Measurer: the rows a registry row measures, its composite grouping factors and the codes
of a column's present levels, each through the measured file that shows it. The pass: a run per
registry row, collected into the measured files."""

import columns
import dimensions
import pandas as pd
import pytest
from conftest import FIXTURES, asOrdered, measuredColumnFactors, mergeShard, parsed, readRows
from measure import Measurement, Measurer


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


def mergedHerds(merger) -> Measurement:
    """The pass over the scratch registry of the two herds rows."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    return Measurement(merger.registry, merger.loader, merger.survey / 'measure')


def test_the_collect_writes_every_rows_measurements_in_registry_order(merger):
    """Array tasks end in any order: the collect follows the registry, a response per row."""
    measurement = mergedHerds(merger)

    measurement.run(1)
    measurement.run(0)
    measurement.collect()

    responses = readRows(merger.registry / 'responses.csv')
    assert [r['response'] for r in responses] == ['weight', 'cases']


def test_the_collect_refuses_a_row_never_run(merger):
    """A task that crashed or was preempted is no row to leave out of the measured files."""
    measurement = mergedHerds(merger)

    measurement.run(0)

    with pytest.raises(FileNotFoundError):
        measurement.collect()
