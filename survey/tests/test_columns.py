"""columns.csv from `fixtures/herds.csv`: types and levels, moments, bounds, shares and rank
correlations, each expected value worked by hand or by scipy, and the shares' ranges over
generated tables."""

import columns
import pandas as pd
import pytest
from columns import COLUMN_STATISTICS
from conftest import GENERATED, asOrdered, measuredColumns, parsed, tables
from hypothesis import given, settings
from measure import Measurer


SHARES = ('outlier_share', 'zero_share', 'min_share', 'max_share', 'unique_share', 'rare_level_share', 'max_abs_rho')  # fmt: skip


def typed(column: dict) -> tuple:
    return (
        column['type'],
        column['K'],
        column['level'],
        column['constant_within'],
        column['in_model'],
    )


def test_column_types_and_levels_by_the_one_rule(herds, rows):
    """Model 1 leaves breed, feed, parity and sick as covariate columns (response, factors
    and the ignore list are out). breed and feed are declared categoricals; parity is an
    integer with four distinct values, continuous all the same (#108); sick has two values,
    hence binary.
    feed is constant within every herd, so group-level there, but varies within region."""
    measured = columns.measure(Measurer(herds, parsed(rows[0])))
    assert [c['column'] for c in measured] == ['breed', 'feed', 'parity', 'sick']
    assert typed(measured[0]) == ('categorical', 4, 'within', '', 'yes')
    assert typed(measured[1]) == ('categorical', 3, 'group', 'herd', 'yes')
    assert typed(measured[2]) == ('continuous', '', 'within', '', 'no')
    assert typed(measured[3]) == ('binary', 2, 'within', '', 'no')
    assert measured[0]['tier'] == 'D' and measured[0]['model_index'] == 1
    assert {c['missing_share'] for c in measured} == {0}


def test_ordered_and_missing_values(herds, rows):
    """An ordered categorical keeps its own type; one missing value in fourteen."""
    varied = herds.assign(parity=herds['parity'].astype(pd.CategoricalDtype([1, 2, 3, 4], ordered=True)))  # fmt: skip
    varied.loc[0, 'weight'] = float('nan')
    row = rows[0] | {'response': 'sick', 'covariates': 'weight', 'ignore': 'id;cases;trials'}  # fmt: skip
    measured = {c['column']: c for c in columns.measure(Measurer(varied, parsed(row)))}
    assert set(measured) == {'breed', 'feed', 'parity', 'weight'}
    assert (measured['parity']['type'], measured['parity']['K']) == ('ordered', 4)
    assert (measured['weight']['type'], measured['weight']['K']) == ('continuous', '')
    assert measured['weight']['missing_share'] == pytest.approx(1 / 14, abs=1e-4)


def test_the_missing_share_comes_with_the_shape_and_the_shape_counts_present_values(herds):
    """The flat pass measures tables that have no registry row, so one column's missing share
    and shape need no Measurer. One weight missing in fourteen; the thirteen present weights
    are all distinct, a unique share of 1, not 13/14."""
    weight = herds['weight'].copy()
    weight[0] = float('nan')
    shape = columns.measureShape(weight, 'continuous')
    assert (shape['missing_share'], shape['unique_share']) == (0.0714, 1)


def test_a_continuous_columns_moments(herds, rows):
    """Weight under model 2 against scipy.stats.skew and kurtosis with bias=False, the
    sample-adjusted G1 and G2. Fourteen rows cannot hold |z| > 4 (at most 13/√14 ≈ 3.47)."""
    weight = measuredColumns(herds, rows[1]).loc['weight']
    assert (weight['skewness'], weight['excess_kurtosis']) == (0.5207, -0.6651)
    assert weight['outlier_share'] == 0


