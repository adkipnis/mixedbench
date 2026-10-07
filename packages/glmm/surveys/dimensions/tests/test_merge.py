"""The merge script at its file seams: shard in, canonical CSVs and refusals out (#17)."""

import csv
from pathlib import Path

import pandas as pd
import pytest
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
