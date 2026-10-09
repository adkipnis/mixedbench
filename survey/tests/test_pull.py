"""The pull script at its seams: `sources.yaml` in, `candidates.csv`, `help/` and the pre-screen
shard out, and the screen rule on hand-made tables (#19).
The frame is one CRAN source, the package's fixture tarball served from memory with a call
counter, so the tests never touch the network and can see a second download."""

import csv
from pathlib import Path

import pandas as pd
import pytest
import yaml
from merge import Merger
from mixedbench.datasets import Loader
from pull import Puller, screen

# the loader's own fixture: five documented data objects, one of them a data() text file
TARBALL = (
    Path(__file__).resolve().parents[2] / 'tests' / 'datasets' / 'fixtures' / 'fixture_1.0.tar.gz'
)
CURRENT = 'https://cloud.r-project.org/src/contrib/fixture_1.0.tar.gz'


class Server:
    """Serves the fixture tarball at its CRAN URL and counts every fetch."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, url: str) -> bytes | None:
        self.calls += 1
        return TARBALL.read_bytes() if url == CURRENT else None


def writeFrame(root: Path, cap: int | None) -> None:
    fixture = {'kind': 'cran', 'pin': '1.0'}
    if cap is not None:
        fixture['cap'] = cap
    frame = {'seed': 0, 'tiers': {'R': {'fixture': fixture}}, 'dropped': []}
    (root / 'sources.yaml').write_text(yaml.safe_dump(frame, sort_keys=False))


def pull(registry: Path, survey: Path, server: Server) -> Puller:
    puller = Puller(registry, survey, loader=Loader(registry / 'cache', fetch=server))
    puller.enumerate()
    puller.copyHelp()
    puller.flush()
    return puller


def readRows(path: Path) -> list[dict]:
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


@pytest.fixture
def root(tmp_path: Path) -> Path:
    writeFrame(tmp_path, cap=None)
    return tmp_path


def test_every_object_gets_a_candidates_row_and_a_help_page(root):
    """The census denominator: one row per enumerated object with its counts and route, and
    its documentation copied where the reading agents look."""
    pull(root, root, Server())
    rows = readRows(root / 'candidates.csv')
    assert [(r['tier'], r['source'], r['pin'], r['object']) for r in rows] == [
        ('R', 'fixture', '1.0', 'growth'),
        ('R', 'fixture', '1.0', 'pets'),
        ('R', 'fixture', '1.0', 'plots'),
        ('R', 'fixture', '1.0', 'scores'),
        ('R', 'fixture', '1.0', 'trials'),
        ('R', 'fixture', '1.0', 'visits'),
        ('R', 'fixture', '1.0', 'wide'),
    ]
    growth, pets, plots, scores, trials, visits, wide = rows
    assert (pets['file'], pets['n_rows'], pets['n_cols']) == ('data/pets.rda', '6', '3')
    dtypes = (pets['n_numeric'], pets['n_categorical'], pets['n_string'], pets['n_other'])
    assert dtypes == ('2', '1', '0', '0')
    readers = (
        growth['reader'],
        plots['reader'],
        scores['reader'],
        trials['reader'],
        visits['reader'],
    )
    assert readers == ('deparse', 'pandas', 'pyreadr', 'pandas', 'rscript')
    assert (wide['n_rows'], wide['n_cols'], wide['n_numeric']) == ('', '', '')
    assert [r['screen'] for r in rows] == ['pass'] * 6 + ['no frame']
    assert {r['capped'] for r in rows} == {'no'}
    assert (root / 'help' / 'fixture' / 'trials.txt').read_text().startswith('\\name{trials}')
    assert not (root / 'help' / 'fixture' / 'wide.txt').exists()
    shard = readRows(root / 'shards' / 'excluded_prescreen.csv')
    assert shard == [
        {'source': 'fixture', 'object': 'wide', 'reason': 'unreadable format', 'detail': 'no frame'}
    ]


def test_a_help_page_ends_with_the_dtypes_and_first_rows_of_its_table(root):
    """The read prompt promises agents the first rows next to the documentation, and agents
    run nothing: the pull appends them to the help page."""
    pull(root, root, Server())
    page = (root / 'help' / 'fixture' / 'pets.txt').read_text()
    head = page[page.index('# first rows') :]
    assert '# first rows (of 6)' in head
    assert 'category' in head
    assert head.count('\n') >= 2 + 2 + 6  # banner, dtype lines, header and rows


def test_a_source_over_its_cap_keeps_a_seeded_draw_and_lists_the_rest_as_capped(tmp_path):
    """Two of the six passing objects are read; the other four stay enumerated with `capped`
    set and get no help page, the screened-out one is not capped but not read either; the
    same seed draws the same two on a second run."""
    writeFrame(tmp_path, cap=None)
    pull(tmp_path, tmp_path, Server())  # six pages; the capped run below must leave only two
    writeFrame(tmp_path, cap=2)
    pull(tmp_path, tmp_path, Server())
    first = readRows(tmp_path / 'candidates.csv')
    kept = [r['object'] for r in first if r['capped'] == 'no' and r['screen'] == 'pass']
    left = [r['object'] for r in first if r['capped'] == 'yes']
    assert len(kept) == 2 and len(left) == 4
    assert [r['capped'] for r in first if r['screen'] != 'pass'] == ['no']
    assert sorted(f.stem for f in (tmp_path / 'help' / 'fixture').iterdir()) == sorted(kept)
    pull(tmp_path, tmp_path, Server())
    second = readRows(tmp_path / 'candidates.csv')
    assert [r['object'] for r in second if r['capped'] == 'no' and r['screen'] == 'pass'] == kept


def test_rerunning_the_pull_downloads_nothing_and_rewrites_the_same_file(root):
    server = Server()
    pull(root, root, server)
    before = (root / 'candidates.csv').read_bytes()
    pull(root, root, server)
    assert server.calls == 1
    assert (root / 'candidates.csv').read_bytes() == before


def test_candidates_follow_frame_order_not_the_alphabet(tmp_path):
    """Tier first, then the order of `sources.yaml`: `alpha` is listed after `fixture` because
    it comes later in the file, although it sorts first."""
    frame = {
        'seed': 0,
        'tiers': {
            'E': {'later': {'kind': 'cran', 'name': 'fixture', 'pin': '1.0'}},
            'R': {
                'fixture': {'kind': 'cran', 'pin': '1.0'},
                'alpha': {'kind': 'cran', 'name': 'fixture', 'pin': '1.0'},
            },
        },
        'dropped': [],
    }
    (tmp_path / 'sources.yaml').write_text(yaml.safe_dump(frame, sort_keys=False))
    pull(tmp_path, tmp_path, Server())
    rows = readRows(tmp_path / 'candidates.csv')
    assert [r['source'] for r in rows[::7]] == ['fixture', 'alpha', 'later']


@pytest.mark.parametrize(
    'table, verdict',
    [
        ({'y': [1.0, 2.0, 3.0], 'g': ['a', 'a', 'b']}, 'pass'),
        ({'y': [1.0, 2.0, 3.0], 'g': [1.0, 1.0, 2.0]}, 'pass'),  # R codes arrive as doubles
        ({'y': [1.0, 2.0, 3.0], 'g': [0.5, 0.5, 2.0]}, 'no repeated column'),  # fractional
        ({'y': [1.0, 2.0, 3.0], 'g': ['a', 'b', 'c']}, 'no repeated column'),  # an id
        ({'y': [1.0, 2.0, 3.0], 'g': ['a', 'a', 'a']}, 'no repeated column'),  # constant
        ({'y': [1.0, 2.0, 3.0]}, 'one column'),
        ({'y': [1.0, 2.0], 'g': ['a', 'a']}, 'under 3 rows'),
        (None, 'no frame'),
    ],
)
def test_screen_keeps_every_table_that_could_hold_groups(table, verdict):
    """Conservative by design: anything with a column that could index groups passes; only
    what cannot be a grouped table at all is discarded."""
    df = None if table is None else pd.DataFrame(table)
    assert screen(df) == verdict


def test_the_prescreen_shard_merges_into_the_exclusions(root):
    """The pull never writes a canonical file; its discards reach excluded.csv through the
    merge like any agent shard, with the tier filled in."""
    puller = pull(root, root, Server())
    merger = Merger(root, root, loader=puller.loader)
    merger.load(root / 'shards' / 'excluded_prescreen.csv')
    merger.validate()
    merger.append()
    merger.flush()
    rows = readRows(root / 'excluded.csv')
    assert [(r['tier'], r['source'], r['object'], r['reason']) for r in rows] == [
        ('R', 'fixture', 'wide', 'unreadable format')
    ]


def test_the_pull_writes_help_pages_to_the_registry_and_its_lists_to_the_survey(tmp_path):
    """registry/ holds the frame, the cache and the help pages; the candidate list and the
    pre-screen shard are survey working files."""
    registry, survey = tmp_path / 'registry', tmp_path / 'survey'
    registry.mkdir()
    survey.mkdir()
    writeFrame(registry, cap=None)
    pull(registry, survey, Server())
    assert sorted(p.name for p in registry.iterdir()) == ['cache', 'help', 'sources.yaml']
    assert sorted(p.name for p in survey.iterdir()) == ['candidates.csv', 'shards']
    assert (registry / 'help' / 'fixture' / 'trials.txt').exists()
