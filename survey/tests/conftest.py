"""A scratch survey root: `sources.yaml` pins two url sources served from memory by an injected
fetch, `herds` (Tier D) and `cattle` (Tier R), the same hand-made grouped table under two
column namings, so that duplicate flagging has a real pair to find, and a CRAN package `pens`
(Tier R) holding the herds table as `herds.rds`, whose DESCRIPTION states its license. The
table: region > herd nested, herd `h4` a singleton, `breed` a four-level categorical, `feed`
herd-level, `weight` continuous, `sick` binary, `cases` out of `trials` binomial, `id` a column
to ignore. Also the one recipe that merges a shard, the one reader of a written CSV, and what
the measured files' tests share: the herds table and rows, a registry row parsed as the merge
parses it, the measured rows of one registry row by key, and the generated tables.
"""

import hashlib
import io
import sys
import tarfile
import tempfile
import zipfile
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
import pytest
import yaml
from hypothesis import strategies as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # survey scripts are research code outside the package
sys.path.insert(0, str(HERE))  # the tests import mergeShard and readRows from here

import columns
import groups
from columns import COLUMN_COLUMNS
from fits import FIT_COLUMNS
from groups import COLUMN_FACTOR_COLUMNS
from measure import Measurer, measureRegistry
from merge import Merger
from mixedbench.datasets import Loader
from mixedbench.registry.row import Row, readCsv, writeCsv
from schema import EXCLUDED, REGISTRY
from summarize import Summarizer

FIXTURES = HERE / 'fixtures'
HERDS_URL = 'https://example.org/herds.zip'
CATTLE_URL = 'https://example.org/cattle.zip'
PENS_URL = 'https://cloud.r-project.org/src/contrib/pens_1.0.tar.gz'
PENS_LICENSE = 'GPL (>= 2)'
RENAMED = 'row,area,farm,type,diet,calving,kg,ill,positives,tested'


