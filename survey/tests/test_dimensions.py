"""dimensions.csv from `fixtures/herds.csv`: group sizes, the Dirichlet concentration, the
relation, the design columns and the condition indexes, each expected value worked by hand or
by numpy, and the condition index's range over generated tables."""

import dimensions
import numpy as np
import pandas as pd
import pytest
from conftest import GENERATED, parsed, tables
from dimensions import DIMENSION_COLUMNS, fitAlpha
from hypothesis import given, settings
from measure import Measurer


def measuredDimensions(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The dimensions.csv rows of one registry row, by factor; a statistic left out is blank."""
    measured = dimensions.measure(Measurer(table, parsed(cells)))
    return pd.DataFrame(measured, columns=DIMENSION_COLUMNS).set_index('factor')


def sizes(dimension: dict) -> tuple:
    keys = (
        'group_size_min',
        'group_size_p10',
        'group_size_p50',
        'group_size_p90',
        'group_size_max',
    )
    return tuple(dimension[k] for k in keys)


def test_group_sizes_per_factor(herds, rows):
    """Region holds 5, 5 and 4 rows; herd holds 3, 2, 4, 1 and 4, so h4 is a singleton.
    Quantiles are observed sizes (at or below the level under p50, at or above from p50 on);
    the coefficient of variation uses the population standard deviation."""
    measured = dimensions.measure(Measurer(herds, parsed(rows[0])))
    assert [d['factor'] for d in measured] == ['region', 'herd']
    region, herd = measured
    assert (region['source'], region['object'], region['model_index'], region['tier']) == ('herds', 'herds.csv', 1, 'D')  # fmt: skip
    assert region['n_obs'] == 14 and herd['n_obs'] == 14
    assert (region['n_groups'], herd['n_groups']) == (3, 5)
    assert sizes(region) == (4, 4, 5, 5, 5)
    assert sizes(herd) == (1, 1, 3, 4, 4)
    assert (region['singleton_share'], herd['singleton_share']) == (0, 0.2)
    assert region['cv'] == pytest.approx(0.10102, abs=1e-4)
    assert herd['cv'] == pytest.approx(0.41650, abs=1e-4)


def test_alpha_by_moment_matching(herds, rows):
    """Region sizes 5, 5, 4 give α = 65 exactly ((1 − 1/m) / (m s²) = 196); herd sizes
    3, 2, 4, 1, 4 give 4.41. A balanced allocation has zero variance, so α is infinite."""
    region, herd = dimensions.measure(Measurer(herds, parsed(rows[0])))
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
    measured = dimensions.measure(Measurer(herds, parsed(row)))
    assert {d['relation'] for d in measured} == {relation}
    assert {d['n_factors'] for d in measured} == {len(measured)}


def test_design_columns_of_the_documented_model_and_of_the_whole_table(herds, rows):
    """Model 1: breed (4 levels) and feed (3) give d_doc = 3 + 2 = 5; parity (an integer) and
    sick (binary) bring d_all to 7; an interaction breed:feed adds 3 × 2 to both, so d_all is
    never below d_doc. Model 2 names only breed, and the region column, no longer a factor,
    counts 2 in its d_all."""
    measured = dimensions.measure(Measurer(herds, parsed(rows[0])))
    assert {(d['d_doc'], d['d_all']) for d in measured} == {(5, 7)}
    interacting = rows[0] | {'interactions': 'breed:feed'}
    interacted = dimensions.measure(Measurer(herds, parsed(interacting)))[0]
    assert (interacted['d_doc'], interacted['d_all']) == (11, 13)
    model2 = dimensions.measure(Measurer(herds, parsed(rows[1])))[0]
    assert (model2['d_doc'], model2['d_all']) == (3, 10)


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
    dimension = dimensions.measure(Measurer(herds, parsed(weighed)))[0]
    assert dimension['condition_doc'] == round(singular[0] / singular[-1], 4)
    alone = weighed | {'ignore': 'id;region;feed;parity;sick'}
    dimension = dimensions.measure(Measurer(herds, parsed(alone)))[0]
    assert dimension['condition_all'] == dimension['condition_doc']


def test_a_rank_deficient_design_has_an_infinite_condition_index(herds, rows):
    """Breed and feed leave cells empty, so their interaction has columns of zeros; a dose that
    never varies is collinear with the intercept, though the contract standardizes it to 0/0;
    weight in pounds repeats weight in kilograms, among every measured column only."""
    interacting = rows[0] | {'interactions': 'breed:feed'}
    assert dimensions.measure(Measurer(herds, parsed(interacting)))[0]['condition_doc'] == np.inf
    dosed = rows[1] | {'covariates': 'breed;dose'}
    assert dimensions.measure(Measurer(herds.assign(dose=2.5), parsed(dosed)))[0]['condition_doc'] == np.inf  # fmt: skip
    pounds = herds.assign(pounds=herds['weight'] * 2.2046)
    alone = rows[1] | {'covariates': 'weight;breed', 'ignore': 'id;region;feed;parity;sick'}
    dimension = dimensions.measure(Measurer(pounds, parsed(alone)))[0]
    assert dimension['condition_doc'] < np.inf
    assert dimension['condition_all'] == np.inf


@pytest.mark.parametrize(
    ('x', 'condition'),
    [([0.0, 0.0, 0.0, 1.0], 1.7321), ([2.0, 2.0, 2.0, 2.0], np.inf)],
    ids=['gram-eigenvalues-3/2-and-1/2', 'a-constant-repeats-the-intercept'],
)
def test_the_condition_index_of_a_design_frame(x, condition):
    """The flat pass builds designs that have no registry row, so the index takes the design
    itself. Scaled to unit length, the intercept and x = (0, 0, 0, 1) have the Gram matrix
    [[1, 1/2], [1/2, 1]], whose eigenvalues 3/2 and 1/2 give the index √3."""
    design = pd.DataFrame({'Intercept': [1.0] * 4, 'x': x})
    assert dimensions.computeConditionIndex(design) == condition


def test_a_design_wider_than_its_rows_has_an_infinite_condition_index():
    """More columns than rows are dependent whatever their values, so the index needs no
    decomposition; a flat table's date strings give tens of thousands of contrasts."""
    design = pd.DataFrame({'Intercept': [1.0, 1.0], 'x': [0.0, 1.0], 'z': [3.0, -1.0]})
    assert dimensions.computeConditionIndex(design) == np.inf


def test_no_condition_index_where_the_contract_builds_no_problem(herds, rows):
    """The contract refuses a categorical response, so neither design exists. A column missing
    on every measured row leaves no row complete in every column: only the documented design
    exists."""
    refused = rows[1] | {'response': 'breed', 'response_type': 'categorical', 'trials': '', 'covariates': 'weight'}  # fmt: skip
    conditions = measuredDimensions(herds, refused)[['condition_doc', 'condition_all']]
    assert conditions.isna().all().all()
    empty = pd.Categorical([None] * len(herds), categories=['low', 'high'], ordered=True)
    herd = measuredDimensions(herds.assign(empty=empty), rows[1]).loc['herd']
    assert herd['condition_doc'] >= 1
    assert pd.isna(herd['condition_all'])


@settings(max_examples=100, deadline=None)
@given(table=tables())
def test_a_condition_index_is_at_least_one(table):
    """Whatever the columns, the largest singular value is at least the smallest."""
    documented = GENERATED | {'covariates': 'x;o'}
    dimensions = measuredDimensions(table, documented)
    for condition in ('condition_doc', 'condition_all'):
        assert (dimensions[condition].dropna() >= 1).all(), condition
