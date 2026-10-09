"""The dataset loader at its three public seams: enumerate, load, help (#15, #16).

Fixtures are served by an injected fetch, so the tests never touch the network: a CRAN-shaped
tarball (`fixture_1.0.tar.gz`, built by `make_fixture.R`), and the url and git downloads
`make_fixtures.py` builds (a deposit zip, a GitHub archive, single files as the repositories
serve them).
"""

from __future__ import annotations

import hashlib
import io
import shutil
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import pytest
from mixedbench import registry
from mixedbench.datasets import DataObject, Loader, ManifestRow, Source, readers

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
SCHOOLS = (FIXTURES / 'schools').read_bytes()  # a csv figshare serves without a suffix
SCHOOLS_URL = 'https://ndownloader.example.org/files/123'
APNEA = (FIXTURES / 'apnea.tsv.gz').read_bytes()
APNEA_URL = 'https://media.example.org/pmlb/apnea.tsv.gz'
DATASETS = (FIXTURES / 'datasets.tar.gz').read_bytes()  # Arrow files, as MixedModels.jl ships
DATASETS_URL = 'https://osf.io/abcde/download?version=9'
PUPILS = (FIXTURES / 'dataset_42.pq').read_bytes()  # OpenML's parquet rendering
PUPILS_URL = 'https://data.openml.org/datasets/0000/0042/dataset_42.pq'
SERVED = {SCHOOLS_URL: SCHOOLS, APNEA_URL: APNEA, DATASETS_URL: DATASETS, PUPILS_URL: PUPILS}


def serveCurrent(url: str) -> bytes | None:
    return TARBALL if url == CURRENT else None


def serveNothing(url: str) -> bytes | None:
    return None


def serveDeposit(url: str) -> bytes | None:
    return DEPOSIT if url == DEPOSIT_URL else None


def serveExample(url: str) -> bytes | None:
    return EXAMPLE if url == EXAMPLE_ARCHIVE else None


def serveFiles(url: str) -> bytes | None:
    return SERVED.get(url)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifestRow(file: str, data: bytes) -> ManifestRow:
    return ManifestRow(file, sha(data), len(data))


def objectsByName(loader: Loader, source: Source) -> dict[str, DataObject]:
    return {o.name: o for o in loader.objects(source)}


