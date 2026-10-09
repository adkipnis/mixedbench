"""Measuring one loaded table against its registry row (#18): group sizes per factor, the
Dirichlet α, the relation between factors, column types and levels, d_doc and d_all, every
expected value computed by hand from `fixtures/herds.csv`."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from conftest import readRows
from measure import Measurer, fitAlpha

FIXTURES = Path(__file__).parent / 'fixtures'
CATEGORICAL = ('region', 'herd', 'breed', 'feed')


@pytest.fixture
def herds() -> pd.DataFrame:
    """The table as the loader returns it: the declared columns as pandas categoricals."""
    df = pd.read_csv(FIXTURES / 'herds.csv')
    return df.astype({c: 'category' for c in CATEGORICAL})


@pytest.fixture
def rows() -> list[dict]:
    rows = readRows(FIXTURES / 'registry_herds.csv')
    for row in rows:
        row['tier'] = 'D'
    return rows


def test_group_sizes_per_factor(herds, rows):
    """Region holds 5, 5 and 4 rows; herd holds 3, 2, 4, 1 and 4, so h4 is a singleton.
    Quantiles are observed sizes (at or below the level under p50, at or above from p50 on);
    the coefficient of variation uses the population standard deviation."""
    dimensions = Measurer(herds, rows[0]).dimensions()
    assert [d['factor'] for d in dimensions] == ['region', 'herd']
    region, herd = dimensions
    assert (region['source'], region['object'], region['model_index'], region['tier']) == ('herds', 'herds.csv', '1', 'D')  # fmt: skip
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
    region, herd = Measurer(unmeasured, rows[0]).dimensions()
    assert (region['n_obs'], herd['n_obs']) == (13, 13)
    assert (region['group_size_min'], herd['group_size_min']) == (4, 1)
    assert herd['group_size_p50'] == 2


def test_alpha_by_moment_matching(herds, rows):
    """Region sizes 5, 5, 4 give α = 65 exactly ((1 − 1/G) / (G s²) = 196); herd sizes
    3, 2, 4, 1, 4 give 4.41. A balanced allocation has zero variance, so α is infinite."""
    region, herd = Measurer(herds, rows[0]).dimensions()
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
    dimensions = Measurer(herds, row).dimensions()
    assert {d['relation'] for d in dimensions} == {relation}
    assert {d['n_factors'] for d in dimensions} == {len(dimensions)}


def test_a_composite_grouping_factor_is_built_from_its_parts(herds, rows):
    """`region:breed` names no column: the measurer combines the two, a group per pair of
    levels present. Twelve pairs, north:angus and south:jersey hold two rows, the ten others
    one; the composite lies in region, so the relation is nested. breed and herd, no longer
    a factor, are covariate columns; the composite does not appear in columns.csv."""
    row = rows[0] | {'grouping_factors': 'region;region:breed'}
    measurer = Measurer(herds, row)
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
    columns = Measurer(herds, rows[0]).columns()
    assert [c['column'] for c in columns] == ['breed', 'feed', 'parity', 'sick']
    typed = lambda c: (c['type'], c['K'], c['level'], c['constant_within'], c['in_model'])
    assert typed(columns[0]) == ('categorical', 4, 'within', '', 'yes')
    assert typed(columns[1]) == ('categorical', 3, 'group', 'herd', 'yes')
    assert typed(columns[2]) == ('categorical', 4, 'within', '', 'no')
    assert typed(columns[3]) == ('binary', 2, 'within', '', 'no')
    assert columns[0]['tier'] == 'D' and columns[0]['model_index'] == '1'
    assert {c['missing_share'] for c in columns} == {0}


def test_ordered_declared_continuous_and_missing_values(herds, rows):
    """An ordered categorical keeps its own type; a registry declaration of continuous
    overrides the ten-distinct-values rule for an integer; one missing value in fourteen."""
    varied = herds.assign(parity=herds['parity'].astype(pd.CategoricalDtype([1, 2, 3, 4], ordered=True)))  # fmt: skip
    varied.loc[0, 'weight'] = float('nan')
    row = rows[0] | {'response': 'sick', 'covariates': 'weight', 'ignore': 'id;cases;trials', 'types': 'parity=continuous'}  # fmt: skip
    columns = {c['column']: c for c in Measurer(varied, row).columns()}
    assert set(columns) == {'breed', 'feed', 'parity', 'weight'}
    assert (columns['parity']['type'], columns['parity']['K']) == ('ordered', 4)
    assert (columns['weight']['type'], columns['weight']['K']) == ('continuous', '')
    assert columns['weight']['missing_share'] == pytest.approx(1 / 14, abs=1e-4)
    declared = rows[0] | {'types': 'parity=continuous'}
    columns = {c['column']: c for c in Measurer(herds, declared).columns()}
    assert columns['parity']['type'] == 'continuous'


def test_design_columns_of_the_documented_model_and_of_the_whole_table(herds, rows):
    """Model 1: breed (4 levels) and feed (3) give d_doc = 3 + 2 = 5; parity (4) and sick (binary)
    bring d_all to 9; an interaction breed:feed adds 3 × 2 to both, so d_all is never below
    d_doc. Model 2 names only breed, and the region column, no longer a factor, counts 2 in
    its d_all."""
    dimensions = Measurer(herds, rows[0]).dimensions()
    assert {(d['d_doc'], d['d_all']) for d in dimensions} == {(5, 9)}
    interacting = rows[0] | {'interactions': 'breed:feed'}
    interacted = Measurer(herds, interacting).dimensions()[0]
    assert (interacted['d_doc'], interacted['d_all']) == (11, 15)
    assert Measurer(herds, rows[1]).dimensions()[0]['d_doc'] == 3
    assert Measurer(herds, rows[1]).dimensions()[0]['d_all'] == 12
