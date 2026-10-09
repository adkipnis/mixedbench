"""The loader at its seams: `objects` enumerates a source, `load` returns one typed table, `tree`
is the source's extracted files, and the module's `fetch` is the default download.

A `Server` serves the fixtures from memory, so the tests never touch the network: a CRAN-shaped
tarball (`fixture_1.0.tar.gz`, built by `make_fixture.R`), and the url and git downloads
`make_fixtures.py` builds (a deposit zip, a GitHub archive, single files as the repositories
serve them).
"""

from __future__ import annotations

import hashlib
import io
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest
from mixedbench import registry
from mixedbench.datasets import DataObject, Loader, ManifestRow, Source, fetch

FIXTURES = Path(__file__).parent / 'fixtures'
TARBALL = (FIXTURES / 'fixture_1.0.tar.gz').read_bytes()
CURRENT = 'https://cloud.r-project.org/src/contrib/fixture_1.0.tar.gz'
ARCHIVE = 'https://cloud.r-project.org/src/contrib/Archive/fixture/fixture_1.0.tar.gz'
FIXTURE = Source(kind='cran', name='fixture', pin='1.0')
OBJECTS = {'growth', 'pets', 'plots', 'scores', 'trials', 'visits', 'wide'}

DEPOSIT = (FIXTURES / 'deposit.zip').read_bytes()
DEPOSIT_URL = 'https://example.org/deposit.zip'
EXAMPLE = (FIXTURES / 'example-c0ffee1.tar.gz').read_bytes()
EXAMPLE_REPO = 'https://github.com/acme/example'
EXAMPLE_ARCHIVE = 'https://github.com/acme/example/archive/c0ffee1.tar.gz'
RADON = 'https://raw.githubusercontent.com/acme/example/c0ffee1/data/radon.csv'
SCHOOLS = (FIXTURES / 'schools').read_bytes()  # a csv figshare serves without a suffix
SCHOOLS_URL = 'https://ndownloader.example.org/files/123'
DATASETS = (FIXTURES / 'datasets.tar.gz').read_bytes()  # Arrow files, as MixedModels.jl ships
DATASETS_URL = 'https://osf.io/abcde/download?version=9'

BASE = Source(kind='cran', name='datasets', pin='4.6.1')
BASE_URL = 'https://cloud.r-project.org/src/base/R-4/R-4.6.1.tar.gz'
SLEEP_R = b'sleep <- data.frame(extra = c(0.7, -1.6, 3.4, 0.8), group = gl(2, 2))\n'


class Server:
    """Answers the URLs it holds and None to any other, recording every URL asked."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files
        self.asked: list[str] = []

    def __call__(self, url: str) -> bytes | None:
        self.asked.append(url)
        return self.files.get(url)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def urlSource(url: str, data: bytes, **keys: str) -> Source:
    """A url source as `registry.sources()` reads one: the file's sha256 is pin and checksum."""
    return Source(kind='url', name=url, pin=sha(data), checksum=sha(data), **keys)


def manifestRow(file: str, data: bytes) -> ManifestRow:
    return ManifestRow(file, sha(data))


