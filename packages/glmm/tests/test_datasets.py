"""The dataset loader at its three public seams: enumerate, load, help (#15).

A CRAN-shaped fixture tarball (`fixtures/fixture_1.0.tar.gz`, built by `make_fixture.R`) is
served by an injected fetch, so the tests never touch the network.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest
from metabeta.glmm.datasets import DataObject, Loader, Source

FIXTURES = Path(__file__).parent / 'fixtures'
TARBALL = (FIXTURES / 'fixture_1.0.tar.gz').read_bytes()
CURRENT = 'https://cloud.r-project.org/src/contrib/fixture_1.0.tar.gz'
ARCHIVE = 'https://cloud.r-project.org/src/contrib/Archive/fixture/fixture_1.0.tar.gz'
FIXTURE = Source(kind='cran', name='fixture', pin='1.0')
# the loader dumps every data() file through Rscript; the fixture ships one (`trials.csv`)
pytestmark = pytest.mark.skipif(shutil.which('Rscript') is None, reason='needs Rscript')


def serveCurrent(url: str) -> bytes | None:
    return TARBALL if url == CURRENT else None


def serveNothing(url: str) -> bytes | None:
    return None


def objectsByName(loader: Loader, source: Source) -> dict[str, DataObject]:
    return {o.name: o for o in loader.objects(source)}


def test_objects_enumerates_the_tarball(tmp_path):
    """The census denominator: every data object listed with its counts."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    objects = objectsByName(loader, FIXTURE)
    assert set(objects) == {'pets', 'scores', 'trials'}
    pets, scores, trials = objects['pets'], objects['scores'], objects['trials']
    assert (pets.file, pets.n_rows, pets.n_cols) == ('data/pets.rda', 6, 3)
    assert (scores.file, scores.n_rows, scores.n_cols) == ('data/scores.rds', 4, 2)
    assert (trials.file, trials.n_rows, trials.n_cols) == ('data/trials.csv', 5, 2)


def test_load_keeps_factor_levels_in_r_order(tmp_path):
    """pyreadr's own `read_r` sorts factor levels and drops unused ones; the loader restores
    R's order from parser internals, which this test pins (`bird` is an unused level)."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    pets = loader.load(FIXTURE, 'pets')
    assert list(pets['species'].cat.categories) == ['dog', 'cat', 'fish', 'bird']
    assert list(pets['species']) == ['dog', 'cat', 'fish', 'dog', 'cat', 'dog']
    assert pets['age'].dtype.kind == 'i' and pets['weight'].dtype.kind == 'f'
    scores = loader.load(FIXTURE, 'scores')
    assert list(scores['grade'].cat.categories) == ['low', 'mid', 'high']


def test_help_returns_the_rd_page_text(tmp_path):
    loader = Loader(tmp_path, fetch=serveCurrent)
    page = loader.help(FIXTURE, 'pets')
    assert page.startswith('\\name{pets}')
    assert 'Species, age in years and weight in kg of six pets.' in page


def test_archive_url_is_tried_after_a_miss(tmp_path):
    """CRAN moves a superseded version to `Archive/`; a pinned source must stay loadable, and
    a version at neither location must fail loudly rather than silently yield nothing."""
    asked = []

    def serveArchive(url: str) -> bytes | None:
        asked.append(url)
        return TARBALL if url == ARCHIVE else None

    loader = Loader(tmp_path, fetch=serveArchive)
    objects = objectsByName(loader, FIXTURE)
    assert set(objects) == {'pets', 'scores', 'trials'}
    assert asked == [CURRENT, ARCHIVE]
    offline = Loader(tmp_path / 'empty', fetch=serveNothing)
    with pytest.raises(FileNotFoundError, match='fixture 1.0'):
        offline.objects(FIXTURE)


def test_checksum_mismatch_is_refused(tmp_path):
    """The second call hits the cache, so the check must run on cache hits too."""
    sha = hashlib.sha256(TARBALL).hexdigest()
    good = Source(kind='cran', name='fixture', pin='1.0', checksum=sha)
    bad = Source(kind='cran', name='fixture', pin='1.0', checksum='0' * 64)
    loader = Loader(tmp_path, fetch=serveCurrent)
    assert len(loader.objects(good)) == 3
    with pytest.raises(ValueError, match='checksum'):
        loader.objects(bad)


def test_second_loader_over_the_same_cache_fetches_nothing(tmp_path):
    """The cache lives on disk, not in the instance: a new process must not download again."""
    calls = []

    def counting(url: str) -> bytes | None:
        calls.append(url)
        return serveCurrent(url)

    Loader(tmp_path, fetch=counting).load(FIXTURE, 'pets')
    Loader(tmp_path, fetch=counting).load(FIXTURE, 'pets')
    assert calls == [CURRENT]


def test_csv_data_object_takes_the_rscript_route(tmp_path):
    """A `.csv` in `data/` is read by R's `data()` rules (`sep = ';'`, strings as factors);
    the loader dumps it through Rscript and reports that route."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    trials = objectsByName(loader, FIXTURE)['trials']
    assert trials.reader == 'rscript'
    df = loader.load(FIXTURE, 'trials')
    assert list(df['arm'].cat.categories) == ['control', 'treated']
    assert list(df['outcome']) == [0, 1, 1, 1, 0]


def test_base_r_datasets_are_dumped_from_the_namespace(tmp_path):
    """Base R's `datasets` ships no tarball; its tree is a dump of the namespace made by R."""
    base = Source(kind='cran', name='datasets', pin='base')
    loader = Loader(tmp_path, fetch=serveNothing)
    iris = objectsByName(loader, base)['iris']
    assert (iris.file, iris.n_rows, iris.n_cols) == ('data/iris.rds', 150, 5)
    species = loader.load(base, 'iris')['Species']
    assert list(species.cat.categories) == ['setosa', 'versicolor', 'virginica']
