"""readers.py defines which file formats exist, how each becomes tables and which files hold data.

An R file goes through pyreadr (with R's level order restored)
or through the pure-Python rdata where librdata rejects it (_RFile).
A file in a CRAN package's data/ folder is read by utils::data()'s rules (_DataFolder).
Base R's data/*.R files are read by the deparse reader.
Every other format goes through pandas (PandasFile, JsonFile):
one table per file, named by its label, or one per data sheet of a workbook.
The R routes agree on pyreadr's types, so a table is the same whichever reader made it:
an integer int32 (float where it holds NA), a logical bool, a factor in R's level order.
An object that is no table is kept by name as None, so a source still lists it.

pipeline:
---------
a file in a source's tree
-> data, not documentation                               isData
-> its format family, by suffix and folder               read
-> every object of the file as a table (by name)         _RFile | _DataFolder | PandasFile .read
"""

from __future__ import annotations

import gzip
import io
import json
import struct
import warnings
import zipfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import pandas as pd
import pyreadstat
import rdata
from mixedbench.datasets.deparse import Deparse, DeparseError
from pyreadr import LibrdataError, PyreadrError
from pyreadr._pyreadr_parser import PyreadrParser

# =====================================================================================
# file kinds
# =====================================================================================
# the suffixes each reader takes, and the names that point to documentation.
R_FILES = {'.rda', '.rdata', '.rds'}  # meant for pyreadr, or rdata
DATA_FILES = {'.r', '.tab', '.txt', '.csv'}  # meant for utils::data()
TABLE_FILES = {  # meant for pandas
    '.csv', '.tsv', '.tab', '.txt', '.dat', '.xlsx', '.xls', '.json', '.dta', '.sav',
    '.arrow', '.pq',
}  # fmt: skip
DOC_STEMS = ('readme', 'codebook', 'description', 'notes', 'metadata', 'variables', 'dictionary')
Reader = Literal['pyreadr', 'rdata', 'pandas', 'deparse']


# =====================================================================================
# helpers
# =====================================================================================
# the three calls the loader makes, and the name helpers shared with the survey.
def read(
    file: Path, label: str, *, layout: tuple[str, ...] | None = None, cran: bool = False
) -> tuple[dict[str, pd.DataFrame | None], Reader]:
    """The file's objects as tables, by name, and the reader that read them."""
    if file.suffix.lower() in R_FILES:
        return _RFile.read(file)
    if cran:
        return _DataFolder.read(file)
    return PandasFile.read(file, label, layout), 'pandas'


def isData(file: Path, *, cran: bool = False) -> bool:
    """What utils::data() reads in a CRAN package's data/ folder, elsewhere what R or pandas
    read less documentation, and never Stan initial values or a zip's resource forks."""
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


def numbers(values: pd.Series) -> pd.Series:
    """Text as numbers, typed as pd.to_numeric types them,
    a float by Python's float(), which rounds correctly on every platform."""
    typed = pd.to_numeric(values)
    if typed.dtype != 'float64':
        return typed
    # pandas' own conversion is not correctly rounded, and computes in long double,
    # 80-bit on x86 and 64-bit on ARM: an ulp off, on each platform for other numbers
    return values.astype('float64')


