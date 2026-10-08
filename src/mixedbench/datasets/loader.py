"""Dataset loader for the dimension survey: pinned source as input, typed DataFrame as output.
The pipeline url -> archive -> tree -> files -> frames, the cache and the Rscript dump route
live here; the formats are `readers.py`, the help pages `docs.py`."""

from __future__ import annotations

import hashlib
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import pandas as pd
from mixedbench.datasets import docs, readers
from mixedbench.datasets.readers import DATA_FILES, R_ERRORS, R_FILES, TABLE_FILES, Frames

CRAN = 'https://cloud.r-project.org/src/contrib'
ARCHIVES = ('.zip', '.tar.gz', '.tgz', '.tar')
Reader = Literal['pyreadr', 'rscript', 'pandas']
ColumnType = Literal['categorical', 'ordered', 'continuous']  # what a registry row may declare

# Reads one data/ file the way utils::data() does and saves each object in it as its own .rds,
# in serialization v2, which librdata reads where it rejects some v3 files (geepack's muscatine)
DUMP_R = """
args <- commandArgs(trailingOnly = TRUE)
file <- args[1]
out <- args[2]
env <- new.env()
ext <- tolower(tools::file_ext(file))
stem <- tools::file_path_sans_ext(basename(file))
if (ext == 'r') sys.source(file, envir = env, chdir = TRUE) else
if (ext %in% c('rda', 'rdata')) load(file, envir = env) else
if (ext == 'rds') assign(stem, readRDS(file), envir = env) else
if (ext %in% c('tab', 'txt'))
    assign(stem, read.table(file, header = TRUE, as.is = FALSE), envir = env) else
if (ext == 'csv')
    assign(stem, read.table(file, header = TRUE, sep = ';', as.is = FALSE), envir = env) else
    stop(paste('no data() rule for', file))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
for (name in ls(env))
    saveRDS(get(name, envir = env), file.path(out, paste0(name, '.rds')), version = 2)
"""

# Lays out base R's `datasets` (lazy data, no tarball) like a source tree: every object as its
# own .rds under data/, every help page from R's Rd database under man/
BASE_R = """
tree <- commandArgs(trailingOnly = TRUE)[1]
dir.create(file.path(tree, 'data'), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(tree, 'man'), showWarnings = FALSE)
items <- sort(sub(' .*', '', data(package = 'datasets')$results[, 'Item']), method = 'radix')
# CO2 and co2 would be one file on a case-insensitive file system: the later name in C order
# gets a tilde, which the loader strips again
files <- ifelse(duplicated(tolower(items)), paste0(items, '~'), items)
for (i in seq_along(items))
    saveRDS(get(items[i], envir = as.environment('package:datasets')),
            file.path(tree, 'data', paste0(files[i], '.rds')), version = 2)
pages <- tools::Rd_db('datasets')
stems <- tools::file_path_sans_ext(names(pages))
pageFiles <- ifelse(duplicated(tolower(stems)), paste0(stems, '~'), stems)
for (i in seq_along(pages))
    writeLines(paste(as.character(pages[[i]]), collapse = ''),
               file.path(tree, 'man', paste0(pageFiles[i], '.Rd')))
"""


