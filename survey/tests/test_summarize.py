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
FIT_AXES = (
    'sigma2_fixed', 'sigma2_random', 'sigma2_residual', 'sigma2_distribution', 'sd_eta',
    'r2_marginal', 'r2_conditional', 'q', 'sigma2', 'icc', 'icc_adjusted',
)  # fmt: skip
FLAT_AXES = ('n_obs', 'd_all', 'condition_all', 'K', *COLUMN_AXES)  # the axes both samples share
RESPONSE_AXES = (
    'response_K', 'response_skewness', 'response_excess_kurtosis', 'response_outlier_share',
    'response_zero_share', 'response_min_share', 'response_max_share', 'response_unique_share',
    'response_rare_level_share', 'response_max_abs_rho',
)  # fmt: skip


def test_quantiles_carry_every_axis_pooled_per_tier_and_without_agridat(merger):
    """Per-factor axes count once per grouping factor (region, herd, herd), dataset axes once
    per registry row; the shares, the K distribution over the documented models' categoricals
    and the implied column counts of a 9- and a 14-term model follow (#18)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    assert (quantiles['n_rows'], quantiles['n_objects'], quantiles['n_factor_rows']) == (2, 1, 3)
    axes = quantiles['axes']
    assert set(axes) == set(FACTOR_AXES) | set(ROW_AXES) | {'K'} | set(QUIRK_AXES) | set(FIT_AXES) | set(RESPONSE_AXES)  # fmt: skip
    for name, axis in axes.items():
        assert list(axis)[:3] == ['pooled', 'tiers', 'without_agridat']
        assert set(axis['pooled']) == set(QUANTILE_KEYS)
        if name in FIT_AXES:  # the scratch registry's fits.csv holds no row yet
            assert set(axis['tiers']) <= {'D'}
        else:
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
    released = QUIRK_AXES + FIT_AXES + RESPONSE_AXES
    assert tuple(axes)[-len(released) :] == released
    counts = {axis: axes[axis]['pooled']['n'] for axis in QUIRK_AXES}
    assert counts == {
        'skewness': 2, 'excess_kurtosis': 2, 'outlier_share': 2, 'zero_share': 3, 'min_share': 3,
        'max_share': 3, 'unique_share': 10, 'rare_level_share': 8, 'max_abs_rho': 5,
        'between_group_share': 7, 'group_level_r2': 2, 'absent_level_share': 12, 'size_rho': 7,
        'within_sd_cv': 7, 'empty_cell_share': 0, 'condition_doc': 2, 'condition_all': 2,
    }  # fmt: skip
    assert axes['between_group_share']['pooled']['min'] == -0.2986  # negatives kept


def test_response_statistics_count_once_per_registry_row(merger):
    """A response's statistics take axes of their own, beside the covariates' of the same name:
    model 1's weight and model 2's share of cases, both continuous, so neither has levels."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    axes = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())['axes']
    counts = {axis: axes[axis]['pooled']['n'] for axis in RESPONSE_AXES}
    assert counts == {
        'response_K': 0, 'response_skewness': 2, 'response_excess_kurtosis': 2,
        'response_outlier_share': 2, 'response_zero_share': 2, 'response_min_share': 2,
        'response_max_share': 2, 'response_unique_share': 2, 'response_rare_level_share': 0,
        'response_max_abs_rho': 2,
    }  # fmt: skip
    skewness = axes['response_skewness']['pooled']
    assert (skewness['min'], skewness['max']) == (0.5207, 0.6362)


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


def test_fit_statistics_count_once_per_registry_row_or_factor_and_status_is_a_share(merger):
    """The pilot's fits.csv, which the merge leaves as it is: 20 registry rows, 17 of them fitted
    with estimates (8 gaussian, with a residual) over 21 factors; the statuses share the 20 rows."""
    (merger.registry / 'fits.csv').write_bytes((FIXTURES / 'fits.csv').read_bytes())
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    counts = {axis: quantiles['axes'][axis]['pooled']['n'] for axis in FIT_AXES}
    assert counts == {
        'sigma2_fixed': 17, 'sigma2_random': 17, 'sigma2_residual': 8, 'sigma2_distribution': 17,
        'sd_eta': 17, 'r2_marginal': 17, 'r2_conditional': 17, 'q': 21, 'sigma2': 21, 'icc': 21,
        'icc_adjusted': 21,
    }  # fmt: skip
    assert quantiles['shares']['status'] == {'ok': 0.6, 'singular': 0.2, 'error': 0.1, 'warning': 0.05, 'no_formula': 0.05}  # fmt: skip


def copyFlatFiles(merger) -> None:
    """Three flat tables of eight columns and two named responses, as the flat pass wrote them;
    a merge leaves them."""
    for name in ('flat.csv', 'flat_columns.csv', 'flat_response_statistics.csv'):
        (merger.registry / name).write_bytes((FIXTURES / name).read_bytes())


