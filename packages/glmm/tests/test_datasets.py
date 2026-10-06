"""The dataset loader at its three public seams: enumerate, load, help (#15, #16).

Fixtures are served by an injected fetch, so the tests never touch the network: a CRAN-shaped
tarball (`fixture_1.0.tar.gz`, built by `make_fixture.R`), a data deposit zip and a GitHub
archive (`deposit.zip`, `example-c0ffee1.tar.gz`, built by `make_fixtures.py`).
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
# the loader dumps every CRAN data() file through Rscript; the fixture ships one (`trials.csv`)
needsRscript = pytest.mark.skipif(shutil.which('Rscript') is None, reason='needs Rscript')

DEPOSIT = (FIXTURES / 'deposit.zip').read_bytes()
DEPOSIT_URL = 'https://example.org/deposit.zip'
DEPOSIT_SHA = hashlib.sha256(DEPOSIT).hexdigest()
EXAMPLE = (FIXTURES / 'example-c0ffee1.tar.gz').read_bytes()
EXAMPLE_REPO = 'https://github.com/acme/example'
EXAMPLE_ARCHIVE = 'https://github.com/acme/example/archive/c0ffee1.tar.gz'


def serveCurrent(url: str) -> bytes | None:
    return TARBALL if url == CURRENT else None


def serveNothing(url: str) -> bytes | None:
    return None


def serveDeposit(url: str) -> bytes | None:
    return DEPOSIT if url == DEPOSIT_URL else None


def serveExample(url: str) -> bytes | None:
    return EXAMPLE if url == EXAMPLE_ARCHIVE else None


def objectsByName(loader: Loader, source: Source) -> dict[str, DataObject]:
    return {o.name: o for o in loader.objects(source)}


@needsRscript
def test_objects_enumerates_the_tarball(tmp_path):
    """The census denominator: every data object listed with its counts."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    objects = objectsByName(loader, FIXTURE)
    assert set(objects) == {'pets', 'scores', 'trials'}
    pets, scores, trials = objects['pets'], objects['scores'], objects['trials']
    assert (pets.file, pets.n_rows, pets.n_cols) == ('data/pets.rda', 6, 3)
    assert (scores.file, scores.n_rows, scores.n_cols) == ('data/scores.rds', 4, 2)
    assert (trials.file, trials.n_rows, trials.n_cols) == ('data/trials.csv', 5, 2)


@needsRscript
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


@needsRscript
def test_help_returns_the_rd_page_text(tmp_path):
    loader = Loader(tmp_path, fetch=serveCurrent)
    page = loader.help(FIXTURE, 'pets')
    assert page.startswith('\\name{pets}')
    assert 'Species, age in years and weight in kg of six pets.' in page


@needsRscript
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


@needsRscript
def test_checksum_mismatch_is_refused(tmp_path):
    """The second call hits the cache, so the check must run on cache hits too."""
    sha = hashlib.sha256(TARBALL).hexdigest()
    good = Source(kind='cran', name='fixture', pin='1.0', checksum=sha)
    bad = Source(kind='cran', name='fixture', pin='1.0', checksum='0' * 64)
    loader = Loader(tmp_path, fetch=serveCurrent)
    assert len(loader.objects(good)) == 3
    with pytest.raises(ValueError, match='checksum'):
        loader.objects(bad)


@needsRscript
def test_second_loader_over_the_same_cache_fetches_nothing(tmp_path):
    """The cache lives on disk, not in the instance: a new process must not download again."""
    calls = []

    def counting(url: str) -> bytes | None:
        calls.append(url)
        return serveCurrent(url)

    Loader(tmp_path, fetch=counting).load(FIXTURE, 'pets')
    Loader(tmp_path, fetch=counting).load(FIXTURE, 'pets')
    assert calls == [CURRENT]


@needsRscript
def test_csv_data_object_takes_the_rscript_route(tmp_path):
    """A `.csv` in `data/` is read by R's `data()` rules (`sep = ';'`, strings as factors);
    the loader dumps it through Rscript and reports that route."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    trials = objectsByName(loader, FIXTURE)['trials']
    assert trials.reader == 'rscript'
    df = loader.load(FIXTURE, 'trials')
    assert list(df['arm'].cat.categories) == ['control', 'treated']
    assert list(df['outcome']) == [0, 1, 1, 1, 0]


@needsRscript
def test_base_r_datasets_are_dumped_from_the_namespace(tmp_path):
    """Base R's `datasets` ships no tarball; its tree is a dump of the namespace made by R."""
    base = Source(kind='cran', name='datasets', pin='base')
    loader = Loader(tmp_path, fetch=serveNothing)
    iris = objectsByName(loader, base)['iris']
    assert (iris.file, iris.n_rows, iris.n_cols) == ('data/iris.rds', 150, 5)
    species = loader.load(base, 'iris')['Species']
    assert list(species.cat.categories) == ['setosa', 'versicolor', 'virginica']