@needsRscript
def test_objects_enumerates_the_tarball(tmp_path):
    """The census denominator: every data object listed with its counts."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    objects = objectsByName(loader, FIXTURE)
    assert set(objects) == {'pets', 'scores', 'trials', 'visits', 'wide'}
    pets, scores, trials = objects['pets'], objects['scores'], objects['trials']
    assert (pets.file, pets.n_rows, pets.n_cols) == ('data/pets.rda', 6, 3)
    assert (scores.file, scores.n_rows, scores.n_cols) == ('data/scores.rds', 4, 2)
    assert (trials.file, trials.n_rows, trials.n_cols) == ('data/trials.csv', 5, 2)


@needsRscript
def test_an_r_file_librdata_rejects_is_re_saved_by_r(tmp_path):
    """geepack's muscatine is a plain data frame librdata calls an unrecognized object; the
    Rscript dump turns it into a version-2 .rds pyreadr reads (spec #14, user story 15)."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    visits = objectsByName(loader, FIXTURE)['visits']
    assert (visits.reader, visits.n_rows, visits.n_cols) == ('rscript', 3, 2)
    assert list(loader.load(FIXTURE, 'visits')['clinic'].cat.categories) == ['north', 'south']


@needsRscript
def test_an_object_pyreadr_cannot_frame_is_listed_without_counts(tmp_path):
    """gamlss.data's aep holds a matrix column; the object stays in the census with None
    counts rather than failing the whole source."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    wide = objectsByName(loader, FIXTURE)['wide']
    assert (wide.reader, wide.n_rows, wide.n_cols) == ('pyreadr', None, None)


def test_a_package_without_a_data_folder_has_no_objects(tmp_path):
    """GLMMadaptive ships no data; the census lists nothing for it instead of failing."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        info = tarfile.TarInfo('nodata/DESCRIPTION')
        info.size = len(b'Package: nodata\n')
        tar.addfile(info, io.BytesIO(b'Package: nodata\n'))

    def serveNodata(url: str) -> bytes | None:
        return buffer.getvalue()

    loader = Loader(tmp_path, fetch=serveNodata)
    assert loader.objects(Source(kind='cran', name='nodata', pin='0.1')) == []


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
    assert not scores['grade'].dtype.ordered


@needsRscript
def test_an_integer_column_with_na_loads_as_float_not_object(tmp_path):
    """pyreadr renders an R integer vector with NA as an object column of ints and NaN, which
    no numeric check accepts (mlmRev's `star`); the loader makes it a float column."""
    rds = tmp_path / 'scores.rds'
    # R writes a frame with an integer column holding one NA and a plain string column
    Loader._rscript(
        "saveRDS(data.frame(score = c(1L, NA, 3L), note = c('a', 'b', 'c')),"
        ' commandArgs(TRUE)[1], version = 2)',
        str(rds),
    )
    frames = readers.readR(rds)
    scores = frames['scores']
    assert scores['score'].dtype.kind == 'f'
    assert scores['score'].isna().sum() == 1
    assert pd.api.types.is_string_dtype(scores['note'])


@needsRscript
def test_a_declared_ordered_column_keeps_its_levels_and_becomes_ordered(tmp_path):
    """pyreadr cannot tell an ordered factor from a plain one, so the registry declares it:
    an R factor keeps its level order, a plain column gets sorted levels."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    scores = loader.load(FIXTURE, 'scores', types={'grade': 'ordered'})
    assert scores['grade'].dtype.ordered
    assert list(scores['grade'].cat.categories) == ['low', 'mid', 'high']
    pets = loader.load(FIXTURE, 'pets', types={'age': 'ordered'})
    assert pets['age'].dtype.ordered
    assert list(pets['age'].cat.categories) == sorted(set(pets['age']))


@needsRscript
def test_help_returns_the_rd_page_text(tmp_path):
    loader = Loader(tmp_path, fetch=serveCurrent)
    page = loader.help(FIXTURE, 'pets')
    assert page.startswith('\\name{pets}')
    assert 'Species, age in years and weight in kg of six pets.' in page


def test_licence_is_the_license_field_of_the_packages_description(tmp_path):
    """The registry's `licence` column of a CRAN source comes from the package itself, verbatim;
    the survey normalises it (ADR 0003)."""
    loader = Loader(tmp_path, fetch=serveCurrent)
    assert loader.licence(FIXTURE) == 'CC0'


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
    assert set(objects) == {'pets', 'scores', 'trials', 'visits', 'wide'}
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
    assert len(loader.objects(good)) == 5
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


@needsRscript
def test_base_r_objects_report_the_rscript_route_and_have_help_pages(tmp_path):
    """The survey records the route per object (#19); base R arrives only through R, and its
    help pages come from R's own Rd database since there is no tarball with a man/ folder."""
    base = Source(kind='cran', name='datasets', pin='base')
    loader = Loader(tmp_path, fetch=serveNothing)
    assert objectsByName(loader, base)['iris'].reader == 'rscript'
    page = loader.help(base, 'iris')
    assert '\\alias{iris}' in page
    assert 'Anderson' in page


@needsRscript
def test_base_r_names_differing_in_case_only_both_survive_the_dump(tmp_path):
    """Base R holds CO2 (a grouped table) and co2 (a time series); on a case-insensitive file
    system one `<name>.rds` would overwrite the other, as happened in the #23 pull."""
    base = Source(kind='cran', name='datasets', pin='base')
    loader = Loader(tmp_path, fetch=serveNothing)
    objects = objectsByName(loader, base)
    assert (objects['CO2'].n_rows, objects['CO2'].n_cols) == (84, 5)
    assert (objects['co2'].n_rows, objects['co2'].n_cols) == (468, 1)  # the Mauna Loa series
    assert 'Potvin' in loader.help(base, 'CO2')
    assert 'Mauna Loa' in loader.help(base, 'co2')


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
    page = loader.help(deposit, 'data/schools.csv')
    assert page.startswith('# codebook.txt\n')  # found walking up; the dotfile beside it is no doc
    assert 'school: one of three schools A, B, C' in page


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
    assert {'formats/trials.xlsx', 'formats/visits.json', 'formats/births.dta'} <= set(objects)
    assert {o.reader for o in objects.values()} == {'pandas'}
    trials = loader.load(formats, 'formats/trials.xlsx')
    assert list(trials['arm']) == ['control', 'treated', 'control']
    visits = loader.load(formats, 'formats/visits.json')
    assert list(visits['visits']) == [3, 1, 4, 2]
    births = loader.load(formats, 'formats/births.dta')
    assert list(births['hospital'].cat.categories) == ['north', 'south']
    assert list(births['weight']) == [3.2, 2.9, 3.5, 3.1]


def test_url_without_a_suffix_is_saved_under_the_file_the_frame_names(tmp_path):
    """figshare and OSF serve a file from a URL whose path has no suffix, so the frame says
    what the download is (`file`); the object is named after it and read by that suffix."""
    schools = Source(kind='url', name=SCHOOLS_URL, pin=sha(SCHOOLS), file='schools.csv')
    loader = Loader(tmp_path, fetch=serveFiles)
    objects = objectsByName(loader, schools)
    assert set(objects) == {'schools.csv'}
    df = loader.load(schools, 'schools.csv')
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']


def test_a_stan_data_dict_is_the_table_of_its_observation_length_arrays(tmp_path):
    """posteriordb and the Stan examples keep data as a dict of arrays: the arrays of the modal
    length are the observations and become the columns, an N-row matrix (a design matrix X)
    its numbered columns; scalars (N, J), group-level arrays (u, of length J) and an array of
    three dimensions (Z) are not part of the table. A `.json.zip` holds the same dict zipped.
    A dict without arrays (a descriptor) is no table."""
    stan = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='stan/data')
    loader = Loader(tmp_path, fetch=serveExample)
    objects = objectsByName(loader, stan)
    assert set(objects) == {
        'stan/data/radon.json',
        'stan/data/radon.json.zip',
        'stan/data/meta.json',
    }  # not `radon.init.json`: Stan initial values beside the data are no data
    radon = objects['stan/data/radon.json']
    assert (radon.n_rows, radon.n_cols) == (5, 5)
    assert objects['stan/data/meta.json'].n_rows is None
    df = loader.load(stan, 'stan/data/radon.json.zip')
    assert list(df.columns) == ['county', 'log_radon', 'floor', 'X_1', 'X_2']
    assert list(df['county']) == [1, 1, 2, 2, 2]
    assert list(df['X_2']) == [0, 1, 0, 0, 1]


def test_a_gzipped_tsv_is_read_as_the_tsv_it_wraps(tmp_path):
    """PMLB serves every table as `.tsv.gz`; the wrapper names no format of its own."""
    apnea = Source(kind='url', name=APNEA_URL, pin=sha(APNEA))
    loader = Loader(tmp_path, fetch=serveFiles)
    assert set(objectsByName(loader, apnea)) == {'apnea.tsv.gz'}
    df = loader.load(apnea, 'apnea.tsv.gz')
    assert list(df.columns) == ['Scorer', 'Subject', 'target']
    assert list(df['Subject']) == [1, 1, 2, 2]


def test_arrow_files_in_a_tarball_from_a_suffixless_url_load(tmp_path):
    """MixedModels.jl ships its datasets as one OSF tarball of Arrow files; the frame names the
    download `datasets.tar.gz`, which is extracted, and each `.arrow` is an object."""
    datasets = Source(kind='url', name=DATASETS_URL, pin=sha(DATASETS), file='datasets.tar.gz')
    loader = Loader(tmp_path, fetch=serveFiles)
    objects = objectsByName(loader, datasets)
    assert set(objects) == {'kb07.arrow'}
    assert objects['kb07.arrow'].reader == 'pandas'
    df = loader.load(datasets, 'kb07.arrow')
    assert list(df['subj']) == ['S1', 'S1', 'S2', 'S2']


def test_help_finds_the_same_stem_info_file_and_names_the_dropped_arrays(tmp_path):
    """posteriordb documents `data/data/radon.json.zip` in `data/info/radon.info.json`: a file
    named after the object's stem with a documentation suffix counts in a sibling folder. For a
    Stan data dict the page also says which entries are not in the table, so the reader knows
    the group-level data exist."""
    stan = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='stan/data')
    loader = Loader(tmp_path, fetch=serveExample)
    page = loader.help(stan, 'stan/data/radon.json.zip')
    assert page.startswith('# stan/info/radon.info.json\n{"name": "radon"')
    assert (
        'not in the table: N (scalar), J (scalar), u (length 2), Z (5 x 1 x 2 array); '
        'X is a 5 x 2 matrix'
    ) in page


