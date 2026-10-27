"""The merge script at its file seams: shard in, canonical CSVs and refusals out (#17)."""

import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml
from conftest import FIXTURES, mergeShard, readRows
from merge import Merger, ShardRefused
from mixedbench.registry.row import readCsv, writeCsv
from sources import readFrame

RENAMED_TYPES = 'area=categorical;farm=categorical;type=categorical;diet=categorical'
SURVEY = Path(__file__).resolve().parents[1]
MEASURED = ('dimensions.csv', 'columns.csv', 'column_factors.csv', 'factor_pairs.csv', 'responses.csv')  # fmt: skip


def test_passing_registry_shard_merges_with_tier_and_reader_filled_in(merger):
    """The whole contract on one good shard: two documented models of the herds table land in
    registry.csv with the script columns the agent never types."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    rows = readRows(merger.registry / 'registry.csv')
    assert [(r['source'], r['object'], r['model_index']) for r in rows] == [
        ('herds', 'herds.csv', '1'),
        ('herds', 'herds.csv', '2'),
    ]
    assert {r['tier'] for r in rows} == {'D'}
    assert {r['reader'] for r in rows} == {'pandas'}
    assert rows[0]['sources'] == 'herds:herds.csv'
    assert rows[1]['formula'] == 'cbind(cases, trials - cases) ~ breed + (1 | herd)'
    assert {r['license'] for r in rows} == {'CC0-1.0'}  # sources.yaml: `CC0 1.0 Universal`
    columns = list(rows[0])
    assert columns[columns.index('trials') + 1] == 'family'
    assert columns[columns.index('formula') + 1] == 'documented_prior'
    assert columns[columns.index('reader') + 1] == 'license'


def writeShard(path: Path, rows: list[dict]) -> Path:
    writeCsv(pd.DataFrame(rows), path)
    return path


def test_a_cran_sources_license_is_read_from_its_description(merger):
    """CRAN entries of sources.yaml carry no `license:` key: the merge reads the package's own
    DESCRIPTION through the loader and normalizes it (ADR 0003)."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= {'source': 'pens', 'object': 'herds'}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'registry_pens.csv', rows[:1]))
    merged = readRows(merger.registry / 'registry.csv')
    assert [(r['source'], r['license']) for r in merged] == [('pens', 'GPL-2.0-or-later')]


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
        ({'covariates': 'breed;herd'}, 'grouping_factors', 'herd is also a covariate'),
        ({'family': 'poisson'}, 'family', 'not a family: poisson'),  # the rule is the empty cell
        ({'verified': 'yes'}, 'verified', 'not a verification: yes'),
        ({'verified': ''}, 'verified', 'not a verification: '),
        ({'random_slopes': 'breed'}, 'random_slopes', 'not a slope term: breed'),
        ({'random_slopes': 'weight|herd'}, 'random_slopes', 'weight is not a covariate'),
        ({'random_slopes': 'breed||farm'}, 'random_slopes', 'farm is not a grouping factor'),
        ({'interactions': 'breed:parity'}, 'interactions', 'parity is not a covariate'),
        (
            {'documented_prior': 'sd ~ student_t(3, 0, 2.5)', 'published_model': 'no'},
            'documented_prior',
            'only on a published model',
        ),
    ],
)
def test_a_reading_the_table_contradicts_is_refused_with_the_row_named(
    merger, edit, column, problem
):
    """Reading errors are caught mechanically: the shard is refused, the line and key of the
    offending row are printed, and nothing is written."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= edit
    shard = writeShard(merger.survey / 'shards' / 'registry_bad.csv', rows)
    problems = refusal(merger, shard)
    assert list(problems['line']) == [2]
    assert problems.iloc[0]['key'].startswith('herds herds.csv')
    assert list(problems['column']) == [column]
    assert problems.iloc[0]['problem'] == problem
    assert readRows(merger.registry / 'registry.csv') == []


def test_slope_terms_on_a_covariate_over_a_grouping_factor_merge(merger):
    """The gate refuses only what ADR 0001 forbids: a correlated and an uncorrelated slope on
    the row's own covariates and factors pass and land as written."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= {'random_slopes': 'breed|herd;feed||region'}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'registry_slopes.csv', rows))
    merged = readRows(merger.registry / 'registry.csv')
    assert [r['random_slopes'] for r in merged] == ['breed|herd;feed||region', '']


