"""The formats at their two seams: `read` turns a file into tables and names its reader,
`isData` says which files of a tree hold data. The fixtures are the extracted archives
`make_fixture.R` and `make_fixtures.py` build: a CRAN-shaped package and a GitHub archive of
the awkward files met in the pull, plus single R files as deposits serve them."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pandas as pd
import pytest
from mixedbench.datasets import readers

FIXTURES = Path(__file__).parent / 'fixtures'


def extracted(tmp_path_factory: pytest.TempPathFactory, archive: str) -> Path:
    dir = tmp_path_factory.mktemp(archive.split('.')[0])
    with tarfile.open(FIXTURES / archive) as tar:
        tar.extractall(dir, filter='data')
    return dir


@pytest.fixture(scope='module')
def package(tmp_path_factory) -> Path:
    """The CRAN-shaped fixture package, extracted."""
    return extracted(tmp_path_factory, 'fixture_1.0.tar.gz') / 'fixture'


@pytest.fixture(scope='module')
def example(tmp_path_factory) -> Path:
    """The GitHub-archive fixture at revision c0ffee1, extracted."""
    return extracted(tmp_path_factory, 'example-c0ffee1.tar.gz') / 'example-c0ffee1'


def readCran(package: Path, file: str) -> tuple[dict[str, pd.DataFrame | None], readers.Reader]:
    return readers.read(package / file, file, cran=True)


def readFixture(name: str) -> tuple[dict[str, pd.DataFrame | None], readers.Reader]:
    return readers.read(FIXTURES / name, name)


def readExample(example: Path, file: str, layout: tuple[str, ...] | None = None) -> pd.DataFrame:
    """The one frame of a file that is not a workbook of several sheets."""
    tables, _ = readers.read(example / file, file, layout=layout)
    return tables[file]


# ==============================================================================================
# R files
# ==============================================================================================


def test_r_factor_levels_keep_r_order(package):
    """pyreadr's own `read_r` sorts factor levels and drops unused ones; the reader restores
    R's order from parser internals, which this test pins (`bird` is an unused level)."""
    tables, reader = readCran(package, 'data/pets.rda')
    pets = tables['pets']
    assert reader == 'pyreadr'
    assert list(pets['species'].cat.categories) == ['dog', 'cat', 'fish', 'bird']
    assert list(pets['species']) == ['dog', 'cat', 'fish', 'dog', 'cat', 'dog']
    assert pets['age'].dtype.kind == 'i' and pets['weight'].dtype.kind == 'f'
    scores = readCran(package, 'data/scores.rds')[0]['scores']
    assert list(scores['grade'].cat.categories) == ['low', 'mid', 'high']
    assert not scores['grade'].dtype.ordered


def test_an_integer_column_with_na_reads_as_float_not_object():
    """pyreadr renders an R integer vector with NA as an object column of ints and NaN, which
    no numeric check accepts (mlmRev's `star`); the reader makes it a float column."""
    # R wrote a frame with an integer column holding one NA and a plain string column
    tables, _ = readFixture('counts.rds')
    counts = tables['counts']
    assert counts['score'].dtype.kind == 'f'
    assert counts['score'].isna().sum() == 1
    assert pd.api.types.is_string_dtype(counts['note'])


def test_an_object_pyreadr_cannot_frame_has_no_table(package):
    """gamlss.data's aep holds a matrix column; the object stays in the census without a
    table rather than failing the whole source."""
    tables, reader = readCran(package, 'data/wide.rda')
    assert (tables, reader) == ({'wide': None}, 'pyreadr')


def test_an_r_file_librdata_rejects_is_read_by_rdata(package):
    """geepack's muscatine is a plain data frame librdata calls an unrecognized object; the
    pure-Python rdata reads it, so no object needs R (ADR 0003, #9)."""
    tables, reader = readCran(package, 'data/visits.rda')
    visits = tables['visits']
    assert reader == 'rdata'
    assert list(visits['clinic'].cat.categories) == ['north', 'south']
    assert list(visits.index) == [0, 1, 2]
    assert visits['count'].dtype == 'int32'  # an R integer, as pyreadr reads one