def test_help_renders_a_stata_files_labels_as_its_codebook(tmp_path):
    """Stata's manual data ship no text beside them, but a `.dta` carries a data label,
    variable labels and value labels, which is the codebook a reader needs."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    page = loader.help(formats, 'formats/births.dta')
    # nothing documents the file within the pinned path: not the data `.txt` beside it, nor the
    # README above the path
    assert page.startswith('# Stata labels\nBirths\n')
    assert 'hospital: Hospital of birth\nweight: Birth weight (kg)\n' in page
    assert 'hospital values: north, south' in page


def test_help_is_empty_where_the_tree_holds_no_documentation(tmp_path):
    """MixedModels.jl's tarball and the PyMC data folder document nothing beside the files;
    the page is then empty rather than an error, the pull adds the first rows, and the
    reading agent is told where the source documents its data."""
    datasets = Source(kind='url', name=DATASETS_URL, pin=sha(DATASETS), file='datasets.tar.gz')
    loader = Loader(tmp_path, fetch=serveFiles)
    assert loader.help(datasets, 'kb07.arrow') == ''


def test_whitespace_aligned_text_and_latin1_text_load(tmp_path):
    """The ARM `.dat` files align their columns with runs of spaces, which the separator
    sniffer miscounts; such a file is read whitespace-separated. A csv in latin-1 (a degree
    sign) is read with the undecodable bytes replaced rather than refused."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    schools = loader.load(formats, 'formats/schools.dat')
    assert list(schools.columns) == ['school', 'estimate', 'sd']
    assert list(schools['estimate']) == [28, 8, -3]
    degrees = loader.load(formats, 'formats/degrees.csv')
    assert list(degrees['site']) == ['A', 'B']
    notes = objectsByName(loader, formats)['formats/notes.csv']
    assert notes.n_rows is None  # a banner above the table: no frame, listed without counts