def zipped(folder: str, filename: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(f'{folder}/{filename}', text)
    return buffer.getvalue()


def cranTarball(package: str, license: str, table: pd.DataFrame, name: str) -> bytes:
    """A CRAN source tarball: a DESCRIPTION and the table as `data/<name>.rds`."""
    description = f'Package: {package}\nVersion: 1.0\nLicense: {license}\n'
    with tempfile.TemporaryDirectory() as dir:
        root = Path(dir) / package
        (root / 'data').mkdir(parents=True)
        (root / 'DESCRIPTION').write_text(description)
        pyreadr.write_rds(root / 'data' / f'{name}.rds', table)
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            archive.add(root, arcname=package)
    return buffer.getvalue()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mergeShard(merger: Merger, shard: Path) -> Merger:
    """The steps of `merge.py`'s `__main__`, in its order."""
    merger.load(shard)
    merger.validate()
    merger.upsert()
    merger.supersede()
    merger.reconcile()
    measureRegistry(merger.registry, merger.loader)
    merger.writeManifest()
    Summarizer(merger.registry, merger.survey).flush()
    merger.report()
    return merger


def readRows(path: Path) -> list[dict]:
    return readCsv(path).to_dict('records')


def emptyCensus(registry: Path) -> None:
    """The repository's registry/ always holds both census files and fits.csv, which no merge
    writes; a scratch one starts with them empty."""
    for table in (REGISTRY, EXCLUDED):
        writeCsv(pd.DataFrame(columns=table.columns), registry / f'{table.name}.csv')
    writeCsv(pd.DataFrame(columns=FIT_COLUMNS), registry / 'fits.csv')


def scratchMerger(registry: Path, survey: Path) -> Merger:
    """A merger over a scratch registry whose loader fetches the two zips from memory."""
    herdsText = (FIXTURES / 'herds.csv').read_text()
    cattleText = RENAMED + herdsText[herdsText.index('\n') :]
    archives = {
        HERDS_URL: zipped('herds', 'herds.csv', herdsText),
        CATTLE_URL: zipped('cattle', 'cattle.csv', cattleText),
        PENS_URL: cranTarball('pens', PENS_LICENSE, pd.read_csv(FIXTURES / 'herds.csv'), 'herds'),
    }
    sources = {
        'seed': 0,
        'tiers': {
            'D': {
                'herds': {
                    'kind': 'url',
                    'name': HERDS_URL,
                    'pin': sha(archives[HERDS_URL]),
                    'license': 'CC0 1.0 Universal',
                }
            },
            'R': {
                'cattle': {
                    'kind': 'url',
                    'name': CATTLE_URL,
                    'pin': sha(archives[CATTLE_URL]),
                    'license': 'not stated',
                },
                'pens': {'kind': 'cran', 'pin': '1.0'},
            },
        },
    }
    registry.mkdir(exist_ok=True)
    (registry / 'sources.yaml').write_text(yaml.safe_dump(sources, sort_keys=False))
    emptyCensus(registry)
    (survey / 'shards').mkdir(parents=True)

    def serve(url: str) -> bytes | None:
        return archives.get(url)

    return Merger(registry, survey, loader=Loader(registry / 'cache', fetch=serve))


@pytest.fixture
def merger(tmp_path: Path) -> Merger:
    """One scratch folder serving as both the registry and the survey."""
    return scratchMerger(tmp_path, tmp_path)


@pytest.fixture
def splitMerger(tmp_path: Path) -> Merger:
    """The repository's layout: the registry and the survey in two folders."""
    return scratchMerger(tmp_path / 'registry', tmp_path / 'survey')


CATEGORICAL = ('region', 'herd', 'breed', 'feed')


@pytest.fixture
def herds() -> pd.DataFrame:
    """The table as the loader returns it: the declared columns as pandas categoricals."""
    table = pd.read_csv(FIXTURES / 'herds.csv')
    return table.astype({c: 'category' for c in CATEGORICAL})


@pytest.fixture
def rows() -> list[dict]:
    rows = readRows(FIXTURES / 'registry_herds.csv')
    for row in rows:
        row['tier'] = 'D'
    return rows


def parsed(cells: dict) -> Row:
    """A shard row as the merge reads it: the script columns blank, but the tier."""
    blank = {c: '' for c in REGISTRY.scriptColumns}
    return Row.parse(blank | cells)


def asOrdered(values: pd.Series, levels: list) -> pd.Series:
    return values.astype(pd.CategoricalDtype(levels, ordered=True))


GENERATED = readRows(FIXTURES / 'registry_herds.csv')[0] | {
    'response': 'y', 'grouping_factors': 'g', 'covariates': '', 'ignore': '', 'types': '',
}  # fmt: skip


def roundedFloats() -> st.SearchStrategy[float]:
    """Floats as a real column holds them, four decimals: a tiny value would underflow when
    squared and leave a nearly constant column with no mean squares to share."""
    return st.floats(-100, 100).map(partial(round, ndigits=4))


@st.composite
def tables(draw: st.DrawFn) -> pd.DataFrame:
    """A table of one to thirty rows whose covariate columns take any kind the typing rule
    gives them: ties, gaps, a single value or two."""
    n = draw(st.integers(1, 30))
    number = st.one_of(roundedFloats(), st.sampled_from([0.0, 1.0]), st.none())
    word = st.sampled_from(['lo', 'mid', 'hi', None])
    words = draw(st.lists(word, min_size=n, max_size=n))
    return pd.DataFrame({
        'y': np.arange(n, dtype=float),
        'g': draw(st.lists(st.sampled_from('ab'), min_size=n, max_size=n)),
        'x': draw(st.lists(number, min_size=n, max_size=n)),
        'k': draw(st.lists(st.integers(0, 4), min_size=n, max_size=n)),
        's': words,
        'o': pd.Categorical(words, categories=['lo', 'mid', 'hi'], ordered=True),
    })  # fmt: skip


def measuredColumns(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The columns.csv rows of one registry row, by column; a statistic left out is blank."""
    measured = columns.measure(Measurer(table, parsed(cells)))
    return pd.DataFrame(measured, columns=COLUMN_COLUMNS).set_index('column')


def measuredColumnFactors(table: pd.DataFrame, cells: dict) -> pd.DataFrame:
    """The column_factors.csv rows of one registry row, by column and factor; a statistic left
    out is blank."""
    pairs = groups.measure(Measurer(table, parsed(cells)))
    return pd.DataFrame(pairs, columns=COLUMN_FACTOR_COLUMNS).set_index(['column', 'factor'])
