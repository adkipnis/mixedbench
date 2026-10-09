"""Dataset loader for the dimension survey: pinned source as input, typed DataFrame as output.
The pipeline url -> archive -> tree -> files -> frames and the cache live here, without R
(ADR 0003); the formats are `readers.py`, the help pages `docs.py`."""

from __future__ import annotations

import hashlib
import re
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
from mixedbench.datasets import docs, readers
from mixedbench.datasets.readers import Reader

CRAN = 'https://cloud.r-project.org/src/contrib'
R_SOURCES = 'https://cloud.r-project.org/src/base'
ARCHIVES = ('.zip', '.tar.gz', '.tgz', '.tar')
# Intermediate certificates a source's server leaves out of its chain, which OpenSSL, unlike
# macOS and Windows, does not fetch itself: Harvard's content.sph.harvard.edu (Fitzmaurice et
# al.) sends InCommon's instead of Sectigo's OV R36, from its leaf's CA Issuers URL
TLS = ssl.create_default_context()
TLS.load_verify_locations(Path(__file__).parent / 'intermediates.pem')
ColumnType = Literal['categorical', 'ordered', 'continuous']  # what a registry row may declare


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
    file: str  # relative to the source tree; a label for the survey table, never opened
    n_rows: int | None  # None: the object is no table (a model fit, a list, a time series)
    n_cols: int | None
    reader: Reader  # the file's route: pyreadr, rdata, pandas or the deparse reader


@dataclass(frozen=True)
class ManifestRow:
    file: str  # the object's file, relative to the source tree
    sha256: str  # of that file
    size: int  # in bytes


Manifest = Mapping[tuple[Source, str], ManifestRow]  # (source, object name) -> its file


def fetch(url: str) -> bytes | None:
    """The default fetch; None on a 404 or a refusal so the caller can try the next location;
    a 429 (OSF after a burst of downloads) waits the `Retry-After` seconds and tries again."""
    req = urllib.request.Request(url, headers={'User-Agent': 'mixedbench'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120, context=TLS) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):  # Dryad refuses a script with 401
                return None
            if e.code != 429 or attempt == 2:
                raise
            time.sleep(int(e.headers.get('Retry-After', 10)))


# ==============================================================================================
# loader
# ==============================================================================================