@dataclass(frozen=True)
class Source:
    kind: Literal['cran', 'git', 'url']
    name: str  # CRAN package ('datasets' is base R), GitHub repository URL, or URL of a file
    pin: str  # CRAN version, git revision, or the file's sha256
    checksum: str | None = None  # sha256 of a CRAN or git archive; None skips the check
    path: str | None = None  # git, url: file or folder inside the tree; None -> all of it
    file: str | None = None  # url: the download's file name where the URL's path has none
    layout: tuple[str, ...] | None = None  # url: the columns of a headerless text file


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
        self._frames: dict[Source, dict[str, tuple[DataObject, pd.DataFrame | None]]] = {}

    def objects(self, source: Source) -> list[DataObject]:
        pairs = self._read(source).values()
        return [obj for obj, _ in pairs]

    def load(
        self, source: Source, name: str, types: Mapping[str, ColumnType] | None = None
    ) -> pd.DataFrame:
        """The object as one typed table: `types` declares what a file format without column
        types (delimited text, Excel) cannot carry, and `ordered` what pyreadr drops from an R
        factor; a plain column declared categorical or ordered gets sorted levels."""
        obj, df = self._read(source)[name]
        if df is None:
            raise ValueError(f'{source.name} {source.pin} {obj.file}: {name!r} is no DataFrame')
        declared = {}
        for column, kind in (types or {}).items():
            if kind == 'continuous':
                declared[column] = pd.to_numeric(self._decimalPoint(df[column]))
            else:  # a categorical keeps its levels under a CategoricalDtype without categories
                declared[column] = df[column].astype(pd.CategoricalDtype(ordered=kind == 'ordered'))
        return df.assign(**declared)

    @staticmethod
    def _decimalPoint(values: pd.Series) -> pd.Series:
        """A string column with decimal commas and no points (a European csv, kleisner_2026's
        BMI) read with points; anything else as it is, so a thousands separator fails loudly."""
        if not pd.api.types.is_string_dtype(values):
            return values
        if values.str.contains('.', regex=False).any():
            return values
        return values.str.replace(',', '.', regex=False)

    def help(self, source: Source, name: str) -> str:
        """What documents `name`: the Rd page of a CRAN object; otherwise the text files named
        after the object's stem in its folder or a sibling folder (posteriordb's
        `data/info/radon.info.json` beside `data/data/`), else those in the file's folder or the
        nearest folder above it within the pinned path that has any; a Stan data dict adds which
        entries are not in the table, a Stata or SPSS file its labels, a workbook its contents
        sheet, and a repository that is an R package (rethinking, ROS's `rpackage/`) the Rd
        page named after the file's stem."""
        tree = self._tree(source)
        if source.kind == 'cran':
            page = docs.rdPage(tree / 'man', name)
            if page is None:
                raise KeyError(f'{source.name} {source.pin} has no help page for {name!r}')
            return page
        file = tree / self._read(source)[name][0].file
        root = tree / (source.path or '')  # documentation is sought within the pinned path
        if root.is_file():
            root = root.parent
        found = docs.sameStemDocs(tree, file) or docs.docsBeside(root, file)
        pages = [f'# {f.relative_to(tree)}\n{f.read_text(errors="replace")}' for f in found]
        pages.append(docs.selfNote(file))
        for man in sorted(tree.rglob('man')):  # a repository that is an R package (rethinking)
            pages.append(docs.rdPage(man, readers.bare(file).stem))
        return '\n'.join(page for page in pages if page)

    # ------------------------------------------------------------------------------------------
    # pipeline: url -> archive -> tree -> files -> frames
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def _getBytes(url: str) -> bytes | None:
        """Default fetch; None on a 404 so the caller can try the next location; a 429 (OSF
        after a burst of downloads) waits the `Retry-After` seconds and tries again."""
        req = urllib.request.Request(url, headers={'User-Agent': 'mixedbench'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code != 429 or attempt == 2:
                    raise
                time.sleep(int(e.headers.get('Retry-After', 10)))

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
        filename = source.file or Path(urlparse(urls[0]).path).name
        file = self._dir(source) / filename
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._fetchFirst(source, urls))
        checksum = source.checksum
        if source.kind == 'url':  # the file's sha256 is its pin
            checksum = source.pin
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if checksum is not None and digest != checksum:
            raise ValueError(f'{file} checksum {digest} differs from pinned {checksum}')
        return file

    def _fetchFirst(self, source: Source, urls: list[str]) -> bytes:
        for url in urls:
            data = self.fetch(url)
            if data is not None:
                return data
        raise FileNotFoundError(f'{source.name} {source.pin}: not at {", ".join(urls)}')

    def _tree(self, source: Source) -> Path:
        """The source's files, extracted once: a CRAN package, a repository at a revision, or
        what a URL serves (an archive's content, else the file in a folder of its own)."""
        dir = self._dir(source)
        if source.name == 'datasets':  # base R ships no tarball: R lays its namespace out as one
            tree = dir / 'datasets'
            if not tree.exists():
                self._rscript(BASE_R, str(tree))
            return tree
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
        it; otherwise the pinned path (a file, or a folder walked) in what R or pandas read,
        less the text files that are documentation."""
        if source.kind == 'cran':  # data() ignores other files (`datalist`)
            candidates = []
            if (tree / 'data').exists():  # GLMMadaptive ships no data
                candidates = (tree / 'data').iterdir()
            readable = R_FILES | DATA_FILES
        else:
            root = tree / (source.path or '')
            candidates = [root]
            if root.is_dir():
                candidates = root.rglob('*')
            readable = R_FILES | TABLE_FILES
        files = [f for f in candidates if f.is_file() and readers.bare(f).suffix in readable]
        files = [f for f in files if not f.name.endswith('.init.json')]  # Stan initial values
        files = [f for f in files if '__MACOSX' not in f.parts]  # a zip's resource forks
        if source.kind != 'cran':
            files = [f for f in files if not docs.isDoc(f) and not docs.describesSibling(f)]
        return sorted(files)

    def _read(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        """Every data object of the source by name, with its frame; parsed once per source,
        since one survey merge asks for a table several times and pyreadr is slow on factors."""
        if source not in self._frames:
            self._frames[source] = self._parse(source)
        return self._frames[source]

    def _parse(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
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

    def _readFile(self, file: Path, source: Source, label: str) -> tuple[Frames, Reader]:
        """An R file through pyreadr; a CRAN data/ text file follows utils::data() rules only R
        knows, so R saves it as .rds first; pandas reads the rest."""
        if source.name == 'datasets':  # every file is an .rds R dumped
            return self._readDumped(file), 'rscript'
        if file.suffix.lower() in R_FILES:
            return self._readRFile(file, source)
        if source.kind == 'cran':
            return self._readViaR(file, source), 'rscript'
        return readers.readTables(file, label, source.layout), 'pandas'

    def _readRFile(self, file: Path, source: Source) -> tuple[Frames, Reader]:
        """An R file librdata rejects (geepack's muscatine, a plain data frame) is re-saved by R."""
        try:
            return readers.readR(file), 'pyreadr'
        except R_ERRORS:
            return self._readViaR(file, source), 'rscript'

    def _readViaR(self, file: Path, source: Source) -> Frames:
        dir = self._dir(source) / 'rds' / file.stem
        if not dir.exists():
            self._rscript(DUMP_R, str(file), str(dir))
        frames = {}
        for rds in sorted(dir.glob('*.rds')):
            frames |= self._readDumped(rds)
        return frames

    def _readDumped(self, rds: Path) -> Frames:
        """An .rds R saved; what librdata still rejects is no table (boot's cd4.nested, a list)."""
        name = rds.stem.removesuffix('~')  # BASE_R marks base R's co2 beside CO2 with a tilde
        try:
            frames = readers.readR(rds)
        except R_ERRORS:
            return {name: None}
        if not frames:  # a list object (base R's Harman23.cor) holds no table
            return frames
        return {name: frames[rds.stem]}

    @staticmethod
    def _rscript(script: str, *args: str) -> None:
        subprocess.run(['Rscript', '-e', script, *args], check=True)
