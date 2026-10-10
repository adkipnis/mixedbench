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
from hypothesis import given
from hypothesis import strategies as st
from mixedbench.contract import Prior, Problem, Refused, Scale
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
    assert list(problem.table.columns) == [*problem.design, 'y', 'block', 'block:plot', 'rows', 'groups']  # fmt: skip


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


def test_a_table_with_no_complete_row_is_refused() -> None:
    """A pharmacokinetic event table (nlme Phenobarb, Quinidine) has the dose on dosing rows
    and the response on observation rows, so every row misses a model value: there is no
    problem to state, and `build` says so rather than returning an empty one."""
    table = fixtureTable().assign(y=NAN)
    with pytest.raises(Refused, match='fixture/trial/1: no row has every model value'):
        Problem.build(fixtureRow(), table)


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
    """One prior serves every problem (ADR 0001), keyed by brms's class so item 5's call reads
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
    return problem.table[['rows', 'groups']].astype(str)


def test_the_splits_are_a_pure_function_of_the_problem_id() -> None:
    """The seed is the first 8 bytes of sha256 of the id (ADR 0001), so a rebuild anywhere
    gives the same split, and another problem over the same table gets another split."""
    table = groupedTable([10] * 20)
    problem = Problem.build(groupedRow(), table)
    again = Problem.build(groupedRow(), table)
    other = Problem.build(groupedRow(source='other'), table)
    assert set(regimes(problem).stack()) == {'seen', 'held'}
    assert regimes(problem).equals(regimes(again))
    assert not regimes(problem)['rows'].equals(regimes(other)['rows'])
    assert not regimes(problem)['groups'].equals(regimes(other)['groups'])


SIZES = st.lists(st.integers(1, 8), min_size=3, max_size=40)
SOURCES = st.text(alphabet='abcxyz', min_size=1, max_size=8)


@given(sizes=SIZES, crossed=st.integers(0, 5), source=SOURCES)
def test_regime_rows_holds_out_a_tenth_and_every_group_keeps_a_seen_row(
    sizes: list[int], crossed: int, source: str
) -> None:
    """Regime `rows` predicts inside seen groups, so every group of every factor keeps a seen
    row and a single-row group keeps its row; it holds out the nearest whole number to 10% of
    the rows, fewer only when the groups leave no more, as with one factor and n − G < n/10."""
    table = groupedTable(sizes, crossed)
    problem = Problem.build(groupedRow(source, crossed=bool(crossed)), table)
    held = problem.table['rows'] == 'held'
    tenth = len(table) / 10
    for factor in problem.factors:
        seen = problem.table.loc[~held, factor]
        assert set(seen) == set(problem.table[factor])
    singletons = problem.table.groupby('g')['g'].transform('size') == 1
    assert not (held & singletons).any()
    assert held.sum() <= tenth + 0.5
    if not crossed:
        assert abs(held.sum() - tenth) <= 0.5 or held.sum() == len(table) - len(sizes)


@given(sizes=SIZES, source=SOURCES)
def test_regime_groups_holds_out_a_tenth_of_the_first_factors_groups_whole(
    sizes: list[int], source: str
) -> None:
    """Regime `groups` predicts new groups: the nearest whole number to 10% of the first
    factor's groups is held with all its rows, at least one group and at least two remaining
    (ADR 0001); a 3-group factor holds out one."""
    table = groupedTable(sizes)
    problem = Problem.build(groupedRow(source), table)
    held = problem.table['groups'] == 'held'
    heldGroups = set(problem.table.loc[held, 'g'])
    seenGroups = set(problem.table.loc[~held, 'g'])
    assert not heldGroups & seenGroups
    assert len(heldGroups) >= 1
    assert len(seenGroups) >= 2
    assert abs(len(heldGroups) - len(sizes) / 10) <= 0.5 or len(heldGroups) == 1


def test_a_first_factor_of_two_groups_has_no_groups_regime() -> None:
    """Holding one of two groups leaves one, so ADR 0001's rule cannot hold: the problem keeps
    the posterior track and regime `rows`, and has no `groups` column (ten registry rows)."""
    problem = Problem.build(groupedRow(), groupedTable([6, 6]))
    assert 'rows' in problem.table.columns
    assert 'groups' not in problem.table.columns


# ==============================================================================================
# scales
# ==============================================================================================


def momentsOf(values: list[float], seen: pd.Series) -> Scale:
    kept = np.asarray(values)[seen.to_numpy()]
    return Scale(mean=float(np.mean(kept)), sd=float(np.std(kept, ddof=1)))


def test_each_regime_scales_the_continuous_columns_by_the_rows_it_sees() -> None:
    """No held-out row leaks into a scaler (ADR 0001): `full` holds the table's moments and each
    regime its seen rows' (sample SD, as R's `scale`), for the continuous covariate `x` and the
    continuous response `y` only; the table itself stays in raw units."""
    problem = Problem.build(fixtureRow(), fixtureTable())
    everyRow = pd.Series([True] * 12)
    assert problem.scales == {
        'full': {'x': momentsOf(X, everyRow), 'y': momentsOf(Y, everyRow)},
        'rows': {
            'x': momentsOf(X, problem.table['rows'] == 'seen'),
            'y': momentsOf(Y, problem.table['rows'] == 'seen'),
        },
        'groups': {
            'x': momentsOf(X, problem.table['groups'] == 'seen'),
            'y': momentsOf(Y, problem.table['groups'] == 'seen'),
        },
    }
    assert problem.table['x'].tolist() == X
    assert problem.table['y'].tolist() == Y
    count = Problem.build(fixtureRow(response='n', response_type='count'), fixtureTable())
    assert set(count.scales['full']) == {'x'}


def test_a_level_present_only_in_held_rows_leaves_an_all_zero_column_in_that_regime() -> None:
    """The coding is the full table's (ADR 0001, amended 2026-10-09): `kind` gives each group
    its own level beside a shared reference, so the held group's level has no seen row, and
    its contrast column stays in the design, all zero over the seen rows, not dropped."""
    table = groupedTable([4, 4, 4])
    table['kind'] = pd.Categorical(
        ['base', 'k0', 'k0', 'k0', 'base', 'k1', 'k1', 'k1', 'base', 'k2', 'k2', 'k2'],
        categories=['base', 'k0', 'k1', 'k2'],
    )
    row = replace(groupedRow(), covariates=('x', 'kind'), types={'kind': 'categorical'})
    problem = Problem.build(row, table)
    seen = problem.table['groups'] == 'seen'
    [heldLevel] = set(table.loc[~seen, 'kind']) - {'base'}
    assert problem.design == ('Intercept', 'x', 'kind[k0]', 'kind[k1]', 'kind[k2]')
    assert problem.table.loc[seen, f'kind[{heldLevel}]'].eq(0).all()
    assert problem.table.loc[~seen, f'kind[{heldLevel}]'].eq(1).any()
