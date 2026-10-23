"""The Measurer: the rows a registry row measures, its composite grouping factors and the codes
of a column's present levels, each through the measured file that shows it."""

import columns
import dimensions
import pandas as pd
import pytest
from conftest import asOrdered, measuredColumnFactors, parsed
from measure import Measurer


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
