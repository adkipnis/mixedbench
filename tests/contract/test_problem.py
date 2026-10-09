"""`Problem.build` at its seam (#28): a typed registry row and the loader's typed table in, the
coded design, the response, the family, the prior and the parameter names out (ADR 0001).

The fixture is one hand-made grouped table: a continuous covariate carrying a `-1`, a binary
string, a three-level categorical, an ordered factor, the interaction `x:sex`, the factors
`block` and the composite `block:plot`, the slope `x|block`, and two planted missing rows (one
in `x`, one in `block`); every expected value below is computed by hand from it.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from mixedbench.contract import Prior, Problem, refusal
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
ROW = Row(
    source='fixture', tier='R', sources=('fixture:trial',), object='trial', reader='pandas',
    licence='MIT', model_index=1, response='y', response_type='continuous', trials='', family='',
    grouping_factors=('block', 'block:plot'), covariates=('x', 'sex', 'diet', 'grade'),
    interactions=('x:sex',), random_slopes=(SlopeTerm('x', 'block', correlated=True),),
    ignore=(), types={'diet': 'categorical', 'grade': 'ordered'},
    formula='y ~ x * sex + diet + grade + (x | block) + (1 | block:plot)', documented_prior='',
    published_model='yes', domain='test', confidence='high', verified='hand', notes='',
)  # fmt: skip


def fixtureTable() -> pd.DataFrame:
    """Rows 0–11 are kept; row 12 misses `x`, row 13 misses `block`."""
    return pd.DataFrame(
        {
            'block': ['A'] * 4 + ['B'] * 4 + ['C'] * 4 + ['A', None],
            'plot': ['p1', 'p1', 'p2', 'p2'] * 3 + ['p1', 'p1'],
            'x': X + [NAN, 1.0],
            'sex': ['fm'[s] for s in SEX] + ['f', 'm'],
            'diet': pd.Categorical(['a', 'b', 'c'] * 4 + ['a', 'b'], categories=['a', 'b', 'c']),
            'grade': pd.Categorical(
                ['lo', 'mid', 'hi'] * 4 + ['lo', 'mid'],
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
    K − 1 treatment contrasts against the first level, an interaction the product."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.design == ('Intercept', 'x', 'sex', 'diet[b]', 'diet[c]', 'grade[mid]', 'grade[hi]', 'x:sex')  # fmt: skip
    design = problem.table[list(problem.design)]
    assert design['Intercept'].tolist() == [1.0] * 12
    assert design['x'].tolist() == X
    assert design['sex'].tolist() == SEX
    assert design['diet[b]'].tolist() == [0, 1, 0] * 4
    assert design['diet[c]'].tolist() == [0, 0, 1] * 4
    assert design['grade[mid]'].tolist() == [0, 1, 0] * 4
    assert design['grade[hi]'].tolist() == [0, 0, 1] * 4
    assert design['x:sex'].tolist() == [x * s for x, s in zip(X, SEX)]
    assert all(design[c].dtype == np.float64 for c in problem.design)


def test_a_grouping_factor_is_integer_coded_with_its_levels_listed() -> None:
    """A factor column holds 0-based codes in the loaded level order and `levels` says which
    level each code is; the composite `block:plot` is built from its parts, its levels the
    pairs present. `levels` lists every recoded column, so the JSON can say `sex` 1 is `m`."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.factors == ('block', 'block:plot')
    assert problem.table['block'].tolist() == [0] * 4 + [1] * 4 + [2] * 4
    assert problem.table['block:plot'].tolist() == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    assert problem.levels == {
        'sex': ('f', 'm'),
        'diet': ('a', 'b', 'c'),
        'grade': ('lo', 'mid', 'hi'),
        'block': ('A', 'B', 'C'),
        'block:plot': ('A:p1', 'A:p2', 'B:p1', 'B:p2', 'C:p1', 'C:p2'),
    }
    assert list(problem.table.columns) == [*problem.design, 'y', 'block', 'block:plot']


# ==============================================================================================
# rows
# ==============================================================================================


def test_the_dropped_share_counts_the_rows_missing_a_model_value() -> None:
    """Two of 14 rows miss a model value (`x`, `block`); a row missing a part of the composite
    factor counts too. Values as loaded are values: the `-1` in `x` is no missing code."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    assert problem.dropped_share == 2 / 14
    assert -1.0 in problem.table['x'].tolist()
    withoutPlot = fixtureTable().assign(plot=lambda df: df['plot'].mask(df.index == 0))
    assert Problem.build(fixtureRow(), withoutPlot).dropped_share == 3 / 14


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
    expectedLevels = {'binary': ('no', 'yes'), 'ordinal': (1, 3, 5)}.get(response_type)
    assert problem.levels.get(response) == expectedLevels


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
    """The admission script lists refused rows by `refusal` without loading a table; `build`
    on such a row fails with the same reason rather than fitting a model of another quantity."""
    row = fixtureRow(**overrides)
    assert refusal(row) == reason
    with pytest.raises(ValueError, match=reason.replace('(', r'\(').replace(')', r'\)')):
        Problem.build(row, fixtureTable())


def test_any_other_documented_family_takes_the_rule_in_suite_1_1() -> None:
    """A negative binomial (and from suite 1.2 on a probit) replaces the rule only later (ADR
    0001); in 1.1 the row is admitted and its family is the rule's."""
    row = fixtureRow(response='n', response_type='count', family='negbinomial')
    assert refusal(row) is None
    assert (Problem.build(row, fixtureTable()).family) == 'poisson'


# ==============================================================================================
# prior and parameter names
# ==============================================================================================

NORMAL = Prior('normal', (0, 2.5))
HALF_T = Prior('student_t', (3, 0, 2.5))


def test_the_prior_record_states_adr_0001s_prior_per_parameter_group_the_problem_has() -> None:
    """One prior serves every problem (ADR 0001), keyed by brms's class so item 4's call reads
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
    interceptOnly = fixtureRow(
        response='n', response_type='count', covariates=(), interactions=(), random_slopes=()
    )
    assert Problem.build(interceptOnly, fixtureTable()).prior == {'Intercept': NORMAL, 'sd': HALF_T}
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
    """Where the rule is silent the name is brms's at the pinned version: cumulative's K − 1
    thresholds are `Intercept[k]` (brms's `b_Intercept[k]` without the `b_` that `Intercept`
    drops too), and there is no `Intercept`."""
    problem = Problem.build(fixtureRow(response='rating', response_type='ordinal'), fixtureTable())
    assert problem.parameters[:3] == ('Intercept[1]', 'Intercept[2]', 'x')
    assert 'Intercept' not in problem.parameters
    assert problem.parameters[-1] == 'sd[block:plot]'
