"""loader.py defines how a pinned source becomes typed tables and where it is cached.

pipeline:
---------
a pinned Source
-> the download from the first URL that answers (verified)     _urls, _download
-> its tree (the source's files on disk)                       tree
-> the files holding data                                      _fetchFile | _files
-> every object of those files as a frame (by name)            readers.read
-> one object as a typed table                                 load
"""

from __future__ import annotations

import hashlib
import ssl
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlparse

import pandas as pd
from mixedbench.datasets import readers

# =====================================================================================
# where sources are fetched
# =====================================================================================
# the hosts behind every pin and the default fetch.
CRAN = 'https://cloud.r-project.org/src/contrib'
R_SOURCES = 'https://cloud.r-project.org/src/base'
ARCHIVES = ('.zip', '.tar.gz')
# intermediate certificates a server leaves out of its chain
TLS = ssl.create_default_context()
TLS.load_verify_locations(Path(__file__).parent / 'intermediates.pem')


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={'User-Agent': 'mixedbench'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120, context=TLS) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                return None
            if e.code != 429 or attempt == 2:
                raise
            time.sleep(int(e.headers.get('Retry-After', 10)))


# =====================================================================================
# sources and objects
# =====================================================================================
# what the registry pins, what the loader finds in it, and the column types a row declares.
ColumnType = Literal['categorical', 'ordered', 'continuous']


@dataclass(frozen=True)
class Source:
    kind: Literal['cran', 'git', 'url']
    name: str  # CRAN package ('datasets' is base R's), GitHub repository URL, or URL of a file
    pin: str  # CRAN or R version, git revision, or the file's sha256
    checksum: str | None = None  # sha256 of the download (a url's pin); None skips the check
    path: str | None = None  # git, url: file or folder inside the tree; None -> all of it
    file: str | None = None  # url: the download's file name where the URL's path has none
    layout: tuple[str, ...] | None = None  # url: the columns of a headerless text file
    mirror: str | None = None  # url: the package's copy where the host refuses (ADR 0003)


@dataclass(frozen=True)
class DataObject:
    name: str  # the R object, or the file's path inside the source
    file: str  # relative to the source tree
    n_rows: int | None  # None: the object is no table (a model fit, a list, a time series)
    n_cols: int | None
    reader: readers.Reader  # the file's route: pyreadr, rdata, pandas or the deparse reader


@dataclass(frozen=True)
class ManifestRow:
    file: str  # the object's file, relative to the source tree
    sha256: str  # of that file


Manifest = Mapping[tuple[Source, str], ManifestRow]  # (source, object name) -> its file