def test_a_shard_with_another_header_is_refused_naming_each_column(merger):
    """An agent's misspelt column is reported like any other problem, on the header's line 1,
    before any check reads the misspelt column."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    for row in rows:
        row['domains'] = row.pop('domain')
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'registry_typo.csv', rows))
    assert problems[['line', 'column', 'problem']].values.tolist() == [
        [1, 'domain', 'missing'],
        [1, 'domains', 'unknown'],
    ]


def withLicenseKey(merger: Merger, label: str, license: str | None) -> Merger:
    """The scratch merger over a sources.yaml whose `label` has another `license:` key, or none."""
    path = merger.registry / 'sources.yaml'
    sources = yaml.safe_load(path.read_text())
    entries = {label: entry for tier in sources['tiers'].values() for label, entry in tier.items()}
    entries[label].pop('license', None)
    if license is not None:
        entries[label]['license'] = license
    path.write_text(yaml.safe_dump(sources, sort_keys=False))
    return Merger(merger.registry, merger.survey, loader=merger.loader)


@pytest.mark.parametrize(
    'license, problem',
    [
        ('Creative Commons Zero', 'not in the license lookup'),
        (None, 'no license: key in sources.yaml'),  # an absent key means nobody has looked
    ],
)
def test_a_license_the_lookup_cannot_classify_refuses_the_merge(merger, license, problem):
    """A new spelling is classified on sight, never silently made `other`: the merge names the
    source and the string and writes nothing."""
    merger = withLicenseKey(merger, 'herds', license)
    problems = refusal(merger, FIXTURES / 'registry_herds.csv')
    assert list(problems['key']) == ['herds']
    assert list(problems['value']) == [license or '']
    assert list(problems['problem']) == [problem]
    assert readRows(merger.registry / 'registry.csv') == []


def test_a_one_level_grouping_factor_is_refused(merger):
    """A grouping factor needs at least two levels and one level with two or more rows; a
    constant column has one level, `id` has fourteen singleton levels."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0]['grouping_factors'] = 'id'
    rows[1]['grouping_factors'] = 'herd;feed'  # feed has three levels; herd is fine
    shard = writeShard(merger.survey / 'shards' / 'registry_levels.csv', rows)
    problems = refusal(merger, shard)
    assert list(problems['problem']) == ['id has no level with two rows']


def test_excluded_shard_merges_with_its_tier_and_rivals_the_registry(merger):
    """An object is in the registry or in the exclusions, never both: the merge refuses the
    shard that would put it in the second file, naming the row."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    rows = readRows(merger.registry / 'excluded.csv')
    assert [(r['source'], r['object'], r['tier']) for r in rows] == [('cattle', 'cattle.csv', 'R')]
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    both = readRows(FIXTURES / 'excluded_cattle.csv')
    both[0] |= {'source': 'herds', 'object': 'herds.csv'}
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'excluded_both.csv', both))
    assert list(problems['key']) == ['herds herds.csv']
    assert problems.iloc[0]['problem'] == 'also in registry.csv'
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0] |= {'source': 'cattle', 'object': 'cattle.csv', 'types': RENAMED_TYPES, 'response': 'kg', 'grouping_factors': 'area;farm', 'covariates': 'type;diet', 'ignore': 'row'}  # fmt: skip
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'registry_both.csv', rows[:1]))
    assert list(problems['key']) == ['cattle cattle.csv 1']
    assert problems.iloc[0]['problem'] == 'also in excluded.csv'


def test_merging_the_same_shard_twice_changes_nothing(merger):
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    before = {p.name: p.read_bytes() for p in merger.registry.glob('*.csv')}
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert merger.replaced == 2
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    after = {p.name: p.read_bytes() for p in merger.registry.glob('*.csv')}
    assert after == before


def test_a_replaced_row_keeps_its_place(merger, tmp_path):
    """A shard re-merging a row replaces it where it stands, so a correction shows in the
    registry's diff as that row alone and the registry order a seeded draw reads holds."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    first = readRows(FIXTURES / 'registry_herds.csv')[0]
    shard = writeShard(tmp_path / 'registry_herds_note.csv', [first | {'notes': 're-read'}])
    mergeShard(merger, shard)
    rows = readRows(merger.registry / 'registry.csv')
    assert [(r['model_index'], r['notes']) for r in rows][0] == ('1', 're-read')
    assert [r['model_index'] for r in rows] == ['1', '2']