def test_an_outlier_lies_beyond_four_sample_standard_deviations(herds, rows):
    """The table three times over with the first weight at 5000: that weight lies at z ≈ 6.3,
    the 41 others below 0.2 in absolute value; scipy gives G1 6.4398 and G2 41.6368."""
    skewed = pd.concat([herds, herds, herds], ignore_index=True)
    skewed.loc[0, 'weight'] = 5000.0
    weight = measuredColumns(skewed, rows[1]).loc['weight']
    assert (weight['skewness'], weight['excess_kurtosis']) == (6.4398, 41.6368)
    assert weight['outlier_share'] == round(1 / 42, 4)


def test_a_constant_column_has_no_moments(herds, rows):
    """A constant column has no standard deviation to scale by, so its moments are blank."""
    dose = measuredColumns(herds.assign(dose=2.5), rows[1]).loc['dose']
    assert dose['type'] == 'continuous'
    assert dose[['skewness', 'excess_kurtosis', 'outlier_share']].isna().all()


def test_a_continuous_columns_shares_at_zero_and_at_its_bounds(herds, rows):
    """Weight's minimum and maximum occur once each, zero never. Three weights set to zero
    make zero the minimum, held by three rows. A constant column sits at both bounds."""
    weight = measuredColumns(herds, rows[1]).loc['weight']
    assert (weight['zero_share'], weight['min_share'], weight['max_share']) == (0, 0.0714, 0.0714)
    zeroed = herds.copy()
    zeroed.loc[:2, 'weight'] = 0.0
    weight = measuredColumns(zeroed, rows[1]).loc['weight']
    assert (weight['zero_share'], weight['min_share']) == (0.2143, 0.2143)
    dose = measuredColumns(herds.assign(dose=2.5), rows[1]).loc['dose']
    assert (dose['zero_share'], dose['min_share'], dose['max_share']) == (0, 1, 1)


def test_an_ordered_columns_bounds_are_its_lowest_and_highest_levels(herds, rows):
    """Parity as an ordered factor: five rows at its lowest level, one at its highest. Its
    zero share reads the levels as loaded: levels 0 to 3 put the five lowest rows at zero,
    and named levels leave it blank."""
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    parity = measuredColumns(numbered, rows[1]).loc['parity']
    assert (parity['zero_share'], parity['min_share'], parity['max_share']) == (0, 0.3571, 0.0714)
    fromZero = herds.assign(parity=asOrdered(herds['parity'] - 1, [0, 1, 2, 3]))
    assert measuredColumns(fromZero, rows[1]).loc['parity', 'zero_share'] == 0.3571
    names = ['first', 'second', 'third', 'fourth']
    named = herds.assign(parity=asOrdered(herds['parity'].map(dict(zip([1, 2, 3, 4], names))), names))  # fmt: skip
    parity = measuredColumns(named, rows[1]).loc['parity']
    assert pd.isna(parity['zero_share'])
    assert (parity['min_share'], parity['max_share']) == (0.3571, 0.0714)


def test_unique_and_rare_level_shares(herds, rows):
    """Model 2's columns: weight is all distinct and has no levels; breed has four levels, the
    smallest held by three rows; sick has two, five rows ill; parity, an integer, has four
    distinct values and no levels; ordered, its smallest level holds a 4 once. A categorical's
    unused level holds no row and is not its rarest."""
    columns = measuredColumns(herds, rows[1])
    shares = columns[['unique_share', 'rare_level_share']]
    assert shares.loc['weight', 'unique_share'] == 1
    assert pd.isna(shares.loc['weight', 'rare_level_share'])
    assert tuple(shares.loc['breed']) == (0.2857, 0.2143)
    assert tuple(shares.loc['sick']) == (0.1429, 0.3571)
    assert shares.loc['parity', 'unique_share'] == 0.2857
    assert pd.isna(shares.loc['parity', 'rare_level_share'])
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    assert measuredColumns(numbered, rows[1]).loc['parity', 'rare_level_share'] == 0.0714
    unused = herds.assign(breed=herds['breed'].cat.add_categories('dexter'))
    assert measuredColumns(unused, rows[1]).loc['breed', 'rare_level_share'] == 0.2143


