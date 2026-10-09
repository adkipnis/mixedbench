"""File to frames, by format, and which files of a tree hold data: R files through pyreadr,
or rdata where librdata rejects one; a CRAN package's data/ folder as utils::data() reads it;
delimited and fixed-width text, Excel workbooks, JSON records and Stan data dicts, SPSS, Stata
and Arrow through pandas."""

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

R_FILES = {'.rda', '.rdata', '.rds'}  # meant for pyreadr, or rdata
_DATA_FILES = {'.r', '.tab', '.txt', '.csv'}  # meant for utils::data()
TABLE_FILES = {  # meant for pandas
    '.csv', '.tsv', '.tab', '.txt', '.dat', '.xlsx', '.xls', '.json', '.dta', '.sav',
    '.arrow', '.pq', '.parquet',
}  # fmt: skip
DOC_STEMS = ('readme', 'codebook', 'description', 'notes', 'metadata', 'variables', 'dictionary')
NOTE_SHEETS = ('contents', 'readme', 'codebook', 'notes', 'description')  # a workbook's codebook
# LibrdataError is not a PyreadrError; the IndexError is pyreadr's value-label handler indexing
# past the column names of a labelled data frame inside an .RData (a Tier D deposit, 2026-10-08)
_R_ERRORS = (PyreadrError, LibrdataError, IndexError)
# rdata on what it cannot parse: bytecode and ALTREP in the Tier D deposits' model fits, an
# object type it does not know (ValueError); an environment (boot's cd4.nested, AssertionError)
RDATA_ERRORS = (ValueError, AssertionError)
# a class rdata has no constructor for, read as the data frame it extends
FRAME_CLASSES = r'Missing constructor for R class "(data\.table|tbl_df|tbl)"'
Reader = Literal['pyreadr', 'rdata', 'pandas', 'deparse']
Frames = dict[str, pd.DataFrame | None]  # object name -> its table; None when it has no table


def read(
    file: Path, label: str, *, layout: tuple[str, ...] | None = None, cran: bool = False
) -> tuple[Frames, Reader]:
    """The file's objects and its route. An R file through pyreadr, or rdata where librdata
    rejects it (geepack's muscatine, a plain data frame); a file in a CRAN package's data/
    folder by utils::data()'s rules; any other file one object named by its `label`, or one per
    sheet of a workbook, read by pandas as `layout` declares a headerless text file."""
    suffix = file.suffix.lower()
    if suffix in R_FILES:
        try:
            return readR(file), 'pyreadr'
        except _R_ERRORS:
            return readRdata(file), 'rdata'
    if cran and suffix == '.r':
        try:
            return Deparse(file).frames(), 'deparse'
        except DeparseError:  # most of base R's data/*.R files: time series, matrices
            return {file.stem: None}, 'deparse'
    if cran:
        return readData(file), 'pandas'
    if bare(file).suffix in ('.xlsx', '.xls'):
        return readWorkbook(file, label), 'pandas'
    if layout is not None:
        return {label: readLayout(file, layout)}, 'pandas'
    return {label: readTable(file)}, 'pandas'


def isData(file: Path, *, cran: bool = False) -> bool:
    """In a CRAN package's data/ folder, what utils::data() reads; elsewhere what R or pandas
    read, less the text files that are documentation. Never Stan initial values beside a data
    dict, nor a zip's resource forks."""
    readable = R_FILES | TABLE_FILES
    if cran:
        readable = R_FILES | _DATA_FILES
    if bare(file).suffix not in readable:
        return False
    if file.name.endswith('.init.json') or '__MACOSX' in file.parts:
        return False
    if cran:
        return True
    return not isDoc(file) and not describesSibling(file)


def isDoc(file: Path) -> bool:
    """Markdown and reST; a `.txt` named like documentation (`codebook.txt`, not a data
    file such as the PyMC examples' `Guber1999data.txt`); a suffix-less file in capitals
    (`README`, `LICENSE`), not a dotfile or a suffix-less data file."""
    suffix = file.suffix.lower()
    if suffix in ('.md', '.rst'):
        return True
    if suffix == '.txt':
        return any(stem in file.stem.lower() for stem in DOC_STEMS)
    return suffix == '' and file.name.isupper()


def describesSibling(file: Path) -> bool:
    """A `.txt` named after a data file of another format beside it (Fitzmaurice's `lead.txt`
    beside `lead.dta`, ROS's `bypass.txt` beside `bypass.csv`) is its description, no data."""
    if file.suffix.lower() != '.txt':
        return False
    siblings = [f for f in file.parent.iterdir() if f.is_file() and f != file]
    return any(bare(f).stem == file.stem.lower() for f in siblings)


def bare(file: Path) -> Path:
    """The file's name without its `.zip` or `.gz` wrapper (posteriordb's `radon.json.zip`,
    PMLB's `apnea.tsv.gz`): the suffix says how to read it, the stem what documents it."""
    return Path(file.name.lower().removesuffix('.zip').removesuffix('.gz'))


