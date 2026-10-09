"""The registry row (#24): the package is the one reader of a `registry.csv` row, so the
contract and the survey's merge never parse a cell themselves."""

from __future__ import annotations

import pytest
from mixedbench import registry
from mixedbench.registry.row import Row, SlopeTerm, parts, readCsv


def installedRow(source: str, object: str, model_index: int) -> registry.Row:
    rows = registry.rows()
    matches = [r for r in rows if (r.source, r.object, r.model_index) == (source, object, model_index)]  # fmt: skip
    assert len(matches) == 1
    return matches[0]


def test_an_installed_row_has_its_lists_split_and_its_types_as_a_mapping() -> None:
    """lme4 VerbAgg #1 fills every list column: two folded sources, two grouping factors, six
    interactions, an ignored column declared ordered."""
    row = installedRow('lme4', 'VerbAgg', 1)
    assert row.sources == ('lme4:VerbAgg', 'mixedmodels_jl:verbagg.arrow')
    assert row.response_type == 'binary'
    assert row.grouping_factors == ('id', 'item')
    assert row.covariates == ('Anger', 'Gender', 'btype', 'situ')
    assert row.interactions[:2] == ('Anger:Gender', 'Anger:btype')
    assert len(row.interactions) == 6
    assert row.ignore == ('resp',)
    assert row.types == {'resp': 'ordered'}
    assert row.trials == row.family == ''


def test_a_composite_term_splits_into_its_parts() -> None:
    """nlme Alfalfa's whole plots are `Block:Variety`, no column of the table: the term keeps
    its name and `parts` gives the columns it combines."""
    row = installedRow('nlme', 'Alfalfa', 1)
    assert row.grouping_factors == ('Block', 'Block:Variety')
    assert parts(row.grouping_factors[1]) == ('Block', 'Variety')


def verbAggCells() -> dict[str, str]:
    cells = readCsv(registry.path('registry.csv'))
    return cells[cells['object'] == 'VerbAgg'].iloc[0].to_dict()


@pytest.mark.parametrize(
    'column, text, reason',
    [
        ('model_index', 'one', 'not an integer: one'),
        ('response_type', 'gaussian', 'not a response type: gaussian'),
        ('family', 'poisson', 'not a family: poisson'),  # the rule is the empty cell
        ('types', 'resp=factor', 'not a column type: factor'),
        ('types', 'resp', 'not a column type: '),
        ('interactions', 'Anger:', 'a term with an empty part: Anger:'),
        ('grouping_factors', 'id;:item', 'a term with an empty part: :item'),
        ('random_slopes', 'Anger', 'not a slope term: Anger'),
        ('random_slopes', 'Anger|||id', 'not a slope term: Anger|||id'),
        ('random_slopes', 'Anger | id', 'not a slope term: Anger | id'),
        ('verified', 'yes', 'not a verification: yes'),
        ('verified', '', 'not a verification: '),  # required: every row says why it is in
    ],
)
def test_a_cell_the_grammar_refuses_raises_naming_the_row_and_the_column(
    column: str, text: str, reason: str
) -> None:
    """The merge keeps such a cell out of the registry; a hand edit or a scratch registry can
    still carry one, and the reader must say where instead of returning a wrong row."""
    cells = verbAggCells() | {column: text}
    with pytest.raises(ValueError) as info:
        Row.parse(cells)
    key = f'lme4 VerbAgg {cells["model_index"]}'  # the row as the file names it
    assert str(info.value) == f'registry row {key}, column {column}: {reason}'


def test_a_row_carries_its_slope_terms_structured_and_its_verification() -> None:
    """The contract reads a random slope as a covariate, a factor and whether it is correlated
    with the factor's intercept, never the `x|g` text (ADR 0001); `x||g` is uncorrelated and a
    composite factor stays one term."""
    cells = verbAggCells() | {'random_slopes': 'Anger|id;btype||item;situ|id:item', 'verified': 'hand'}  # fmt: skip
    row = Row.parse(cells)
    assert row.random_slopes == (
        SlopeTerm(covariate='Anger', factor='id', correlated=True),
        SlopeTerm(covariate='btype', factor='item', correlated=False),
        SlopeTerm(covariate='situ', factor='id:item', correlated=True),
    )
    assert row.verified == 'hand'


def test_a_slope_on_a_column_whose_name_has_spaces_is_one_covariate() -> None:
    """Some loaded tables name a column with spaces (goldstein_msm `activity 1`); the term's
    bars, not whitespace, separate the covariate from the factor."""
    cells = verbAggCells() | {'random_slopes': 'activity 1|id;Age centered about 13 years||item'}  # fmt: skip
    row = Row.parse(cells)
    assert row.random_slopes == (
        SlopeTerm(covariate='activity 1', factor='id', correlated=True),
        SlopeTerm(covariate='Age centered about 13 years', factor='item', correlated=False),
    )