def _readText(read: Callable[..., pd.DataFrame], file: Path, **options) -> pd.DataFrame:
    """A pandas text reader's table, its float columns read again as text and made numbers."""
    table = read(file, **options)
    floats = table.columns[table.dtypes == 'float64']
    text = read(file, **options, dtype={column: str for column in floats})
    return table.assign(**{column: numbers(text[column]) for column in floats})


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
class _RFile:
    """An .rda, .RData or .rds file, through pyreadr, or through rdata where librdata refuses."""

    R_ERRORS = (PyreadrError, LibrdataError, IndexError)
    RDATA_ERRORS = (ValueError, AssertionError)
    FRAME_CLASSES = r'Missing constructor for R class "(data\.table|tbl_df|tbl)"'

    @staticmethod
    def read(path: Path) -> tuple[dict[str, pd.DataFrame | None], Reader]:
        try:
            return _RFile._pyreadr(path), 'pyreadr'
        except _RFile.R_ERRORS:
            return _RFile._rdata(path), 'rdata'

    # ------------------------------------------------------------------------------------------
    # file -> pyreadr | rdata -> tables
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def _pyreadr(path: Path) -> dict[str, pd.DataFrame | None]:
        """Like `pyreadr.read_r`, but factor levels keep R's order
        and an object pyreadr cannot turn into a DataFrame is None."""
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
            tables[name] = _RFile._numbersAsFloat(table)
        return tables

    @staticmethod
    def _numbersAsFloat(table: pd.DataFrame) -> pd.DataFrame:
        """An object column of ints and NaN, pyreadr's R integer vector with NA, becomes float."""
        numbers = {}
        for column in table.columns[table.dtypes == object]:
            present = table[column].dropna()
            if present.map(lambda v: isinstance(v, (int, float))).all():
                numbers[column] = pd.to_numeric(table[column])
        return table.assign(**numbers)

    @staticmethod
    def _rdata(path: Path) -> dict[str, pd.DataFrame | None]:
        """Through the pure-Python rdata, where a list or a model fit is no table."""
        try:
            objects = _RFile._rdataObjects(path)
        except _RFile.RDATA_ERRORS:
            return {path.stem: None}
        tables = {}
        for name, value in objects.items():
            if name.startswith('.'):  # R's hidden objects (`.Random.seed`), left out as ls() does
                continue
            tables[name] = None
            if isinstance(value, pd.DataFrame):
                # R's integer row names, 1-based or a subset's, as pyreadr's 0-based range
                tables[name] = _RFile._pyreadrTypes(value.reset_index(drop=True))
        return tables

    @staticmethod
    def _rdataObjects(path: Path) -> dict:
        """An .rds holds one object, named by the file as `_pyreadr` names it."""
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', _RFile.FRAME_CLASSES, UserWarning)
            if path.suffix.lower() == '.rds':
                return {path.stem: rdata.read_rds(path)}
            return rdata.read_rda(path)

    @staticmethod
    def _pyreadrTypes(table: pd.DataFrame) -> pd.DataFrame:
        """The nullable dtypes of rdata as pyreadr's: an R integer column int32, a logical bool,
        either float where it holds NA, a string column pandas' default string."""
        types = {}
        for column in table.columns[table.dtypes == 'Int32']:
            types[column] = 'int32'
        for column in table.columns[table.dtypes == 'boolean']:
            types[column] = 'bool'
        for column in list(types):
            if table[column].isna().any():
                types[column] = 'float64'
        for column in table.columns[table.dtypes == 'string']:
            types[column] = 'str'
        return table.astype(types)


# =====================================================================================
# a CRAN package's data/ folder
# =====================================================================================
class _DataFolder:
    """A text or .R file in a CRAN package's data/ folder, read as utils::data() reads it."""

    R_LOGICALS = {
        'T': True, 'TRUE': True, 'true': True, 'True': True,
        'F': False, 'FALSE': False, 'false': False, 'False': False,
    }  # fmt: skip

    @staticmethod
    def read(file: Path) -> tuple[dict[str, pd.DataFrame | None], Reader]:
        if file.suffix.lower() == '.r':
            return _DataFolder._deparse(file), 'deparse'
        return _DataFolder._readTable(file), 'pandas'

    # ------------------------------------------------------------------------------------------
    # file -> deparse | read.table -> tables
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def _deparse(file: Path) -> dict[str, pd.DataFrame | None]:
        try:
            return Deparse(file).tables()
        except DeparseError:  # most of base R's data/*.R files: time series, matrices
            return {file.stem: None}

    @staticmethod
    def _readTable(file: Path) -> dict[str, pd.DataFrame | None]:
        """read.table(header = TRUE, as.is = FALSE), with `sep = ';'` for a `.csv`.
        Levels sort by code point, as R sorts them in the C locale, not by ICU collation."""
        sep = r'\s+'
        if file.suffix.lower() == '.csv':
            sep = ';'
        options = {'sep': sep, 'quotechar': '"', 'na_values': ['NA'], 'keep_default_na': False}
        table = _readText(pd.read_csv, file, **options)
        return {file.stem: table.assign(**_DataFolder._typeConvert(table))}

    @staticmethod
    def _typeConvert(table: pd.DataFrame) -> dict[str, pd.Series]:
        """R's type.convert on the columns pandas read: integers int32 (float where they hold NA),
        logicals and factors as R types them."""
        converted = {}
        for column in table.columns[table.dtypes == 'int64']:
            converted[column] = table[column].astype('int32')
        for column in table.columns[table.dtypes.map(pd.api.types.is_string_dtype)]:
            converted[column] = _DataFolder._logicalOrFactor(table[column])
        return converted

    @staticmethod
    def _logicalOrFactor(values: pd.Series) -> pd.Series:
        """A column of R's logical spellings (`T`, `FALSE`) is bool, or float where it holds NA."""
        present = set(values.dropna())
        if not present <= set(_DataFolder.R_LOGICALS):
            return values.astype('category')
        logical = values.map(_DataFolder.R_LOGICALS)
        if logical.isna().any():
            return logical.astype('float64')
        return logical.astype('bool')


