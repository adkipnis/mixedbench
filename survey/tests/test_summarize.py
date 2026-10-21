"""The summarizer at its file seams: the measured registry in, `quantiles.yaml` and `SUMMARY.md`
out (#18), over the scratch registry of conftest."""

import re

import pandas as pd
import pytest
import yaml
from conftest import FIXTURES, mergeShard, readRows
from mixedbench.registry.row import writeCsv
from summarize import PRACTICE, PRACTICE_FAMILIES, TEMPLATE

QUANTILE_KEYS = ('n', 'min', 'p5', 'p10', 'p50', 'p90', 'p95', 'max')
FACTOR_AXES = ('n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max', 'singleton_share', 'cv', 'alpha')  # fmt: skip
ROW_AXES = ('n_obs', 'n_grouping_factors', 'd_doc', 'd_all')
COLUMN_AXES = (
    'skewness', 'excess_kurtosis', 'outlier_share', 'zero_share', 'min_share', 'max_share',
    'unique_share', 'rare_level_share', 'max_abs_rho',
)  # fmt: skip
COLUMN_FACTOR_AXES = ('between_group_share', 'group_level_r2', 'absent_level_share', 'size_rho', 'within_sd_cv')  # fmt: skip
FACTOR_PAIR_AXES = ('empty_cell_share',)
CONDITION_AXES = ('condition_doc', 'condition_all')
QUIRK_AXES = (*COLUMN_AXES, *COLUMN_FACTOR_AXES, *FACTOR_PAIR_AXES, *CONDITION_AXES)