def test_a_column_missing_on_every_measured_row_has_no_statistic(herds, rows):
    """Eight columns of the registry are missing wherever the response is measured."""
    empty = measuredColumns(herds.assign(empty=float('nan')), rows[1]).loc['empty']
    assert empty[list(COLUMN_STATISTICS)].isna().all()


def test_max_abs_rho_ranks_continuous_binary_and_ordered_columns(herds, rows):
    """Model 2 ranks weight, sick and integer parity, by scipy.stats.spearmanr: 0.6841 between
    weight and sick, parity 0.3029 with weight and 0.4864 with sick. Region, breed and feed are
    categoricals of more than two levels and pair with nothing. Ordered, parity ranks by its
    levels, to the same values."""
    rho = measuredColumns(herds, rows[1])['max_abs_rho']
    assert (rho['weight'], rho['sick'], rho['parity']) == (0.6841, 0.6841, 0.4864)
    assert rho[['region', 'breed', 'feed']].isna().all()
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    rho = measuredColumns(numbered, rows[1])['max_abs_rho']
    assert (rho['weight'], rho['sick'], rho['parity']) == (0.6841, 0.6841, 0.4864)


def test_max_abs_rho_ranks_the_typed_columns_of_a_table(herds):
    """The flat pass ranks tables that have no registry row, so the step takes a table and its
    column types. The values are model 2's, by scipy.stats.spearmanr; the herds columns given
    no type (id, cases, trials and the factors) take no part, as a row's response does."""
    types = {
        'weight': ('continuous', ''),
        'sick': ('binary', 2),
        'parity': ('continuous', ''),
        'breed': ('categorical', 4),
    }
    rho = columns.measureMaxAbsRho(herds, types)
    assert list(rho.index) == ['weight', 'sick', 'parity', 'breed']
    assert (rho['weight'], rho['sick'], rho['parity']) == (0.6841, 0.6841, 0.4864)
    assert pd.isna(rho['breed'])


def test_max_abs_rho_pairs_over_the_rows_both_columns_observe(herds, rows):
    """A missing weight leaves 13 rows to pair with sick (scipy: 0.6761) and parity (0.2856). A
    column observed on the nine healthy rows only pairs with weight (0.5295) and parity (0.0404)
    there, not with sick, constant on those rows. A constant column pairs with nothing; neither
    does model 1's sick once parity is ignored, the one other column there that is not a
    categorical of more than two levels."""
    unweighed = herds.copy()
    unweighed.loc[0, 'weight'] = float('nan')
    assert measuredColumns(unweighed, rows[1]).loc['weight', 'max_abs_rho'] == 0.6761
    tested = herds['trials'].where(herds['sick'] == 0).astype(float)
    rho = measuredColumns(herds.assign(tested=tested, dose=2.5), rows[1])['max_abs_rho']
    assert (rho['tested'], rho['weight'], rho['sick']) == (0.5295, 0.6841, 0.6841)
    assert pd.isna(rho['dose'])
    alone = rows[0] | {'ignore': 'id;cases;trials;parity'}
    assert pd.isna(measuredColumns(herds, alone).loc['sick', 'max_abs_rho'])


@settings(max_examples=100, deadline=None)
@given(table=tables())
def test_shares_and_correlations_lie_in_the_unit_interval_and_no_level_is_above_its_share(table):
    """Whatever the column, a share and an absolute correlation lie in [0, 1] or are blank, and
    the rarest of K levels holds at most 1/K of the rows."""
    columns = measuredColumns(table, GENERATED)
    for share in SHARES:
        values = columns[share].dropna()
        assert values.between(0, 1).all(), share
    levelled = columns.dropna(subset='rare_level_share')
    assert (levelled['rare_level_share'] <= 1 / levelled['K'].astype(int) + 1e-4).all()