# =====================================================================================
# pandas files
# =====================================================================================
class PandasFile:
    """Any other file, through pandas: one table named by its label,
    or one per data sheet of a workbook."""

    # the names of a workbook's codebook sheets
    NOTE_SHEETS = ('contents', 'readme', 'codebook', 'notes', 'description')

    # ------------------------------------------------------------------------------------------
    # file -> workbook | layout | extension -> tables
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def read(
        file: Path, label: str, layout: tuple[str, ...] | None
    ) -> dict[str, pd.DataFrame | None]:
        """`layout` declares the columns of a headerless text file."""
        if bare(file).suffix in ('.xlsx', '.xls'):
            return PandasFile._readWorkbook(file, label)
        if layout is not None:
            return {label: PandasFile._readLayout(file, layout)}
        return {label: PandasFile._readByExtension(file)}

    @staticmethod
    def _readWorkbook(file: Path, label: str) -> dict[str, pd.DataFrame | None]:
        """One object per data sheet, `<label>!<sheet>`, a workbook of one data sheet the file.
        Sheets named like documentation (`Contents`) and empty ones (`Sheet2`) are none."""
        sheets = pd.read_excel(file, sheet_name=None)
        data = []
        for name, table in sheets.items():
            if not PandasFile.isNoteSheet(name) and len(table):
                data.append(name)
        objects = {}
        for name in data:
            key = f'{label}!{name}'
            if len(data) == 1:
                key = label
            # names stripped as in text files
            objects[key] = sheets[name].rename(columns=lambda c: str(c).strip())
        return objects

    @staticmethod
    def isNoteSheet(name: str) -> bool:
        return any(stem in name.lower() for stem in PandasFile.NOTE_SHEETS)

    @staticmethod
    def _readLayout(file: Path, layout: tuple[str, ...]) -> pd.DataFrame:
        """`name:start-end` entries are fixed-width columns, plain names whitespace-separated ones.
        Character positions count from 1, as layout sheets do."""
        names, spans = [], []
        for entry in layout:
            name, _, span = entry.partition(':')
            names.append(name)
            if span:
                start, _, end = span.partition('-')
                spans.append((int(start) - 1, int(end or start)))
        if spans:
            return _readText(pd.read_fwf, file, colspecs=spans, names=names, header=None)
        return _readText(pd.read_csv, file, sep=r'\s+', names=names, header=None)

    @staticmethod
    def _readByExtension(file: Path) -> pd.DataFrame | None:
        suffix = bare(file).suffix
        if suffix == '.json':
            return JsonFile.read(file)
        if suffix == '.dta':
            return PandasFile._readStata(file)
        if suffix == '.sav':
            return PandasFile._readSpss(file)
        if suffix == '.arrow':
            return pd.read_feather(file)
        if suffix == '.pq':
            return pd.read_parquet(file)
        return PandasFile._readDelimited(file)

    @staticmethod
    def _readStata(file: Path) -> pd.DataFrame:
        """Read by pandas, or by pyreadstat where pandas misparses the value-label section,
        with the labels applied the same way."""
        try:
            return pd.read_stata(file)
        except struct.error:
            labeled = {'apply_value_formats': True, 'formats_as_category': True}
            table, _ = pyreadstat.read_dta(str(file), **labeled)
            return table

    @staticmethod
    def _readSpss(file: Path) -> pd.DataFrame:
        """Value labels that cover every value of a column make it a categorical in code order.
        Labels on a scale's extremes alone (`lowest`, `highest`) leave it numeric."""
        table, meta = pyreadstat.read_sav(str(file))
        labeled = {}
        for column, labels in meta.variable_value_labels.items():
            present = set(table[column].dropna())
            if present <= set(labels):  # pandas would make every value a category
                levels = [labels[code] for code in sorted(labels)]
                labeled[column] = pd.Categorical(table[column].map(labels), categories=levels)
        return table.assign(**labeled)

    @staticmethod
    def _readDelimited(file: Path) -> pd.DataFrame | None:
        """The separator sniffed, or whitespace where the header holds none of the usual ones.
        A `#` banner above the table is skipped, and what does not parse is no table."""
        # undecodable bytes (a latin-1 degree sign) replaced, a byte-order mark dropped
        options = {'encoding': 'utf-8-sig', 'encoding_errors': 'replace'}
        lines, header = PandasFile.banner(file)
        # the sniffer needs the python engine, which ignores quotes under a regex separator; the C
        # engine honors them, as read.table does (R's write.table output)
        sep, engine = None, 'python'
        if not any(mark in header for mark in ',;\t|'):  # columns aligned with runs of spaces
            sep, engine = r'\s+', 'c'
        try:  # pandas opens a `.gz` itself
            table = _readText(
                pd.read_csv, file, sep=sep, skiprows=len(lines), engine=engine, **options
            )
        except pd.errors.ParserError:
            return None
        return PandasFile._tidyText(table)

    @staticmethod
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

    @staticmethod
    def _tidyText(table: pd.DataFrame) -> pd.DataFrame:
        """Padded names and fields (`NA       `) stripped,
        so that a column of numbers with `NA` is numeric with missing values."""
        table = table.rename(columns=lambda name: str(name).strip())
        tidy = {}
        for column in table.columns[table.dtypes.map(pd.api.types.is_string_dtype)]:
            values = table[column].str.strip().replace({'': None, 'NA': None})
            parsed = pd.to_numeric(values, errors='coerce')
            if parsed.notna().sum() == values.notna().sum():  # every present value a number
                values = numbers(values)
            tidy[column] = values
        return table.assign(**tidy)


