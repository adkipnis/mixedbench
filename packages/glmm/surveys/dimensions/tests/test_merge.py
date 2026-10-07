"""The merge script at its file seams: shard in, canonical CSVs and refusals out (#17)."""

import csv
import re
from pathlib import Path

import pandas as pd
import pytest
import yaml
from merge import Merger, ShardRefused

FIXTURES = Path(__file__).parent / 'fixtures'
RENAMED_TYPES = 'area=categorical;farm=categorical;type=categorical;diet=categorical'


def mergeShard(merger: Merger, shard: Path) -> Merger:
    merger.load(shard)
    merger.validate()
    merger.append()
    merger.flush()
    return merger


def readRows(path: Path) -> list[dict]:
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def test_passing_registry_shard_merges_with_tier_and_reader_filled_in(merger):
    """The whole contract on one good shard: two documented models of the herds table land in
    registry.csv with the script columns the agent never types."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    rows = readRows(merger.root / 'registry.csv')
    assert [(r['source'], r['object'], r['model_index']) for r in rows] == [
        ('herds', 'herds.csv', '1'),
        ('herds', 'herds.csv', '2'),
    ]
    assert {r['tier'] for r in rows} == {'D'}
    assert {r['reader'] for r in rows} == {'pandas'}
    assert rows[0]['sources'] == 'herds:herds.csv'
    assert rows[1]['formula'] == 'cbind(cases, trials - cases) ~ breed + (1 | herd)'


def writeShard(path: Path, rows: list[dict]) -> Path:
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    return path


def refusal(merger: Merger, shard: Path) -> pd.DataFrame:
    with pytest.raises(ShardRefused) as info:
        mergeShard(merger, shard)
    return info.value.problems


@pytest.mark.parametrize(
    'edit, column, problem',
    [
        ({'domain': 'farming'}, 'domain', 'not allowed'),
        ({'covariates': 'breed;fed'}, 'covariates', 'no such column: fed'),
        ({'grouping_factors': 'region:bred'}, 'grouping_factors', 'no such column: bred'),
        ({'types': 'breed=factor'}, 'types', 'not a column type: factor'),
        ({'response': 'cases', 'response_type': 'binomial'}, 'trials', 'binomial names its trials'),
        ({'response_type': 'count'}, 'response_type', 'weight is not integer-valued'),
        ({'model_index': '4'}, 'model_index', 'at most 3 models per object'),
    ],
)
def test_a_reading_the_table_contradicts_is_refused_with_the_row_named(
    merger, edit, column, problem
):
    """Reading errors are caught mechanically: the shard is refused, the line and key of the
    offending row are printed, and nothing is written."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= edit
    shard = writeShard(merger.root / 'shards' / 'registry_bad.csv', rows)
    problems = refusal(merger, shard)
    assert list(problems['line']) == [2]
    assert problems.iloc[0]['key'].startswith('herds herds.csv')
    assert list(problems['column']) == [column]
    assert problems.iloc[0]['problem'] == problem
    assert not (merger.root / 'registry.csv').exists()


def test_a_one_level_grouping_factor_is_refused(merger):
    """A grouping factor needs at least two levels and one level with two or more rows; a
    constant column has one level, `id` has fourteen singleton levels."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0]['grouping_factors'] = 'id'
    rows[1]['grouping_factors'] = 'herd;feed'  # feed has three levels; herd is fine
    shard = writeShard(merger.root / 'shards' / 'registry_levels.csv', rows)
    problems = refusal(merger, shard)
    assert list(problems['problem']) == ['id has no level with two rows']


def test_excluded_shard_merges_with_its_tier_and_rivals_the_registry(merger):
    """An object is in the registry or in the exclusions, never both: the merge refuses the
    shard that would put it in the second file, naming the row."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    rows = readRows(merger.root / 'excluded.csv')
    assert [(r['source'], r['object'], r['tier']) for r in rows] == [('cattle', 'cattle.csv', 'R')]
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    both = readRows(FIXTURES / 'excluded_cattle.csv')
    both[0] |= {'source': 'herds', 'object': 'herds.csv'}
    problems = refusal(merger, writeShard(merger.root / 'shards' / 'excluded_both.csv', both))
    assert list(problems['key']) == ['herds herds.csv']
    assert problems.iloc[0]['problem'] == 'also in registry.csv'
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= {'source': 'cattle', 'object': 'cattle.csv', 'types': RENAMED_TYPES, 'response': 'kg', 'grouping_factors': 'area;farm', 'covariates': 'type;diet', 'ignore': 'row'}  # fmt: skip
    problems = refusal(merger, writeShard(merger.root / 'shards' / 'registry_both.csv', rows[:1]))
    assert list(problems['key']) == ['cattle cattle.csv 1']
    assert problems.iloc[0]['problem'] == 'also in excluded.csv'


