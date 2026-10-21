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
QUIRK_AXES = (
    'skewness', 'excess_kurtosis', 'outlier_share', 'zero_share', 'min_share', 'max_share',
    'unique_share', 'rare_level_share', 'max_abs_rho', 'between_group_share', 'group_level_r2',
    'absent_level_share', 'size_rho', 'within_sd_cv', 'empty_cell_share', 'condition_doc',
    'condition_all',
)  # fmt: skip


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
    assert axes['d_doc']['pooled']['max'] == 5 and axes['d_all']['pooled']['max'] == 12
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
    (all ten have a unique share, only weight a skewness), a column and grouping factor, a
    crossed pair (the herds rows have none) and a registry row, so the condition numbers count
    two rows, not three grouping factors. The released keys and axes stay first (#101)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert list(quantiles) == ['n_rows', 'n_objects', 'n_factor_rows', 'axes', 'imbalance', 'shares', 'k_distribution', 'implied_columns']  # fmt: skip
    axes = quantiles['axes']
    assert tuple(axes)[-len(QUIRK_AXES) :] == QUIRK_AXES
    counts = {axis: axes[axis]['pooled']['n'] for axis in QUIRK_AXES}
    assert counts == {
        'skewness': 1, 'excess_kurtosis': 1, 'outlier_share': 1, 'zero_share': 2, 'min_share': 2,
        'max_share': 2, 'unique_share': 10, 'rare_level_share': 9, 'max_abs_rho': 4,
        'between_group_share': 6, 'group_level_r2': 2, 'absent_level_share': 13, 'size_rho': 6,
        'within_sd_cv': 6, 'empty_cell_share': 0, 'condition_doc': 2, 'condition_all': 2,
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


def test_summary_template_has_no_hand_typed_digits():
    assert not re.search(r'\d', re.sub(r'\bv1\b', '', TEMPLATE.read_text()))  # a stage name


def test_summary_tables_end_with_the_practice_p90_read_from_the_practice_file(merger):
    """One table per axis, rows pooled, per tier and without agridat; the pooled row's last
    column is the practice survey's p90, the maximum over the v1 families (the minimum for the
    smallest group size), taken from the snapshot `practice_quantiles.yaml` at merge time."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    summary = (merger.registry / 'SUMMARY.md').read_text()
    families = yaml.safe_load(PRACTICE.read_text())['families']
    p90 = lambda key: [families[f]['p90'][key] for f in PRACTICE_FAMILIES]
    tables = {m.group(1): m.group(0) for m in re.finditer(r'\| (\w+) \| n \| min \|.*?(?=\n\n)', summary, re.DOTALL)}  # fmt: skip
    assert set(tables) >= {'n_obs', 'n_groups', 'group_size_min', 'alpha', 'd_doc', 'K'}
    rows = lambda axis: [line.split(' | ') for line in tables[axis].splitlines()[2:]]
    assert [r[0] for r in rows('n_obs')] == ['| pooled', '| tier D', '| without agridat']
    assert rows('n_obs')[0] == ['| pooled', '2', '14', '14', '14', '14', '14', '14', '14', f'{max(p90("n_obs"))} |']  # fmt: skip
    assert rows('n_groups')[0][-1] == f'{max(p90("n_groups_per_factor"))} |'
    assert rows('group_size_min')[0][-1] == f'{min(p90("group_size_min"))} |'
    assert rows('d_doc')[0][-1] == f'{max(p90("n_fixed_effects"))} |'
    assert rows('alpha')[0][-1] == '– |'
    assert 'Excluded: 1 objects' in summary and 'derived or duplicated table 1' in summary
