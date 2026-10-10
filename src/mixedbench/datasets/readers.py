"""readers.py defines which file formats exist, how each becomes tables and which files hold data.

An R file goes through pyreadr (with R's level order restored)
or through the pure-Python rdata where librdata rejects it.
A file in a CRAN package's data/ folder is read by utils::data()'s rules.
Base R's data/*.R files are read by the deparse reader.
Every other format goes through pandas:
one table per file, named by its label, or one per data sheet of a workbook.

pipeline:
---------
a file in a source's tree
-> data, not documentation                               isData
-> its reader, by suffix and folder                      read
-> every object of the file as a table (by name)         _readR | _readRdata | Deparse.tables |
                                                         _readData | _readWorkbook | _readLayout |
                                                         _readTable
"""

from __future__ import annotations

import gzip
import io
import json
import struct
import warnings
import zipfile
from pathlib import Path
from typing import Literal

import pandas as pd
import pyreadstat
import rdata
from mixedbench.datasets.deparse import Deparse, DeparseError
from pyreadr import LibrdataError, PyreadrError
from pyreadr._pyreadr_parser import PyreadrParser

# =====================================================================================
# file kinds and R errors
# =====================================================================================
# the suffices each reader takes, and the names that point to documentation.
R_FILES = {'.rda', '.rdata', '.rds'}  # meant for pyreadr, or rdata
DATA_FILES = {'.r', '.tab', '.txt', '.csv'}  # meant for utils::data()
TABLE_FILES = {  # meant for pandas
    '.csv', '.tsv', '.tab', '.txt', '.dat', '.xlsx', '.xls', '.json', '.dta', '.sav',
    '.arrow', '.pq',
}  # fmt: skip
DOC_STEMS = ('readme', 'codebook', 'description', 'notes', 'metadata', 'variables', 'dictionary')
NOTE_SHEETS = ('contents', 'readme', 'codebook', 'notes', 'description')  # a workbook's codebook
Reader = Literal['pyreadr', 'rdata', 'pandas', 'deparse']
R_ERRORS = (PyreadrError, LibrdataError, IndexError)
RDATA_ERRORS = (ValueError, AssertionError)
FRAME_CLASSES = r'Missing constructor for R class "(data\.table|tbl_df|tbl)"'


# =====================================================================================
# helpers
# =====================================================================================
# the two calls the loader makes, and the name helpers shared with the survey.
def read(
    file: Path, label: str, *, layout: tuple[str, ...] | None = None, cran: bool = False
) -> tuple[dict[str, pd.DataFrame | None], Reader]:
    """The file's objects as tables, by name, and the reader that read them.
    A file other than a workbook is one object, named by its `label`.
    `layout` declares the columns of a headerless text file."""
    suffix = file.suffix.lower()
    if suffix in R_FILES:
        try:
            return _readR(file), 'pyreadr'
        except R_ERRORS:
            return _readRdata(file), 'rdata'
    if cran and suffix == '.r':
        try:
            return Deparse(file).tables(), 'deparse'
        except DeparseError:  # most of base R's data/*.R files: time series, matrices
            return {file.stem: None}, 'deparse'
    if cran:
        return _readData(file), 'pandas'
    if bare(file).suffix in ('.xlsx', '.xls'):
        return _readWorkbook(file, label), 'pandas'
    if layout is not None:
        return {label: _readLayout(file, layout)}, 'pandas'
    return {label: _readTable(file)}, 'pandas'


def isData(file: Path, *, cran: bool = False) -> bool:
    """In a CRAN package's data/ folder, what utils::data() reads.
    Elsewhere what R or pandas read, less the text files that document data,
    and never Stan initial values beside a data dict or a zip's resource forks."""
    readable = R_FILES | TABLE_FILES
    if cran:
        readable = R_FILES | DATA_FILES
    if bare(file).suffix not in readable:
        return False
    if file.name.endswith('.init.json') or '__MACOSX' in file.parts:
        return False
    if cran:
        return True
    return not isDoc(file) and not _describesSibling(file)


