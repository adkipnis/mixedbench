"""Measuring one loaded table against its registry row: its rows of the four measured files
from `fixtures/herds.csv`, each expected value worked by hand or by scipy, statsmodels or numpy,
and the statistics' ranges over generated tables."""

import numpy as np
import pandas as pd
import pytest
from conftest import FIXTURES, readRows
from hypothesis import given, settings
from hypothesis import strategies as st
from measure import (
    COLUMN_COLUMNS,
    COLUMN_FACTOR_COLUMNS,
    COLUMN_FACTOR_STATISTICS,
    COLUMN_STATISTICS,
    DIMENSION_COLUMNS,
    FACTOR_PAIR_COLUMNS,
    Measurer,
    fitAlpha,
)
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
    integer with four distinct values, continuous all the same (#108); sick has two values,
    hence binary.
    feed is constant within every herd, so group-level there, but varies within region."""
    columns = Measurer(herds, parsed(rows[0])).columns()
    assert [c['column'] for c in columns] == ['breed', 'feed', 'parity', 'sick']
    typed = lambda c: (c['type'], c['K'], c['level'], c['constant_within'], c['in_model'])
    assert typed(columns[0]) == ('categorical', 4, 'within', '', 'yes')
    assert typed(columns[1]) == ('categorical', 3, 'group', 'herd', 'yes')
    assert typed(columns[2]) == ('continuous', '', 'within', '', 'no')
    assert typed(columns[3]) == ('binary', 2, 'within', '', 'no')
    assert columns[0]['tier'] == 'D' and columns[0]['model_index'] == 1
    assert {c['missing_share'] for c in columns} == {0}


def test_ordered_and_missing_values(herds, rows):
    """An ordered categorical keeps its own type; one missing value in fourteen."""
    varied = herds.assign(parity=herds['parity'].astype(pd.CategoricalDtype([1, 2, 3, 4], ordered=True)))  # fmt: skip
    varied.loc[0, 'weight'] = float('nan')
    row = rows[0] | {'response': 'sick', 'covariates': 'weight', 'ignore': 'id;cases;trials'}  # fmt: skip
    columns = {c['column']: c for c in Measurer(varied, parsed(row)).columns()}
    assert set(columns) == {'breed', 'feed', 'parity', 'weight'}
    assert (columns['parity']['type'], columns['parity']['K']) == ('ordered', 4)
    assert (columns['weight']['type'], columns['weight']['K']) == ('continuous', '')
    assert columns['weight']['missing_share'] == pytest.approx(1 / 14, abs=1e-4)


def test_design_columns_of_the_documented_model_and_of_the_whole_table(herds, rows):
    """Model 1: breed (4 levels) and feed (3) give d_doc = 3 + 2 = 5; parity (an integer) and
    sick (binary) bring d_all to 7; an interaction breed:feed adds 3 × 2 to both, so d_all is
    never below d_doc. Model 2 names only breed, and the region column, no longer a factor,
    counts 2 in its d_all."""
    dimensions = Measurer(herds, parsed(rows[0])).dimensions()
    assert {(d['d_doc'], d['d_all']) for d in dimensions} == {(5, 7)}
    interacting = rows[0] | {'interactions': 'breed:feed'}
    interacted = Measurer(herds, parsed(interacting)).dimensions()[0]
    assert (interacted['d_doc'], interacted['d_all']) == (11, 13)
    assert Measurer(herds, parsed(rows[1])).dimensions()[0]['d_doc'] == 3
    assert Measurer(herds, parsed(rows[1])).dimensions()[0]['d_all'] == 10


def unitLength(design: np.ndarray) -> np.ndarray:
    return design / np.linalg.norm(design, axis=0)


def test_the_condition_index_of_the_documented_design(herds, rows):
    """Model 2 with weight: the intercept, weight centered and breed's contrasts against angus,
    its first level, each scaled to unit length; the index is the ratio of the extreme singular
    values (Belsley, Kuh and Welsch 1980). Scaling makes weight's standard deviation
    irrelevant. With every other column ignored, the all-column design is the same."""
    weighed = rows[1] | {'covariates': 'weight;breed'}
    weight = herds['weight'].to_numpy()
    breed = herds['breed'].to_numpy()
    design = np.column_stack([
        np.ones(len(herds)), weight - weight.mean(),
        breed == 'hereford', breed == 'holstein', breed == 'jersey',
    ]).astype(float)  # fmt: skip
    singular = np.linalg.svd(unitLength(design), compute_uv=False)
    dimension = Measurer(herds, parsed(weighed)).dimensions()[0]
    assert dimension['condition_doc'] == round(singular[0] / singular[-1], 4)
    alone = weighed | {'ignore': 'id;region;feed;parity;sick'}
    dimension = Measurer(herds, parsed(alone)).dimensions()[0]
    assert dimension['condition_all'] == dimension['condition_doc']


def test_a_rank_deficient_design_has_an_infinite_condition_index(herds, rows):
    """Breed and feed leave cells empty, so their interaction has columns of zeros; a dose that
    never varies is collinear with the intercept, though the contract standardizes it to 0/0;
    weight in pounds repeats weight in kilograms, among every measured column only."""
    interacting = rows[0] | {'interactions': 'breed:feed'}
    assert Measurer(herds, parsed(interacting)).dimensions()[0]['condition_doc'] == np.inf
    dosed = rows[1] | {'covariates': 'breed;dose'}
    assert Measurer(herds.assign(dose=2.5), parsed(dosed)).dimensions()[0]['condition_doc'] == np.inf  # fmt: skip
    pounds = herds.assign(pounds=herds['weight'] * 2.2046)
    alone = rows[1] | {'covariates': 'weight;breed', 'ignore': 'id;region;feed;parity;sick'}
    dimension = Measurer(pounds, parsed(alone)).dimensions()[0]
    assert dimension['condition_doc'] < np.inf
    assert dimension['condition_all'] == np.inf


def measuredDimensions(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The dimensions.csv rows of one registry row, by factor; a statistic left out is blank."""
    dimensions = Measurer(table, parsed(cells)).dimensions()
    return pd.DataFrame(dimensions, columns=DIMENSION_COLUMNS).set_index('factor')


def test_no_condition_index_where_the_contract_builds_no_problem(herds, rows):
    """The contract refuses a categorical response, so neither design exists. A column missing
    on every measured row leaves no row complete in every column, and an undeclared column of
    strings and numbers has no level order (#105): only the documented design exists."""
    refused = rows[1] | {'response': 'breed', 'response_type': 'categorical', 'trials': '', 'covariates': 'weight'}  # fmt: skip
    conditions = measuredDimensions(herds, refused)[['condition_doc', 'condition_all']]
    assert conditions.isna().all().all()
    empty = pd.Categorical([None] * len(herds), categories=['low', 'high'], ordered=True)
    depth = pd.Series(['>1m', 0.7, 1] * 4 + ['>1m', 0.7], dtype=object)
    for edited in (herds.assign(empty=empty), herds.assign(depth=depth)):
        herd = measuredDimensions(edited, rows[1]).loc['herd']
        assert herd['condition_doc'] >= 1
        assert pd.isna(herd['condition_all'])


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


def measuredColumnFactors(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The column_factors.csv rows of one registry row, by column and factor; a statistic left
    out is blank."""
    pairs = Measurer(table, parsed(cells)).columnFactors()
    return pd.DataFrame(pairs, columns=COLUMN_FACTOR_COLUMNS).set_index(['column', 'factor'])


def test_one_row_per_column_and_grouping_factor(herds, rows):
    """Model 1 measures its four columns against region and herd: eight rows, in the order of
    columns.csv and then of the row's factors, each under the registry row's key."""
    pairs = Measurer(herds, parsed(rows[0])).columnFactors()
    assert [(p['column'], p['factor']) for p in pairs] == [
        ('breed', 'region'), ('breed', 'herd'), ('feed', 'region'), ('feed', 'herd'),
        ('parity', 'region'), ('parity', 'herd'), ('sick', 'region'), ('sick', 'herd'),
    ]  # fmt: skip
    keys = {(p['source'], p['object'], p['model_index'], p['tier']) for p in pairs}
    assert keys == {('herds', 'herds.csv', 1, 'D')}


def test_between_group_share_is_the_adjusted_intraclass_correlation(herds, rows):
    """Sick within herd: MSB = 0.5476 / 4, MSW = 2.6667 / 9 and k₀ = (14 − 46 / 14) / 4, so
    (MSB − MSW) / (MSB + (k₀ − 1) MSW) = −0.2513, kept negative. Weight within herd under
    model 2: 0.0461, as (F − 1) / (F + k₀ − 1) from scipy.stats.f_oneway's F."""
    sick = measuredColumnFactors(herds, rows[0]).loc[('sick', 'herd')]
    assert sick['between_group_share'] == -0.2513
    weight = measuredColumnFactors(herds, rows[1]).loc[('weight', 'herd')]
    assert weight['between_group_share'] == 0.0461


def test_a_group_level_column_lies_wholly_between_groups(herds, rows):
    """Feed is constant within each herd, so declared ordered it has no within-herd variance and
    a between-group share of 1; within region it varies. As loaded, feed is a categorical of
    three levels, which has no between-group share, nor has breed."""
    graded = herds.assign(feed=asOrdered(herds['feed'], ['grass', 'grain', 'mixed']))
    feed = measuredColumnFactors(graded, rows[0])['between_group_share'].loc['feed']
    assert feed['herd'] == 1
    assert feed['region'] < 1
    shares = measuredColumnFactors(herds, rows[0])['between_group_share']
    assert shares.loc[['breed', 'feed']].isna().all()


def test_singleton_groups_and_a_constant_column_have_no_between_group_share(herds, rows):
    """With each row its own group nothing varies within a group, so there is no within-group
    mean square to compare against; a constant column has no variance to share."""
    singletons = rows[1] | {'grouping_factors': 'id', 'ignore': ''}
    sick = measuredColumnFactors(herds, singletons).loc[('sick', 'id')]
    assert pd.isna(sick['between_group_share'])
    dose = measuredColumnFactors(herds.assign(dose=2.5), rows[1]).loc[('dose', 'herd')]
    assert pd.isna(dose['between_group_share'])


def test_a_constant_column_relates_to_no_factor_however_its_value_rounds(herds, rows):
    """A dose of 0.1 is constant, but its group means differ from 0.1 in the last bit, which a
    test for exactly zero variance lets through: a between-group share of 0.7302 within herd,
    as for ros' Helicopters, whose constant width and length read 1.0. A constant column has
    nothing to share, rank, spread or explain."""
    dose = measuredColumnFactors(herds.assign(dose=0.1), rows[0]).loc['dose']
    numeric = ['between_group_share', 'group_level_r2', 'size_rho', 'within_sd_cv']
    assert dose[numeric].isna().all().all()


def test_absent_levels_are_the_empty_group_by_level_cells(herds, rows):
    """Each herd is fed one of three feeds, so 10 of the 5 × 3 cells are empty; the herds hold
    13 of 20 herd × breed cells; h4's one cow is sick, so 1 of 10 cells is empty. A level no row
    holds is no cell, and weight, continuous, has no levels."""
    absent = measuredColumnFactors(herds, rows[0])['absent_level_share']
    assert (absent[('feed', 'herd')], absent[('breed', 'herd')]) == (0.6667, 0.35)
    assert absent[('sick', 'herd')] == 0.1
    unused = herds.assign(breed=herds['breed'].cat.add_categories('dexter'))
    assert measuredColumnFactors(unused, rows[0]).loc[('breed', 'herd'), 'absent_level_share'] == 0.35  # fmt: skip
    assert pd.isna(measuredColumnFactors(herds, rows[1]).loc[('weight', 'herd'), 'absent_level_share'])  # fmt: skip


def test_size_rho_ranks_group_sizes_against_group_means(herds, rows):
    """The herds hold 3, 2, 4, 1 and 4 rows; their mean weights rank 2, 4, 1, 5 and 3, so
    Spearman's ρ is −8 / √95 = −0.8208. Their sick shares, 1/3, 1/2, 1/4, 1 and 1/4, fall as the
    herds grow: −1. Pens of seven rows each, or a constant dose, leave nothing to rank."""
    assert measuredColumnFactors(herds, rows[1]).loc[('weight', 'herd'), 'size_rho'] == -0.8208
    assert measuredColumnFactors(herds, rows[0]).loc[('sick', 'herd'), 'size_rho'] == -1
    pens = herds.assign(pen=['a', 'b'] * 7)
    penned = rows[1] | {'grouping_factors': 'pen'}
    assert pd.isna(measuredColumnFactors(pens, penned).loc[('weight', 'pen'), 'size_rho'])
    dose = measuredColumnFactors(herds.assign(dose=2.5), rows[1]).loc[('dose', 'herd')]
    assert pd.isna(dose['size_rho'])


def test_within_sd_cv_spreads_the_within_group_standard_deviations(herds, rows):
    """The sick shares' sample standard deviations in the four herds of two or more rows,
    0.5774, 0.7071, 0.5 and 0.5, have a population coefficient of variation of 0.1482; h4, a
    singleton, has none. Weight's give 0.3333 by numpy. With singletons there is no standard
    deviation to spread, and a group-level column's are all zero."""
    assert measuredColumnFactors(herds, rows[0]).loc[('sick', 'herd'), 'within_sd_cv'] == 0.1482
    assert measuredColumnFactors(herds, rows[1]).loc[('weight', 'herd'), 'within_sd_cv'] == 0.3333
    singletons = rows[1] | {'grouping_factors': 'id', 'ignore': ''}
    assert pd.isna(measuredColumnFactors(herds, singletons).loc[('weight', 'id'), 'within_sd_cv'])
    graded = herds.assign(feed=asOrdered(herds['feed'], ['grass', 'grain', 'mixed']))
    assert pd.isna(measuredColumnFactors(graded, rows[0]).loc[('feed', 'herd'), 'within_sd_cv'])


def test_group_level_r2_is_what_the_factors_group_level_columns_explain(herds, rows):
    """Feed is model 1's one column constant within herd. Sick on feed's treatment contrasts has
    a row-level R² of 31/270, which five herds and two contrasts adjust to
    1 − (1 − 31/270) · 4 / 2 = −0.7704. A pasture area that follows feed: statsmodels' R² of
    0.9940 on feed adjusts to 0.9880, and sick's on feed and pasture to −2.5400 with p = 3."""
    assert measuredColumnFactors(herds, rows[0]).loc[('sick', 'herd'), 'group_level_r2'] == -0.7704
    area = {'h1': 12.0, 'h2': 30.5, 'h3': 18.0, 'h4': 31.0, 'h5': 13.5}
    pastured = herds.assign(pasture=herds['herd'].map(area).astype(float))
    r2 = measuredColumnFactors(pastured, rows[0])['group_level_r2']
    assert (r2[('pasture', 'herd')], r2[('sick', 'herd')]) == (0.988, -2.54)


def test_group_level_r2_needs_a_partner_and_a_group_to_spare(herds, rows):
    """No column is constant within region, and a dose constant everywhere spans nothing beyond
    the intercept, so sick has no partner there. Under model 2, region's and feed's four
    contrasts saturate the five herds (m − p − 1 = 0). A constant column has nothing to explain,
    and breed, a categorical of four levels, is no number to regress."""
    model1 = measuredColumnFactors(herds.assign(dose=2.5), rows[0])['group_level_r2']
    assert model1[[('sick', 'region'), ('dose', 'herd'), ('breed', 'herd')]].isna().all()
    model2 = measuredColumnFactors(herds, rows[1])['group_level_r2']
    assert pd.isna(model2[('weight', 'herd')])


def test_a_column_missing_on_every_measured_row_is_no_partner(herds, rows):
    """A column with no observed value is constant within every group, but as a partner it
    would leave no row complete, as radon's windoor blanked every R² against county. Sick keeps
    its R² of −0.7704 on feed alone."""
    empty = herds.assign(empty=float('nan'))
    r2 = measuredColumnFactors(empty, rows[0]).loc[('sick', 'herd'), 'group_level_r2']
    assert r2 == -0.7704


def test_a_column_missing_on_every_measured_row_relates_to_no_factor(herds, rows):
    """Two ordered columns of the registry are missing wherever the response is measured, so
    they have no groups and no levels to relate."""
    empty = pd.Categorical([None] * len(herds), categories=['low', 'high'], ordered=True)
    pairs = measuredColumnFactors(herds.assign(empty=empty), rows[1]).loc['empty']
    assert pairs[list(COLUMN_FACTOR_STATISTICS)].isna().all().all()


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


def measuredFactorPairs(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The factor_pairs.csv rows of one registry row, by pair of factors; a statistic left out
    is blank."""
    pairs = Measurer(table, parsed(cells)).factorPairs()
    return pd.DataFrame(pairs, columns=FACTOR_PAIR_COLUMNS).set_index(['factor_a', 'factor_b'])


def test_a_nested_pairs_superior_holds_whole_groups_of_the_other(herds, rows):
    """Each herd lies in one region, so region is superior in either order, and the nested pair
    has no empty-cell share. Model 2's one factor makes no pair."""
    pairs = Measurer(herds, parsed(rows[0])).factorPairs()
    assert [(p['factor_a'], p['factor_b']) for p in pairs] == [('region', 'herd')]
    assert (pairs[0]['source'], pairs[0]['model_index'], pairs[0]['tier']) == ('herds', 1, 'D')
    pair = measuredFactorPairs(herds, rows[0]).loc[('region', 'herd')]
    assert (pair['relation'], pair['superior']) == ('nested', 'region')
    assert pd.isna(pair['empty_cell_share'])
    reversed = rows[0] | {'grouping_factors': 'herd;region'}
    assert measuredFactorPairs(herds, reversed).loc[('herd', 'region'), 'superior'] == 'region'
    assert Measurer(herds, parsed(rows[1])).factorPairs() == []


def test_a_crossed_pairs_empty_cells(herds, rows):
    """Breeds recur across herds, so herd and breed cross: the herds hold 3, 2, 3, 1 and 4 of
    the four breeds, 13 of 20 cells, and the crossed pair has no superior. A breed no row holds
    is no cell."""
    crossed = rows[0] | {'grouping_factors': 'herd;breed', 'covariates': 'feed'}
    pair = measuredFactorPairs(herds, crossed).loc[('herd', 'breed')]
    assert (pair['relation'], pair['empty_cell_share']) == ('crossed', 0.35)
    assert pd.isna(pair['superior'])
    unused = herds.assign(breed=herds['breed'].cat.add_categories('dexter'))
    assert measuredFactorPairs(unused, crossed).loc[('herd', 'breed'), 'empty_cell_share'] == 0.35


def test_two_factors_that_partition_the_rows_alike_have_no_superior(herds, rows):
    """Pens that relabel the herds hold whole herds and lie in whole herds, so neither factor is
    superior to the other, though the pair is nested."""
    pens = herds.assign(pen=herds['herd'].str.replace('h', 'p'))
    alike = rows[1] | {'grouping_factors': 'herd;pen'}
    pair = measuredFactorPairs(pens, alike).loc[('herd', 'pen')]
    assert pair['relation'] == 'nested'
    assert pair[['superior', 'empty_cell_share']].isna().all()


SHARES = ('outlier_share', 'zero_share', 'min_share', 'max_share', 'unique_share', 'rare_level_share', 'max_abs_rho')  # fmt: skip
GENERATED = readRows(FIXTURES / 'registry_herds.csv')[0] | {
    'response': 'y', 'grouping_factors': 'g', 'covariates': '', 'ignore': '', 'types': '',
}  # fmt: skip


@st.composite
def tables(draw: st.DrawFn) -> pd.DataFrame:
    """A table of one to thirty rows whose covariate columns take any kind the typing rule
    gives them: ties, gaps, a single value or two."""
    n = draw(st.integers(1, 30))
    number = st.one_of(st.floats(-100, 100), st.sampled_from([0.0, 1.0]), st.none())
    word = st.sampled_from(['lo', 'mid', 'hi', None])
    words = draw(st.lists(word, min_size=n, max_size=n))
    return pd.DataFrame({
        'y': np.arange(n, dtype=float),
        'g': draw(st.lists(st.sampled_from('ab'), min_size=n, max_size=n)),
        'x': draw(st.lists(number, min_size=n, max_size=n)),
        'k': draw(st.lists(st.integers(0, 4), min_size=n, max_size=n)),
        's': words,
        'o': pd.Categorical(words, categories=['lo', 'mid', 'hi'], ordered=True),
    })  # fmt: skip


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


@settings(max_examples=200, deadline=None)
@given(table=tables())
def test_column_factor_statistics_lie_in_their_ranges(table):
    """Whatever the column and however its rows fall into groups, an absent-level share lies in
    [0, 1], a between-group share and an adjusted R² at most 1, a rank correlation in [−1, 1]
    and a coefficient of variation at or above 0, or each is blank."""
    pairs = measuredColumnFactors(table, GENERATED)
    assert pairs['absent_level_share'].dropna().between(0, 1).all()
    assert (pairs['between_group_share'].dropna() <= 1).all()
    assert (pairs['group_level_r2'].dropna() <= 1).all()
    assert pairs['size_rho'].dropna().between(-1, 1).all()
    assert (pairs['within_sd_cv'].dropna() >= 0).all()


@st.composite
def groupLevelTables(draw: st.DrawFn) -> pd.DataFrame:
    """Two to twelve groups of two to six rows and a column that takes one distinct integer
    value per group."""
    m = draw(st.integers(2, 12))
    values = draw(st.lists(st.integers(-1000, 1000), min_size=m, max_size=m, unique=True))
    sizes = draw(st.lists(st.integers(2, 6), min_size=m, max_size=m))
    groups = np.repeat(np.arange(m), sizes)
    return pd.DataFrame({
        'y': np.arange(len(groups), dtype=float),
        'g': groups.astype(str),
        'x': np.repeat(values, sizes).astype(float),
    })  # fmt: skip


@settings(max_examples=100, deadline=None)
@given(table=groupLevelTables())
def test_a_column_constant_within_groups_lies_wholly_between_them(table):
    shares = measuredColumnFactors(table, GENERATED)['between_group_share']
    assert shares[('x', 'g')] == 1


@settings(max_examples=20, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_white_noise_lies_within_groups(seed):
    """Normal noise in 2000 groups of three rows: at ρ = 0 Fisher's large-sample variance,
    2 / (k (k − 1) (m − 1)), gives the adjusted share a standard error of 0.013, so 0.1 is eight
    of them. The unadjusted η² would lie near (m − 1) / (n − 1) ≈ 1/3."""
    rng = np.random.default_rng(seed)
    groups = np.repeat(np.arange(2000), 3)
    noise = pd.DataFrame({'y': np.zeros(len(groups)), 'g': groups.astype(str), 'x': rng.normal(size=len(groups))})  # fmt: skip
    share = measuredColumnFactors(noise, GENERATED).loc[('x', 'g'), 'between_group_share']
    assert abs(share) < 0.1


@settings(max_examples=50, deadline=None)
@given(m_a=st.integers(2, 6), m_b=st.integers(2, 6), replicates=st.integers(1, 3))
def test_a_full_cross_has_no_empty_cell(m_a, m_b, replicates):
    a, b = np.meshgrid(np.arange(m_a), np.arange(m_b), indexing='ij')
    cells = pd.DataFrame({'a': a.ravel().astype(str), 'b': b.ravel().astype(str)})
    table = pd.concat([cells] * replicates, ignore_index=True).assign(y=0.0)
    pair = measuredFactorPairs(table, GENERATED | {'grouping_factors': 'a;b'}).loc[('a', 'b')]
    assert (pair['relation'], pair['empty_cell_share']) == ('crossed', 0)


@settings(max_examples=100, deadline=None)
@given(table=tables())
def test_a_condition_index_is_at_least_one(table):
    """Whatever the columns, the largest singular value is at least the smallest."""
    documented = GENERATED | {'covariates': 'x;o'}
    dimensions = measuredDimensions(table, documented)
    for condition in ('condition_doc', 'condition_all'):
        assert (dimensions[condition].dropna() >= 1).all(), condition
