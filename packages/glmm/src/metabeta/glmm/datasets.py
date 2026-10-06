"""Dataset loader for the dimension survey: pinned source as input, typed DataFrame as output."""

from __future__ import annotations

import hashlib
import re
import subprocess
import tarfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
from pyreadr import LibrdataError, PyreadrError
from pyreadr._pyreadr_parser import PyreadrParser

# ==============================================================================================
# globals
# ==============================================================================================

CRAN = 'https://cloud.r-project.org/src/contrib'
R_FILES = {'.rda', '.rdata', '.rds'}  # meant for pyreadr
DATA_FILES = {'.r', '.tab', '.txt', '.csv'}  # meant for utils::data()
R_ERRORS = (PyreadrError, LibrdataError)  # LibrdataError is not a PyreadrError
Reader = Literal['pyreadr', 'rscript']

# Reads one data/ file the way utils::data() does and saves each object in it as its own .rds
# Uses serialization v2 because librdata rejects v3
DUMP_R = """
args <- commandArgs(trailingOnly = TRUE)
file <- args[1]
out <- args[2]
env <- new.env()
ext <- tolower(tools::file_ext(file))
if (ext == 'r') sys.source(file, envir = env, chdir = TRUE) else
if (ext %in% c('rda', 'rdata')) load(file, envir = env) else
if (ext %in% c('tab', 'txt')) assign(tools::file_path_sans_ext(basename(file)),
    read.table(file, header = TRUE, as.is = FALSE), envir = env) else
if (ext == 'csv') assign(tools::file_path_sans_ext(basename(file)),
    read.table(file, header = TRUE, sep = ';', as.is = FALSE), envir = env) else
    stop(paste('no data() rule for', file))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
for (name in ls(env))
    saveRDS(get(name, envir = env), file.path(out, paste0(name, '.rds')), version = 2)
"""

# Saves every object of base R's `datasets` (lazy data, no tarball) as its own .rds
BASE_R = """
out <- commandArgs(trailingOnly = TRUE)[1]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
items <- data(package = 'datasets')$results[, 'Item']
for (name in sub(' .*', '', items))
    saveRDS(get(name, envir = as.environment('package:datasets')),
            file.path(out, paste0(name, '.rds')), version = 2)
"""


@dataclass(frozen=True)
class Source:
    kind: Literal['cran']  # 'git' and 'url' follow in #16
    name: str  # CRAN package; 'datasets' is base R
    pin: str  # CRAN version
    checksum: str | None = None  # sha256 of the archive; None skips the check


@dataclass(frozen=True)
class DataObject:
    name: str
    file: str  # relative to the source tree; a label for the survey table, never opened
    n_rows: int | None  # None: pyreadr cannot turn the object into a DataFrame
    n_cols: int | None
    reader: Reader  # pyreadr read the file itself, or an .rds that Rscript dumped from it


# ==============================================================================================
# loader
# ==============================================================================================