def test_a_rejected_r_file_keeps_its_frames_and_its_lists_without_a_table():
    """A Tier D `.RData` keeps model fits and lists beside its tables; rdata reads the frame,
    the list has no table, as pyreadr's unframable objects have none."""
    tables, reader = readFixture('fits.rda')
    assert reader == 'rdata'
    assert tables['fit'] is None
    roster = tables['roster']
    assert roster.shape == (3, 2)
    assert list(roster['ward'].cat.categories) == ['a', 'b']
    assert roster['beds'].isna().sum() == 1  # an integer column with NA is float, as pyreadr's


def test_a_rejected_rds_is_named_by_its_file_and_one_rdata_cannot_parse_has_no_table():
    """An .rds holds one unnamed object, named by its file as pyreadr names it; a model fit's
    bytecode, which rdata cannot parse, leaves the file one object without a table rather
    than failing the source."""
    tables, reader = readFixture('roster.rds')
    assert reader == 'rdata'
    assert tables['roster'].shape == (3, 2)
    assert readFixture('fit.rds') == ({'fit': None}, 'rdata')


# ==============================================================================================
# utils::data() files read without R (#8)
# ==============================================================================================


def test_a_data_txt_reads_as_read_table_reads_it(package):
    """agridat ships its tables as `data/*.txt`, which utils::data() reads with
    read.table(header = TRUE, as.is = FALSE): quoted strings become factors with sorted
    levels, `NA` is missing. The reader does the same in Python (ADR 0003)."""
    tables, reader = readCran(package, 'data/plots.txt')
    plots = tables['plots']
    assert reader == 'pandas'
    assert list(plots.columns) == ['field', 'variety', 'plants', 'yield']
    assert list(plots['field']) == ['north A', 'south B', 'north A', 'west']
    assert list(plots['variety'].cat.categories) == ['a', 'b', 'c']
    assert plots['plants'].isna().sum() == 1
    assert list(plots['yield'].dropna()) == [1.5, 2.0, 3.25]


def test_a_data_csv_is_read_with_semicolons(package):
    """utils::data() reads a `.csv` in `data/` with `sep = ';'`, strings as factors."""
    trials = readCran(package, 'data/trials.csv')[0]['trials']
    assert list(trials['arm'].cat.categories) == ['control', 'treated']
    assert list(trials['outcome']) == [0, 1, 1, 1, 0]


def test_a_data_r_file_reads_to_the_frame_r_makes_of_it(package):
    """Base R's `data/*.R` files are deparsed tables; the deparse reader evaluates them to the
    frame R makes (`growth.rda`, saved by make_fixture.R): labels in level order, numeric
    levels sorted as numbers, R's integers, `ordered` dropped as pyreadr drops it."""
    tables, reader = readCran(package, 'data/growth.R')
    twin, _ = readFixture('growth.rda')
    assert reader == 'deparse'
    pd.testing.assert_frame_equal(tables['growth'], twin['growth'])


def test_a_data_r_file_outside_the_deparse_subset_has_no_table(tmp_path):
    """Most of base R's data/*.R files are time series or matrices; enumerating the source
    must not fail on them, as it does not on an R object pyreadr cannot frame."""
    file = tmp_path / 'lynx.R'
    file.write_text('lynx <- stats::ts(c(269, 321))\n')
    assert readers.read(file, 'data/lynx.R', cran=True) == ({'lynx': None}, 'deparse')


# ==============================================================================================
# pandas files (m3#16)
# ==============================================================================================


def test_excel_json_and_stata_files_read(example):
    """The reader follows the extension: Excel, JSON records and Stata, whose value labels
    arrive as a categorical in label order."""
    trials = readExample(example, 'formats/trials.xlsx')
    assert list(trials['arm']) == ['control', 'treated', 'control']
    visits = readExample(example, 'formats/visits.json')
    assert list(visits['visits']) == [3, 1, 4, 2]
    births, reader = readers.read(example / 'formats/births.dta', 'formats/births.dta')
    assert reader == 'pandas'
    assert list(births['formats/births.dta']['hospital'].cat.categories) == ['north', 'south']
    assert list(births['formats/births.dta']['weight']) == [3.2, 2.9, 3.5, 3.1]