def test_an_empty_shard_migrates_a_registry_of_the_old_shape(merger):
    """The one-time migration of #7 is a merge of a shard with the new header and no rows: the
    old rows gain `family` and `documented_prior` empty and `license` filled, in the new column
    order; merging it again changes nothing."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    path = merger.registry / 'registry.csv'
    current = readCsv(path)
    old = current.drop(columns=['family', 'documented_prior', 'license'])
    writeCsv(old, path)
    header = ','.join(readRows(FIXTURES / 'registry_herds.csv')[0])
    shard = merger.survey / 'shards' / 'registry_schema.csv'
    shard.write_text(header + '\n')
    mergeShard(merger, shard)
    migrated = path.read_bytes()
    assert readCsv(path).equals(current)
    mergeShard(merger, shard)
    assert path.read_bytes() == migrated


def test_equal_row_count_and_column_cardinalities_flag_a_duplicate_candidate(merger):
    """The same table under two namings is flagged, not merged: an agent must confirm. The pair
    is written earliest tier first and the registry keeps both until then."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert not (merger.survey / 'duplicates.csv').exists()
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    flagged = readRows(merger.survey / 'duplicates.csv')
    assert [(r['source_a'], r['object_a'], r['source_b'], r['object_b'], r['verdict']) for r in flagged] == [
        ('cattle', 'cattle.csv', 'herds', 'herds.csv', 'flagged')
    ]  # fmt: skip
    assert len(readRows(merger.registry / 'registry.csv')) == 3
    # a `different` verdict keeps both rows and the pair is not flagged again
    verdict = {'source_a': 'herds', 'object_a': 'herds.csv', 'source_b': 'cattle', 'object_b': 'cattle.csv', 'verdict': 'different', 'notes': 'other herds'}  # fmt: skip
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'duplicates_check.csv', [verdict]))
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    rows = readRows(merger.survey / 'duplicates.csv')
    assert [(r['source_a'], r['verdict']) for r in rows] == [('cattle', 'different')]
    assert len(readRows(merger.registry / 'registry.csv')) == 3


def test_a_confirmed_duplicate_collapses_into_the_earliest_tier_row_listing_both_sources(merger):
    """Duplicates must not weight the quantiles: the confirmed pair becomes one object, Tier R
    before Tier D, and re-merging the folded shard cannot resurrect it."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    verdict = {'source_a': 'cattle', 'object_a': 'cattle.csv', 'source_b': 'herds', 'object_b': 'herds.csv', 'verdict': 'same', 'notes': 'herds is the deposit cattle was built from'}  # fmt: skip
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'duplicates_check.csv', [verdict]))
    rows = readRows(merger.registry / 'registry.csv')
    assert [(r['source'], r['model_index'], r['tier']) for r in rows] == [('cattle', '1', 'R')]
    assert rows[0]['sources'] == 'cattle:cattle.csv;herds:herds.csv'
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')  # a merge with the folded row absent
    rows = readRows(merger.registry / 'registry.csv')
    assert [r['source'] for r in rows] == ['cattle']
    assert rows[0]['sources'] == 'cattle:cattle.csv;herds:herds.csv'
    assert len(readRows(merger.survey / 'duplicates.csv')) == 1


def test_within_a_tier_the_frame_order_of_sources_yaml_decides_which_duplicate_survives(tmp_path):
    """nlme is listed before MEMSS and mlmRev, so a re-export folds into the nlme row; an
    alphabetical tie-break would keep MEMSS and discard the spot-checked row."""
    entries = {label: {'kind': 'cran', 'pin': '1.0'} for label in ['nlme', 'MEMSS', 'agridat']}
    sources = {'seed': 0, 'tiers': {'R': entries, 'D': {'deposit': {'kind': 'cran', 'pin': '1.0'}}}}
    (tmp_path / 'sources.yaml').write_text(yaml.safe_dump(sources, sort_keys=False))
    frame = readFrame(tmp_path)
    keys = [('deposit', 'x'), ('agridat', 'x'), ('MEMSS', 'x'), ('nlme', 'x')]
    assert sorted(keys, key=frame.rank) == [
        ('nlme', 'x'),
        ('MEMSS', 'x'),
        ('agridat', 'x'),
        ('deposit', 'x'),
    ]


def test_a_dropped_shard_moves_an_object_from_the_exclusions_to_the_registry(merger):
    """The rival rule leaves no way to re-file a misjudged object; a dropped shard empties
    both files of it, the re-filing shard then empties dropped.csv again. An object in neither
    file cannot be dropped."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    drop = {'source': 'cattle', 'object': 'cattle.csv', 'reason': 'farms are the grouping'}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'dropped_cattle.csv', [drop]))
    assert readRows(merger.registry / 'excluded.csv') == []
    assert [(r['object'], r['tier']) for r in readRows(merger.survey / 'dropped.csv')] == [
        ('cattle.csv', 'R')
    ]
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')
    assert [r['source'] for r in readRows(merger.registry / 'registry.csv')] == ['cattle']
    assert readRows(merger.survey / 'dropped.csv') == []
    stray = {'source': 'herds', 'object': 'herds.csv', 'reason': 'never filed'}
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'dropped_stray.csv', [stray]))
    assert list(problems['problem']) == ['not in registry.csv or excluded.csv']