# =====================================================================================
# JSON files
# =====================================================================================
class JsonFile:
    """A .json or .json.zip file: JSON records, or a Stan data dict as the table of its
    observations."""

    # ------------------------------------------------------------------------------------------
    # file -> dict -> observations -> table
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def read(file: Path) -> pd.DataFrame | None:
        data = JsonFile.unwrap(file)
        content = json.loads(data)
        if not isinstance(content, dict):
            return pd.read_json(io.BytesIO(data), precise_float=True)
        return JsonFile._observations(content)

    @staticmethod
    def unwrap(file: Path) -> bytes:
        if file.suffix.lower() != '.zip':
            return file.read_bytes()
        with zipfile.ZipFile(file) as z:
            member = z.namelist()[0]
            return z.read(member)

    @staticmethod
    def _observations(content: dict) -> pd.DataFrame | None:
        """The arrays of the modal length are the columns, a dict without arrays no table.
        Scalars, arrays of another length and of three or more dimensions are no columns."""
        n = JsonFile.observationLength(content)
        if n is None:
            return None
        columns = {}
        for name, value in content.items():
            if not isinstance(value, list) or len(value) != n:
                continue
            depth = JsonFile.arrayDepth(value)
            if depth > 2:
                continue
            if depth == 2:  # a matrix, one row per observation, as numbered columns
                for k in range(len(value[0])):
                    columns[f'{name}_{k + 1}'] = [row[k] for row in value]
            else:
                columns[name] = value
        return pd.DataFrame(columns)

    @staticmethod
    def observationLength(content: dict) -> int | None:
        """The modal length of the dict's arrays, a Stan data dict's number of observations.
        A tie goes to the longer length, since observations outnumber groups."""
        lengths = Counter(len(value) for value in content.values() if isinstance(value, list))
        if not lengths:
            return None
        return max(lengths, key=lambda length: (lengths[length], length))

    @staticmethod
    def arrayDepth(value: list) -> int:
        """Dimensions of a nested array: 1 for a vector, 2 for a matrix, and so on."""
        return len(JsonFile.arrayShape(value))

    @staticmethod
    def arrayShape(value: list) -> list[int]:
        shape = []
        while isinstance(value, list):
            shape.append(len(value))
            value = value[0] if value else None
        return shape
