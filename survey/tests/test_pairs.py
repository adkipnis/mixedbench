"""factor_pairs.csv from `fixtures/herds.csv`: a nested pair's superior, a crossed pair's empty
cells, and a full cross over generated tables."""

import numpy as np
import pairs
import pandas as pd
from conftest import GENERATED, parsed
from hypothesis import given, settings
from hypothesis import strategies as st
from measure import Measurer
from pairs import FACTOR_PAIR_COLUMNS


def measuredFactorPairs(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The factor_pairs.csv rows of one registry row, by pair of factors; a statistic left out
    is blank."""
    measured = pairs.measure(Measurer(table, parsed(cells)))
    return pd.DataFrame(measured, columns=FACTOR_PAIR_COLUMNS).set_index(['factor_a', 'factor_b'])


def test_a_nested_pairs_superior_holds_whole_groups_of_the_other(herds, rows):
    """Each herd lies in one region, so region is superior in either order, and the nested pair
    has no empty-cell share. Model 2's one factor makes no pair."""
    measured = pairs.measure(Measurer(herds, parsed(rows[0])))
    assert [(p['factor_a'], p['factor_b']) for p in measured] == [('region', 'herd')]
    assert (measured[0]['source'], measured[0]['model_index'], measured[0]['tier']) == (
        'herds',
        1,
        'D',
    )
    pair = measuredFactorPairs(herds, rows[0]).loc[('region', 'herd')]
    assert (pair['relation'], pair['superior']) == ('nested', 'region')
    assert pd.isna(pair['empty_cell_share'])
    reversed = rows[0] | {'grouping_factors': 'herd;region'}
    assert measuredFactorPairs(herds, reversed).loc[('herd', 'region'), 'superior'] == 'region'
    assert pairs.measure(Measurer(herds, parsed(rows[1]))) == []


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


@settings(max_examples=50, deadline=None)
@given(m_a=st.integers(2, 6), m_b=st.integers(2, 6), replicates=st.integers(1, 3))
def test_a_full_cross_has_no_empty_cell(m_a, m_b, replicates):
    a, b = np.meshgrid(np.arange(m_a), np.arange(m_b), indexing='ij')
    cells = pd.DataFrame({'a': a.ravel().astype(str), 'b': b.ravel().astype(str)})
    table = pd.concat([cells] * replicates, ignore_index=True).assign(y=0.0)
    pair = measuredFactorPairs(table, GENERATED | {'grouping_factors': 'a;b'}).loc[('a', 'b')]
    assert (pair['relation'], pair['empty_cell_share']) == ('crossed', 0)
