"""`Problem.build` at its seam (#28): a typed registry row and the loader's typed table in, the
coded design, the response, the family, the prior and the parameter names out (ADR 0001).

The fixture is one hand-made grouped table: a continuous covariate carrying a `-1`, a binary
string, a three-level categorical, an ordered factor, the interaction `x:sex`, the factors
`block` and the composite `block:plot`, the slope `x|block`, and two planted missing rows (one
in `x`, one in `block`); every expected value below is computed by hand from it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st
from mixedbench import frequentist
from mixedbench.contract import Dimensions, Prior, Problem, Refused, Scale, codeCovariate
from mixedbench.registry.row import Row, SlopeTerm

NAN = float('nan')
X = [1.0, 2.5, -1.0, 0.5, 3.0, 1.5, 2.0, 0.0, 1.0, 4.0, 2.5, 3.5]
SEX = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0]  # f = 0, m = 1
HIT = [0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]  # no = 0, yes = 1
Y = [5.1, 6.0, 3.2, 4.8, 7.5, 5.5, 6.1, 4.0, 5.0, 8.2, 6.6, 7.0]
N = [0, 3, 1, 2, 5, 2, 4, 1, 0, 7, 3, 6]
WINS = [0, 2, 1, 1, 4, 2, 3, 1, 0, 5, 2, 4]
GAMES = [4, 5, 3, 4, 6, 5, 5, 3, 2, 8, 4, 6]
RATING = [1, 5, 3, 1, 5, 3, 5, 1, 3, 5, 3, 5]  # three levels, not 1..3
# a Latin square against diet's `a b c` repeats, so no grade contrast is a diet contrast
GRADE = ['lo', 'mid', 'hi', 'mid', 'hi', 'lo', 'hi', 'lo', 'mid', 'lo', 'mid', 'hi']
ROW = Row(
    source='fixture', tier='R', sources=('fixture:trial',), object='trial', reader='pandas',
    license='MIT', model_index=1, response='y', response_type='continuous', trials='', family='',
    grouping_factors=('block', 'block:plot'), covariates=('x', 'sex', 'diet', 'grade'),
    interactions=('x:sex',), random_slopes=(SlopeTerm('x', 'block', correlated=True),),
    ignore=(), types={'diet': 'categorical', 'grade': 'ordered'}, stack=None,
    formula='y ~ x * sex + diet + grade + (x | block) + (1 | block:plot)', documented_prior='',
    published_model='yes', domain='test', confidence='high', verified='hand', notes='',
)  # fmt: skip


def fixtureTable() -> pd.DataFrame:
    """Rows 0-11 are kept; row 12 misses `x`, row 13 misses `block`."""
    return pd.DataFrame(
        {
            'block': ['A'] * 3 + ['B'] * 3 + ['C'] * 2 + ['D'] * 2 + ['E'] * 2 + ['A', None],
            'plot': ['p1', 'p1', 'p2'] * 2 + ['p1'] * 6 + ['p1', 'p1'],
            'x': X + [NAN, 1.0],
            'sex': ['fm'[s] for s in SEX] + ['f', 'm'],
            'diet': pd.Categorical(['a', 'b', 'c'] * 4 + ['a', 'b'], categories=['a', 'b', 'c']),
            'grade': pd.Categorical(
                GRADE + ['lo', 'mid'],
                categories=['lo', 'mid', 'hi'],
                ordered=True,
            ),
            'y': Y + [1.0, 2.0],
            'hit': [['no', 'yes'][h] for h in HIT] + ['no', 'no'],
            'n': N + [1, 1],
            'wins': WINS + [1, 1],
            'games': GAMES + [2, 2],
            'rating': RATING + [1, 1],
        }
    )


def fixtureRow(**overrides) -> Row:
    return replace(ROW, **overrides)


# ==============================================================================================
# design
# ==============================================================================================


def test_the_design_has_the_coded_columns_in_order_with_the_intercept_first() -> None:
    """ADR 0001's coding, one column per parameter in the row's order: a continuous covariate
    raw, a binary 0/1 with the first loaded level 0, a categorical and an ordered factor as
    k − 1 treatment contrasts against the first level, an interaction the product.
    The table holds no interaction column, since a fitter builds it from its parts, as lme4 and
    brms do (#155)."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.design == ('Intercept', 'x', 'sex', 'diet[b]', 'diet[c]', 'grade[mid]', 'grade[hi]', 'x:sex')  # fmt: skip
    coded = problem.table[list(problem.design[:-1])]
    assert coded['Intercept'].tolist() == [1.0] * 12
    assert coded['x'].tolist() == X
    assert coded['sex'].tolist() == SEX
    assert coded['diet[b]'].tolist() == [0, 1, 0] * 4
    assert coded['diet[c]'].tolist() == [0, 0, 1] * 4
    assert coded['grade[mid]'].tolist() == [0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0]
    assert coded['grade[hi]'].tolist() == [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1]
    assert all(coded[c].dtype == np.float64 for c in coded)
    assert 'x:sex' not in problem.table


@pytest.mark.parametrize(
    ('values', 'coded'),
    [
        (pd.Series([1.0, -1.0, 2.5], name='x'), {'x': [1.0, -1.0, 2.5]}),
        (pd.Series(['m', 'f', 'm'], name='sex'), {'sex': [1.0, 0.0, 1.0]}),
        (
            pd.Series(
                pd.Categorical(['b', 'a', 'c', 'a'], categories=['a', 'b', 'c']), name='diet'
            ),
            {'diet[b]': [1.0, 0.0, 0.0, 0.0], 'diet[c]': [0.0, 0.0, 1.0, 0.0]},
        ),
        (
            pd.Series(
                pd.Categorical(['hi', 'lo', 'mid'], categories=['lo', 'mid', 'hi'], ordered=True),
                name='grade',
            ),
            {'grade[mid]': [0.0, 0.0, 1.0], 'grade[hi]': [1.0, 0.0, 0.0]},
        ),
    ],
    ids=[
        'continuous-raw',
        'binary-first-level-0',
        'categorical-contrasts',
        'ordered-by-its-levels',
    ],
)
def test_one_column_codes_into_the_design_columns_its_kind_gives(
    values: pd.Series, coded: dict[str, list[float]]
) -> None:
    """The flat pass codes a table that has no registry row, so the coding of one column is
    callable alone, its kind by the typing rule. An ordered factor's reference is its first
    level, `lo`, not the first in the alphabet."""
    columns = codeCovariate(values)
    assert {name: column.tolist() for name, column in columns.items()} == coded


def test_an_integer_covariate_is_continuous_unless_it_arrives_as_a_categorical() -> None:
    """An integer column with few values is one slope, as its source fits it (#108).
    An R factor, or a column the row declares categorical, reaches the contract as a pandas
    categorical (the loader applies `types`) and becomes treatment contrasts."""
    row = fixtureRow(covariates=('x', 'rating'), interactions=())
    plain = Problem.build(row, fixtureTable())
    assert plain.design == ('Intercept', 'x', 'rating')
    assert plain.table['rating'].tolist() == RATING
    assert plain.scales['full'][0]['rating'] == momentsOf(RATING, pd.Series([True] * 12))
    factor = fixtureTable().astype({'rating': 'category'})
    coded = Problem.build(row, factor)
    assert coded.design == ('Intercept', 'x', 'rating[3]', 'rating[5]')


def test_an_undeclared_column_mixing_numbers_and_strings_orders_its_numbers_first() -> None:
    """A plain column orders its levels as the loader orders a declared one (#105):
    numbers first, then strings, as a depth column holding `'>1m'` among its numbers."""
    depth = pd.Series([0.7, '>1m', 1] * 4 + [0.7, 1], dtype=object)
    row = fixtureRow(covariates=('x', 'depth'), interactions=())
    problem = Problem.build(row, fixtureTable().assign(depth=depth))
    assert problem.levels['depth'] == (0.7, 1, '>1m')
    assert problem.design == ('Intercept', 'x', 'depth[1]', 'depth[>1m]')


def test_a_grouping_factor_is_integer_coded_with_its_levels_listed() -> None:
    """A factor column holds 0-based codes in the loaded level order and `levels` says which
    level each code is; the composite `block:plot` is built from its parts, its levels the
    pairs present. `levels` lists every recoded column, so the JSON can say `sex` 1 is `m`."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.factors == ('block', 'block:plot')
    assert problem.table['block'].tolist() == [0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4]
    assert problem.table['block:plot'].tolist() == [0, 0, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6]
    assert problem.levels == {
        'sex': ('f', 'm'),
        'diet': ('a', 'b', 'c'),
        'grade': ('lo', 'mid', 'hi'),
        'block': ('A', 'B', 'C', 'D', 'E'),
        'block:plot': ('A:p1', 'A:p2', 'B:p1', 'B:p2', 'C:p1', 'D:p1', 'E:p1'),
    }
    assert list(problem.table.columns) == [*problem.design[:-1], 'y', 'block', 'block:plot', 'rows', 'groups']  # fmt: skip


@pytest.mark.parametrize(
    'herd, design',
    [
        pytest.param(['u', 'v'] * 7, ('herd',), id='two levels, one 0/1 column'),
        pytest.param(
            ['u', 'v', 'w', 'z'] * 3 + ['u', 'v'], ('herd[v]', 'herd[w]', 'herd[z]'),
            id='four levels, treatment contrasts',
        ),
        pytest.param(
            [1, 2, 3, 4] * 3 + [1, 2], ('herd[2]', 'herd[3]', 'herd[4]'),
            id='four integer codes, contrasts and not one slope',
        ),
        pytest.param(
            [1, 2, 3, 4] * 3 + [5, 1], ('herd[2]', 'herd[3]', 'herd[4]'),
            id='a fifth level only on the row dropped for a missing x',
        ),
    ],
)  # fmt: skip
def test_a_grouping_factor_of_fewer_than_five_levels_becomes_a_categorical_covariate(
    herd: list, design: tuple[str, ...]
) -> None:
    """Two to four groups barely inform a standard deviation, and the reference sampler diverges
    in the funnel they leave (#160). So `build` fits such a factor's levels as fixed effects
    (Harrison et al. 2018), counted over the kept rows. Its columns follow the row's covariates
    and precede its interactions, as R orders a formula's terms."""
    row = fixtureRow(
        grouping_factors=('block', 'herd', 'block:plot'), covariates=('x', 'sex'),
        types={},
    )  # fmt: skip
    problem = Problem.build(row, fixtureTable().assign(herd=herd))
    assert problem.design == ('Intercept', 'x', 'sex', *design, 'x:sex')
    assert problem.factors == ('block', 'block:plot')
    assert 'sd[herd]' not in problem.parameters


@pytest.mark.parametrize(
    'call', [Problem.build, Problem.countColumns], ids=['build', 'countColumns']
)
@pytest.mark.parametrize(
    'random_slopes, reason',
    [
        pytest.param((), 'every grouping factor has fewer than 5 levels', id='no factor left'),
        pytest.param(
            (SlopeTerm('x', 'herd', correlated=True),),
            'random slopes on herd, which has fewer than 5 levels',
            id='a slope on it, named before the count',
        ),
    ],
)  # fmt: skip
def test_a_factor_of_fewer_than_five_levels_alone_or_with_slopes_is_refused(
    call: Callable[[Row, pd.DataFrame], object], random_slopes: tuple[SlopeTerm, ...], reason: str
) -> None:
    """Only a random intercept turns into fixed levels. A problem left without a grouping factor
    is no mixed model (nlme Wheat2), and a slope varying over fixed levels would be an
    interaction the source did not fit (ARM earnings, weaving df_ALL). So `build` refuses both,
    and counting the columns raises as `build` does."""
    row = fixtureRow(grouping_factors=('herd',), random_slopes=random_slopes)
    table = fixtureTable().assign(herd=['u', 'v', 'w'] * 4 + ['u', 'v'])
    with pytest.raises(Refused) as refused:
        call(row, table)
    assert refused.value.reason == reason


# the widths whose columns the columns before them span, over the kept rows 0-11
SUMMED = [x + s for x, s in zip(X, SEX)] + [0.0, 0.0]  # x + sex, as Hoogland's AllKin
PARTNERED = [s * y for s, y in zip(SEX, Y)] + [0.0, 0.0]  # 0 without sex m, as Incentives' v
# no `u` among sex f, the empty cell at width's first level, as shanahan's conventional message
CELLED = pd.Categorical(list('vuwvwvuwvvwwuu'), categories=['u', 'v', 'w'])


@pytest.mark.parametrize(
    'width, interactions, design, dropped',
    [
        pytest.param(
            [4.6] * 14, ('x:sex',), ('x:sex',), ('width',),
            id='a covariate with one value over every row, as ros Helicopters',
        ),
        pytest.param(
            [0.0] * 12 + [5.0, 0.0], ('x:sex',), ('x:sex',), ('width',),
            id='a covariate whose other value sits on the row dropped for a missing x',
        ),
        pytest.param(
            [4.6] * 14, ('x:sex', 'sex:diet'), ('x:sex', 'sex:diet[b]'), ('width', 'sex:diet[c]'),
            id='an interaction contrast of an empty cell, no diet c among sex m',
        ),
        pytest.param(
            SUMMED, ('x:sex',), ('x:sex',), ('width',),
            id='a covariate that sums earlier ones',
        ),
        pytest.param(
            PARTNERED, ('x:sex', 'sex:width'), ('width', 'x:sex'), ('sex:width',),
            id='an interaction repeating a covariate that is 0 without its partner',
        ),
        pytest.param(
            CELLED, ('x:sex', 'sex:width'), ('width[v]', 'width[w]', 'x:sex', 'sex:width[v]'), ('sex:width[w]',),
            id='an empty cell at a first level, its contrasts not constant',
        ),
    ],
)  # fmt: skip
def test_a_design_column_aliased_by_the_columns_before_it_is_dropped_and_recorded(
    width: list, interactions: tuple[str, ...], design: tuple[str, ...], dropped: tuple
) -> None:
    """No likelihood identifies a coefficient whose column the columns before it span:
    a constant column (#131), a sum, a product equal to one of its parts, an empty cell (#151).
    Z-scored a constant is rounding noise or NaN, and the others leave a ridge the prior fills.
    `build` drops the later column, as lme4 drops the columns of a rank-deficient model matrix,
    and says so."""
    row = fixtureRow(covariates=(*ROW.covariates, 'width'), interactions=interactions)
    problem = Problem.build(row, fixtureTable().assign(width=width))
    expected = ('Intercept', 'x', 'sex', 'diet[b]', 'diet[c]', 'grade[mid]', 'grade[hi]', *design)  # fmt: skip
    assert problem.design == expected
    assert problem.dropped_columns == dropped
    standardized = problem.standardized()
    assert list(standardized.columns) == [*expected, 'y', 'block', 'block:plot']
    assert np.linalg.matrix_rank(standardized[list(expected)].to_numpy()) == len(expected)
    assert not set(dropped) & set(problem.table.columns)
    assert not set(dropped) & set(problem.scales['full'][0])
    assert not set(dropped) & set(problem.parameters)
    assert not standardized.isna().any().any()


def test_a_dropped_part_stays_in_the_table_while_a_kept_interaction_needs_it() -> None:
    """`width` sums `x` and `sex`, as Hoogland's AllKin, so the drop removes it, but no earlier
    column spans `diet:width`. lme4 drops `width` and keeps `diet:width` too.
    The table keeps `width`, scaled per fold, so a fitter can build the product (#155)."""
    row = fixtureRow(covariates=(*ROW.covariates, 'width'), interactions=('diet:width',))
    problem = Problem.build(row, fixtureTable().assign(width=SUMMED))
    assert problem.design[-2:] == ('diet[b]:width', 'diet[c]:width')
    assert problem.dropped_columns == ('width',)
    assert 'width' not in problem.parameters
    assert 'width' in problem.scales['full'][0]
    standardized = problem.standardized()
    width = np.array(X) + np.array(SEX)  # (12,) over the kept rows
    z = (width - width.mean()) / width.std(ddof=1)  # (12,)
    assert standardized['diet[b]:width'].to_numpy() == pytest.approx(z * np.array([0, 1, 0] * 4))
    assert not standardized.isna().any().any()


@pytest.mark.lme4
@pytest.mark.parametrize(
    'width, interactions',
    [
        pytest.param(SUMMED, ('x:sex',), id='a covariate that sums earlier ones'),
        pytest.param(
            PARTNERED, ('x:sex', 'sex:width'),
            id='an interaction repeating a covariate that is 0 without its partner',
        ),
        pytest.param(
            CELLED, ('x:sex', 'sex:width'),
            id='an empty cell at a first level, its contrasts not constant',
        ),
        pytest.param(SUMMED, ('diet:width',), id='a dropped part of a kept interaction'),
    ],
)  # fmt: skip
def test_lme4_estimates_the_design_columns_the_contract_keeps(
    tmp_path: Path, width: list, interactions: tuple[str, ...]
) -> None:
    """The drop rewrites R's pivoted QR, so lme4, which runs it on its model matrix, keeps the
    same columns. The row leaves out the ordered `grade`, which R codes as polynomials."""
    row = fixtureRow(
        covariates=('x', 'sex', 'diet', 'width'), interactions=interactions,
        grouping_factors=('block',), random_slopes=(),
    )  # fmt: skip
    table = fixtureTable().assign(width=width)
    problem = Problem.build(row, table)
    terms = ' + '.join([*row.covariates, *interactions])
    fitted = frequentist.fit(table, f'y ~ {terms} + (1 | block)', 'gaussian', tmp_path, 60)
    assert list(fitted.fixed) == [_lme4Name(column) for column in problem.design]


def _lme4Name(column: str) -> str:
    """lme4's name of a design column of the fixture: `sex` is `sexm`, `diet[b]` is `dietb`."""
    if column == 'Intercept':
        return '(Intercept)'
    names = []
    for part in column.split(':'):
        if part == 'sex':
            names.append('sexm')
        else:
            names.append(part.replace('[', '').replace(']', ''))
    return ':'.join(names)


@pytest.mark.parametrize(
    'overrides, columns, counts',
    [
        pytest.param({}, {}, (8, 12), id='the fixture, its two missing rows left out'),
        pytest.param(
            {'interactions': ('diet:grade',)}, {}, (11, 12),
            id='an interaction of two contrasts, their product',
        ),
        pytest.param(
            {'covariates': (*ROW.covariates, 'width'), 'interactions': ('x:sex', 'sex:diet')},
            {'width': [4.6] * 14}, (11, 12),
            id='the columns the drop removes, a constant and an empty cell',
        ),
        pytest.param(
            {'grouping_factors': ('block', 'herd', 'block:plot'), 'covariates': ('x', 'sex')},
            {'herd': [1, 2, 3, 4] * 3 + [5, 1]}, (7, 12),
            id='a factor of four levels over the kept rows, its contrasts',
        ),
    ],
)  # fmt: skip
def test_counting_gives_the_coded_columns_before_the_drop_and_the_complete_rows(
    overrides: dict, columns: dict, counts: tuple[int, int]
) -> None:
    """A design whose coded columns, with `Intercept`, outnumber its complete rows has no
    condition index, and the drop over so wide a design takes days (openml 41434: 97,619
    columns over 39,948 rows). So the survey counts both before it builds."""
    row = fixtureRow(**overrides)
    assert Problem.countColumns(row, fixtureTable().assign(**columns)) == counts


# ==============================================================================================
# rows
# ==============================================================================================


def test_the_dropped_share_counts_the_rows_missing_a_model_value() -> None:
    """Two of 14 rows miss a model value (`x`, `block`); a row missing a part of the composite
    factor counts too. Values as loaded are values: the `-1` in `x` is no missing code."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.dropped_share == 2 / 14
    assert -1.0 in problem.table['x'].tolist()
    without_plot = fixtureTable().assign(plot=lambda table: table['plot'].mask(table.index == 0))
    assert Problem.build(fixtureRow(), without_plot).dropped_share == 3 / 14


def test_a_table_with_no_complete_row_is_refused() -> None:
    """A pharmacokinetic event table (nlme Phenobarb, Quinidine) has the dose on dosing rows
    and the response on observation rows, so every row misses a model value: there is no
    problem to state, and `build` says so rather than returning an empty one."""
    table = fixtureTable().assign(y=NAN)
    with pytest.raises(Refused, match='fixture/trial/1: no row has every model value'):
        Problem.build(fixtureRow(), table)


def test_a_covariate_varying_only_over_rows_without_a_response_is_refused() -> None:
    """Stata's copy of Phenobarb has complete rows, but a dose of 0 on each observation row,
    so its doses vary only over the dosing rows, which have no response (#131).
    Dropping the constant dose would state a model of another quantity, so `build` refuses it,
    as it refuses nlme's copy."""
    row = fixtureRow(covariates=(*ROW.covariates, 'dose'))
    dosed = fixtureTable().assign(y=[NAN, NAN, *Y[2:], 1.0, 2.0], dose=[5.0, 7.0] + [0.0] * 12)
    with pytest.raises(Refused, match='fixture/trial/1: dose varies only over rows without a response'):  # fmt: skip
        Problem.build(row, dosed)


# ==============================================================================================
# response and family
# ==============================================================================================


@pytest.mark.parametrize(
    'response_type, response, coded, family',
    [
        ('continuous', 'y', Y, ('gaussian', 'identity')),
        ('binary', 'hit', HIT, ('bernoulli', 'logit')),
        ('count', 'n', N, ('poisson', 'log')),
        ('binomial', 'wins', WINS, ('binomial', 'logit')),
        ('ordinal', 'rating', [1, 3, 2, 1, 3, 2, 3, 1, 2, 3, 2, 3], ('cumulative', 'logit')),
    ],
)
def test_the_response_is_coded_by_its_type_and_the_family_follows_the_rule(
    response_type: str, response: str, coded: list, family: tuple[str, str]
) -> None:
    """Continuous raw, binary 0/1 with the first loaded level 0, count as loaded, binomial the
    successes as loaded beside the trials column, ordinal its 1-based index in the loaded
    level order (the ratings 1, 3, 5 become 1, 2, 3); the family by ADR 0001's rule."""
    trials = 'games' if response_type == 'binomial' else ''
    row = fixtureRow(response=response, response_type=response_type, trials=trials)
    problem = Problem.build(row, fixtureTable())
    assert problem.response == response
    assert problem.table[response].tolist() == coded
    assert (problem.family, problem.link) == family
    assert problem.trials == (trials or None)
    if trials:
        assert problem.table[trials].tolist() == GAMES
    expected_levels = {'binary': ('no', 'yes'), 'ordinal': (1, 3, 5)}.get(response_type)
    assert problem.levels.get(response) == expected_levels


@pytest.mark.parametrize(
    'overrides, reason',
    [
        (
            {'response_type': 'categorical'},
            'a categorical response is outside suite 1.1 (ADR 0001)',
        ),
        ({'family': 'cox'}, 'family cox is a censored model, outside suite 1.1 (ADR 0001)'),
        ({'family': 'weibull'}, 'family weibull is a censored model, outside suite 1.1 (ADR 0001)'),
    ],
)
def test_a_categorical_or_censored_row_is_refused_naming_the_reason(
    overrides: dict, reason: str
) -> None:
    """`build` on such a row refuses it rather than fitting a model of another quantity, and
    the refusal carries the reason the admission script writes to `refused.csv`."""
    row = fixtureRow(**overrides)
    with pytest.raises(Refused) as refused:
        Problem.build(row, fixtureTable())
    assert refused.value.reason == reason


def test_any_other_documented_family_takes_the_rule_in_suite_1_1() -> None:
    """A negative binomial (and from suite 1.2 on a probit) replaces the rule only later (ADR
    0001); in 1.1 the row is admitted and its family is the rule's."""
    row = fixtureRow(response='n', response_type='count', family='negbinomial')
    assert (Problem.build(row, fixtureTable()).family) == 'poisson'


# ==============================================================================================
# prior and parameter names
# ==============================================================================================

NORMAL = Prior('normal', (0, 2.5))
HALF_T = Prior('student_t', (3, 0, 2.5))


def test_the_prior_record_states_adr_0001s_prior_per_parameter_group_the_problem_has() -> None:
    """One prior serves every problem (ADR 0001), keyed by brms's class so the runner (#62) reads
    it; a group the problem lacks is absent, since brms refuses a prior on an absent class: a
    Poisson intercept-only model has no `b`, `cor` or `sigma`, an ordinal model no `Intercept`
    (its thresholds take brms's default)."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.prior == {
        'Intercept': NORMAL,
        'b': NORMAL,
        'sd': HALF_T,
        'cor': Prior('lkj', (1,)),
        'sigma': HALF_T,
    }
    intercept_only = fixtureRow(
        response='n', response_type='count', covariates=(), interactions=(), random_slopes=()
    )
    prior = Problem.build(intercept_only, fixtureTable()).prior
    assert prior == {'Intercept': NORMAL, 'sd': HALF_T}
    ordinal = fixtureRow(response='rating', response_type='ordinal')
    assert 'Intercept' not in Problem.build(ordinal, fixtureTable()).prior


def test_the_parameter_names_follow_the_rule_in_brmss_block_order() -> None:
    """Draws and scores join on names: `Intercept`, the design columns, then per factor
    `sd[<factor>]`, `sd[<x>|<factor>]` with `<x>` the coded column, `cor[<factor>]` for
    correlated slopes, then `sigma`; the cor block's elements are the intercept and the
    slope terms in their order, listed so that element (i, j) is defined."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.parameters == (
        'Intercept', 'x', 'sex', 'diet[b]', 'diet[c]', 'grade[mid]', 'grade[hi]', 'x:sex',
        'sd[block]', 'sd[x|block]', 'cor[block]', 'sd[block:plot]', 'sigma',
    )  # fmt: skip
    assert problem.correlations == {'block': ('Intercept', 'x')}


def test_a_slope_on_a_categorical_names_each_contrast_and_an_uncorrelated_one_has_no_cor() -> None:
    """`sex|block;diet||block:plot`: the correlated slope joins block's cor block after the
    intercept, the uncorrelated categorical slope gives one `sd` per contrast and no block."""
    slopes = (
        SlopeTerm('x', 'block', correlated=True),
        SlopeTerm('sex', 'block', correlated=True),
        SlopeTerm('diet', 'block:plot', correlated=False),
    )
    row = fixtureRow(response='n', response_type='count', random_slopes=slopes)
    problem = Problem.build(row, fixtureTable())
    assert problem.parameters[8:] == (
        'sd[block]', 'sd[x|block]', 'sd[sex|block]', 'cor[block]',
        'sd[block:plot]', 'sd[diet[b]|block:plot]', 'sd[diet[c]|block:plot]',
    )  # fmt: skip
    assert problem.correlations == {'block': ('Intercept', 'x', 'sex')}


def test_an_ordinal_problem_names_its_thresholds_as_brms_does() -> None:
    """Where the rule is silent the name is brms's at the pinned version: cumulative's k − 1
    thresholds are `Intercept[k]` (brms's `b_Intercept[k]` without the `b_` that `Intercept`
    drops too), and there is no `Intercept`."""
    problem = Problem.build(fixtureRow(response='rating', response_type='ordinal'), fixtureTable())
    assert problem.parameters[:3] == ('Intercept[1]', 'Intercept[2]', 'x')
    assert 'Intercept' not in problem.parameters
    assert problem.parameters[-1] == 'sd[block:plot]'


# ==============================================================================================
# splits
# ==============================================================================================


def groupedTable(sizes: list[int], crossed: int = 0) -> pd.DataFrame:
    """`sizes[i]` rows in group `g{i}` of `g`; with `crossed`, a second factor `h` cycling
    through that many levels; a continuous `x` and `y` that differ on every row."""
    groups = [f'g{i}' for i, size in enumerate(sizes) for _ in range(size)]
    n = len(groups)
    table = pd.DataFrame({'g': groups, 'x': np.arange(n) * 0.5, 'y': np.arange(n) ** 0.5})
    if crossed:
        table['h'] = [f'h{i % crossed}' for i in range(n)]
    return table


def groupedRow(source: str = 'fixture', crossed: bool = False) -> Row:
    factors = ('g', 'h') if crossed else ('g',)
    return fixtureRow(
        source=source, grouping_factors=factors, covariates=('x',), interactions=(),
        random_slopes=(), types={},
    )  # fmt: skip


def regimes(problem: Problem) -> pd.DataFrame:
    return problem.table[['rows', 'groups']]


def test_the_splits_are_a_pure_function_of_the_problem_id() -> None:
    """The seed is the first 8 bytes of sha256 of the id (ADR 0001), so a rebuild anywhere
    gives the same folds, and another problem over the same table gets other folds."""
    table = groupedTable([10] * 20)
    problem = Problem.build(groupedRow(), table)
    again = Problem.build(groupedRow(), table)
    other = Problem.build(groupedRow(source='other'), table)
    assert regimes(problem).equals(regimes(again))
    assert not regimes(problem)['rows'].equals(regimes(other)['rows'])
    assert not regimes(problem)['groups'].equals(regimes(other)['groups'])


SIZES = st.lists(st.integers(1, 8), min_size=5, max_size=40)
SOURCES = st.text(alphabet='abcxyz', min_size=1, max_size=8)


@given(sizes=SIZES, crossed=st.one_of(st.just(0), st.integers(5, 8)), source=SOURCES)
def test_regime_rows_deals_every_row_but_a_first_per_group_into_five_even_folds(
    sizes: list[int], crossed: int, source: str
) -> None:
    """Regime `rows` predicts inside seen groups.
    So every group of every factor keeps a row that no fold holds (-1), and a single-row group
    keeps its row. With one factor it keeps only that row, and every other row is held out once,
    in one of five folds of even size."""
    table = groupedTable(sizes, crossed)
    problem = Problem.build(groupedRow(source, crossed=bool(crossed)), table)
    folds = problem.table['rows']
    never = folds == -1
    for factor in problem.factors:
        assert set(problem.table.loc[never, factor]) == set(problem.table[factor])
    if not crossed:
        assert never.sum() == len(sizes)
    assert set(folds) <= {-1, 0, 1, 2, 3, 4}
    counts = folds[~never].value_counts().reindex(range(5), fill_value=0)
    assert counts.max() - counts.min() <= 1


@given(sizes=SIZES, source=SOURCES)
def test_regime_groups_deals_the_first_factors_groups_whole_into_five_folds(
    sizes: list[int], source: str
) -> None:
    """Regime `groups` predicts new groups: each group of the first factor is held out once,
    with all its rows, in one of five folds that differ by at most one group.
    A factor has at least five groups, so a fold leaves at least four seen."""
    table = groupedTable(sizes)
    problem = Problem.build(groupedRow(source), table)
    folds_per_group = problem.table.groupby('g')['groups'].nunique()
    assert (folds_per_group == 1).all()
    groups_per_fold = problem.table.groupby('g')['groups'].first().value_counts()
    assert sorted(groups_per_fold.index) == list(range(5))
    assert groups_per_fold.max() - groups_per_fold.min() <= 1


def test_regime_groups_deals_the_first_factor_left_after_the_conversion() -> None:
    """A first factor of fewer than five levels becomes a covariate, as nlme Gun's `Physique`,
    so regime `groups` holds out the groups of the next factor."""
    row = fixtureRow(grouping_factors=('herd', 'block', 'block:plot'))
    problem = Problem.build(row, fixtureTable().assign(herd=['u', 'v', 'w'] * 4 + ['u', 'v']))
    assert problem.factors == ('block', 'block:plot')
    assert (problem.table.groupby('block')['groups'].nunique() == 1).all()
    assert problem.table['groups'].nunique() == 5


# ==============================================================================================
# scales
# ==============================================================================================


def momentsOf(values: list[float], seen: pd.Series) -> Scale:
    kept = np.asarray(values)[seen.to_numpy()]
    return Scale(mean=float(np.mean(kept)), sd=float(np.std(kept, ddof=1)))


def foldMoments(problem: Problem, regime: str, folds: int) -> tuple[dict[str, Scale], ...]:
    """The moments of `x` and `y` over the rows each fold's fit sees."""
    moments = []
    for fold in range(folds):
        seen = problem.table[regime] != fold
        moments.append({'x': momentsOf(X, seen), 'y': momentsOf(Y, seen)})
    return tuple(moments)


def test_each_fold_scales_the_continuous_columns_by_the_rows_its_fit_sees() -> None:
    """No held-out row leaks into a scaler (ADR 0001): `full` is one fold with the table's
    moments, and each fold of a split regime holds its seen rows' (sample SD, as R's `scale`),
    for the continuous covariate `x` and the continuous response `y` only. The fixture's five
    holdable rows fill five folds, and its five blocks fill five. The table stays in raw units."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    every_row = pd.Series([True] * 12)
    assert problem.scales == {
        'full': ({'x': momentsOf(X, every_row), 'y': momentsOf(Y, every_row)},),
        'rows': foldMoments(problem, 'rows', 5),
        'groups': foldMoments(problem, 'groups', 5),
    }
    assert problem.table['x'].tolist() == X
    assert problem.table['y'].tolist() == Y
    count = Problem.build(fixtureRow(response='n', response_type='count'), fixtureTable())
    assert set(count.scales['full'][0]) == {'x'}


def test_a_level_present_only_in_held_rows_leaves_an_all_zero_column_in_that_fold() -> None:
    """The coding is the full table's (ADR 0001, amended 2026-10-09): `kind` gives each group
    its own level beside a shared reference, so the group fold 0 holds has a level no seen row
    has, and its contrast column stays in the design, all zero over the seen rows, not dropped."""
    table = groupedTable([4] * 5)
    kinds = []
    for group in range(5):
        kinds += ['base', f'k{group}', f'k{group}', f'k{group}']
    levels = ['base', 'k0', 'k1', 'k2', 'k3', 'k4']
    table['kind'] = pd.Categorical(kinds, categories=levels)
    row = replace(groupedRow(), covariates=('x', 'kind'), types={'kind': 'categorical'})
    problem = Problem.build(row, table)
    seen = problem.table['groups'] != 0
    [held_level] = set(table.loc[~seen, 'kind']) - {'base'}
    assert problem.design == ('Intercept', 'x', *[f'kind[{level}]' for level in levels[1:]])
    assert problem.table.loc[seen, f'kind[{held_level}]'].eq(0).all()
    assert problem.table.loc[~seen, f'kind[{held_level}]'].eq(1).any()


# ==============================================================================================
# the standardized table
# ==============================================================================================
Z = (np.array(X) - np.mean(X)) / np.std(X, ddof=1)  # (12,) `x` z-scored over every row


@given(sizes=SIZES, source=SOURCES)
def test_each_continuous_column_of_a_standardized_table_has_mean_0_and_sd_1(
    sizes: list[int], source: str
) -> None:
    """References and scores are stated on the standardized scale.
    Each fold z-scores `x` and `y` over the rows its fit sees."""
    problem = Problem.build(groupedRow(source), groupedTable(sizes))
    for regime, folds in problem.scales.items():
        for fold in range(len(folds)):
            table = problem.standardized(regime, fold)
            for column in ('x', 'y'):
                assert table[column].mean() == pytest.approx(0, abs=1e-12)
                assert table[column].std() == pytest.approx(1)


def test_an_interaction_is_the_product_of_its_standardized_parts() -> None:
    """`x:sex` is the z-scored `x` times the 0/1 `sex`.
    Z-scoring the raw product would give another column."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    table = problem.standardized()
    assert table['x:sex'].to_numpy() == pytest.approx(Z * np.array(SEX))
    assert table['sex'].tolist() == SEX


def test_an_interaction_with_a_level_holding_a_colon_finds_its_parts() -> None:
    """A level may contain `:`, as a time does.
    So `diet[b:c]:x` is `diet[b:c]` times `x`, and a split on `:` would name no column."""
    table = fixtureTable()
    table['diet'] = table['diet'].cat.rename_categories({'b': 'b:c'})
    row = fixtureRow(interactions=('diet:x',))
    problem = Problem.build(row, table)
    standardized = problem.standardized()
    assert problem.design[-2:] == ('diet[b:c]:x', 'diet[c]:x')
    assert standardized['diet[b:c]:x'].to_numpy() == pytest.approx(Z * np.array([0, 1, 0] * 4))


def test_a_three_way_interaction_is_the_product_of_its_three_standardized_parts() -> None:
    """Some candidates carry a three-way term (`MASS/npk/1`), so a name holds more than two parts."""
    row = fixtureRow(interactions=('x:sex:diet',))
    standardized = Problem.build(row, fixtureTable()).standardized()
    expected = Z * np.array(SEX) * np.array([0, 1, 0] * 4)
    assert standardized['x:sex:diet[b]'].to_numpy() == pytest.approx(expected)


# ==============================================================================================
# the draw names
# ==============================================================================================
SLOPES = (
    SlopeTerm('x', 'block', correlated=True),
    SlopeTerm('sex', 'block', correlated=True),
    SlopeTerm('diet', 'block:plot', correlated=False),
)


def test_the_global_draws_expand_each_cor_block_to_its_pairs_in_brmss_order() -> None:
    """A draw file has one column per scalar.
    So `cor[block]` over (Intercept, x, sex) becomes three pairs, in brms's order (#63)."""
    row = fixtureRow(response='n', response_type='count', random_slopes=SLOPES)
    problem = Problem.build(row, fixtureTable())
    assert problem.globalDraws() == (
        'Intercept', 'x', 'sex', 'diet[b]', 'diet[c]', 'grade[mid]', 'grade[hi]', 'x:sex',
        'sd[block]', 'sd[x|block]', 'sd[sex|block]',
        'cor[block][Intercept,x]', 'cor[block][Intercept,sex]', 'cor[block][x,sex]',
        'sd[block:plot]', 'sd[diet[b]|block:plot]', 'sd[diet[c]|block:plot]',
    )  # fmt: skip


def test_the_local_draws_name_each_group_by_its_code_in_the_table() -> None:
    """Random effects are named like their `sd`, with the group's code.
    So a group's draws join its rows through the factor column of the standardized table."""
    row = fixtureRow(response='n', response_type='count', random_slopes=SLOPES)
    problem = Problem.build(row, fixtureTable())
    local = problem.localDraws()
    assert local['block'] == (
        *[f'r[block][{j}]' for j in range(5)],
        *[f'r[x|block][{j}]' for j in range(5)],
        *[f'r[sex|block][{j}]' for j in range(5)],
    )
    assert list(local) == ['block', 'block:plot']
    assert local['block:plot'][6:9] == (
        'r[block:plot][6]',
        'r[diet[b]|block:plot][0]',
        'r[diet[b]|block:plot][1]',
    )
    assert len(local['block:plot']) == 3 * 7
    codes = problem.standardized()['block:plot']
    assert {f'r[block:plot][{j}]' for j in codes} == set(local['block:plot'][:7])


def test_a_factors_slopes_follow_its_sd_parameters_not_the_design() -> None:
    """The handoff writes the formula and reads effects back through `slopes`.
    So the slopes follow the `sd` order, here `sex` before `x`.
    A categorical slope gives its contrast columns, and `block:plot` does not take `block`'s."""
    slopes = (
        SlopeTerm('sex', 'block', correlated=False),
        SlopeTerm('x', 'block', correlated=False),
        SlopeTerm('diet', 'block:plot', correlated=False),
    )
    row = fixtureRow(response='n', response_type='count', random_slopes=slopes)
    problem = Problem.build(row, fixtureTable())
    assert problem.slopes('block') == ('sex', 'x')
    assert problem.slopes('block:plot') == ('diet[b]', 'diet[c]')


# ==============================================================================================
# dimensions
# ==============================================================================================
# a factor crossing `block`: site s1 lies in blocks A, B and E, block A holds sites s1-s3
SITE = ['s1', 's2', 's3', 's4', 's5'] * 2 + ['s1', 's2', 's1', 's2']
HERD = ['u', 'v'] * 7  # two levels, so the five-level rule makes it a covariate


@pytest.mark.parametrize(
    'overrides, columns, dimensions',
    [
        pytest.param(
            {}, {},
            Dimensions(n=12, d=8, grouping='nested', m=(5, 7), q=(2, 1), n_i_min=(2, 1), n_i_max=(3, 2)),
            id='the fixture, its two missing rows dropped and its slope x on block',
        ),
        pytest.param(
            {'random_slopes': (SlopeTerm('diet', 'block', correlated=True),)}, {},
            Dimensions(n=12, d=8, grouping='nested', m=(5, 7), q=(3, 1), n_i_min=(2, 1), n_i_max=(3, 2)),
            id='a slope on a categorical counts its two contrasts',
        ),
        pytest.param(
            {'grouping_factors': ('block', 'site')}, {'site': SITE},
            Dimensions(n=12, d=8, grouping='crossed', m=(5, 5), q=(2, 1), n_i_min=(2, 2), n_i_max=(3, 3)),
            id='a factor crossing block',
        ),
        pytest.param(
            {'grouping_factors': ('block', 'herd')}, {'herd': HERD},
            Dimensions(n=12, d=9, grouping='single', m=(5,), q=(2,), n_i_min=(2,), n_i_max=(3,)),
            id='a two-level factor made a covariate leaves one factor and adds a column',
        ),
    ],
)  # fmt: skip
def test_a_problem_measures_its_dimensions_after_the_drop_and_the_five_level_rule(
    overrides: dict, columns: dict, dimensions: Dimensions
) -> None:
    """The candidate list's axes (#193) describe the problem a user loads.
    That is the kept rows and the factors left after the five-level rule, not the registry
    row's table, which `dimensions.csv` measures."""
    row = fixtureRow(**overrides)
    problem = Problem.build(row, fixtureTable().assign(**columns))
    assert problem.measureDimensions() == dimensions
