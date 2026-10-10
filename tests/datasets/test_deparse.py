"""The deparse reader on base R's `data/*.R` grammar: the tables it evaluates, the constructs it
refuses, and a property test that any frame R would deparse reads back as itself."""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from mixedbench.datasets.deparse import Deparse


def test_row_names_of_data_frame_are_no_column(tmp_path):
    """`row.names =` is an argument of data.frame(), not a column (base R's LifeCycleSavings
    came out with six columns where R has five, found by the census re-pull of #9)."""
    file = tmp_path / 'savings.R'
    file.write_text('savings <- data.frame(sr = c(11.43, 12.07), row.names = c("A", "B"))\n')
    savings = Deparse(file).tables()['savings']
    assert list(savings.columns) == ['sr']


def test_unary_minus_binds_tighter_than_a_range(tmp_path):
    """In R, `-1:3` runs from -1 to 3, not from -1 to -3."""
    file = tmp_path / 'steps.R'
    file.write_text('steps <- data.frame(x = -1:3)\n')
    steps = Deparse(file).tables()['steps']
    assert list(steps['x']) == [-1, 0, 1, 2, 3]


def test_a_construct_outside_the_deparse_subset_raises_naming_file_and_construct(tmp_path):
    """The reader is for base R's seven data files, not for R: a time series fails loudly."""
    file = tmp_path / 'series.R'
    file.write_text('series <- ts(c(1, 2, 3), start = 1990)\n')
    with pytest.raises(ValueError, match=r'series\.R: function ts\(\)'):
        Deparse(file).tables()


# a frame of numeric and string columns, written as base R's data/*.R files write one
NAMES = st.from_regex(r'[a-z][a-z0-9_.]{0,8}', fullmatch=True)
NUMBERS = st.floats(allow_nan=False, allow_infinity=False) | st.none()
# R deparses quotes, backslashes and control characters as escapes, which the subset has none of
STRINGS = (
    st.text(alphabet=st.characters(exclude_categories=['Cc', 'Cs'], exclude_characters='"\\'))
    | st.none()
)


def holdsAValue(column: list) -> bool:
    """An all-NA column is logical in R (`c(NA)`), neither numeric nor string."""
    return any(value is not None for value in column)


@st.composite
def tables(draw) -> dict[str, list]:
    n = draw(st.integers(1, 5))
    names = draw(st.lists(NAMES, min_size=1, max_size=4, unique=True))
    columns = {}
    for name in names:
        values = draw(st.sampled_from([NUMBERS, STRINGS]))
        columns[name] = draw(st.lists(values, min_size=n, max_size=n).filter(holdsAValue))
    return columns


def literal(value: float | str | None) -> str:
    """A value as R deparses it."""
    if value is None:
        return 'NA'
    if isinstance(value, str):
        return f'"{value}"'
    return repr(value)


def deparsed(columns: dict[str, list]) -> str:
    """`drawn <- data.frame(a = c(...), ...)`, as base R's data/*.R files write a frame."""
    parts = []
    for name, values in columns.items():
        literals = ', '.join(literal(value) for value in values)
        parts.append(f'{name} = c({literals})')
    return f'drawn <- data.frame({", ".join(parts)})\n'


@given(tables())
@settings(max_examples=200, deadline=None)
def test_deparsed_numeric_and_string_vectors_round_trip(tmp_path_factory, columns):
    """Any frame of numbers, strings and NA that R would deparse reads back as itself."""
    file = tmp_path_factory.mktemp('deparse') / 'drawn.R'
    file.write_text(deparsed(columns), encoding='utf-8')
    expected = pd.DataFrame(columns)
    actual = Deparse(file).tables()['drawn']
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