def test_a_stan_data_dict_is_the_table_of_its_observation_length_arrays(example):
    """posteriordb and the Stan examples keep data as a dict of arrays: the arrays of the modal
    length are the observations and become the columns, an N-row matrix (a design matrix X)
    its numbered columns; scalars (N, J), group-level arrays (u, of length J) and an array of
    three dimensions (Z) are not part of the table. A `.json.zip` holds the same dict zipped.
    A dict without arrays (a descriptor) is no table."""
    radon = readExample(example, 'stan/data/radon.json')
    zipped = readExample(example, 'stan/data/radon.json.zip')
    pd.testing.assert_frame_equal(radon, zipped)
    assert list(radon.columns) == ['county', 'log_radon', 'floor', 'X_1', 'X_2']
    assert list(radon['county']) == [1, 1, 2, 2, 2]
    assert list(radon['X_2']) == [0, 1, 0, 0, 1]
    assert readExample(example, 'stan/data/meta.json') is None


def test_a_gzipped_tsv_is_read_as_the_tsv_it_wraps():
    """PMLB serves every table as `.tsv.gz`; the wrapper names no format of its own."""
    tables, _ = readFixture('apnea.tsv.gz')
    apnea = tables['apnea.tsv.gz']
    assert list(apnea.columns) == ['Scorer', 'Subject', 'target']
    assert list(apnea['Subject']) == [1, 1, 2, 2]


def test_a_parquet_file_reads():
    """OpenML serves every dataset as `dataset_<id>.pq`; the Tier O hits come that way."""
    tables, _ = readFixture('dataset_42.pq')
    assert list(tables['dataset_42.pq']['school']) == ['GP', 'GP', 'MS']


def test_whitespace_aligned_text_and_latin1_text_read(example):
    """The ARM `.dat` files align their columns with runs of spaces, which the separator
    sniffer miscounts; such a file is read whitespace-separated. A csv in latin-1 (a degree
    sign) is read with the undecodable bytes replaced rather than refused."""
    schools = readExample(example, 'formats/schools.dat')
    assert list(schools.columns) == ['school', 'estimate', 'sd']
    assert list(schools['estimate']) == [28, 8, -3]
    degrees = readExample(example, 'formats/degrees.csv')
    assert list(degrees['site']) == ['A', 'B']
    assert readExample(example, 'formats/notes.csv') is None  # a banner it cannot parse past


def test_padded_delimited_text_reads_with_clean_names_and_missing_values(example):
    """The ARM `.dat` files separate the header with comma and space and pad every field, so
    a naive read gives ` recovered` as a name and `NA       ` as a string: names and fields
    are stripped, `NA` and empty fields are missing, a column of numbers is numeric. A
    byte-order mark (one pingouin csv) is not part of the first column's name."""
    padded = readExample(example, 'formats/padded.csv')
    assert list(padded.columns) == ['group', 'recovered', 'scenario']
    assert list(padded['group']) == ['NN', 'NN', 'PP']
    assert padded['recovered'].dtype.kind == 'f'
    assert padded['recovered'].isna().tolist() == [False, True, False]


def test_a_banner_of_hash_lines_above_the_table_is_skipped(example):
    """Diggle's course files open with `#` comment lines above a whitespace-aligned table."""
    cd4 = readExample(example, 'formats/cd4.txt')
    assert list(cd4.columns) == ['time', 'cd4', 'id']
    assert list(cd4['id']) == [1, 1, 2]


def test_r_write_table_output_reads_with_its_quotes_and_row_names(example):
    """ARM's ideo2.dat is R's write.table output: quoted strings, one holding a space, and row
    names under a header one field short. Quotes delimit a field, as read.table reads them, and
    the row names are no column."""
    ideology = readExample(example, 'formats/ideology.dat')
    assert list(ideology.columns) == ['state', 'score']
    assert list(ideology['state']) == ['NEW HAM', 'NEW HAM', 'NEVADA']