def test_a_dropped_object_the_census_no_longer_enumerates_leaves_every_file(merger):
    """A re-pull can stop enumerating an excluded object (base R's beaver1 once beavers.R
    reads as one object, #14); nothing can re-file it, so dropping it deletes its key."""
    gone = {'source': 'cattle', 'object': 'cattle.old', 'reason': 'no grouping structure', 'detail': ''}  # fmt: skip
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'excluded_gone.csv', [gone]))
    drop = {'source': 'cattle', 'object': 'cattle.old', 'reason': 'no longer a census object'}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'dropped_gone.csv', [drop]))
    assert readRows(merger.registry / 'excluded.csv') == []
    assert readRows(merger.survey / 'dropped.csv') == []


def test_the_census_lands_in_the_registry_and_the_bookkeeping_in_the_survey(splitMerger):
    """registry/ is what the package ships, so a merge writes only the census there; the
    duplicate flags and the dropped list stay with the survey's working files."""
    merger = splitMerger
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    drop = {'source': 'cattle', 'object': 'cattle.csv', 'reason': 'farms are the grouping'}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'dropped_cattle.csv', [drop]))
    mergeShard(merger, FIXTURES / 'registry_cattle.csv')  # flags the pair with herds
    registryFiles = sorted(p.name for p in merger.registry.iterdir() if p.is_file())
    surveyFiles = sorted(p.name for p in merger.survey.iterdir() if p.is_file())
    assert registryFiles == ['SUMMARY.md', 'column_factors.csv', 'columns.csv', 'dimensions.csv', 'excluded.csv', 'factor_pairs.csv', 'fits.csv', 'flat.csv', 'flat_columns.csv', 'manifest.csv', 'quantiles.yaml', 'registry.csv', 'responses.csv', 'sources.yaml']  # fmt: skip
    assert surveyFiles == ['dropped.csv', 'duplicates.csv', 'flat_agreement.csv', 'flat_response_agreement.csv', 'flat_response_recheck_agreement.csv', 'flat_responses.csv', 'flat_screen.csv', 'flat_verdicts.csv']  # fmt: skip


