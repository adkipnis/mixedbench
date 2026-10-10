"""The summariser at its file seams: the measured registry in, `quantiles.yaml` and `SUMMARY.md`
out (#18), over the scratch registry of conftest."""

import re

import pytest
import yaml
from conftest import FIXTURES, mergeShard
from summarise import PRACTICE, PRACTICE_FAMILIES, TEMPLATE

QUANTILE_KEYS = ('n', 'min', 'p5', 'p10', 'p50', 'p90', 'p95', 'max')
FACTOR_AXES = ('n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max', 'singleton_share', 'cv', 'alpha')  # fmt: skip
ROW_AXES = ('n_obs', 'n_grouping_factors', 'd_doc', 'd_all')


def test_quantiles_carry_every_axis_pooled_per_tier_and_without_agridat(merger):
    """Per-factor axes count once per grouping factor (region, herd, herd), dataset axes once
    per registry row; the shares, the K distribution over the documented models' categoricals
    and the implied column counts of a 9- and a 14-term model follow (#18)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert (quantiles['n_rows'], quantiles['n_objects'], quantiles['n_factor_rows']) == (2, 1, 3)
    axes = quantiles['axes']
    assert set(axes) == set(FACTOR_AXES) | set(ROW_AXES) | {'K'}
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


def test_merge_rewrites_the_readme_counts_block_and_nothing_else(merger):
    """The README's counts block is the summary's Corpus paragraph verbatim, rewritten on every
    merge so that the README never goes stale; every byte around the block stays as it was."""
    readme = merger.survey / 'README.md'
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    expected = (
        '# pens\n\nA pitch.\n\n'
        '<!-- corpus: written by survey/merge.py from registry/SUMMARY.md -->\n'
        '**Corpus.** 2 registry rows over 1 datasets and 3 grouping\n'
        'factors; per tier D 2. Excluded: 0 objects (none).\n'
        '<!-- /corpus -->\n\n## Install\n'
    )
    assert readme.read_text() == expected