class Loader:
    def __init__(self, cache: Path, fetch: Callable[[str], bytes | None] | None = None):
        self.cache = Path(cache)
        self.fetch = fetch or self._getBytes

    def objects(self, source: Source) -> list[DataObject]:
        pairs = self._read(source).values()
        return [obj for obj, _ in pairs]

    def load(self, source: Source, name: str) -> pd.DataFrame:
        obj, df = self._read(source)[name]
        if df is None:
            raise ValueError(f'{source.name} {source.pin} {obj.file}: {name!r} is no DataFrame')
        return df

    def help(self, source: Source, name: str) -> str:
        """The raw Rd page documenting `name`."""
        pages = sorted((self._tree(source) / 'man').glob('*.Rd'))
        alias = rf'\\alias\{{{re.escape(name)}\}}'
        for page in pages:
            text = page.read_text()
            if re.search(alias, text):
                return text
        raise KeyError(f'{source.name} {source.pin} has no help page for {name!r}')

    # ------------------------------------------------------------------------------------------
    # pipeline: url -> tarball -> tree -> data files -> frames
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def _getBytes(url: str) -> bytes | None:
        """Default fetch; None on a 404 so the caller can try the next location."""
        req = urllib.request.Request(url, headers={'User-Agent': 'metabeta-survey'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _tarball(self, source: Source) -> Path:
        """Fetched once from CRAN's current location (or after a miss from `Archive/`)."""
        stem = f'{source.name}_{source.pin}'
        tarball = self.cache / source.kind / f'{stem}.tar.gz'
        if not tarball.exists():
            current = f'{CRAN}/{stem}.tar.gz'
            archive = f'{CRAN}/Archive/{source.name}/{stem}.tar.gz'
            data = self.fetch(current)
            if data is None:  # CRAN moves superseded versions to Archive/
                data = self.fetch(archive)
            if data is None:
                raise FileNotFoundError(f'{source.name} {source.pin}: not at {current}, {archive}')
            tarball.parent.mkdir(parents=True, exist_ok=True)
            tarball.write_bytes(data)
        digest = hashlib.sha256(tarball.read_bytes()).hexdigest()  # checked on cache hits too
        if source.checksum is not None and digest != source.checksum:
            raise ValueError(f'{tarball} checksum {digest} differs from pinned {source.checksum}')
        return tarball

    def _tree(self, source: Source) -> Path:
        """The package's source tree (extracted once)."""
        dir = self.cache / source.kind / f'{source.name}_{source.pin}'
        if source.name == 'datasets':  # base R ships no tarball: R dumps the namespace into data/
            data = dir / 'datasets' / 'data'
            if not dir.exists():
                self._rscript(BASE_R, str(data))
            return dir / 'datasets'
        tarball = self._tarball(source)
        if not dir.exists():
            with tarfile.open(tarball) as archive:
                archive.extractall(dir, filter='data')
        return dir / source.name

    def _read(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        """Every data object of the source by name, with its frame."""
        tree = self._tree(source)
        files = sorted((tree / 'data').iterdir())
        objects = {}
        for file in files:
            is_data = file.suffix.lower() in R_FILES | DATA_FILES
            if not is_data:
                continue  # data() ignores other files (an index named `datalist`) as well
            frames, reader = self._readFile(file, tree)
            label = str(file.relative_to(tree))
            for name, df in frames.items():
                shape = df.shape if df is not None else (None, None)
                objects[name] = DataObject(name, label, *shape, reader), df
        return objects

    def _readFile(self, file: Path, tree: Path) -> tuple[dict[str, pd.DataFrame | None], Reader]:
        """pyreadr reads an R file directly; anything else R first saves object by object as .rds."""
        if file.suffix.lower() in R_FILES:
            return self._readR(file), 'pyreadr'
        dir = tree.parent / 'rds' / file.stem
        if not dir.exists():
            self._rscript(DUMP_R, str(file), str(dir))
        dumped = sorted(dir.glob('*.rds'))
        frames = {}
        for rds in dumped:
            frames |= self._readR(rds)
        return frames, 'rscript'

    @staticmethod
    def _rscript(script: str, *args: str) -> None:
        subprocess.run(['Rscript', '-e', script, *args], check=True)

    @staticmethod
    def _readR(path: Path) -> dict[str, pd.DataFrame | None]:
        """`pyreadr.read_r`, except that factor levels keep R's order and that whatever pyreadr
        cannot turn into a DataFrame is None: arrays beyond two dimensions, files librdata rejects."""
        parser = PyreadrParser()
        try:
            parser.parse(bytes(path))
        except R_ERRORS:  # base R's Titanic, a 4-d table, is one
            return {path.stem: None}
        frames = {}
        for table in parser.table_data:
            name = table.name or path.stem  # an .rds carries no object name
            if table.dim_num > 2:  # pyreadr hands these to xarray
                frames[name] = None
                continue
            df = table.convert_to_dataframe()
            for position, labels in table.value_labels.items():  # {column: {code: label}}
                column = df.columns[position]
                levels = [labels[code] for code in sorted(labels)]  # R orders levels by code
                # pyreadr used astype('category'), which sorts levels and drops unused ones
                df[column] = df[column].cat.set_categories(levels)
            frames[name] = df
        return frames
