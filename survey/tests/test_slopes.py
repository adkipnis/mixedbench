"""The slope parser (#27): the random terms of `formula` as `random_slopes` terms where their
shape is plain, a report of every other shape for Alex to decide."""

import pandas as pd
from slopes import randomSlopes


def registryRows(rows: list[tuple[str, ...]]) -> pd.DataFrame:
    """Registry rows (formula, covariates, grouping factors, optionally types) as the dialect
    reads them, with only the columns the parser reads; the object is the row's position."""
    rows = [(*row, '')[:4] for row in rows]
    frame = pd.DataFrame(rows, columns=['formula', 'covariates', 'grouping_factors', 'types'])
    frame.insert(0, 'source', 'lme4')
    frame.insert(1, 'object', [f'object{i}' for i in range(len(rows))])
    frame.insert(2, 'model_index', '1')
    return frame


def test_plain_sums_of_covariates_over_one_factor_fill_correlated_terms() -> None:
    """The shapes most slopes take: one covariate, a sum with a leading `1 +`, a term per
    factor; an intercept-only model has no slope."""
    registry = registryRows(
        [
            ('Reaction ~ Days + (Days|Subject)', 'Days', 'Subject'),
            ('y ~ a + b + (1 + a + b | g)', 'a;b', 'g'),
            ('y ~ x + (1 + x | s) + (1 + x | i)', 'x', 's;i'),
            ('y ~ x + (1 | g)', 'x', 'g'),
        ]
    )
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['Days|Subject', 'a|g;b|g', 'x|s;x|i', '']
    assert report.empty


def test_a_double_bar_gives_uncorrelated_terms() -> None:
    """`||` drops the correlation with the intercept of `g` (lme4), so the term keeps both
    bars; a double bar on the intercept alone has no slope."""
    registry = registryRows(
        [
            ('y ~ floor + (1 + floor || county)', 'floor', 'county'),
            ('y ~ x + (1 || g)', 'x', 'g'),
        ]
    )
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['floor||county', '']
    assert report.empty


def test_a_nested_factor_expands_as_grouping_factors_does() -> None:
    """`a/b` is `a` and `a:b` (lme4), so a slope over it is a slope over each, the composite
    named as `grouping_factors` names it."""
    registry = registryRows([('y ~ x + (1 + x | Block/Variety)', 'x', 'Block;Block:Variety')])
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['x|Block;x|Block:Variety']
    assert report.empty


def test_every_other_shape_is_reported_with_its_row_and_formula_and_left_empty() -> None:
    """Alex decides what the parser cannot fill: a slope without the random intercept, an
    interaction, a nonlinear model's parameters or a transformed column, a factor the row does
    not name, brms's shared-correlation `|c|`; one such term empties the whole row."""
    registry = registryRows(
        [
            ('y ~ x + (1 | g) + (0 + x | g)', 'x', 'g'),
            ('y ~ a * b + (1 + a * b | g)', 'a;b', 'g'),
            ('conc ~ SSfpl(age, A, B, xmid, scal) + (A + B | Lot)', 'age', 'Lot'),
            ('y ~ x + I(x^2) + (x + I(x^2) | g)', 'x', 'g'),
            ('y ~ day + (day | Dog) + (1 | Dog:Side)', 'day', 'Dog;Side'),
            ('y ~ x + (x | Dog:Side)', 'x', 'Dog;Side'),
            ('se ~ time + (1 + time | c | id)', 'time', 'id'),
            ('y ~ a + b + (1 + a | s) + (1 + a:b | i)', 'a;b', 's;i'),
        ]
    )
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['', '', '', '', 'day|Dog', '', '', '']
    assert list(report['object']) == ['object0', 'object1', 'object2', 'object3', 'object5', 'object6', 'object7']  # fmt: skip
    assert list(report['formula']) == list(registry['formula'].drop(4))
    assert list(report['reason']) == [
        'no random intercept',
        'interaction in the slope',
        'A is not a covariate; B is not a covariate',
        'I(x^2) is not a covariate',
        'Dog:Side is not a grouping factor',
        'not a random term',
        'interaction in the slope',
    ]


def test_an_intercept_only_term_is_never_reported_and_a_function_is_no_interaction() -> None:
    """brms's `|p|` on the intercept alone carries no slope, so the row has nothing to decide
    (stan_arm sesame); a `*` inside a function's brackets is part of a transformed column, not
    an interaction (nlme Ovary)."""
    registry = registryRows(
        [
            ('y ~ x + (1 | p | g)', 'x', 'g'),
            ('y ~ sin(2*pi*Time) + (1 | Mare) + (sin(2*pi*Time) | Mare)', 'Time', 'Mare'),
        ]
    )
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['', '']
    assert list(report['reason']) == ['sin(2*pi*Time) is not a covariate']


def test_a_double_bar_on_a_categorical_covariate_is_reported() -> None:
    """lme4's `||` splits a factor's slope into its own correlated block of indicator columns,
    brms decorrelates every column: the glyph alone does not say which the source meant
    (timmer_2024_osf_15 and _16)."""
    registry = registryRows([('y ~ cue + (1 + cue || subject)', 'cue', 'subject', 'cue=categorical')])  # fmt: skip
    slopes, report = randomSlopes(registry)
    assert list(slopes) == ['']
    assert list(report['reason']) == ['double bar on categorical cue']


def test_the_report_carries_the_terms_the_parser_recognised() -> None:
    """Alex decides a reported row from the slopes the grammar can hold: a covariate's slope
    beside its transformed one, the main effects `a * b` expands to (R's formula semantics),
    but nothing from an interaction-only `a:b`, and no slope over a factor the row lacks."""
    registry = registryRows(
        [
            ('y ~ p + (p + I(p^2) | s)', 'p', 's'),
            ('y ~ m * t + (1 + t | P) + (1 + m * t | T)', 'm;t', 'P;T'),
            ('y ~ a + b + (1 + a:b | g)', 'a;b', 'g'),
            ('y ~ v + (v | W) + (v | W:S)', 'v', 'W;S'),
        ]
    )
    slopes, report = randomSlopes(registry)
    assert list(report['candidates']) == ['p|s', 't|P;m|T;t|T', '', 'v|W']