# ==============================================================================================
# R files
# ==============================================================================================


def readR(path: Path) -> Frames:
    """`pyreadr.read_r`, except that factor levels keep R's order and that an object pyreadr
    cannot turn into a DataFrame is None; a file librdata rejects raises."""
    parser = PyreadrParser()
    parser.parse(bytes(path))
    frames = {}
    for table in parser.table_data:
        name = table.name or path.stem  # an .rds carries no object name
        if table.dim_num > 2:  # pyreadr hands these to xarray (base R's Titanic)
            frames[name] = None
            continue
        try:
            df = table.convert_to_dataframe()
        except PyreadrError:  # a matrix column (gamlss.data's aep)
            frames[name] = None
            continue
        for position, labels in table.value_labels.items():  # {column: {code: label}}
            column = df.columns[position]
            levels = [labels[code] for code in sorted(labels)]  # R orders levels by code
            # pyreadr used astype('category'), which sorts levels and drops unused ones
            df[column] = df[column].cat.set_categories(levels)
        frames[name] = numbersAsFloat(df)
    return frames


def readRdata(path: Path) -> Frames:
    """An R file librdata rejects (geepack's muscatine, plonsky_2019_osf's .RData) through the
    pure-Python rdata; a list or a model fit is no table."""
    try:
        objects = rdataObjects(path)
    except RDATA_ERRORS:
        return {path.stem: None}
    frames = {}
    for name, value in objects.items():
        if name.startswith('.'):  # R's hidden objects (`.Random.seed`), left out as ls() does
            continue
        frames[name] = None
        if isinstance(value, pd.DataFrame):
            # R's integer row names, 1-based (or a subset's, jing_2020_osf): pyreadr's 0-based range
            frames[name] = pyreadrTypes(value.reset_index(drop=True))
    return frames


def rdataObjects(path: Path) -> dict:
    """An .rds holds one object, named by the file as `readR` names it."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', FRAME_CLASSES, UserWarning)
        if path.suffix.lower() == '.rds':
            return {path.stem: rdata.read_rds(path)}
        return rdata.read_rda(path)


def pyreadrTypes(df: pd.DataFrame) -> pd.DataFrame:
    """rdata's nullable dtypes as pyreadr's: an R integer column int32, float where it holds
    NA (`numbersAsFloat`), a string column pandas' default string."""
    types = {}
    for column in df.columns[df.dtypes == 'Int32']:
        types[column] = 'int32'
        if df[column].isna().any():
            types[column] = 'float64'
    for column in df.columns[df.dtypes == 'string']:
        types[column] = 'str'
    return df.astype(types)


def numbersAsFloat(df: pd.DataFrame) -> pd.DataFrame:
    """pyreadr renders an R integer vector with NA as an object column of ints and NaN
    (mlmRev's `star`); such a column becomes float, a string column stays as it is."""
    numbers = {}
    for column in df.columns[df.dtypes == object]:
        present = df[column].dropna()
        if present.map(lambda v: isinstance(v, (int, float))).all():
            numbers[column] = pd.to_numeric(df[column])
    return df.assign(**numbers)


# ==============================================================================================
# utils::data() text files
# ==============================================================================================


def readData(file: Path) -> Frames:
    """A CRAN package's `data/*.txt`, `.tab` or `.csv` as utils::data() reads it:
    read.table(header = TRUE, as.is = FALSE), with `sep = ';'` for a `.csv`. Strings become
    categoricals with sorted levels, as read.table sorts them: in codepoint order, R's in the
    C locale, where R's ICU collation sorts agridat's lillemo.wheat `Ba04` before `BT06`."""
    sep = r'\s+'
    if file.suffix.lower() == '.csv':
        sep = ';'
    df = pd.read_csv(file, sep=sep, quotechar='"', na_values=['NA'], keep_default_na=False)
    strings = df.columns[df.dtypes.map(pd.api.types.is_string_dtype)]
    factors = {column: df[column].astype('category') for column in strings}
    return {file.stem: df.assign(**factors)}


# ==============================================================================================
# pandas files
# ==============================================================================================


def readWorkbook(file: Path, label: str) -> Frames:
    """One object per data sheet, `<label>!<sheet>`, names stripped as in text files; a
    workbook of one data sheet is the file. The sheets named like documentation (`Contents`)
    and the empty ones (Excel's default `Sheet2` and `Sheet3`) are none."""
    sheets = pd.read_excel(file, sheet_name=None)
    data = [name for name, df in sheets.items() if not isNoteSheet(name) and len(df)]
    objects = {}
    for name in data:
        key = f'{label}!{name}'
        if len(data) == 1:
            key = label
        objects[key] = sheets[name].rename(columns=lambda c: str(c).strip())
    return objects