# ----------------------------------------------------------------------------------------------
# url and git sources (#16)
# ----------------------------------------------------------------------------------------------


def test_url_zip_enumerates_loads_and_documents(tmp_path):
    """A data deposit: the `.csv` is the object, named by its path inside the zip (the zip's
    single top-level folder is layout, not content), read by pandas with the separator sniffed;
    the codebook at the root documents it, found by walking up from the file's directory."""
    deposit = Source(kind='url', name=DEPOSIT_URL, pin=DEPOSIT_SHA)
    loader = Loader(tmp_path, fetch=serveDeposit)
    objects = objectsByName(loader, deposit)
    assert set(objects) == {'data/schools.csv'}
    schools = objects['data/schools.csv']
    assert (schools.file, schools.n_rows, schools.n_cols) == ('data/schools.csv', 5, 3)
    assert schools.reader == 'pandas'
    df = loader.load(deposit, 'data/schools.csv')
    assert list(df['score']) == [10.5, 12.0, 9.5, 15.0, 11.0]
    assert 'school: one of three schools A, B, C' in loader.help(deposit, 'data/schools.csv')


def test_url_pin_is_the_checksum(tmp_path):
    """A URL has no version; the file's sha256 is its pin and is always checked."""
    wrong = Source(kind='url', name=DEPOSIT_URL, pin='0' * 64)
    loader = Loader(tmp_path, fetch=serveDeposit)
    with pytest.raises(ValueError, match='checksum'):
        loader.objects(wrong)


def test_git_source_is_fetched_as_an_archive_at_its_revision_and_cached(tmp_path):
    """A repository pinned to a revision comes as GitHub's archive tarball of that revision, so
    one fetch serves every file and README; the pinned path narrows the objects to its folder;
    a second loader over the same cache asks for nothing."""
    asked = []

    def counting(url: str) -> bytes | None:
        asked.append(url)
        return serveExample(url)

    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    loader = Loader(tmp_path, fetch=counting)
    objects = objectsByName(loader, example)
    assert set(objects) == {'data/radon.csv'}
    radon = objects['data/radon.csv']
    assert (radon.n_rows, radon.n_cols, radon.reader) == (5, 3, 'pandas')
    df = loader.load(example, 'data/radon.csv')
    assert list(df['county']) == ['Anoka', 'Anoka', 'Clay', 'Clay', 'Clay']
    assert loader.help(example, 'data/radon.csv').startswith(
        '# data/README.md\ncounty: county name'
    )
    Loader(tmp_path, fetch=counting).load(example, 'data/radon.csv')
    assert asked == [EXAMPLE_ARCHIVE]


def test_declared_column_types_are_applied(tmp_path):
    """Delimited text carries no types, so the registry row declares them: a declared
    categorical arrives as a categorical with sorted levels (R's `factor()` default), a declared
    continuous stays numeric, an undeclared numeric column is left as pandas read it."""
    deposit = Source(kind='url', name=DEPOSIT_URL, pin=DEPOSIT_SHA)
    loader = Loader(tmp_path, fetch=serveDeposit)
    declared = {'school': 'categorical', 'score': 'continuous'}
    df = loader.load(deposit, 'data/schools.csv', types=declared)
    assert list(df['school'].cat.categories) == ['A', 'B', 'C']
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']
    assert df['score'].dtype.kind == 'f'
    assert df['size'].dtype.kind == 'i'


def test_excel_json_and_stata_files_load(tmp_path):
    """The reader follows the extension: Excel (first sheet), JSON records and Stata, whose
    value labels arrive as a categorical in label order."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    objects = objectsByName(loader, formats)
    assert set(objects) == {'formats/trials.xlsx', 'formats/visits.json', 'formats/births.dta'}
    assert {o.reader for o in objects.values()} == {'pandas'}
    trials = loader.load(formats, 'formats/trials.xlsx')
    assert list(trials['arm']) == ['control', 'treated', 'control']
    visits = loader.load(formats, 'formats/visits.json')
    assert list(visits['visits']) == [3, 1, 4, 2]
    births = loader.load(formats, 'formats/births.dta')
    assert list(births['hospital'].cat.categories) == ['north', 'south']
    assert list(births['weight']) == [3.2, 2.9, 3.5, 3.1]
