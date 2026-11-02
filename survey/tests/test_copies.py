"""Which pairs of tables may be copies: a grouped table drawn by seed against a disguised copy
of it (#168)."""

import string

import copies
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

A = ('first', 'table')
B = ('second', 'table')
TablePair = tuple[pd.DataFrame, pd.DataFrame]


def _groupedTable(rng: np.random.Generator) -> pd.DataFrame:
    """Five to ten schools of four to eight pupils: a score and a covariate of four significant
    digits, a school label of six letters."""
    m = int(rng.integers(5, 11))
    sizes = rng.integers(4, 9, size=m)
    labels = [''.join(rng.choice(list(string.ascii_lowercase), 6)) for _ in range(m)]
    n = int(sizes.sum())
    return pd.DataFrame({
        'school': np.repeat(labels, sizes),
        'score': rng.integers(1000, 10000, size=n) / 100,
        'ses': rng.integers(-9999, 10000, size=n) / 1000,
    })  # fmt: skip


def _disguisedCopy(table: pd.DataFrame, rng: np.random.Generator) -> TablePair:
    """The table renamed, its columns reversed and its rows shuffled, the numbers stored as
    float32, a pupil number added and the school label recoded as an integer, as plm Males
    recodes wooldridge wagepan."""
    copy = table.sample(frac=1, random_state=rng).reset_index(drop=True)
    copy['school'] = pd.factorize(copy['school'])[0]
    copy[['score', 'ses']] = copy[['score', 'ses']].astype('float32')
    copy['pupil'] = np.arange(len(copy))
    copy = copy[copy.columns[::-1]].rename(columns=str.upper)
    return table, copy


def _half(table: pd.DataFrame, rng: np.random.Generator) -> TablePair:
    """Half the rows: a large table holds most of a small one's four-digit numbers by chance,
    which flagged 740 unrelated pairs in the registry when the row counts could differ freely,
    so a subset this small goes unflagged too."""
    return table, table.sample(frac=0.5, random_state=rng)


def _unrelated(table: pd.DataFrame, rng: np.random.Generator) -> TablePair:
    """Other values in the same rows and columns, one school more."""
    n = len(table)
    schools = table['school'].nunique() + 1
    labels = [''.join(rng.choice(list(string.ascii_lowercase), 6)) for _ in range(schools)]
    other = pd.DataFrame({
        'school': np.array(labels)[np.arange(n) % schools],
        'score': rng.integers(1000, 10000, size=n) / 100,
        'ses': rng.integers(-9999, 10000, size=n) / 1000,
    })  # fmt: skip
    return table, other


def _bareCopy(table: pd.DataFrame, rng: np.random.Generator) -> TablePair:
    """School codes and grades, no distinctive value, renamed and shuffled: the equal row count
    and column cardinalities find it, as they found 85 of the 469 copies confirmed before #168
    (nlme's tables in MEMSS among them)."""
    bare = pd.DataFrame({'school': pd.factorize(table['school'])[0], 'grade': rng.integers(1, 7, size=len(table))})  # fmt: skip
    copy = bare.sample(frac=1, random_state=rng).rename(columns=str.upper)
    return bare, copy


@pytest.mark.parametrize(
    'disguise, paired',
    [
        pytest.param(_disguisedCopy, True, id='a renamed, reordered, recoded copy with an extra column pairs'),
        pytest.param(_unrelated, False, id='an unrelated table of the same rows and columns does not pair'),
        pytest.param(_half, False, id='a table of under four fifths of the rows does not pair'),
        pytest.param(_bareCopy, True, id='a copy without distinctive values pairs by its row count and cardinalities'),
    ],
)  # fmt: skip
@settings(max_examples=50, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_two_tables_pair_when_one_may_be_a_copy_of_the_other(disguise, paired, seed):
    rng = np.random.default_rng(seed)
    left, right = disguise(_groupedTable(rng), rng)
    pairs = copies.findPairs({A: copies.profileTable(left), B: copies.profileTable(right)})
    assert pairs == ([(A, B)] if paired else [])