def test_a_declared_layout_reads_a_headerless_file(example):
    """The Bristol CMM `.DAT` files are fixed-width with their columns in a prose `.ASC`, and
    Goldstein's partnership file whitespace-separated with a codes list; the frame declares
    the columns as `name:start-end` (positions from 1) or as bare names."""
    fixed = ('school:2-3', 'class:4', 'pupil:5', 'score:6-7')
    pupils = readExample(example, 'formats/pupils.dat', layout=fixed)
    assert list(pupils.columns) == ['school', 'class', 'pupil', 'score']
    assert list(pupils['school']) == [11, 11, 22]
    assert list(pupils['score']) == [7, 9, 8]
    partners = readExample(example, 'formats/partners.txt', layout=('id', 'age', 'status'))
    assert list(partners['id']) == [1, 1, 2]
    assert list(partners['status']) == [0, 1, 0]


def test_a_workbook_of_several_sheets_is_one_object_per_data_sheet(example):
    """Snijders & Bosker's companion is one workbook, a sheet per chapter dataset and a
    `Contents` sheet describing them: each data sheet is an object `<file>!<sheet>`, the
    contents sheet none; a single-sheet workbook is the file."""
    tables, _ = readers.read(example / 'formats/chapters.xlsx', 'formats/chapters.xlsx')
    assert set(tables) == {'formats/chapters.xlsx!03A', 'formats/chapters.xlsx!03B'}
    assert list(tables['formats/chapters.xlsx!03B']['score']) == [10, 12, 8]
    schools = tables['formats/chapters.xlsx!03A']
    assert list(schools.columns) == ['school', 'size']  # padded names stripped, as in text files
    single, _ = readers.read(example / 'formats/trials.xlsx', 'formats/trials.xlsx')
    assert set(single) == {'formats/trials.xlsx'}


def test_an_spss_file_reads_with_its_value_labels(example):
    """Hox's companion is 23 `.sav` files and nothing else: value labels that cover every
    value arrive as a categorical, labels on a scale's extremes alone (`lowest`, `highest`)
    leave the column numeric."""
    popular = readExample(example, 'formats/popular.sav')
    assert list(popular['sex'].cat.categories) == ['boy', 'girl']
    assert list(popular['popular']) == [5.0, 6.5, 4.0]
    assert list(popular['ses']) == [1, 3, 5]  # labels on the extremes only: no categorical


# ==============================================================================================
# which files hold data
# ==============================================================================================


def test_a_data_txt_is_data_and_a_documentation_txt_is_not(example):
    """Textbook companions ship their tables as `.txt` (Zuur, Singer & Willett), so a `.txt`
    is data unless it is named like documentation or after a data file of another format
    beside it (Fitzmaurice's `lead.txt` beside `lead.dta`), which describes that file."""
    assert readers.isData(example / 'formats/Guber1999data.txt')
    assert not readers.isData(example / 'formats/schools.txt')
    assert not readers.isData(example / 'data/README.md')
    assert not readers.isData(example / '.gitattributes')


def test_stan_initial_values_and_resource_forks_are_no_data(example, tmp_path):
    """Stan initial values sit beside the data dict as `<name>.init.json`; a zip made on macOS
    carries a `__MACOSX` copy of every file."""
    assert readers.isData(example / 'stan/data/radon.json')
    assert not readers.isData(example / 'stan/data/radon.init.json')
    fork = tmp_path / '__MACOSX' / 'radon.csv'
    fork.parent.mkdir()
    fork.write_text('county\n')
    assert not readers.isData(fork)


def test_a_cran_data_folder_holds_what_utils_data_reads(package, tmp_path):
    """utils::data() reads R files, `.R`, `.tab`, `.txt` and `.csv` in `data/` and ignores the
    rest (`datalist`); a text file there is never documentation."""
    assert readers.isData(package / 'data/growth.R', cran=True)
    assert readers.isData(package / 'data/plots.txt', cran=True)
    datalist = tmp_path / 'datalist'
    datalist.write_text('pets\n')
    readme = tmp_path / 'codebook.txt'
    readme.write_text('x y\n1 2\n')
    assert not readers.isData(datalist, cran=True)
    assert readers.isData(readme, cran=True)