def test_a_composite_grouping_factor_merges_and_gets_its_own_dimension_row(merger):
    """`region:breed` is no column of the table; the merge checks its parts, builds the
    combination and measures it like any factor (the pilot's split-plot whole plots, #20)."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0]['grouping_factors'] = 'region;region:breed'
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'registry_pairs.csv', rows[:1]))
    dimensions = readRows(merger.registry / 'dimensions.csv')
    assert [(r['factor'], r['n_groups'], r['relation']) for r in dimensions] == [
        ('region', '3', 'nested'),
        ('region:breed', '12', 'nested'),
    ]


def test_every_merge_measures_the_registry_into_dimensions_and_columns(merger):
    """No measured number is typed: the merge loads every registry row's table and writes one
    dimension row per grouping factor and one column row per covariate column (#18). An
    excluded shard merged afterwards regenerates both files unchanged."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    dimensions = readRows(merger.registry / 'dimensions.csv')
    assert [(r['model_index'], r['factor'], r['n_groups'], r['relation']) for r in dimensions] == [
        ('1', 'region', '3', 'nested'),
        ('1', 'herd', '5', 'nested'),
        ('2', 'herd', '5', 'single'),
    ]
    assert dimensions[0]['tier'] == 'D' and dimensions[0]['alpha'] == '65.0'
    columns = readRows(merger.registry / 'columns.csv')
    assert [(r['model_index'], r['column'], r['type']) for r in columns][:5] == [
        ('1', 'breed', 'categorical'),
        ('1', 'feed', 'categorical'),
        ('1', 'parity', 'ordered'),  # declared in the shard: pyreadr drops R's ordering
        ('1', 'sick', 'binary'),
        ('2', 'region', 'categorical'),
    ]
    assert len(columns) == 10
    before = {p.name: p.read_bytes() for p in merger.registry.glob('*.csv')}
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    after = {p.name: p.read_bytes() for p in merger.registry.glob('*.csv')}
    assert after == before | {'excluded.csv': after['excluded.csv']}


def test_every_merge_writes_the_measured_headers_and_a_left_out_statistic_as_blank(merger):
    """column_factors.csv and factor_pairs.csv carry their released headers, and dimensions.csv
    the two condition numbers after d_all. The nested region and herd pair has no empty-cell
    share, written as a blank cell (#99, #100)."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    column_factors = readRows(merger.registry / 'column_factors.csv')
    assert list(column_factors[0]) == [
        'source', 'object', 'model_index', 'tier', 'column', 'factor', 'between_group_share',
        'group_level_r2', 'absent_level_share', 'size_rho', 'within_sd_cv',
    ]  # fmt: skip
    pairs = readRows(merger.registry / 'factor_pairs.csv')
    assert list(pairs[0]) == [
        'source', 'object', 'model_index', 'tier', 'factor_a', 'factor_b', 'relation', 'superior',
        'empty_cell_share',
    ]  # fmt: skip
    assert pairs[0]['empty_cell_share'] == ''
    columns = list(readRows(merger.registry / 'dimensions.csv')[0])
    after = columns.index('d_all') + 1
    assert columns[after : after + 2] == ['condition_doc', 'condition_all']


def test_a_merge_leaves_fits_csv_as_the_last_fits_pass_wrote_it(merger):
    """The fits run on a cluster, apart from the merge (ADR 0006)."""
    fits = (FIXTURES / 'fits.csv').read_bytes()
    (merger.registry / 'fits.csv').write_bytes(fits)
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    assert (merger.registry / 'fits.csv').read_bytes() == fits


def test_a_merge_leaves_the_flat_files_as_the_last_flat_pass_wrote_them(merger):
    """The flat pass loads a thousand tables and refuses while a flagged one has no verdict,
    so a shard merged during the second reading neither reruns it nor fails (#115)."""
    written = {}
    for name in ('flat.csv', 'flat_columns.csv'):
        written[name] = (FIXTURES / name).read_bytes()
        (merger.registry / name).write_bytes(written[name])
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    for name, text in written.items():
        assert (merger.registry / name).read_bytes() == text


def test_every_registry_row_has_one_measured_response(merger):
    """responses.csv is keyed like dimensions.csv, one row per registry row and its response."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    responses = readRows(merger.registry / 'responses.csv')
    keys = [
        (r['source'], r['object'], r['model_index'], r['tier'], r['response']) for r in responses
    ]
    assert keys == [
        ('herds', 'herds.csv', '1', 'D', 'weight'),
        ('herds', 'herds.csv', '2', 'D', 'cases'),
    ]


def test_the_measure_script_writes_what_the_merge_writes(merger):
    """`measure.py` reruns the merge's measure pass without a shard to merge, so a changed
    statistic reaches the whole registry in one run (#98). It loads from the cache the merge
    filled, so the run is offline."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    merged = {name: (merger.registry / name).read_bytes() for name in MEASURED}
    for name in MEASURED:
        (merger.registry / name).unlink()
    command = [sys.executable, SURVEY / 'measure.py', '--registry', merger.registry, '--survey', merger.survey]  # fmt: skip
    subprocess.run(command, check=True)
    assert {name: (merger.registry / name).read_bytes() for name in MEASURED} == merged


def test_every_merge_names_each_registry_objects_file_in_the_manifest(merger):
    """The lean fetch (#4) loads an object from the file the manifest names, checked against
    its sha256: one row per registry object, however many models it has, taken from the
    whole source in the survey's cache."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    herds = (FIXTURES / 'herds.csv').read_text().encode()  # as conftest zips it
    sha256 = hashlib.sha256(herds).hexdigest()
    rows = readRows(merger.registry / 'manifest.csv')
    assert rows == [
        {'source': 'herds', 'object': 'herds.csv', 'file': 'herds.csv', 'sha256': sha256, 'size': str(len(herds))}
    ]  # fmt: skip


VERDICT = {'source': 'cattle', 'object': 'cattle.csv', 'verdict': 'wide', 'evidence': 'calvings as columns'}  # fmt: skip


def test_a_verdict_shard_merges_into_the_survey_with_its_tier_filled_in(splitMerger):
    """The second reading's verdicts are survey bookkeeping, beside dropped.csv; a verdict
    decides its flat table and moves the object out of no file."""
    merger = splitMerger
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'flat_second.csv', [VERDICT]))
    assert readRows(merger.survey / 'flat_verdicts.csv') == [VERDICT | {'tier': 'R'}]
    assert [r['object'] for r in readRows(merger.registry / 'excluded.csv')] == ['cattle.csv']


@pytest.mark.parametrize(
    'edit, column, problem',
    [
        ({'verdict': 'grouped'}, 'verdict', 'not allowed'),
        ({'evidence': ''}, 'evidence', 'required'),
        ({'object': 'cattle.old'}, 'object', 'not in registry.csv or excluded.csv'),
    ],
    ids=['a-verdict-outside-the-glossary', 'no-evidence', 'an-object-the-census-lacks'],
)
def test_a_verdict_outside_the_vocabulary_or_on_an_unknown_object_is_refused_naming_the_row(
    merger, edit, column, problem
):
    """Checked as a dropped shard is: the glossary's three verdicts, a line of evidence each,
    and an object the census holds."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    verdict = VERDICT | edit
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'flat_bad.csv', [verdict]))
    assert problems[['line', 'key', 'column', 'problem']].values.tolist() == [
        [2, f'cattle {verdict["object"]}', column, problem]
    ]
    assert readRows(merger.survey / 'flat_verdicts.csv') == []


RESPONSE = {'source': 'cattle', 'object': 'cattle.csv', 'response': 'kg', 'evidence': 'lm(kg ~ diet + calving) in its help page'}  # fmt: skip


@pytest.mark.parametrize('response', ['kg', 'none'])
def test_a_response_shard_merges_into_the_survey_with_its_tier_filled_in(splitMerger, response):
    """A flat table's response is survey bookkeeping, beside the verdicts; `none` is a reading
    too, for a table no documented model fits."""
    merger = splitMerger
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    reading = RESPONSE | {'response': response}
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'response_first.csv', [reading]))
    assert readRows(merger.survey / 'flat_responses.csv') == [reading | {'tier': 'R'}]


