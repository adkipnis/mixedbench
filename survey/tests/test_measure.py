"""Measuring one loaded table against its registry row (#18): group sizes per factor, the
Dirichlet α, the relation between factors, column types and levels, d_doc and d_all, every
expected value computed by hand from `fixtures/herds.csv`."""

import numpy as np
import pandas as pd
import pytest
from conftest import FIXTURES, readRows
from measure import COLUMN_COLUMNS, Measurer, fitAlpha
from mixedbench.registry.row import Row
from schema import REGISTRY

CATEGORICAL = ('region', 'herd', 'breed', 'feed')


@pytest.fixture
def herds() -> pd.DataFrame:
    """The table as the loader returns it: the declared columns as pandas categoricals."""
    table = pd.read_csv(FIXTURES / 'herds.csv')
    return table.astype({c: 'category' for c in CATEGORICAL})


@pytest.fixture
def rows() -> list[dict]:
    rows = readRows(FIXTURES / 'registry_herds.csv')
    for row in rows:
        row['tier'] = 'D'
    return rows


def parsed(cells: dict) -> Row:
    """A shard row as the merge reads it: the script columns blank, but the tier."""
    blank = {c: '' for c in REGISTRY.scriptColumns}
    return Row.parse(blank | cells)


def measuredColumns(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The columns.csv rows of one registry row, by column; a statistic left out is blank."""
    columns = Measurer(table, parsed(cells)).columns()
    return pd.DataFrame(columns, columns=COLUMN_COLUMNS).set_index('column')


def test_group_sizes_per_factor(herds, rows):
    """Region holds 5, 5 and 4 rows; herd holds 3, 2, 4, 1 and 4, so h4 is a singleton.
    Quantiles are observed sizes (at or below the level under p50, at or above from p50 on);
    the coefficient of variation uses the population standard deviation."""
    dimensions = Measurer(herds, parsed(rows[0])).dimensions()
    assert [d['factor'] for d in dimensions] == ['region', 'herd']
    region, herd = dimensions
    assert (region['source'], region['object'], region['model_index'], region['tier']) == ('herds', 'herds.csv', 1, 'D')  # fmt: skip
    assert region['n_obs'] == 14 and herd['n_obs'] == 14
    assert (region['n_groups'], herd['n_groups']) == (3, 5)
    sizes = lambda d: tuple(d[k] for k in ('group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max'))  # fmt: skip
    assert sizes(region) == (4, 4, 5, 5, 5)
    assert sizes(herd) == (1, 1, 3, 4, 4)
    assert (region['singleton_share'], herd['singleton_share']) == (0, 0.2)
    assert region['cv'] == pytest.approx(0.10102, abs=1e-4)
    assert herd['cv'] == pytest.approx(0.41650, abs=1e-4)


def test_rows_without_a_measured_response_are_not_observations(herds, rows):
    """A pharmacokinetic table carries dosing rows with no concentration (the pilot's Phenobarb:
    744 rows, 155 measured); only rows with a response count, here 13 of 14 once the first
    weight is missing, so north holds 4 and h1 2."""
    unmeasured = herds.copy()
    unmeasured.loc[0, 'weight'] = float('nan')
    region, herd = Measurer(unmeasured, parsed(rows[0])).dimensions()
    assert (region['n_obs'], herd['n_obs']) == (13, 13)
    assert (region['group_size_min'], herd['group_size_min']) == (4, 1)
    assert herd['group_size_p50'] == 2


def test_alpha_by_moment_matching(herds, rows):
    """Region sizes 5, 5, 4 give α = 65 exactly ((1 − 1/m) / (m s²) = 196); herd sizes
    3, 2, 4, 1, 4 give 4.41. A balanced allocation has zero variance, so α is infinite."""
    region, herd = Measurer(herds, parsed(rows[0])).dimensions()
    assert region['alpha'] == pytest.approx(65.0, abs=1e-3)
    assert herd['alpha'] == pytest.approx(4.4118, abs=1e-3)
    assert fitAlpha(pd.Series([10, 10, 10, 10])) == float('inf')


@pytest.mark.parametrize('alpha', [0.3, 2.0, 20.0])
def test_alpha_recovers_the_generating_concentration(alpha):
    """Moment matching on proportions drawn from a symmetric Dirichlet with many groups gives
    the concentration back; sizes are the proportions times a large n_obs."""
    rng = np.random.default_rng(0)
    proportions = rng.dirichlet(np.full(2000, alpha))
    sizes = pd.Series(np.round(proportions * 1e7).astype(int))
    assert fitAlpha(sizes) == pytest.approx(alpha, rel=0.1)


@pytest.mark.parametrize(
    'factors, relation',
    [
        ('herd', 'single'),
        ('region;herd', 'nested'),  # every herd lies in one region
        ('herd;breed', 'crossed'),  # angus occurs in four herds, h1 holds three breeds
        ('region;herd;breed', 'mixed'),  # one nested pair, two crossed ones
    ],
)
def test_relation_between_grouping_factors_is_computed_from_the_data(
    herds, rows, factors, relation
):
    row = rows[0] | {'grouping_factors': factors, 'covariates': ''}  # breed may be a factor here
    dimensions = Measurer(herds, parsed(row)).dimensions()
    assert {d['relation'] for d in dimensions} == {relation}
    assert {d['n_factors'] for d in dimensions} == {len(dimensions)}


def test_a_composite_grouping_factor_is_built_from_its_parts(herds, rows):
    """`region:breed` names no column: the measurer combines the two, a group per pair of
    levels present. Twelve pairs, north:angus and south:jersey hold two rows, the ten others
    one; the composite lies in region, so the relation is nested. breed and herd, no longer
    a factor, are covariate columns; the composite does not appear in columns.csv."""
    row = rows[0] | {'grouping_factors': 'region;region:breed'}
    measurer = Measurer(herds, parsed(row))
    region, pairs = measurer.dimensions()
    assert pairs['factor'] == 'region:breed'
    assert (pairs['n_groups'], pairs['group_size_min'], pairs['group_size_max']) == (12, 1, 2)
    assert pairs['singleton_share'] == pytest.approx(10 / 12, abs=1e-4)
    assert (region['relation'], pairs['relation']) == ('nested', 'nested')
    assert [c['column'] for c in measurer.columns()] == ['herd', 'breed', 'feed', 'parity', 'sick']  # fmt: skip


def test_column_types_and_levels_by_the_one_rule(herds, rows):
    """Model 1 leaves breed, feed, parity and sick as covariate columns (response, factors
    and the ignore list are out). breed and feed are declared categoricals; parity is an
    integer with four distinct values, hence categorical; sick has two values, hence binary.
    feed is constant within every herd, so group-level there, but varies within region."""
    columns = Measurer(herds, parsed(rows[0])).columns()
    assert [c['column'] for c in columns] == ['breed', 'feed', 'parity', 'sick']
    typed = lambda c: (c['type'], c['K'], c['level'], c['constant_within'], c['in_model'])
    assert typed(columns[0]) == ('categorical', 4, 'within', '', 'yes')
    assert typed(columns[1]) == ('categorical', 3, 'group', 'herd', 'yes')
    assert typed(columns[2]) == ('categorical', 4, 'within', '', 'no')
    assert typed(columns[3]) == ('binary', 2, 'within', '', 'no')
    assert columns[0]['tier'] == 'D' and columns[0]['model_index'] == 1
    assert {c['missing_share'] for c in columns} == {0}


def test_ordered_declared_continuous_and_missing_values(herds, rows):
    """An ordered categorical keeps its own type; a registry declaration of continuous
    overrides the ten-distinct-values rule for an integer; one missing value in fourteen."""
    varied = herds.assign(parity=herds['parity'].astype(pd.CategoricalDtype([1, 2, 3, 4], ordered=True)))  # fmt: skip
    varied.loc[0, 'weight'] = float('nan')
    row = rows[0] | {'response': 'sick', 'covariates': 'weight', 'ignore': 'id;cases;trials', 'types': 'parity=continuous'}  # fmt: skip
    columns = {c['column']: c for c in Measurer(varied, parsed(row)).columns()}
    assert set(columns) == {'breed', 'feed', 'parity', 'weight'}
    assert (columns['parity']['type'], columns['parity']['K']) == ('ordered', 4)
    assert (columns['weight']['type'], columns['weight']['K']) == ('continuous', '')
    assert columns['weight']['missing_share'] == pytest.approx(1 / 14, abs=1e-4)
    declared = rows[0] | {'types': 'parity=continuous'}
    columns = {c['column']: c for c in Measurer(herds, parsed(declared)).columns()}
    assert columns['parity']['type'] == 'continuous'


def test_design_columns_of_the_documented_model_and_of_the_whole_table(herds, rows):
    """Model 1: breed (4 levels) and feed (3) give d_doc = 3 + 2 = 5; parity (4) and sick (binary)
    bring d_all to 9; an interaction breed:feed adds 3 × 2 to both, so d_all is never below
    d_doc. Model 2 names only breed, and the region column, no longer a factor, counts 2 in
    its d_all."""
    dimensions = Measurer(herds, parsed(rows[0])).dimensions()
    assert {(d['d_doc'], d['d_all']) for d in dimensions} == {(5, 9)}
    interacting = rows[0] | {'interactions': 'breed:feed'}
    interacted = Measurer(herds, parsed(interacting)).dimensions()[0]
    assert (interacted['d_doc'], interacted['d_all']) == (11, 15)
    assert Measurer(herds, parsed(rows[1])).dimensions()[0]['d_doc'] == 3
    assert Measurer(herds, parsed(rows[1])).dimensions()[0]['d_all'] == 12


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


def asOrdered(values: pd.Series, levels: list) -> pd.Series:
    return values.astype(pd.CategoricalDtype(levels, ordered=True))


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
    smallest held by three rows; sick has two, five rows ill; parity, an integer column of four
    levels, holds a 4 once; ordered, its smallest level is the same. A categorical's unused
    level holds no row and is not its rarest."""
    columns = measuredColumns(herds, rows[1])
    shares = columns[['unique_share', 'rare_level_share']]
    assert shares.loc['weight', 'unique_share'] == 1
    assert pd.isna(shares.loc['weight', 'rare_level_share'])
    assert tuple(shares.loc['breed']) == (0.2857, 0.2143)
    assert tuple(shares.loc['sick']) == (0.1429, 0.3571)
    assert tuple(shares.loc['parity']) == (0.2857, 0.0714)
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    assert measuredColumns(numbered, rows[1]).loc['parity', 'rare_level_share'] == 0.0714
    unused = herds.assign(breed=herds['breed'].cat.add_categories('dexter'))
    assert measuredColumns(unused, rows[1]).loc['breed', 'rare_level_share'] == 0.2143


def test_a_column_missing_on_every_measured_row_has_no_statistic(herds, rows):
    """Eight columns of the registry are missing wherever the response is measured."""
    empty = measuredColumns(herds.assign(empty=float('nan')), rows[1]).loc['empty']
    statistics = COLUMN_COLUMNS[COLUMN_COLUMNS.index('in_model') + 1 :]
    assert empty[list(statistics)].isna().all()


def test_max_abs_rho_ranks_continuous_binary_and_ordered_columns(herds, rows):
    """Model 2 ranks weight and sick, 0.6841 by scipy.stats.spearmanr; region, breed, feed and
    integer parity are categoricals of more than two levels and pair with nothing. Ordered,
    parity ranks too: 0.3029 with weight, 0.4864 with sick."""
    rho = measuredColumns(herds, rows[1])['max_abs_rho']
    assert (rho['weight'], rho['sick']) == (0.6841, 0.6841)
    assert rho[['region', 'breed', 'feed', 'parity']].isna().all()
    numbered = herds.assign(parity=asOrdered(herds['parity'], [1, 2, 3, 4]))
    rho = measuredColumns(numbered, rows[1])['max_abs_rho']
    assert (rho['weight'], rho['sick'], rho['parity']) == (0.6841, 0.6841, 0.4864)


def test_max_abs_rho_pairs_over_the_rows_both_columns_observe(herds, rows):
    """A missing weight leaves 13 rows to pair with sick (scipy: 0.6761). A column observed on
    the nine healthy rows only pairs with weight there (0.5295), not with sick, constant on
    those rows. A constant column pairs with nothing; neither does model 1's sick, the one
    column there that is not a categorical of more than two levels."""
    unweighed = herds.copy()
    unweighed.loc[0, 'weight'] = float('nan')
    assert measuredColumns(unweighed, rows[1]).loc['weight', 'max_abs_rho'] == 0.6761
    tested = herds['trials'].where(herds['sick'] == 0).astype(float)
    rho = measuredColumns(herds.assign(tested=tested, dose=2.5), rows[1])['max_abs_rho']
    assert (rho['tested'], rho['weight'], rho['sick']) == (0.5295, 0.6841, 0.6841)
    assert pd.isna(rho['dose'])
    assert pd.isna(measuredColumns(herds, rows[0]).loc['sick', 'max_abs_rho'])