def tarMember(archive: bytes, name: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return tar.extractfile(name).read()


def tarball(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def objectsByName(loader: Loader, source: Source) -> dict[str, DataObject]:
    return {o.name: o for o in loader.objects(source)}


def census(obj: DataObject) -> tuple[str, str, int | None, int | None]:
    return (obj.file, obj.reader, obj.n_rows, obj.n_cols)


# ==============================================================================================
# CRAN sources
# ==============================================================================================


def test_objects_lists_every_data_object_with_its_file_reader_and_counts(tmp_path):
    """The census denominator: what pyreadr, pandas and the deparse reader read, an R file
    only rdata reads (#9), and one pyreadr cannot frame (a matrix column, gamlss.data's aep)
    without counts rather than failing the source."""
    loader = Loader(tmp_path, fetch=Server({CURRENT: TARBALL}))
    objects = objectsByName(loader, FIXTURE)
    assert set(objects) == OBJECTS
    assert census(objects['pets']) == ('data/pets.rda', 'pyreadr', 6, 3)
    assert census(objects['scores']) == ('data/scores.rds', 'pyreadr', 4, 2)
    assert census(objects['trials']) == ('data/trials.csv', 'pandas', 5, 2)
    assert census(objects['plots']) == ('data/plots.txt', 'pandas', 4, 4)
    assert census(objects['growth']) == ('data/growth.R', 'deparse', 8, 7)
    assert census(objects['visits']) == ('data/visits.rda', 'rdata', 3, 2)
    assert census(objects['wide']) == ('data/wide.rda', 'pyreadr', None, None)


def test_a_package_without_a_data_folder_has_no_objects(tmp_path):
    """GLMMadaptive ships no data; the census lists nothing for it instead of failing."""
    nodata = tarball({'nodata/DESCRIPTION': b'Package: nodata\n'})
    url = 'https://cloud.r-project.org/src/contrib/nodata_0.1.tar.gz'
    loader = Loader(tmp_path, fetch=Server({url: nodata}))
    assert loader.objects(Source(kind='cran', name='nodata', pin='0.1')) == []


def test_the_tree_is_the_package_below_the_tarballs_top_level_folder(tmp_path):
    """What the survey reads beside the data (the DESCRIPTION's licence, man/'s help pages)
    sits in the tree, the archive's single top-level folder dropped as layout."""
    tree = Loader(tmp_path, fetch=Server({CURRENT: TARBALL})).tree(FIXTURE)
    assert (tree / 'DESCRIPTION').is_file()
    assert (tree / 'man' / 'pets.Rd').is_file()


def test_a_declared_ordered_column_keeps_its_levels_and_becomes_ordered(tmp_path):
    """pyreadr cannot tell an ordered factor from a plain one, so the registry declares it:
    an R factor keeps its level order, a plain column gets sorted levels."""
    loader = Loader(tmp_path, fetch=Server({CURRENT: TARBALL}))
    scores = loader.load(FIXTURE, 'scores', types={'grade': 'ordered'})
    assert scores['grade'].dtype.ordered
    assert list(scores['grade'].cat.categories) == ['low', 'mid', 'high']
    pets = loader.load(FIXTURE, 'pets', types={'age': 'ordered'})
    assert pets['age'].dtype.ordered
    assert list(pets['age'].cat.categories) == sorted(set(pets['age']))


def test_archive_url_is_tried_after_a_miss(tmp_path):
    """CRAN moves a superseded version to `Archive/`; a pinned source must stay loadable, and
    a version at neither location must fail loudly rather than silently yield nothing."""
    server = Server({ARCHIVE: TARBALL})
    assert set(objectsByName(Loader(tmp_path, fetch=server), FIXTURE)) == OBJECTS
    assert server.asked == [CURRENT, ARCHIVE]
    offline = Loader(tmp_path / 'empty', fetch=Server({}))
    with pytest.raises(FileNotFoundError, match='fixture 1.0'):
        offline.objects(FIXTURE)


def test_checksum_mismatch_is_refused(tmp_path):
    """The second call hits the cache, so the check must run on cache hits too."""
    good = Source(kind='cran', name='fixture', pin='1.0', checksum=sha(TARBALL))
    bad = Source(kind='cran', name='fixture', pin='1.0', checksum='0' * 64)
    loader = Loader(tmp_path, fetch=Server({CURRENT: TARBALL}))
    assert len(loader.objects(good)) == 7
    with pytest.raises(ValueError, match='checksum'):
        loader.objects(bad)


def test_second_loader_over_the_same_cache_fetches_nothing(tmp_path):
    """The cache lives on disk, not in the instance: a new process must not download again."""
    server = Server({CURRENT: TARBALL})
    Loader(tmp_path, fetch=server).load(FIXTURE, 'pets')
    Loader(tmp_path, fetch=server).load(FIXTURE, 'pets')
    assert server.asked == [CURRENT]


def test_base_r_datasets_come_from_rs_source_tarball_without_r(tmp_path):
    """Base R's `datasets` is a package inside R's source tarball, laid out as a CRAN package:
    its data/*.R files load through the deparse reader, a time series among them is listed
    without a table, its man/ holds the help pages, and its manifest file loads like any
    other (ADR 0003)."""
    sources = tarball({
        'R-4.6.1/src/library/datasets/data/sleep.R': SLEEP_R,
        'R-4.6.1/src/library/datasets/data/lynx.R': b'lynx <- stats::ts(c(269, 321))\n',
        'R-4.6.1/src/library/datasets/man/sleep.Rd': b'\\name{sleep}\n\\alias{sleep}\n',
        'R-4.6.1/src/library/stats/DESCRIPTION.in': b'Package: stats\n',
    })  # fmt: skip
    loader = Loader(tmp_path, fetch=Server({BASE_URL: sources}))
    objects = objectsByName(loader, BASE)
    assert census(objects['sleep']) == ('data/sleep.R', 'deparse', 4, 2)
    assert census(objects['lynx']) == ('data/lynx.R', 'deparse', None, None)
    assert list(loader.load(BASE, 'sleep')['group'].cat.categories) == ['1', '2']
    assert (loader.tree(BASE) / 'man' / 'sleep.Rd').is_file()
    manifest = {(BASE, 'sleep'): manifestRow('data/sleep.R', SLEEP_R)}
    alone = Loader(tmp_path, fetch=Server({}), manifest=manifest)
    assert alone.load(BASE, 'sleep').shape == (4, 2)


@pytest.mark.network
def test_the_pinned_r_source_tarball_holds_base_rs_data(tmp_path):
    """The pin in sources.yaml: R 4.6.1's tarball, checksummed, with ChickWeight and sleep."""
    base = registry.sources()['datasets']
    loader = Loader(tmp_path)
    objects = objectsByName(loader, base)
    assert (objects['ChickWeight'].n_rows, objects['ChickWeight'].n_cols) == (578, 4)
    assert loader.load(base, 'sleep').shape == (20, 3)


# ==============================================================================================
# url and git sources (#16)
# ==============================================================================================


def test_a_deposit_zips_objects_are_named_by_their_path_inside_it(tmp_path):
    """A data deposit: the `.csv` is the object, named by its path inside the zip, whose single
    top-level folder is layout, not content; the codebook beside it is in the tree, no object."""
    deposit = urlSource(DEPOSIT_URL, DEPOSIT)
    loader = Loader(tmp_path, fetch=Server({DEPOSIT_URL: DEPOSIT}))
    objects = objectsByName(loader, deposit)
    assert set(objects) == {'data/schools.csv'}
    assert census(objects['data/schools.csv']) == ('data/schools.csv', 'pandas', 5, 3)
    df = loader.load(deposit, 'data/schools.csv')
    assert list(df['score']) == [10.5, 12.0, 9.5, 15.0, 11.0]
    assert (loader.tree(deposit) / 'codebook.txt').is_file()


def test_declared_column_types_are_applied(tmp_path):
    """Delimited text carries no types, so the registry row declares them: a declared
    categorical arrives as a categorical with sorted levels (R's `factor()` default), a declared
    continuous stays numeric, an undeclared numeric column is left as pandas read it."""
    deposit = urlSource(DEPOSIT_URL, DEPOSIT)
    loader = Loader(tmp_path, fetch=Server({DEPOSIT_URL: DEPOSIT}))
    declared = {'school': 'categorical', 'score': 'continuous'}
    df = loader.load(deposit, 'data/schools.csv', types=declared)
    assert list(df['school'].cat.categories) == ['A', 'B', 'C']
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']
    assert df['score'].dtype.kind == 'f'
    assert df['size'].dtype.kind == 'i'


def test_git_source_is_fetched_as_an_archive_at_its_revision_and_cached(tmp_path):
    """A repository pinned to a revision comes as GitHub's archive tarball of that revision, so
    one fetch serves every file and README; the pinned path narrows the objects to its folder;
    a second loader over the same cache asks for nothing."""
    server = Server({EXAMPLE_ARCHIVE: EXAMPLE})
    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    loader = Loader(tmp_path, fetch=server)
    objects = objectsByName(loader, example)
    assert set(objects) == {'data/radon.csv'}
    assert census(objects['data/radon.csv']) == ('data/radon.csv', 'pandas', 5, 3)
    Loader(tmp_path, fetch=server).load(example, 'data/radon.csv')
    assert server.asked == [EXAMPLE_ARCHIVE]


def test_url_without_a_suffix_is_saved_under_the_file_the_frame_names(tmp_path):
    """figshare and OSF serve a file from a URL whose path has no suffix, so the frame says
    what the download is (`file`); the object is named after it and read by that suffix."""
    schools = urlSource(SCHOOLS_URL, SCHOOLS, file='schools.csv')
    loader = Loader(tmp_path, fetch=Server({SCHOOLS_URL: SCHOOLS}))
    assert set(objectsByName(loader, schools)) == {'schools.csv'}
    df = loader.load(schools, 'schools.csv')
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']


def test_arrow_files_in_a_tarball_from_a_suffixless_url_load(tmp_path):
    """MixedModels.jl ships its datasets as one OSF tarball of Arrow files; the frame names the
    download `datasets.tar.gz`, which is extracted, and each `.arrow` is an object."""
    datasets = urlSource(DATASETS_URL, DATASETS, file='datasets.tar.gz')
    loader = Loader(tmp_path, fetch=Server({DATASETS_URL: DATASETS}))
    objects = objectsByName(loader, datasets)
    assert set(objects) == {'kb07.arrow'}
    df = loader.load(datasets, 'kb07.arrow')
    assert list(df['subj']) == ['S1', 'S1', 'S2', 'S2']


def test_a_url_its_host_refuses_loads_from_its_mirror_under_the_same_pin(tmp_path):
    """Dryad refuses scripted downloads of CC0 data, so the package mirrors them (ADR 0003): the
    host is asked first, the mirror after, and the mirror's file must carry the pinned digest."""
    mirror = 'https://github.com/acme/mixedbench/releases/download/mirror-1/schools.csv'
    server = Server({mirror: SCHOOLS})
    schools = urlSource(SCHOOLS_URL, SCHOOLS, file='schools.csv', mirror=mirror)
    df = Loader(tmp_path, fetch=server).load(schools, 'schools.csv')
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']
    assert server.asked == [SCHOOLS_URL, mirror]


# ==============================================================================================
# lean fetch through the manifest (#4)
# ==============================================================================================


def test_a_git_object_is_fetched_alone_from_its_raw_url(tmp_path):
    """With the manifest, a git object is one file at the pinned revision, never the
    repository archive (pymc-examples is 1 GB for a few csv); the cache serves it after."""
    radon = tarMember(EXAMPLE, 'example-c0ffee1/data/radon.csv')
    server = Server({RADON: radon, EXAMPLE_ARCHIVE: EXAMPLE})
    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    manifest = {(example, 'data/radon.csv'): manifestRow('data/radon.csv', radon)}
    df = Loader(tmp_path, fetch=server, manifest=manifest).load(example, 'data/radon.csv')
    assert list(df['county']) == ['Anoka', 'Anoka', 'Clay', 'Clay', 'Clay']
    Loader(tmp_path, fetch=server, manifest=manifest).load(example, 'data/radon.csv')
    assert server.asked == [RADON]


def test_a_git_file_name_with_spaces_is_quoted_in_its_raw_url(tmp_path):
    """ROS keeps `HDI/data/state vote and income, 68-00.dta`; a URL cannot carry the spaces."""
    radon = tarMember(EXAMPLE, 'example-c0ffee1/data/radon.csv')
    quoted = 'https://raw.githubusercontent.com/acme/example/c0ffee1/data/radon%20by%20county.csv'
    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    manifest = {(example, 'data/radon by county.csv'): manifestRow('data/radon by county.csv', radon)}  # fmt: skip
    loader = Loader(tmp_path, fetch=Server({quoted: radon}), manifest=manifest)
    assert len(loader.load(example, 'data/radon by county.csv')) == 5


def test_a_file_differing_from_its_manifest_checksum_is_refused(tmp_path):
    """A per-file fetch keeps the fetch-only guarantee only if every file is checked against
    the digest the package ships, on cache hits too, where a tampered file would sit."""
    radon = tarMember(EXAMPLE, 'example-c0ffee1/data/radon.csv')
    server = Server({RADON: radon})
    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    good = {(example, 'data/radon.csv'): manifestRow('data/radon.csv', radon)}
    bad = {(example, 'data/radon.csv'): ManifestRow('data/radon.csv', '0' * 64)}
    Loader(tmp_path, fetch=server, manifest=good).load(example, 'data/radon.csv')
    with pytest.raises(ValueError, match='checksum'):
        Loader(tmp_path, fetch=server, manifest=bad).load(example, 'data/radon.csv')


def test_a_cran_or_url_archive_object_loads_its_file_from_the_extracted_tree(tmp_path):
    """A CRAN tarball or a deposit zip comes whole (its digest is the pin) and is extracted
    whole, as on the enumerate path; the manifest's file is then checked and read alone."""
    pets = tarMember(TARBALL, 'fixture/data/pets.rda')
    deposit = urlSource(DEPOSIT_URL, DEPOSIT)
    schools = zipfile.ZipFile(io.BytesIO(DEPOSIT)).read('deposit/data/schools.csv')
    manifest = {
        (FIXTURE, 'pets'): manifestRow('data/pets.rda', pets),
        (deposit, 'data/schools.csv'): manifestRow('data/schools.csv', schools),
    }
    server = Server({CURRENT: TARBALL, DEPOSIT_URL: DEPOSIT})
    loader = Loader(tmp_path, fetch=server, manifest=manifest)
    assert list(loader.load(FIXTURE, 'pets')['species'])[:3] == ['dog', 'cat', 'fish']
    assert list(loader.load(deposit, 'data/schools.csv')['score'])[:2] == [10.5, 12.0]


# ==============================================================================================
# the default fetch
# ==============================================================================================


def test_fetch_waits_and_retries_after_a_429(monkeypatch):
    """OSF answers 429 to a burst of downloads; the default fetch waits the `Retry-After`
    seconds and tries again instead of failing the pull."""
    answers = [
        urllib.error.HTTPError('u', 429, 'Too Many Requests', {'Retry-After': '0'}, None),
        io.BytesIO(b'content'),
    ]

    def urlopen(req, timeout, context):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(urllib.request, 'urlopen', urlopen)
    assert fetch('https://osf.io/x/download') == b'content'


@pytest.mark.parametrize('code', [401, 403])
def test_fetch_takes_a_refusal_as_a_miss(monkeypatch, code):
    """Dryad answers 401 to a script; like a 404 the next location (the mirror) is asked."""

    def urlopen(req, timeout, context):
        raise urllib.error.HTTPError('u', code, 'Unauthorized', {}, None)

    monkeypatch.setattr(urllib.request, 'urlopen', urlopen)
    assert fetch('https://datadryad.org/api/v2/files/1/download') is None


@pytest.mark.network
def test_a_server_that_sends_the_wrong_intermediate_certificate_is_verified():
    """Harvard's companion site for Fitzmaurice et al. sends InCommon's intermediate for a leaf
    Sectigo's OV R36 signed; macOS and Windows fetch the right one, OpenSSL does not, so the
    package ships it and the download is verified on every operating system."""
    fev1 = registry.sources()['fitzmaurice_fev1']
    assert sha(fetch(fev1.name)) == fev1.pin
