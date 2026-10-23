"""column_factors.csv from `fixtures/herds.csv`: a column against a grouping factor's groups,
each expected value worked by hand or by scipy, statsmodels or numpy, and the statistics'
ranges over generated and group-level tables."""

import groups
import numpy as np
import pandas as pd
from conftest import GENERATED, asOrdered, measuredColumnFactors, parsed, tables
from groups import COLUMN_FACTOR_STATISTICS
from hypothesis import given, settings
from hypothesis import strategies as st
from measure import Measurer


def test_one_row_per_column_and_grouping_factor(herds, rows):
    """Model 1 measures its four columns against region and herd: eight rows, in the order of
    columns.csv and then of the row's factors, each under the registry row's key."""
    pairs = groups.measure(Measurer(herds, parsed(rows[0])))
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
