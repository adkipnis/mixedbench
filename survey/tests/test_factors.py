"""The grouping-factor audit (#45): a factor the formula nests as `a:b` while the row names `b`
alone pools unrelated groups when `b`'s codes repeat across `a`; the audit regroups those rows
and reports every other formula factor the row does not name."""

import pandas as pd
from factors import regroup


def registryRows(rows: list[tuple[str, str]]) -> pd.DataFrame:
    """Registry rows (formula, grouping factors) with only the columns the audit reads; the
    object is the row's position."""
    frame = pd.DataFrame(rows, columns=['formula', 'grouping_factors'])
    frame.insert(0, 'source', 'lme4')
    frame.insert(1, 'object', [f'object{i}' for i in range(len(rows))])
    frame.insert(2, 'model_index', '1')
    return frame


def tableLookup(tables: dict[str, pd.DataFrame]):
    """A loader over in-memory tables by object; a row the audit should not load fails."""

    def load(row: pd.Series) -> pd.DataFrame:
        return tables[row['object']]

    return load


# casks 1–3 recur in every batch (lme4 Pastes); in `unique` each cask lies in one batch
REPEATED = pd.DataFrame({'batch': ['A', 'A', 'B', 'B'], 'cask': [1, 2, 1, 2], 'y': [1.0, 2.0, 3.0, 4.0]})  # fmt: skip
UNIQUE = pd.DataFrame({'batch': ['A', 'A', 'B', 'B'], 'cask': [1, 2, 3, 4], 'y': [1.0, 2.0, 3.0, 4.0]})  # fmt: skip


def test_a_nested_factor_whose_codes_repeat_is_regrouped_as_the_composite() -> None:
    """`b` alone pools the casks of every batch, so the row takes the formula's `a:b` in its
    place, whether the formula writes `a/b`, `a:b` or a slope over `a:b` (nlme Wafer)."""
    registry = registryRows(
        [
            ('y ~ (1|batch/cask)', 'batch;cask'),
            ('y ~ (1|batch) + (1|batch:cask)', 'batch;cask'),
            ('y ~ x + (x|batch) + (x|batch:cask)', 'batch;cask'),
        ]
    )
    load = tableLookup({f'object{i}': REPEATED for i in range(3)})
    grouping, report = regroup(registry, load)
    assert list(grouping) == ['batch;batch:cask'] * 3
    assert list(report['reason']) == ['codes repeat: regrouped'] * 3


def test_a_nested_factor_whose_codes_are_unique_is_only_reported() -> None:
    """Where each `b` lies in one `a`, `b` and `a:b` group the same rows: the row stands."""
    registry = registryRows([('y ~ (1|batch/cask)', 'batch;cask')])
    grouping, report = regroup(registry, tableLookup({'object0': UNIQUE}))
    assert list(grouping) == ['batch;cask']
    assert list(report['factor']) == ['batch:cask']
    assert list(report['reason']) == ['codes unique']


def test_each_level_of_a_deeper_nesting_is_regrouped_on_its_own() -> None:
    """`a/b/c` checks `a:b` and `a:b:c` separately (zuur_zim SeaGrassV3): sites unique across
    locations stand, transects repeating across sites take the composite; where both repeat,
    both are regrouped."""
    table = pd.DataFrame(
        {'loc': ['A', 'A', 'B', 'B'], 'site': [1, 2, 3, 4], 'tran': [1, 2, 1, 2], 'y': [1.0] * 4}
    )
    registry = registryRows([('y ~ (1|loc/site/tran)', 'loc;site;tran')] * 2)
    tables = {'object0': table, 'object1': table.assign(site=[1, 2, 1, 2])}
    grouping, report = regroup(registry, tableLookup(tables))
    assert list(grouping) == ['loc;site;loc:site:tran', 'loc;loc:site;loc:site:tran']
    assert list(report['reason']) == ['codes unique', 'codes repeat: regrouped', 'codes repeat: regrouped', 'codes repeat: regrouped']  # fmt: skip


def test_a_crossed_factor_beside_its_interaction_is_never_regrouped() -> None:
    """`(1|w) + (1|m) + (1|w:m)` (lme4 Machines) groups by `m` alone too, so the row's `m` is
    the formula's crossed factor and `w:m` a factor the row leaves out."""
    table = REPEATED.rename(columns={'batch': 'w', 'cask': 'm'})
    registry = registryRows([('y ~ (1|w) + (1|m) + (1|w:m)', 'w;m')])
    grouping, report = regroup(registry, tableLookup({'object0': table}))
    assert list(grouping) == ['w;m']
    assert list(report['reason']) == ['one row per level']


def test_every_other_factor_the_row_does_not_name_is_reported_with_its_reason() -> None:
    """What the row cannot hold is decided at admission: a factor that is no column (a
    phylogeny), an observation-level effect (lme4 grouseticks `INDEX`), a column the row leaves
    out, the inner part of a composite the row names (stan_arm srrs2's `county` beside
    `state:county`); a row whose formula names only its own factors loads no table."""
    table = REPEATED.assign(obs=[1, 2, 3, 4])
    registry = registryRows(
        [
            ('y ~ (1|batch) + (1|phylogeny)', 'batch'),
            ('y ~ (1|batch) + (1|obs)', 'batch'),
            ('y ~ (1|batch) + (1|cask)', 'batch'),
            ('y ~ (1|cask)', 'batch:cask'),
            ('y ~ (1|batch)', 'batch'),
        ]
    )
    load = tableLookup({f'object{i}': table for i in range(4)})
    grouping, report = regroup(registry, load)
    assert list(grouping) == ['batch'] * 3 + ['batch:cask', 'batch']
    assert list(report['factor']) == ['phylogeny', 'obs', 'cask', 'cask']
    assert list(report['reason']) == [
        'no such column',
        'one row per level',
        'not a grouping factor of the row',
        'inside a composite of the row',
    ]