def test_the_axes_both_samples_share_carry_a_flat_split_counted_once_per_its_key(merger):
    """The size and design axes count once per flat table (sparse.csv has no complete row, so no
    condition index), K once per categorical or ordered column (not the binary one), a column
    statistic once per column that defines it, a response axis once per named response that
    defines it (milk is ordinal, its rank correlation blank). Grouping factors, pairs and fits
    have no flat counterpart, and the flat type mix is a share of every flat column."""
    copyFlatFiles(merger)
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.registry / 'quantiles.yaml').read_text())
    axes = quantiles['axes']
    assert {name for name, axis in axes.items() if 'flat' in axis} == {*FLAT_AXES, *RESPONSE_AXES}
    counts = {axis: axes[axis]['flat']['n'] for axis in FLAT_AXES}
    assert counts == {
        'n_obs': 3, 'd_all': 3, 'condition_all': 2, 'K': 3, 'skewness': 4, 'excess_kurtosis': 4,
        'outlier_share': 4, 'zero_share': 4, 'min_share': 5, 'max_share': 5, 'unique_share': 8,
        'rare_level_share': 4, 'max_abs_rho': 5,
    }  # fmt: skip
    assert axes['n_obs']['flat'] == {'n': 3, 'min': 8, 'p5': 8, 'p10': 8, 'p50': 12, 'p90': 30, 'p95': 30, 'max': 30}  # fmt: skip
    assert axes['K']['flat'] == {'n': 3, 'min': 3, 'p5': 3, 'p10': 3, 'p50': 4, 'p90': 30, 'p95': 30, 'max': 30}  # fmt: skip
    assert axes['condition_all']['flat'] == {'n': 2, 'min': 1, 'p5': 1, 'p10': 1, 'p50': 2.5, 'p90': 2.5, 'p95': 2.5, 'max': 2.5}  # fmt: skip
    response_counts = {axis: axes[axis]['flat']['n'] for axis in RESPONSE_AXES}
    assert response_counts == {
        'response_K': 1, 'response_skewness': 1, 'response_excess_kurtosis': 1,
        'response_outlier_share': 1, 'response_zero_share': 1, 'response_min_share': 2,
        'response_max_share': 2, 'response_unique_share': 2, 'response_rare_level_share': 1,
        'response_max_abs_rho': 1,
    }  # fmt: skip
    assert axes['response_K']['flat'] == {'n': 1, 'min': 3, 'p5': 3, 'p10': 3, 'p50': 3, 'p90': 3, 'p95': 3, 'max': 3}  # fmt: skip
    assert quantiles['shares']['flat_column_type'] == {'continuous': 0.5, 'categorical': 0.25, 'binary': 0.125, 'ordered': 0.125}  # fmt: skip


def tableRows(text: str, *starts: str) -> list[list[str]]:
    """The cells of the first Markdown table at or after the last of `starts`, section headings
    or a table's header line found one after the other, one list per body row."""
    for start in starts:
        text = text[text.index(start) :]
    rows = []
    for line in text.splitlines():
        if line.startswith('|'):
            rows.append(line.strip('| ').split(' | '))
        elif rows:
            break
    return rows[2:]


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
    statistics = {
        '## Quirk statistics per column\n': COLUMN_AXES,
        '## Quirk statistics per column and grouping factor\n': COLUMN_FACTOR_AXES,
        '## Quirk statistics per factor pair\n': FACTOR_PAIR_AXES,
        '## Quirk statistics per response\n': RESPONSE_AXES,
    }
    for heading, axes in statistics.items():
        assert [row[0] for row in tableRows(summary, heading)] == list(axes)
    assert tableRows(summary, '## Design columns\n', '| statistic |') == [
        ['condition_doc', '2', '3.452', '3.452', '3.452', '6.5784', '6.5784', '6.5784', '6.5784'],
        ['condition_all', '2', '10.2274', '10.2274', '10.2274', '34.2099', '34.2099', '34.2099', '34.2099'],
    ]  # fmt: skip
    pairs = summary.split('## Quirk statistics per factor pair\n', 1)[1]
    assert '| pair relation | n | share |' in pairs and '| superior | n | share |' in pairs
    assert [row[0] for row in tableRows(summary, '## Fits of the documented models\n')] == list(
        FIT_AXES
    )
    assert '| status | n | share |' in summary.split('## Fits of the documented models\n', 1)[1]


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
    assert [row[0] for row in observations] == ['pooled', 'tier D', 'without agridat', 'flat']
    assert observations[0] == ['pooled', '2', '14', '14', '14', '14', '14', '14', '14', f'{max(practiceP90s("n_obs"))}']  # fmt: skip
    assert tableRows(summary, '| n_groups | n | min |')[0][-1] == f'{max(practiceP90s("n_groups_per_factor"))}'  # fmt: skip
    assert tableRows(summary, '| group_size_min | n | min |')[0][-1] == f'{min(practiceP90s("group_size_min"))}'  # fmt: skip
    assert tableRows(summary, '| d_doc | n | min |')[0][-1] == f'{max(practiceP90s("n_fixed_effects"))}'  # fmt: skip
    assert tableRows(summary, '| alpha | n | min |')[0][-1] == '–'
    assert 'Excluded: 1 objects' in summary and 'derived or duplicated table 1' in summary