def isDoc(file: Path) -> bool:
    """Markdown and reST, a `.txt` named like documentation (`codebook.txt`),
    and a suffix-less file in capitals (`README`, `LICENSE`), but no dotfile."""
    suffix = file.suffix.lower()
    if suffix in ('.md', '.rst'):
        return True
    if suffix == '.txt':
        return any(stem in file.stem.lower() for stem in DOC_STEMS)
    return suffix == '' and file.name.isupper()


def _describesSibling(file: Path) -> bool:
    """A `.txt` named after a data file of another format beside it
    (`lead.txt` beside `lead.dta`) describes that file."""
    if file.suffix.lower() != '.txt':
        return False
    siblings = [f for f in file.parent.iterdir() if f.is_file() and f != file]
    return any(bare(f).stem == file.stem.lower() for f in siblings)


def bare(file: Path) -> Path:
    """The file's name without its `.zip` or `.gz` wrapper (`radon.json.zip`, `apnea.tsv.gz`):
    the suffix says how to read it, the stem what documents it."""
    return Path(file.name.lower().removesuffix('.zip').removesuffix('.gz'))


# =====================================================================================
# R files
# =====================================================================================
# pyreadr first, with R's level order restored; the pure-Python rdata where librdata refuses.
def _readR(path: Path) -> dict[str, pd.DataFrame | None]:
    """`pyreadr.read_r`, except that factor levels keep R's order
    and that an object pyreadr cannot turn into a DataFrame is None.
    A file librdata rejects raises."""
    parser = PyreadrParser()
    parser.parse(bytes(path))
    tables = {}
    for parsed in parser.table_data:
        name = parsed.name or path.stem  # an .rds carries no object name
        if parsed.dim_num > 2:  # an array, which pyreadr hands to xarray
            tables[name] = None
            continue
        try:
            table = parsed.convert_to_dataframe()
        except PyreadrError:  # a matrix column
            tables[name] = None
            continue
        for position, labels in parsed.value_labels.items():  # {column: {code: label}}
            column = table.columns[position]
            levels = [labels[code] for code in sorted(labels)]  # R orders levels by code
            # pyreadr used astype('category'), which sorts levels and drops unused ones
            table[column] = table[column].cat.set_categories(levels)
        tables[name] = _numbersAsFloat(table)
    return tables


def _numbersAsFloat(table: pd.DataFrame) -> pd.DataFrame:
    """pyreadr renders an R integer vector with NA as an object column of ints and NaN.
    Such a column becomes float, a string column stays as it is."""
    numbers = {}
    for column in table.columns[table.dtypes == object]:
        present = table[column].dropna()
        if present.map(lambda v: isinstance(v, (int, float))).all():
            numbers[column] = pd.to_numeric(table[column])
    return table.assign(**numbers)


def _readRdata(path: Path) -> dict[str, pd.DataFrame | None]:
    """An R file librdata rejects, through the pure-Python rdata.
    A list or a model fit is no table."""
    try:
        objects = _rdataObjects(path)
    except RDATA_ERRORS:
        return {path.stem: None}
    tables = {}
    for name, value in objects.items():
        if name.startswith('.'):  # R's hidden objects (`.Random.seed`), left out as ls() does
            continue
        tables[name] = None
        if isinstance(value, pd.DataFrame):
            # R's integer row names, 1-based or a subset's, as pyreadr's 0-based range
            tables[name] = _pyreadrTypes(value.reset_index(drop=True))
    return tables


def _rdataObjects(path: Path) -> dict:
    """An .rds holds one object, named by the file as `_readR` names it."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', FRAME_CLASSES, UserWarning)
        if path.suffix.lower() == '.rds':
            return {path.stem: rdata.read_rds(path)}
        return rdata.read_rda(path)


def _pyreadrTypes(table: pd.DataFrame) -> pd.DataFrame:
    """rdata's nullable dtypes as pyreadr's: an R integer column int32,
    float where it holds NA (`_numbersAsFloat`), a string column pandas' default string."""
    types = {}
    for column in table.columns[table.dtypes == 'Int32']:
        types[column] = 'int32'
        if table[column].isna().any():
            types[column] = 'float64'
    for column in table.columns[table.dtypes == 'string']:
        types[column] = 'str'
    return table.astype(types)