def test_quantiles_carry_every_axis_pooled_per_tier_and_without_agridat(merger):
    """Per-factor axes count once per grouping factor (region, herd, herd), dataset axes once
    per registry row; the shares, the K distribution over the documented models' categoricals
    and the implied column counts of a 9- and a 14-term model follow (#18)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert (quantiles['n_rows'], quantiles['n_objects'], quantiles['n_factor_rows']) == (2, 1, 3)
    axes = quantiles['axes']
    assert set(axes) == set(FACTOR_AXES) | set(ROW_AXES) | {'K'} | set(QUIRK_AXES)
    for axis in axes.values():
        assert set(axis) == {'pooled', 'tiers', 'without_agridat'}
        assert set(axis['pooled']) == set(QUANTILE_KEYS)
        assert set(axis['tiers']) == {'D'}
    assert axes['n_groups']['pooled'] == {'n': 3, 'min': 3, 'p5': 3, 'p10': 3, 'p50': 5, 'p90': 5, 'p95': 5, 'max': 5}  # fmt: skip
    assert axes['n_grouping_factors']['pooled'] == {'n': 2, 'min': 1, 'p5': 1, 'p10': 1, 'p50': 2, 'p90': 2, 'p95': 2, 'max': 2}  # fmt: skip
    assert axes['alpha']['pooled']['min'] == pytest.approx(4.4118, abs=1e-3)
    assert axes['alpha']['tiers']['D']['max'] == 65.0
    assert axes['alpha']['without_agridat'] == axes['alpha']['pooled']
    assert axes['d_doc']['pooled']['max'] == 5 and axes['d_all']['pooled']['max'] == 10
    assert axes['K']['pooled'] == {'n': 3, 'min': 3, 'p5': 3, 'p10': 3, 'p50': 4, 'p90': 4, 'p95': 4, 'max': 4}  # fmt: skip
    assert quantiles['imbalance'] == {'balanced_share': 0.0}
    shares = quantiles['shares']
    assert shares['covariate_type'] == {'categorical': 1.0}
    assert shares['level'] == {'within': 0.667, 'group': 0.333}
    assert shares['relation'] == {'nested': 0.667, 'single': 0.333}
    assert shares['response_type'] == {'continuous': 0.5, 'binomial': 0.5}
    assert shares['reader'] == {'pandas': 1.0}
    assert shares['published_model'] == {'yes': 0.5, 'no': 0.5}
    assert quantiles['k_distribution'] == {3: 0.333, 4: 0.667}
    implied = quantiles['implied_columns']
    assert implied['categorical_share'] == 1.0
    assert implied['mean_columns_per_categorical'] == pytest.approx(2.667, abs=1e-3)
    assert implied['terms_9'] == pytest.approx(24.0, abs=1e-2)
    assert implied['terms_14'] == pytest.approx(37.33, abs=1e-2)


def test_quirk_statistics_follow_the_released_axes_counted_once_per_their_key(merger):
    """Each quirk statistic is pooled over the rows of its own file that define it: a column
    (all ten have a unique share, only weight and model 2's undeclared integer parity a
    skewness), a column and grouping factor, a crossed pair (the herds rows have none) and a
    registry row, so the condition numbers count two rows, not three grouping factors. The
    released keys and axes stay first (#101)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert list(quantiles) == ['n_rows', 'n_objects', 'n_factor_rows', 'axes', 'imbalance', 'shares', 'k_distribution', 'implied_columns']  # fmt: skip
    axes = quantiles['axes']
    assert tuple(axes)[-len(QUIRK_AXES) :] == QUIRK_AXES
    counts = {axis: axes[axis]['pooled']['n'] for axis in QUIRK_AXES}
    assert counts == {
        'skewness': 2, 'excess_kurtosis': 2, 'outlier_share': 2, 'zero_share': 3, 'min_share': 3,
        'max_share': 3, 'unique_share': 10, 'rare_level_share': 8, 'max_abs_rho': 5,
        'between_group_share': 7, 'group_level_r2': 2, 'absent_level_share': 12, 'size_rho': 7,
        'within_sd_cv': 7, 'empty_cell_share': 0, 'condition_doc': 2, 'condition_all': 2,
    }  # fmt: skip
    assert axes['between_group_share']['pooled']['min'] == -0.2986  # negatives kept


def test_factor_pairs_share_their_relation_and_the_side_of_their_superior(merger):
    """The herds table's first model with two others: region and herd listed inner factor first,
    and herd crossed with breed. Of the three pairs two are nested, the superior listed first in one and
    second in the other; only the crossed pair has empty cells, 7 of the 20 herd × breed (#101)."""
    first = readRows(FIXTURES / 'registry_herds.csv')[0]
    inverted = first | {'model_index': '2', 'grouping_factors': 'herd;region', 'formula': 'weight ~ breed + feed + (1 | herd) + (1 | region)'}  # fmt: skip
    crossed = first | {'model_index': '3', 'grouping_factors': 'herd;breed', 'covariates': 'feed', 'formula': 'weight ~ feed + (1 | herd) + (1 | breed)'}  # fmt: skip
    shard = merger.survey / 'shards' / 'registry_pairs.csv'
    writeCsv(pd.DataFrame([first, inverted, crossed]), shard)
    mergeShard(merger, shard)
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert quantiles['shares']['pair_relation'] == {'nested': 0.667, 'crossed': 0.333}
    assert quantiles['shares']['superior'] == {'factor_a': 0.5, 'factor_b': 0.5}
    pooled = quantiles['axes']['empty_cell_share']['pooled']
    assert (pooled['n'], pooled['min'], pooled['max']) == (1, 0.35, 0.35)


def tableRows(text: str, header: str) -> list[list[str]]:
    """The cells of the first Markdown table in the text whose header line starts with `header`,
    one list per body row."""
    table = text[text.index(header) :].split('\n\n', 1)[0]
    return [line.strip('| ').split(' | ') for line in table.splitlines()[2:]]


def practiceP90s(axis: str) -> list[int | float]:
    """The practice survey's p90 of an axis, one per v1 family."""
    families = yaml.safe_load(PRACTICE.read_text())['families']
    return [families[f]['p90'][axis] for f in PRACTICE_FAMILIES]


def test_summary_shows_one_pooled_table_per_measured_file(merger):
    """Each measured file's quirk statistics read as one compact table, a statistic per row and
    its pooled quantiles as columns; the condition numbers join the design columns, the pairs'
    shares their statistic (#101)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    summary = (merger.registry / 'SUMMARY.md').read_text()
    columns = summary.split('## Quirk statistics per column\n', 1)[1]
    assert [row[0] for row in tableRows(columns, '| statistic |')] == list(COLUMN_AXES)
    columnFactors = summary.split('## Quirk statistics per column and grouping factor\n', 1)[1]
    assert [row[0] for row in tableRows(columnFactors, '| statistic |')] == list(COLUMN_FACTOR_AXES)
    pairs = summary.split('## Quirk statistics per factor pair\n', 1)[1]
    assert [row[0] for row in tableRows(pairs, '| statistic |')] == list(FACTOR_PAIR_AXES)
    design = summary.split('## Design columns\n', 1)[1]
    assert tableRows(design, '| statistic |') == [
        ['condition_doc', '2', '3.452', '3.452', '3.452', '6.5784', '6.5784', '6.5784', '6.5784'],
        ['condition_all', '2', '10.2274', '10.2274', '10.2274', '34.2099', '34.2099', '34.2099', '34.2099'],
    ]  # fmt: skip
    assert '| pair relation | n | share |' in pairs and '| superior | n | share |' in pairs


def test_summary_template_has_no_hand_typed_digits():
    assert not re.search(r'\d', re.sub(r'\bv1\b', '', TEMPLATE.read_text()))  # a stage name


def test_summary_tables_end_with_the_practice_p90_read_from_the_practice_file(merger):
    """One table per axis, rows pooled, per tier and without agridat; the pooled row's last
    column is the practice survey's p90, the maximum over the v1 families (the minimum for the
    smallest group size), taken from the snapshot `practice_quantiles.yaml` at merge time."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    summary = (merger.registry / 'SUMMARY.md').read_text()
    assert '| K | n | min |' in summary
    observations = tableRows(summary, '| n_obs | n | min |')
    assert [row[0] for row in observations] == ['pooled', 'tier D', 'without agridat']
    assert observations[0] == ['pooled', '2', '14', '14', '14', '14', '14', '14', '14', f'{max(practiceP90s("n_obs"))}']  # fmt: skip
    assert tableRows(summary, '| n_groups | n | min |')[0][-1] == f'{max(practiceP90s("n_groups_per_factor"))}'  # fmt: skip
    assert tableRows(summary, '| group_size_min | n | min |')[0][-1] == f'{min(practiceP90s("group_size_min"))}'  # fmt: skip
    assert tableRows(summary, '| d_doc | n | min |')[0][-1] == f'{max(practiceP90s("n_fixed_effects"))}'  # fmt: skip
    assert tableRows(summary, '| alpha | n | min |')[0][-1] == '–'
    assert 'Excluded: 1 objects' in summary and 'derived or duplicated table 1' in summary