def test_merging_the_same_shard_twice_changes_nothing(merger):
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    before = {p.name: p.read_bytes() for p in merger.root.glob('*.csv')}
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert merger.replaced == 2
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    after = {p.name: p.read_bytes() for p in merger.root.glob('*.csv')}
    assert after == before


def test_equal_row_count_and_column_cardinalities_flag_a_duplicate_candidate(merger):
    """The same table under two namings is flagged, not merged: an agent must confirm. The pair
    is written earliest tier first and the registry keeps both until then."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert not (merger.root / 'duplicates.csv').exists()
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    flagged = readRows(merger.root / 'duplicates.csv')
    assert [(r['source_a'], r['object_a'], r['source_b'], r['object_b'], r['verdict']) for r in flagged] == [
        ('cattle', 'cattle.csv', 'herds', 'herds.csv', 'flagged')
    ]  # fmt: skip
    assert len(readRows(merger.root / 'registry.csv')) == 3
    # a `different` verdict keeps both rows and the pair is not flagged again
    verdict = {'source_a': 'herds', 'object_a': 'herds.csv', 'source_b': 'cattle', 'object_b': 'cattle.csv', 'verdict': 'different', 'notes': 'other herds'}  # fmt: skip
    mergeShard(merger, writeShard(merger.root / 'shards' / 'duplicates_check.csv', [verdict]))
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    rows = readRows(merger.root / 'duplicates.csv')
    assert [(r['source_a'], r['verdict']) for r in rows] == [('cattle', 'different')]
    assert len(readRows(merger.root / 'registry.csv')) == 3


def test_a_confirmed_duplicate_collapses_into_the_earliest_tier_row_listing_both_sources(merger):
    """Duplicates must not weight the quantiles: the confirmed pair becomes one object, Tier R
    before Tier D, and re-merging the folded shard cannot resurrect it."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    verdict = {'source_a': 'cattle', 'object_a': 'cattle.csv', 'source_b': 'herds', 'object_b': 'herds.csv', 'verdict': 'same', 'notes': 'herds is the deposit cattle was built from'}  # fmt: skip
    mergeShard(merger, writeShard(merger.root / 'shards' / 'duplicates_check.csv', [verdict]))
    rows = readRows(merger.root / 'registry.csv')
    assert [(r['source'], r['model_index'], r['tier']) for r in rows] == [('cattle', '1', 'R')]
    assert rows[0]['sources'] == 'cattle:cattle.csv;herds:herds.csv'
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert [r['source'] for r in readRows(merger.root / 'registry.csv')] == ['cattle']
    assert len(readRows(merger.root / 'duplicates.csv')) == 1