# =====================================================================================
# utils::data() text files
# =====================================================================================
# a CRAN package's data/ text files, read as R reads them, without R.
def _readData(file: Path) -> dict[str, pd.DataFrame | None]:
    """A CRAN package's `data/*.txt`, `.tab` or `.csv` as utils::data() reads it:
    read.table(header = TRUE, as.is = FALSE), with `sep = ';'` for a `.csv`.
    Strings become categoricals with levels in code-point order, as read.table sorts them
    in the C locale, not by the ICU collation of R's default locale."""
    sep = r'\s+'
    if file.suffix.lower() == '.csv':
        sep = ';'
    table = pd.read_csv(file, sep=sep, quotechar='"', na_values=['NA'], keep_default_na=False)
    strings = table.columns[table.dtypes.map(pd.api.types.is_string_dtype)]
    factors = {column: table[column].astype('category') for column in strings}
    return {file.stem: table.assign(**factors)}


# =====================================================================================
# pandas files
# =====================================================================================
# every other format: one object per file, except a workbook's data sheets.
def _readWorkbook(file: Path, label: str) -> dict[str, pd.DataFrame | None]:
    """One object per data sheet, `<label>!<sheet>`, names stripped as in text files.
    A workbook of one data sheet is the file.
    Sheets named like documentation (`Contents`) and empty ones (Excel's default `Sheet2`)
    are none."""
    sheets = pd.read_excel(file, sheet_name=None)
    data = [name for name, table in sheets.items() if not isNoteSheet(name) and len(table)]
    objects = {}
    for name in data:
        key = f'{label}!{name}'
        if len(data) == 1:
            key = label
        objects[key] = sheets[name].rename(columns=lambda c: str(c).strip())
    return objects


def isNoteSheet(name: str) -> bool:
    return any(stem in name.lower() for stem in NOTE_SHEETS)


def _readLayout(file: Path, layout: tuple[str, ...]) -> pd.DataFrame:
    """A headerless text file read as its source declares it:
    `name:start-end` entries are fixed-width columns, plain names whitespace-separated ones.
    Character positions count from 1, as layout sheets do."""
    names, spans = [], []
    for entry in layout:
        name, _, span = entry.partition(':')
        names.append(name)
        if span:
            start, _, end = span.partition('-')
            spans.append((int(start) - 1, int(end or start)))
    if spans:
        return pd.read_fwf(file, colspecs=spans, names=names, header=None)
    return pd.read_csv(file, sep=r'\s+', names=names, header=None)


def _readTable(file: Path) -> pd.DataFrame | None:
    """pandas by extension, None where the file holds no table."""
    suffix = bare(file).suffix
    if suffix == '.json':
        return _readJson(unwrap(file))
    if suffix == '.dta':
        return _readStata(file)
    if suffix == '.sav':
        return _readSpss(file)
    if suffix == '.arrow':
        return pd.read_feather(file)
    if suffix == '.pq':
        return pd.read_parquet(file)
    return _readDelimited(file)


def unwrap(file: Path) -> bytes:
    """The file's content, out of its `.zip` wrapper where it has one."""
    if file.suffix.lower() != '.zip':
        return file.read_bytes()
    with zipfile.ZipFile(file) as z:
        member = z.namelist()[0]
        return z.read(member)


def _readStata(file: Path) -> pd.DataFrame:
    """pandas, except for a file whose value-label section it misparses,
    which pyreadstat reads with the labels applied the same way."""
    try:
        return pd.read_stata(file)
    except struct.error:
        table, _ = pyreadstat.read_dta(
            str(file), apply_value_formats=True, formats_as_category=True
        )
        return table


def _readSpss(file: Path) -> pd.DataFrame:
    """A column whose value labels cover every value it holds becomes a categorical in code order.
    Labels on a scale's extremes alone (`lowest`, `highest` on a numeric score) leave it numeric,
    where pandas would make every value a category."""
    table, meta = pyreadstat.read_sav(str(file))
    labelled = {}
    for column, labels in meta.variable_value_labels.items():
        present = set(table[column].dropna())
        if present <= set(labels):
            levels = [labels[code] for code in sorted(labels)]
            labelled[column] = pd.Categorical(table[column].map(labels), categories=levels)
    return table.assign(**labelled)