def readTable(file: Path) -> pd.DataFrame | None:
    """pandas by extension; None where the file holds no table."""
    suffix = bare(file).suffix
    if suffix == '.json':
        return readJson(unwrap(file))
    if suffix == '.dta':
        return readStata(file)
    if suffix == '.sav':
        return readSpss(file)
    if suffix == '.arrow':
        return pd.read_feather(file)
    if suffix in ('.pq', '.parquet'):
        return pd.read_parquet(file)
    return readDelimited(file)


def readStata(file: Path) -> pd.DataFrame:
    """pandas, except for a file whose value-label section it misparses (Rabe-Hesketh's
    scotmap), which pyreadstat reads with the labels applied the same way."""
    try:
        return pd.read_stata(file)
    except struct.error:
        df, _ = pyreadstat.read_dta(str(file), apply_value_formats=True, formats_as_category=True)
        return df


def readSpss(file: Path) -> pd.DataFrame:
    """A column whose value labels cover every value it holds becomes a categorical in code
    order; labels on a scale's extremes alone (Hox's `lowest`, `highest` on a numeric score)
    leave it numeric, where pandas would make every value a category."""
    df, meta = pyreadstat.read_sav(str(file))
    labelled = {}
    for column, labels in meta.variable_value_labels.items():
        present = set(df[column].dropna())
        if present <= set(labels):
            levels = [labels[code] for code in sorted(labels)]
            labelled[column] = pd.Categorical(df[column].map(labels), categories=levels)
    return df.assign(**labelled)


def isNoteSheet(name: str) -> bool:
    return any(stem in name.lower() for stem in NOTE_SHEETS)


def readLayout(file: Path, layout: tuple[str, ...]) -> pd.DataFrame:
    """A headerless text file read as the frame declares it: `name:start-end` entries are
    the fixed-width columns of a file with a layout sheet (the Bristol CMM `.DAT`), plain
    names the whitespace-separated columns of a file with a codes list (Goldstein's
    partnership data). Character positions count from 1, as the layout sheets do."""
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


def readDelimited(file: Path) -> pd.DataFrame | None:
    """The separator sniffed, unless the header holds none of the usual ones: columns
    aligned with runs of spaces (the ARM `.dat` files, Diggle's course files) are then read
    whitespace-separated, which the sniffer would miscount. A banner of `#` lines above the
    table is skipped; what does not parse (a banner the PyMC examples' ice-core csv opens
    with) is no table. Undecodable bytes (a latin-1 degree sign) are replaced, a byte-order
    mark dropped. pandas opens a `.gz` itself."""
    options = {'encoding': 'utf-8-sig', 'encoding_errors': 'replace'}
    lines, header = banner(file)
    # the sniffer needs the python engine, which ignores quotes under a regex separator; the C
    # engine honours them, as read.table does (R's write.table output, ARM's ideo2.dat)
    sep, engine = None, 'python'
    if not any(mark in header for mark in ',;\t|'):
        sep, engine = r'\s+', 'c'
    try:
        df = pd.read_csv(file, sep=sep, skiprows=len(lines), engine=engine, **options)
    except pd.errors.ParserError:
        return None
    return tidyText(df)


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


def tidyText(df: pd.DataFrame) -> pd.DataFrame:
    """Padded fields (the ARM files: `idnum, state, ...`, `NA       `) stripped, so that a
    name is the name and a column of numbers with `NA` is numeric with missing values."""
    df = df.rename(columns=lambda name: str(name).strip())
    tidy = {}
    for column in df.columns[df.dtypes.map(pd.api.types.is_string_dtype)]:
        values = df[column].str.strip().replace({'': None, 'NA': None})
        numbers = pd.to_numeric(values, errors='coerce')
        if numbers.notna().sum() == values.notna().sum():  # every present value a number
            values = numbers
        tidy[column] = values
    return df.assign(**tidy)


def unwrap(file: Path) -> bytes:
    """The file's content, out of its `.zip` wrapper where it has one."""
    if file.suffix.lower() != '.zip':
        return file.read_bytes()
    with zipfile.ZipFile(file) as z:
        member = z.namelist()[0]
        return z.read(member)


# ----------------------------------------------------------------------------------------------
# JSON: records, or a Stan data dict
# ----------------------------------------------------------------------------------------------


def readJson(data: bytes) -> pd.DataFrame | None:
    """JSON records as pandas reads them; a Stan data dict (posteriordb, the Stan examples)
    as the table of its arrays of the modal length, the observations: scalars, the arrays
    of another length (group-level data) and arrays of three or more dimensions are no
    columns, an N-row matrix is its numbered columns (`X_1`, `X_2`); a dict without arrays
    (a descriptor) is no table."""
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


def arrayShape(value: list) -> list[int]:
    shape = []
    while isinstance(value, list):
        shape.append(len(value))
        value = value[0] if value else None
    return shape


def arrayDepth(value: list) -> int:
    """Dimensions of a nested array: 1 for a vector, 2 for a matrix, and so on."""
    return len(arrayShape(value))


def observationLength(content: dict) -> int | None:
    lengths = [len(value) for value in content.values() if isinstance(value, list)]
    if not lengths:
        return None
    return max(set(lengths), key=lengths.count)