@pytest.mark.parametrize(
    'edit, column, problem',
    [
        ({'response': ''}, 'response', 'required'),
        ({'evidence': ''}, 'evidence', 'required'),
        ({'object': 'cattle.old'}, 'object', 'not in registry.csv or excluded.csv'),
        ({'response': 'weight'}, 'response', 'not a column of the table'),
    ],
    ids=['no-response', 'no-evidence', 'an-object-the-census-lacks', 'no-column-of-the-table'],
)
def test_a_response_without_evidence_on_an_unknown_object_or_no_column_is_refused(
    merger, edit, column, problem
):
    """A response is a column of the loaded table or `none`, read with a line of evidence on an
    object the census holds."""
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    reading = RESPONSE | edit
    problems = refusal(merger, writeShard(merger.survey / 'shards' / 'response_bad.csv', [reading]))
    assert problems[['line', 'key', 'column', 'problem']].values.tolist() == [
        [2, f'cattle {reading["object"]}', column, problem]
    ]
    assert readRows(merger.survey / 'flat_responses.csv') == []


def test_a_flat_merge_leaves_the_measured_files_and_the_manifest_as_they_are(merger):
    """A verdict or a response changes no registry row, so its merge skips the measure pass,
    which loads every registry table."""
    mergeShard(merger, FIXTURES / 'registry_herds.csv')
    mergeShard(merger, FIXTURES / 'excluded_cattle.csv')
    files = [merger.registry / name for name in (*MEASURED, 'manifest.csv')]
    written = [file.stat().st_mtime_ns for file in files]
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'flat_second.csv', [VERDICT]))
    mergeShard(merger, writeShard(merger.survey / 'shards' / 'response_first.csv', [RESPONSE]))
    assert [file.stat().st_mtime_ns for file in files] == written