def _readDelimited(file: Path) -> pd.DataFrame | None:
    """The separator sniffed, unless the header holds none of the usual ones:
    columns aligned with runs of spaces are then read whitespace-separated,
    which the sniffer would miscount.
    A banner of `#` lines above the table is skipped, and what does not parse is no table.
    Undecodable bytes (a latin-1 degree sign) are replaced, a byte-order mark dropped.
    pandas opens a `.gz` itself."""
    options = {'encoding': 'utf-8-sig', 'encoding_errors': 'replace'}
    lines, header = banner(file)
    # the sniffer needs the python engine, which ignores quotes under a regex separator; the C
    # engine honours them, as read.table does (R's write.table output)
    sep, engine = None, 'python'
    if not any(mark in header for mark in ',;\t|'):
        sep, engine = r'\s+', 'c'
    try:
        table = pd.read_csv(file, sep=sep, skiprows=len(lines), engine=engine, **options)
    except pd.errors.ParserError:
        return None
    return _tidyText(table)


def banner(file: Path) -> tuple[list[str], str]:
    """The lines starting with `#` that open the file, and the header line after them."""
    opener = open
    if file.suffix.lower() == '.gz':
        opener = gzip.open
    lines = []
    with opener(file, 'rb') as f:
        for raw in f:
            line = raw.decode('utf-8', errors='replace')
            if not line.startswith('#'):
                return lines, line
            lines.append(line.rstrip())
    return lines, ''


def _tidyText(table: pd.DataFrame) -> pd.DataFrame:
    """Padded fields (`idnum, state`, `NA       `) stripped,
    so that a name is the name and a column of numbers with `NA` is numeric with missing values."""
    table = table.rename(columns=lambda name: str(name).strip())
    tidy = {}
    for column in table.columns[table.dtypes.map(pd.api.types.is_string_dtype)]:
        values = table[column].str.strip().replace({'': None, 'NA': None})
        numbers = pd.to_numeric(values, errors='coerce')
        if numbers.notna().sum() == values.notna().sum():  # every present value a number
            values = numbers
        tidy[column] = values
    return table.assign(**tidy)


# -------------------------------------------------------------------------------------
# JSON: records, or a Stan data dict
# -------------------------------------------------------------------------------------
def _readJson(data: bytes) -> pd.DataFrame | None:
    """JSON records as pandas reads them,
    a Stan data dict as the table of its arrays of the modal length, the observations.
    Scalars, arrays of another length (group-level data) and arrays of three or more dimensions
    are no columns, an N-row matrix is its numbered columns (`X_1`, `X_2`).
    A dict without arrays (a descriptor) is no table."""
    content = json.loads(data)
    if not isinstance(content, dict):
        return pd.read_json(io.BytesIO(data))
    n = observationLength(content)
    if n is None:
        return None
    columns = {}
    for name, value in content.items():
        if not isinstance(value, list) or len(value) != n:
            continue
        depth = arrayDepth(value)
        if depth > 2:
            continue
        if depth == 2:  # a matrix, one row per observation
            for k in range(len(value[0])):
                columns[f'{name}_{k + 1}'] = [row[k] for row in value]
        else:
            columns[name] = value
    return pd.DataFrame(columns)


def observationLength(content: dict) -> int | None:
    """The modal length of the dict's arrays, a Stan data dict's number of observations."""
    lengths = [len(value) for value in content.values() if isinstance(value, list)]
    if not lengths:
        return None
    return max(set(lengths), key=lengths.count)


def arrayDepth(value: list) -> int:
    """Dimensions of a nested array: 1 for a vector, 2 for a matrix, and so on."""
    return len(arrayShape(value))


def arrayShape(value: list) -> list[int]:
    shape = []
    while isinstance(value, list):
        shape.append(len(value))
        value = value[0] if value else None
    return shape
