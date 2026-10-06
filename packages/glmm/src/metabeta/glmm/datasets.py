"""Dataset loader for the dimension survey: pinned source as input, typed DataFrame as output."""

from __future__ import annotations

import hashlib
import re
import subprocess
import tarfile
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import pandas as pd
from pyreadr import LibrdataError, PyreadrError
from pyreadr._pyreadr_parser import PyreadrParser

# ==============================================================================================
# globals
# ==============================================================================================

CRAN = 'https://cloud.r-project.org/src/contrib'
R_FILES = {'.rda', '.rdata', '.rds'}  # meant for pyreadr
DATA_FILES = {'.r', '.tab', '.txt', '.csv'}  # meant for utils::data()
TABLE_FILES = {'.csv', '.tsv', '.tab', '.dat', '.xlsx', '.json', '.dta'}  # meant for pandas
DOC_FILES = {'.md', '.txt', '.rst', ''}  # text beside a data file
ARCHIVES = ('.zip', '.tar.gz', '.tgz', '.tar')
R_ERRORS = (PyreadrError, LibrdataError)  # LibrdataError is not a PyreadrError
Reader = Literal['pyreadr', 'rscript', 'pandas']
ColumnType = Literal['categorical', 'continuous']  # what a registry row may declare

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
    kind: Literal['cran', 'git', 'url']
    name: str  # CRAN package ('datasets' is base R), GitHub repository URL, or URL of a file
    pin: str  # CRAN version, git revision, or the file's sha256
    checksum: str | None = None  # sha256 of a CRAN or git archive; None skips the check
    path: str | None = None  # git, url: file or folder inside the tree; None -> all of it