def test_download_waits_and_retries_after_a_429(monkeypatch):
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
    assert Loader._getBytes('https://osf.io/x/download') == b'content'


def test_padded_delimited_text_loads_with_clean_names_and_missing_values(tmp_path):
    """The ARM `.dat` files separate the header with comma and space and pad every field, so
    a naive read gives ` recovered` as a name and `NA       ` as a string: names and fields
    are stripped, `NA` and empty fields are missing, a column of numbers is numeric. A
    byte-order mark (one pingouin csv) is not part of the first column's name."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    df = loader.load(formats, 'formats/padded.csv')
    assert list(df.columns) == ['group', 'recovered', 'scenario']
    assert list(df['group']) == ['NN', 'NN', 'PP']
    assert df['recovered'].dtype.kind == 'f'
    assert df['recovered'].isna().tolist() == [False, True, False]


def test_a_parquet_file_loads(tmp_path):
    """OpenML serves every dataset as `dataset_<id>.pq`; the Tier O hits come that way."""
    pupils = Source(kind='url', name=PUPILS_URL, pin=sha(PUPILS))
    loader = Loader(tmp_path, fetch=serveFiles)
    assert set(objectsByName(loader, pupils)) == {'dataset_42.pq'}
    df = loader.load(pupils, 'dataset_42.pq')
    assert list(df['school']) == ['GP', 'GP', 'MS']


def test_a_data_txt_is_an_object_and_a_sibling_description_is_not(tmp_path):
    """Textbook companions ship their tables as `.txt` (Zuur, Singer & Willett), so a `.txt`
    is a data object unless it is named like documentation or after a data file of another
    format beside it (Fitzmaurice's `lead.txt` beside `lead.dta`), which describes that file."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    objects = objectsByName(loader, formats)
    assert 'formats/Guber1999data.txt' in objects
    assert 'formats/schools.txt' not in objects
    page = loader.help(formats, 'formats/schools.dat')
    assert page.startswith('# formats/schools.txt\nEstimates of a coaching effect')


def test_a_banner_of_hash_lines_above_the_table_is_skipped(tmp_path):
    """Diggle's course files open with `#` comment lines above a whitespace-aligned table."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    cd4 = loader.load(formats, 'formats/cd4.txt')
    assert list(cd4.columns) == ['time', 'cd4', 'id']
    assert list(cd4['id']) == [1, 1, 2]
    assert loader.help(formats, 'formats/cd4.txt') == '# banner\n#\n# CD4 counts by subject\n#'


def test_a_declared_layout_reads_a_headerless_file(tmp_path):
    """The Bristol CMM `.DAT` files are fixed-width with their columns in a prose `.ASC`, and
    Goldstein's partnership file whitespace-separated with a codes list; the frame declares
    the columns as `name:start-end` (positions from 1) or as bare names."""
    pupils = Source(
        kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats/pupils.dat',
        layout=('school:2-3', 'class:4', 'pupil:5', 'score:6-7'),
    )  # fmt: skip
    loader = Loader(tmp_path, fetch=serveExample)
    df = loader.load(pupils, 'formats/pupils.dat')
    assert list(df.columns) == ['school', 'class', 'pupil', 'score']
    assert list(df['school']) == [11, 11, 22]
    assert list(df['score']) == [7, 9, 8]
    partners = Source(
        kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats/partners.txt',
        layout=('id', 'age', 'status'),
    )  # fmt: skip
    df = loader.load(partners, 'formats/partners.txt')
    assert list(df['id']) == [1, 1, 2]
    assert list(df['status']) == [0, 1, 0]


def test_a_workbook_of_several_sheets_is_one_object_per_data_sheet(tmp_path):
    """Snijders & Bosker's companion is one workbook, a sheet per chapter dataset and a
    `Contents` sheet describing them: each data sheet is an object `<file>!<sheet>`, the
    contents sheet is their help page."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    objects = objectsByName(loader, formats)
    assert 'formats/chapters.xlsx!03A' in objects
    assert 'formats/chapters.xlsx!03B' in objects
    assert 'formats/chapters.xlsx!Contents' not in objects
    assert 'formats/chapters.xlsx' not in objects
    assert 'formats/trials.xlsx' in objects  # a single-sheet workbook is the file
    pupils = loader.load(formats, 'formats/chapters.xlsx!03B')
    assert list(pupils['score']) == [10, 12, 8]
    schools = loader.load(formats, 'formats/chapters.xlsx!03A')
    assert list(schools.columns) == ['school', 'size']  # padded names stripped, as in text files
    page = loader.help(formats, 'formats/chapters.xlsx!03B')
    assert page == '# sheet Contents\n03A\tschools\n03B\tpupils'


def test_an_spss_file_loads_with_its_value_labels_and_documents_itself(tmp_path):
    """Hox's companion is 23 `.sav` files and nothing else: value labels that cover every
    value arrive as a categorical, labels on a scale's extremes alone (`lowest`, `highest`)
    leave the column numeric, and the file's labels are its codebook, rendered as the Stata
    ones."""
    formats = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='formats')
    loader = Loader(tmp_path, fetch=serveExample)
    popular = loader.load(formats, 'formats/popular.sav')
    assert list(popular['sex'].cat.categories) == ['boy', 'girl']
    assert list(popular['popular']) == [5.0, 6.5, 4.0]
    assert list(popular['ses']) == [1, 3, 5]  # labels on the extremes only: no categorical
    page = loader.help(formats, 'formats/popular.sav')
    assert page.startswith('# SPSS labels\nPupils\n')
    assert 'class: Class id\nsex: Pupil sex\nses: SES\npopular: Popularity score\n' in page
    assert 'sex values: boy, girl' in page