def test_a_dropped_shard_moves_an_object_from_the_exclusions_to_the_registry(merger):
    """The rival rule leaves no way to re-file a misjudged object; a dropped shard empties
    both files of it, the re-filing shard then empties dropped.csv again. An object in neither
    file cannot be dropped."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    drop = {'source': 'cattle', 'object': 'cattle.csv', 'reason': 'farms are the grouping'}
    mergeShard(merger, writeShard(merger.root / 'shards' / 'dropped_cattle.csv', [drop]))
    assert readRows(merger.root / 'excluded.csv') == []
    assert [(r['object'], r['tier']) for r in readRows(merger.root / 'dropped.csv')] == [
        ('cattle.csv', 'R')
    ]
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    assert [r['source'] for r in readRows(merger.root / 'registry.csv')] == ['cattle']
    assert readRows(merger.root / 'dropped.csv') == []
    stray = {'source': 'herds', 'object': 'herds.csv', 'reason': 'never filed'}
    problems = refusal(merger, writeShard(merger.root / 'shards' / 'dropped_stray.csv', [stray]))
    assert list(problems['problem']) == ['not in registry.csv or excluded.csv']


def test_a_composite_grouping_factor_merges_and_gets_its_own_dimension_row(merger):
    """`region:breed` is no column of the table; the merge checks its parts, builds the
    combination and measures it like any factor (the pilot's split-plot whole plots, #20)."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0]['grouping_factors'] = 'region;region:breed'
    mergeShard(merger, writeShard(merger.root / 'shards' / 'registry_pairs.csv', rows[:1]))
    dimensions = readRows(merger.root / 'dimensions.csv')
    assert [(r['factor'], r['n_groups'], r['relation']) for r in dimensions] == [
        ('region', '3', 'nested'),
        ('region:breed', '12', 'nested'),
    ]


def test_every_merge_measures_the_registry_into_dimensions_and_columns(merger):
    """No measured number is typed: the merge loads every registry row's table and writes one
    dimension row per grouping factor and one column row per covariate column (#18). An
    excluded shard merged afterwards regenerates both files unchanged."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    dimensions = readRows(merger.root / 'dimensions.csv')
    assert [(r['model_index'], r['factor'], r['n_groups'], r['relation']) for r in dimensions] == [
        ('1', 'region', '3', 'nested'),
        ('1', 'herd', '5', 'nested'),
        ('2', 'herd', '5', 'single'),
    ]
    assert dimensions[0]['tier'] == 'D' and dimensions[0]['alpha'] == '65.0'
    columns = readRows(merger.root / 'columns.csv')
    assert [(r['model_index'], r['column'], r['type']) for r in columns][:5] == [
        ('1', 'breed', 'categorical'),
        ('1', 'feed', 'categorical'),
        ('1', 'parity', 'ordered'),  # declared in the shard: pyreadr drops R's ordering
        ('1', 'sick', 'binary'),
        ('2', 'region', 'categorical'),
    ]
    assert len(columns) == 10
    before = {p.name: p.read_bytes() for p in merger.root.glob('*.csv')}
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    after = {p.name: p.read_bytes() for p in merger.root.glob('*.csv')}
    assert after == before | {'excluded.csv': after['excluded.csv']}


QUANTILE_KEYS = ('n', 'min', 'p5', 'p10', 'p50', 'p90', 'p95', 'max')
FACTOR_AXES = ('n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90', 'group_size_max', 'singleton_share', 'cv', 'alpha')  # fmt: skip
ROW_AXES = ('n_obs', 'n_grouping_factors', 'd_doc', 'd_all')


def test_quantiles_carry_every_axis_pooled_per_tier_and_without_agridat(merger):
    """Per-factor axes count once per grouping factor (region, herd, herd), dataset axes once
    per registry row; the shares, the K distribution over the documented models' categoricals
    and the implied column counts of a 9- and a 14-term model follow (#18)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    quantiles = yaml.safe_load((merger.root / 'quantiles.yaml').read_text())
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
    from summarise import TEMPLATE

    assert not re.search(r'\d', re.sub(r'\bv1\b', '', TEMPLATE.read_text()))  # a stage name


def test_summary_tables_end_with_the_practice_p90_read_from_the_practice_file(merger):
    """One table per axis, rows pooled, per tier and without agridat; the pooled row's last
    column is the practice survey's p90, the maximum over the v1 families (the minimum for the
    smallest group size), taken from `../practice/quantiles.yaml` at merge time."""
    from summarise import PRACTICE, PRACTICE_FAMILIES

    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    summary = (merger.root / 'SUMMARY.md').read_text()
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