@dataclass(frozen=True)
class DataObject:
    name: str  # the R object, or the file's path inside the source
    file: str  # relative to the source tree; a label for the survey table, never opened
    n_rows: int | None  # None: pyreadr cannot turn the object into a DataFrame
    n_cols: int | None
    reader: Reader  # pyreadr read the file, an .rds that Rscript dumped from it, or pandas did


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

    def load(
        self, source: Source, name: str, types: Mapping[str, ColumnType] | None = None
    ) -> pd.DataFrame:
        """The object as one typed table: `types` declares what a file format without column
        types (delimited text, Excel) cannot carry; a categorical gets sorted levels."""
        obj, df = self._read(source)[name]
        if df is None:
            raise ValueError(f'{source.name} {source.pin} {obj.file}: {name!r} is no DataFrame')
        declared = {}
        for column, kind in (types or {}).items():
            if kind == 'categorical':
                declared[column] = df[column].astype('category')
            else:
                declared[column] = pd.to_numeric(df[column])
        return df.assign(**declared)

    def help(self, source: Source, name: str) -> str:
        """What documents `name`: the Rd page of a CRAN object; otherwise the text files
        (README, codebook) in the file's folder, or in the nearest folder above it that has any."""
        tree = self._tree(source)
        if source.kind == 'cran':
            return self._rdPage(source, tree, name)
        file = tree / self._read(source)[name][0].file
        folders = [file.parent, *file.parent.parents]
        for folder in folders:
            docs = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in DOC_FILES]
            docs = [f for f in docs if f.is_file()]
            if docs:
                return '\n'.join(f'# {f.relative_to(tree)}\n{f.read_text()}' for f in docs)
            if folder == tree:
                break
        raise KeyError(f'{source.name} {source.pin} has no text file beside {name!r}')

    # ------------------------------------------------------------------------------------------
    # pipeline: url -> archive -> tree -> files -> frames
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

    def _dir(self, source: Source) -> Path:
        """The source's cache folder: the download, its extracted `tree/`, Rscript's `rds/`."""
        if source.kind == 'cran':
            return self.cache / 'cran' / f'{source.name}_{source.pin}'
        if source.kind == 'git':
            owner, repo = source.name.removesuffix('.git').rsplit('/', 2)[-2:]
            return self.cache / 'git' / f'{owner}_{repo}_{source.pin}'
        return self.cache / 'url' / source.pin

    @staticmethod
    def _urls(source: Source) -> list[str]:
        """Where the source's archive is, in the order to try."""
        if source.kind == 'cran':  # CRAN moves superseded versions to Archive/
            stem = f'{source.name}_{source.pin}'
            return [f'{CRAN}/{stem}.tar.gz', f'{CRAN}/Archive/{source.name}/{stem}.tar.gz']
        if source.kind == 'git':  # GitHub's archive of the tree at a revision
            return [f'{source.name}/archive/{source.pin}.tar.gz']
        return [source.name]

    def _download(self, source: Source) -> Path:
        """Fetched once from the first URL that answers; the digest is checked on cache hits too."""
        urls = self._urls(source)
        filename = Path(urlparse(urls[0]).path).name
        file = self._dir(source) / filename
        if not file.exists():
            data = None
            for url in urls:
                data = self.fetch(url)
                if data is not None:
                    break
            if data is None:
                raise FileNotFoundError(f'{source.name} {source.pin}: not at {", ".join(urls)}')
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        checksum = source.checksum
        if source.kind == 'url':  # the file's sha256 is its pin
            checksum = source.pin
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if checksum is not None and digest != checksum:
            raise ValueError(f'{file} checksum {digest} differs from pinned {checksum}')
        return file

    def _tree(self, source: Source) -> Path:
        """The source's files, extracted once: a CRAN package, a repository at a revision, or
        what a URL serves (an archive's content, else the file in a folder of its own)."""
        dir = self._dir(source)
        if source.name == 'datasets':  # base R ships no tarball: R dumps the namespace into data/
            if not dir.exists():
                self._rscript(BASE_R, str(dir / 'datasets' / 'data'))
            return dir / 'datasets'
        file = self._download(source)
        is_archive = file.name.lower().endswith(ARCHIVES)
        if not is_archive:
            return dir
        tree = dir / 'tree'
        if not tree.exists():
            self._extract(file, tree)
        entries = list(tree.iterdir())
        if len(entries) == 1 and entries[0].is_dir():  # a single top-level folder is layout
            return entries[0]
        return tree

    @staticmethod
    def _extract(archive: Path, dir: Path) -> None:
        if archive.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive) as z:
                z.extractall(dir)
        else:
            with tarfile.open(archive) as t:
                t.extractall(dir, filter='data')

    @staticmethod
    def _files(source: Source, tree: Path) -> list[Path]:
        """The files holding data objects: a CRAN package's data/ folder as utils::data() sees
        it; otherwise the pinned path (a file, or a folder walked) in what R or pandas read."""
        if source.kind == 'cran':
            candidates = (tree / 'data').iterdir()  # data() ignores other files (`datalist`)
            readable = R_FILES | DATA_FILES
        else:
            root = tree / (source.path or '')
            candidates = [root]
            if root.is_dir():
                candidates = root.rglob('*')
            readable = R_FILES | TABLE_FILES
        files = [f for f in candidates if f.is_file() and f.suffix.lower() in readable]
        return sorted(files)

    def _read(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        """Every data object of the source by name, with its frame."""
        tree = self._tree(source)
        objects = {}
        for file in self._files(source, tree):
            label = file.relative_to(tree).as_posix()
            frames, reader = self._readFile(file, source, label)
            for name, df in frames.items():
                shape = (None, None)
                if df is not None:
                    shape = df.shape
                objects[name] = DataObject(name, label, *shape, reader), df
        return objects

    def _readFile(
        self, file: Path, source: Source, label: str
    ) -> tuple[dict[str, pd.DataFrame | None], Reader]:
        """pyreadr reads an R file directly; a CRAN data/ file follows utils::data() rules only R
        knows, so R saves it object by object as .rds first; pandas reads the rest, one object
        per file named by its path."""
        if file.suffix.lower() in R_FILES:
            return self._readR(file), 'pyreadr'
        if source.kind == 'cran':
            return self._readViaR(file, source), 'rscript'
        return {label: self._readTable(file)}, 'pandas'

    def _readViaR(self, file: Path, source: Source) -> dict[str, pd.DataFrame | None]:
        dir = self._dir(source) / 'rds' / file.stem
        if not dir.exists():
            self._rscript(DUMP_R, str(file), str(dir))
        frames = {}
        for rds in sorted(dir.glob('*.rds')):
            frames |= self._readR(rds)
        return frames

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

    @staticmethod
    def _readTable(file: Path) -> pd.DataFrame:
        """pandas by extension; delimited text has its separator sniffed."""
        suffix = file.suffix.lower()
        if suffix == '.xlsx':
            return pd.read_excel(file)
        if suffix == '.json':
            return pd.read_json(file)
        if suffix == '.dta':
            return pd.read_stata(file)
        return pd.read_csv(file, sep=None, engine='python')

    @staticmethod
    def _rdPage(source: Source, tree: Path, name: str) -> str:
        """The raw Rd page whose alias is `name`."""
        pages = sorted((tree / 'man').glob('*.Rd'))
        alias = rf'\\alias\{{{re.escape(name)}\}}'
        for page in pages:
            text = page.read_text()
            if re.search(alias, text):
                return text
        raise KeyError(f'{source.name} {source.pin} has no help page for {name!r}')