def test_summary_axis_tables_end_with_a_flat_row_where_the_axis_has_one(merger):
    """The flat sample's quantiles follow `without agridat` in the tables of the axes both
    samples share, with no practice value; a grouping factor's axis has no flat row."""
    copyFlatFiles(merger)
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    summary = (merger.registry / 'SUMMARY.md').read_text()
    for axis in ('n_obs', 'd_all', 'K'):
        rows = tableRows(summary, f'| {axis} | n | min |')
        assert [row[0] for row in rows] == ['pooled', 'tier D', 'without agridat', 'flat']
    assert tableRows(summary, '| n_obs | n | min |')[-1] == ['flat', '3', '8', '8', '8', '12', '30', '30', '30']  # fmt: skip
    assert tableRows(summary, '| n_groups | n | min |')[-1][0] == 'without agridat'


def writeFlatBookkeeping(merger) -> None:
    """The flat pass's files in the survey: a frame of three read tables, two flagged, and one
    prescreened; two responses, one found not flat; three verdicts, one on a copy that has left
    the frame; the shares of the hand sample, the response check and its recheck."""
    screen = [
        ('plain.csv', 'read', 'no'), ('sparse.csv', 'read', 'yes'), ('stored.csv', 'read', 'yes'),
        ('labels.csv', 'prescreened', 'no'),
    ]  # fmt: skip
    screened = pd.DataFrame(screen, columns=['object', 'stratum', 'flagged'])
    writeCsv(screened, merger.survey / 'flat_screen.csv')
    responses = [('plain.csv', 'its help page'), ('labels.csv', 'NOT FLAT: names repeat')]
    writeCsv(pd.DataFrame(responses, columns=['object', 'evidence']), merger.survey / 'flat_responses.csv')  # fmt: skip
    verdicts = [('sparse.csv', 'flat'), ('stored.csv', 'wide'), ('folded.csv', 'wide')]
    writeCsv(pd.DataFrame(verdicts, columns=['object', 'verdict']), merger.survey / 'flat_verdicts.csv')  # fmt: skip
    agreement = pd.DataFrame([('all', '10', '0.9')], columns=['stratum', 'tables', 'stood'])
    writeCsv(agreement, merger.survey / 'flat_agreement.csv')
    responses = pd.DataFrame([('all', '5', '0.6')], columns=['stratum', 'tables', 'stood'])
    writeCsv(responses, merger.survey / 'flat_response_agreement.csv')
    recheck = pd.DataFrame([('all', '4', '0.75')], columns=['stratum', 'tables', 'stood'])
    writeCsv(recheck, merger.survey / 'flat_response_recheck_agreement.csv')


def test_summary_closes_with_the_flat_samples_corpus_type_mix_and_statistics(merger):
    """The flat sample's section reads how the sample came to be from the survey's
    bookkeeping at merge time, then shows its type mix and the flat quantiles of the condition
    index and the column statistics, whose tables above have no flat row."""
    copyFlatFiles(merger)
    writeFlatBookkeeping(merger)
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    section = (merger.registry / 'SUMMARY.md').read_text().split('## Flat sample\n', 1)[1]
    assert (
        '3 flat tables; per stratum read 2, prescreened 1; per tier R 2, D 1. The screen flagged'
        " 2 of the frame's 3 read tables for a second reading and the response reading found 1"
        ' not flat; verdicts wide 2, flat 1. The hand'
        ' sample of 10 tables stood at 0.9. 2 of the 3 tables name a response; the response check'
        ' of 5 tables stood at 0.6, its recheck of 4 `none` tables at 0.75.'
    ) in ' '.join(section.split())
    types = tableRows(section, '| column type | n | share |')
    assert {row[0]: row[1] for row in types} == {'continuous': '4', 'categorical': '2', 'binary': '1', 'ordered': '1'}  # fmt: skip
    statistics = tableRows(section, '| statistic |')
    assert [row[0] for row in statistics] == ['condition_all', *COLUMN_AXES]
    assert statistics[0] == ['condition_all', '2', '1', '1', '1', '2.5', '2.5', '2.5', '2.5']