class Loader:
    def __init__(
        self,
        cache: Path,
        fetch: Callable[[str], bytes | None] = fetch,
        manifest: Manifest | None = None,
    ):
        """With a manifest, `load` reads only the object's file, and fetches only that file of
        a git source (ADR 0003, #4); without one, the whole source, as the survey needs for
        objects not yet merged."""
        self.cache = Path(cache)
        self.fetch = fetch
        self.manifest = manifest
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
        file, df = self._object(source, name)
        if df is None:
            raise ValueError(f'{source.name} {source.pin} {file}: {name!r} is no DataFrame')
        declared = {}
        for column, kind in (types or {}).items():
            if kind == 'continuous':
                declared[column] = pd.to_numeric(self._decimalPoint(df[column]))
            else:  # a categorical keeps its levels under a CategoricalDtype without categories
                declared[column] = df[column].astype(pd.CategoricalDtype(ordered=kind == 'ordered'))
        return df.assign(**declared)

    def tree(self, source: Source) -> Path:
        """The source's files, extracted once: a CRAN package, a repository at a revision, or
        what a URL serves (an archive's content, else the file in a folder of its own)."""
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
        _, package = self._location(source)
        return tree / package

    @staticmethod
    def _decimalPoint(values: pd.Series) -> pd.Series:
        """A string column with decimal commas and no points (a European csv, kleisner_2026's
        BMI) read with points; anything else as it is, so a thousands separator fails loudly."""
        if not pd.api.types.is_string_dtype(values):
            return values
        if values.str.contains('.', regex=False).any():
            return values
        return values.str.replace(',', '.', regex=False)

    def manifestRow(self, source: Source, name: str) -> ManifestRow:
        """What the manifest records of an object, read from the whole source."""
        file = self._read(source)[name][0].file
        data = (self.tree(source) / file).read_bytes()
        return ManifestRow(file, hashlib.sha256(data).hexdigest(), len(data))

    def help(self, source: Source, name: str) -> str:
        """What documents `name`: the Rd page of a CRAN object; otherwise the text files named
        after the object's stem in its folder or a sibling folder (posteriordb's
        `data/info/radon.info.json` beside `data/data/`), else those in the file's folder or the
        nearest folder above it within the pinned path that has any; a Stan data dict adds which
        entries are not in the table, a Stata or SPSS file its labels, a workbook its contents
        sheet, and a repository that is an R package (rethinking, ROS's `rpackage/`) the Rd
        page named after the file's stem."""
        tree = self.tree(source)
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
        pages = [
            f'# {f.relative_to(tree).as_posix()}\n{f.read_text(encoding="utf-8", errors="replace")}'
            for f in found
        ]
        pages.append(docs.selfNote(file))
        for man in sorted(tree.rglob('man')):  # a repository that is an R package (rethinking)
            pages.append(docs.rdPage(man, readers.bare(file).stem))
        return '\n'.join(page for page in pages if page)

    def licence(self, source: Source) -> str:
        """The `License` field of a CRAN package's DESCRIPTION, verbatim."""
        description = (self.tree(source) / 'DESCRIPTION').read_text()
        return re.search(r'^License:\s*(.+)$', description, re.MULTILINE).group(1)

    # ------------------------------------------------------------------------------------------
    # pipeline: url -> archive -> tree -> files -> frames
    # ------------------------------------------------------------------------------------------

    def _dir(self, source: Source) -> Path:
        """The source's cache folder: the download, its extracted `tree/`, a git source's
        manifest files under `files/`."""
        if source.kind == 'cran':
            return self.cache / 'cran' / f'{source.name}_{source.pin}'
        if source.kind == 'git':
            owner, repo = source.name.removesuffix('.git').rsplit('/', 2)[-2:]
            return self.cache / 'git' / f'{owner}_{repo}_{source.pin}'
        return self.cache / 'url' / source.pin

    @staticmethod
    def _location(source: Source) -> tuple[list[str], str]:
        """Where the source's download is, in the order to try, and the source's folder in it."""
        if source.name == 'datasets':  # base R's, laid out in R's sources as a CRAN package is
            major = source.pin.split('.')[0]
            return [f'{R_SOURCES}/R-{major}/R-{source.pin}.tar.gz'], 'src/library/datasets'
        if source.kind == 'cran':  # CRAN moves superseded versions to Archive/
            stem = f'{source.name}_{source.pin}'
            return [f'{CRAN}/{stem}.tar.gz', f'{CRAN}/Archive/{source.name}/{stem}.tar.gz'], ''
        if source.kind == 'git':  # GitHub's archive of the tree at a revision
            return [f'{source.name}/archive/{source.pin}.tar.gz'], ''
        if source.mirror is not None:  # asked after the host, which stays the source
            return [source.name, source.mirror], ''
        return [source.name], ''

    def _download(self, source: Source) -> Path:
        """Fetched once from the first URL that answers; the digest is checked on cache hits too."""
        urls, _ = self._location(source)
        filename = source.file or Path(urlparse(urls[0]).path).name
        file = self._dir(source) / filename
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._fetchFirst(source, urls))
        self._verify(file, source.checksum)
        return file

    @staticmethod
    def _verify(file: Path, checksum: str | None) -> None:
        """None skips the check: a CRAN tarball without a checksum."""
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if checksum is not None and digest != checksum:
            raise ValueError(f'{file} checksum {digest} differs from pinned {checksum}')

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
        """The files holding data objects: in a CRAN package's data/ folder, otherwise in the
        pinned path, a file or a folder walked."""
        cran = source.kind == 'cran'
        if cran:
            candidates = []
            if (tree / 'data').exists():  # GLMMadaptive ships no data
                candidates = (tree / 'data').iterdir()
        else:
            root = tree / (source.path or '')
            candidates = [root]
            if root.is_dir():
                candidates = root.rglob('*')
        files = [f for f in candidates if f.is_file() and readers.isData(f, cran=cran)]
        return sorted(files)

    def _object(self, source: Source, name: str) -> tuple[str, pd.DataFrame | None]:
        """The object's file and frame: the manifest's file alone, else the parsed source."""
        if self.manifest is None:
            obj, df = self._read(source)[name]
            return obj.file, df
        row = self.manifest[source, name]
        file = self._fetchFile(source, row)
        self._verify(file, row.sha256)
        frames, _ = readers.read(file, row.file, layout=source.layout, cran=source.kind == 'cran')
        return row.file, frames[name]

    def _fetchFile(self, source: Source, row: ManifestRow) -> Path:
        """The manifest's file in the extracted tree; a git source's alone from GitHub's raw URL
        at the pinned revision, kept under `files/` so that it never passes for the `tree/` the
        enumerate path reads."""
        if source.kind != 'git':
            return self.tree(source) / row.file
        file = self._dir(source) / 'files' / row.file
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._fetchFirst(source, [self._rawUrl(source, row.file)]))
        return file

    @staticmethod
    def _rawUrl(source: Source, file: str) -> str:
        """Every git source is on GitHub."""
        repo = source.name.removesuffix('.git').removeprefix('https://github.com/')
        return f'https://raw.githubusercontent.com/{repo}/{source.pin}/{quote(file)}'

    def _read(self, source: Source) -> dict[str, tuple[DataObject, pd.DataFrame | None]]:
        """Every data object of the source by name, with its frame; parsed once per source,
        since one survey merge asks for a table several times and pyreadr is slow on factors."""
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