# ----------------------------------------------------------------------------------------------
# lean fetch through the manifest (#4)
# ----------------------------------------------------------------------------------------------


def member(archive: bytes, name: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return tar.extractfile(name).read()


RADON = member(EXAMPLE, 'example-c0ffee1/data/radon.csv')
RADON_RAW = 'https://raw.githubusercontent.com/acme/example/c0ffee1/data/radon.csv'


def serveRaw(url: str) -> bytes | None:
    return RADON if url == RADON_RAW else None


def test_a_git_object_is_fetched_alone_from_its_raw_url(tmp_path):
    """With the manifest, a git object is one file at the pinned revision, never the
    repository archive (pymc-examples is 1 GB for a few csv); the cache serves it after."""
    asked = []

    def counting(url: str) -> bytes | None:
        asked.append(url)
        return serveRaw(url) or serveExample(url)

    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    manifest = {(example, 'data/radon.csv'): manifestRow('data/radon.csv', RADON)}
    loader = Loader(tmp_path, fetch=counting, manifest=manifest)
    df = loader.load(example, 'data/radon.csv')
    assert list(df['county']) == ['Anoka', 'Anoka', 'Clay', 'Clay', 'Clay']
    Loader(tmp_path, fetch=counting, manifest=manifest).load(example, 'data/radon.csv')
    assert asked == [RADON_RAW]


def test_a_file_differing_from_its_manifest_checksum_is_refused(tmp_path):
    """A per-file fetch keeps the fetch-only guarantee only if every file is checked against
    the digest the package ships, on cache hits too, where a tampered file would sit."""
    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    good = {(example, 'data/radon.csv'): manifestRow('data/radon.csv', RADON)}
    bad = {(example, 'data/radon.csv'): ManifestRow('data/radon.csv', '0' * 64, len(RADON))}
    Loader(tmp_path, fetch=serveRaw, manifest=good).load(example, 'data/radon.csv')
    with pytest.raises(ValueError, match='checksum'):
        Loader(tmp_path, fetch=serveRaw, manifest=bad).load(example, 'data/radon.csv')


def test_a_url_archive_object_extracts_only_its_file(tmp_path):
    """A deposit zip is downloaded whole (its sha256 is the pin) but only the manifest's file
    leaves it: the codebook and whatever else the deposit holds stay inside the archive. The
    zip's single top-level folder is layout, as on the enumerate path."""
    deposit = Source(kind='url', name=DEPOSIT_URL, pin=DEPOSIT_SHA)
    schools = zipfile.ZipFile(io.BytesIO(DEPOSIT)).read('deposit/data/schools.csv')
    manifest = {(deposit, 'data/schools.csv'): manifestRow('data/schools.csv', schools)}
    loader = Loader(tmp_path, fetch=serveDeposit, manifest=manifest)
    df = loader.load(deposit, 'data/schools.csv')
    assert list(df['score']) == [10.5, 12.0, 9.5, 15.0, 11.0]
    cached = {f.name for f in tmp_path.rglob('*') if f.is_file()}
    assert cached == {'deposit.zip', 'schools.csv'}


def test_a_cran_object_reads_only_its_file_without_rscript(tmp_path, monkeypatch):
    """The tarball comes whole, but only the object's file is checked and read: loading `pets`
    no longer dumps the fixture's `trials.csv` through R, so no Rscript is on the path."""
    monkeypatch.setenv('PATH', '')
    pets = member(TARBALL, 'fixture/data/pets.rda')
    manifest = {(FIXTURE, 'pets'): manifestRow('data/pets.rda', pets)}
    loader = Loader(tmp_path, fetch=serveCurrent, manifest=manifest)
    assert list(loader.load(FIXTURE, 'pets')['species']) == [
        'dog',
        'cat',
        'fish',
        'dog',
        'cat',
        'dog',
    ]


@needsRscript
def test_a_base_r_object_loads_through_the_manifest_from_rs_dump(tmp_path):
    """Base R's `datasets` has no tarball to take a file from: R dumps the namespace as before,
    and the manifest carries no checksum, since the dump is R's output, not a download."""
    base = Source(kind='cran', name='datasets', pin='base')
    manifest = {(base, 'iris'): ManifestRow('data/iris.rds', None, None)}
    loader = Loader(tmp_path, fetch=serveNothing, manifest=manifest)
    assert loader.load(base, 'iris').shape == (150, 5)


@needsRscript
def test_rs_re_save_of_a_url_file_is_no_object_of_its_own(tmp_path):
    """A url that is no archive has its cache folder as its tree, where R's re-save of a file
    librdata rejects lands too; a later enumeration must still name the download, which the
    manifest records (an OSF `.rds` of johannes_2021b came out as the re-save, #4)."""
    visits = member(TARBALL, 'fixture/data/visits.rda')
    url = 'https://example.org/clinic.rda'  # sorts before `rds/`, as `processed_data.rds` did
    source = Source(kind='url', name=url, pin=sha(visits))

    def serveVisits(asked: str) -> bytes | None:
        return visits if asked == url else None

    Loader(tmp_path, fetch=serveVisits).objects(source)  # R re-saves the file into the cache
    objects = Loader(tmp_path, fetch=serveVisits).objects(source)
    assert [(o.name, o.file, o.reader) for o in objects] == [('visits', 'clinic.rda', 'rscript')]


def test_a_git_file_name_with_spaces_is_quoted_in_its_raw_url(tmp_path):
    """ROS keeps `HDI/data/state vote and income, 68-00.dta`; a URL cannot carry the spaces."""
    quoted = 'https://raw.githubusercontent.com/acme/example/c0ffee1/data/radon%20by%20county.csv'

    def serveQuoted(url: str) -> bytes | None:
        return RADON if url == quoted else None

    example = Source(kind='git', name=EXAMPLE_REPO, pin='c0ffee1', path='data')
    manifest = {(example, 'data/radon by county.csv'): manifestRow('data/radon by county.csv', RADON)}  # fmt: skip
    loader = Loader(tmp_path, fetch=serveQuoted, manifest=manifest)
    assert len(loader.load(example, 'data/radon by county.csv')) == 5


@pytest.mark.network
def test_a_server_that_sends_the_wrong_intermediate_certificate_is_verified():
    """Harvard's companion site for Fitzmaurice et al. sends InCommon's intermediate for a leaf
    Sectigo's OV R36 signed; macOS and Windows fetch the right one, OpenSSL does not, so the
    package ships it and the download is verified on every operating system."""
    fev1 = registry.sources()['fitzmaurice_fev1']
    data = Loader._getBytes(fev1.name)
    assert sha(data) == fev1.pin


def test_a_url_its_host_refuses_loads_from_its_mirror_under_the_same_pin(tmp_path):
    """Dryad refuses scripted downloads of CC0 data, so the package mirrors them (ADR 0003): the
    host is asked first, the mirror after, and the mirror's file must carry the pinned digest."""
    asked = []
    mirror = 'https://github.com/acme/mixedbench/releases/download/mirror-1/schools.csv'

    def serveMirror(url: str) -> bytes | None:
        asked.append(url)
        return SCHOOLS if url == mirror else None

    schools = Source(kind='url', name=SCHOOLS_URL, pin=sha(SCHOOLS), file='schools.csv', mirror=mirror)  # fmt: skip
    df = Loader(tmp_path, fetch=serveMirror).load(schools, 'schools.csv')
    assert list(df['school']) == ['A', 'B', 'A', 'C', 'B']
    assert asked == [SCHOOLS_URL, mirror]


@pytest.mark.parametrize('code', [401, 403])
def test_download_takes_a_refusal_as_a_miss(monkeypatch, code):
    """Dryad answers 401 to a script; like a 404 the next location (the mirror) is asked."""

    def urlopen(req, timeout, context):
        raise urllib.error.HTTPError('u', code, 'Unauthorized', {}, None)

    monkeypatch.setattr(urllib.request, 'urlopen', urlopen)
    assert Loader._getBytes('https://datadryad.org/api/v2/files/1/download') is None