# =====================================================================================
# loader class
# =====================================================================================
class Loader:
    """Typed tables from pinned sources, cached under one folder.
    With a manifest, only an object's own file is fetched and read.
    Without one, the whole source."""

    def __init__(
        self,
        cache: Path,
        fetch: Callable[[str], bytes | None] = fetch,
        manifest: Manifest | None = None,
    ):
        self.cache = Path(cache)
        self.fetch = fetch
        self.manifest = manifest
        self._frames: dict[Source, dict[str, tuple[DataObject, pd.DataFrame | None]]] = {}
        self._verified: set[tuple[Path, str]] = set()  # (file, checksum) pairs that matched

    def objects(self, source: Source) -> list[DataObject]:
        pairs = self._read(source).values()
        return [obj for obj, _ in pairs]

    def load(
        self, source: Source, name: str, types: Mapping[str, ColumnType] | None = None
    ) -> pd.DataFrame:
        file, df = self._object(source, name)
        if df is None:
            raise ValueError(f'{source.name} {source.pin} {file}: {name!r} is no DataFrame')
        return df.assign(**self._declared(df, types or {}))

    def tree(self, source: Source) -> Path:
        """The source's files, extracted once:
        a CRAN package, a repository at a revision, or a URL server."""
        dir = self._dir(source)
        file = self._download(source)
        is_archive = file.name.lower().endswith(ARCHIVES)
        if not is_archive:
            return dir
        tree = dir / 'tree'
        if not tree.exists():
            self._extract(file, tree)
        entries = list(tree.iterdir())
        if len(entries) == 1 and entries[0].is_dir():  # a single top-level folder is layout
            tree = entries[0]
        if source.name == 'datasets':  # base R's, laid out in R's sources as a CRAN package is
            return tree / 'src/library/datasets'
        return tree

    # ------------------------------------------------------------------------------------------
    # url -> archive -> tree -> files -> frames
    # ------------------------------------------------------------------------------------------

    def _dir(self, source: Source) -> Path:
        if source.kind == 'cran':
            return self.cache / 'cran' / f'{source.name}_{source.pin}'
        if source.kind == 'git':
            owner, repo = self._repo(source).split('/')
            return self.cache / 'git' / f'{owner}_{repo}_{source.pin}'
        return self.cache / 'url' / source.pin

    @staticmethod
    def _urls(source: Source) -> list[str]:
        """The download's URLs, in the order to try."""
        if source.name == 'datasets':  # base R's, in R's sources
            major = source.pin.split('.')[0]
            return [f'{R_SOURCES}/R-{major}/R-{source.pin}.tar.gz']
        if source.kind == 'cran':  # CRAN moves superseded versions to Archive/
            stem = f'{source.name}_{source.pin}'
            return [f'{CRAN}/{stem}.tar.gz', f'{CRAN}/Archive/{source.name}/{stem}.tar.gz']
        if source.kind == 'git':  # GitHub's archive of the tree at a revision
            return [f'{source.name}/archive/{source.pin}.tar.gz']
        if source.mirror is not None:  # asked after the host, which stays the source
            return [source.name, source.mirror]
        return [source.name]

    def _download(self, source: Source) -> Path:
        """The digest is checked on a cache hit too."""
        urls = self._urls(source)
        filename = source.file or Path(urlparse(urls[0]).path).name
        file = self._dir(source) / filename
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._fetchFirst(source, urls))
        self._verify(file, source.checksum)
        return file

    def _verify(self, file: Path, checksum: str | None) -> None:
        """Once per file and loader: every manifest load passes through its source's download
        again."""
        if checksum is None or (file, checksum) in self._verified:
            return
        with file.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if digest != checksum:
            raise ValueError(f'{file} checksum {digest} differs from pinned {checksum}')
        self._verified.add((file, checksum))

    def _fetchFirst(self, source: Source, urls: list[str]) -> bytes:
        for url in urls:
            data = self.fetch(url)
            if data is not None:
                return data
        raise FileNotFoundError(f'{source.name} {source.pin}: not at {", ".join(urls)}')

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
        cran = source.kind == 'cran'
        if cran:
            candidates = []
            if (tree / 'data').exists():  # a package may ship no data
                candidates = (tree / 'data').iterdir()
        else:
            root = tree / (source.path or '')
            candidates = [root]
            if root.is_dir():
                candidates = root.rglob('*')
        files = [f for f in candidates if f.is_file() and readers.isData(f, cran=cran)]
        return sorted(files)

    def _object(self, source: Source, name: str) -> tuple[str, pd.DataFrame | None]:
        if self.manifest is None:
            obj, df = self._read(source)[name]
            return obj.file, df
        row = self.manifest[source, name]
        file = self._fetchFile(source, row)
        self._verify(file, row.sha256)
        frames, _ = readers.read(file, row.file, layout=source.layout, cran=source.kind == 'cran')
        return row.file, frames[name]

    def _fetchFile(self, source: Source, row: ManifestRow) -> Path:
        """A git source's file comes alone from GitHub's raw URL,
        under `files/` so it never passes for an extracted `tree/`."""
        if source.kind != 'git':
            return self.tree(source) / row.file
        file = self._dir(source) / 'files' / row.file
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            revision = f'https://raw.githubusercontent.com/{self._repo(source)}/{source.pin}'
            file.write_bytes(self._fetchFirst(source, [f'{revision}/{quote(row.file)}']))
        return file

    @staticmethod
    def _repo(source: Source) -> str:
        return source.name.removeprefix('https://github.com/')

    def _read(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        """Parsed once per source: pyreadr is slow on factors,
        and a survey merge asks for a table several times."""
        if source not in self._frames:
            self._frames[source] = self._parse(source)
        return self._frames[source]

    def _parse(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        tree = self.tree(source)
        cran = source.kind == 'cran'
        objects = {}
        for file in self._files(source, tree):
            label = file.relative_to(tree).as_posix()
            frames, reader = readers.read(file, label, layout=source.layout, cran=cran)
            for name, df in frames.items():
                shape = (None, None)
                if df is not None:
                    shape = df.shape
                objects[name] = DataObject(name, label, *shape, reader), df
        return objects

    @staticmethod
    def _declared(df: pd.DataFrame, types: Mapping[str, ColumnType]) -> dict[str, pd.Series]:
        """What a format cannot carry: column types for text and Excel,
        the order pyreadr drops from an R factor."""
        declared = {}
        for column, kind in types.items():
            if kind == 'continuous':
                declared[column] = pd.to_numeric(Loader._decimalPoint(df[column]))
            else:  # a categorical keeps its levels under a CategoricalDtype without categories
                declared[column] = df[column].astype(pd.CategoricalDtype(ordered=kind == 'ordered'))
        return declared

    @staticmethod
    def _decimalPoint(values: pd.Series) -> pd.Series:
        """Commas become points only in a column without points,
        so a thousands separator fails loudly."""
        if not pd.api.types.is_string_dtype(values):
            return values
        if values.str.contains('.', regex=False).any():
            return values
        return values.str.replace(',', '.', regex=False)
