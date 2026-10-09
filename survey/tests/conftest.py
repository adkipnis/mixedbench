"""A scratch survey root: `sources.yaml` pins two url sources served from memory by an injected
fetch, `herds` (Tier D) and `cattle` (Tier R), the same hand-made grouped table under two
column namings, so that duplicate flagging has a real pair to find, and a CRAN package `pens`
(Tier R) holding the herds table as `herds.rds`, whose DESCRIPTION states its licence. The
table: region > herd nested, herd `h4` a singleton, `breed` a four-level categorical, `feed`
herd-level, `weight` continuous, `sick` binary, `cases` out of `trials` binomial, `id` a column
to ignore. Also the one recipe that merges a shard and the one reader of a written CSV.
"""

import hashlib
import io
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pyreadr
import pytest
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # survey scripts are research code outside the package
sys.path.insert(0, str(HERE))  # the tests import mergeShard and readRows from here

from merge import Merger
from mixedbench.datasets import Loader
from schema import EXCLUDED, REGISTRY, readCsv, writeCsv

FIXTURES = HERE / 'fixtures'
HERDS_URL = 'https://example.org/herds.zip'
CATTLE_URL = 'https://example.org/cattle.zip'
PENS_URL = 'https://cloud.r-project.org/src/contrib/pens_1.0.tar.gz'
PENS_LICENCE = 'GPL (>= 2)'
RENAMED = 'row,area,farm,type,diet,calving,kg,ill,positives,tested'


def zipped(folder: str, filename: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(f'{folder}/{filename}', text)
    return buffer.getvalue()


def cranTarball(package: str, licence: str, table: pd.DataFrame, name: str) -> bytes:
    """A CRAN source tarball: a DESCRIPTION and the table as `data/<name>.rds`."""
    description = f'Package: {package}\nVersion: 1.0\nLicense: {licence}\n'
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
    merger.measure()
    merger.writeManifest()
    merger.summarise()
    merger.report()
    return merger


def readRows(path: Path) -> list[dict]:
    return readCsv(path).to_dict('records')


def emptyCensus(registry: Path) -> None:
    """The repository's registry/ always holds both census files; a scratch one starts with
    them empty."""
    for table in (REGISTRY, EXCLUDED):
        writeCsv(pd.DataFrame(columns=table.columns), registry / f'{table.name}.csv')


def scratchMerger(registry: Path, survey: Path) -> Merger:
    """A merger over a scratch registry whose loader fetches the two zips from memory."""
    herdsText = (FIXTURES / 'herds.csv').read_text()
    cattleText = RENAMED + herdsText[herdsText.index('\n') :]
    archives = {
        HERDS_URL: zipped('herds', 'herds.csv', herdsText),
        CATTLE_URL: zipped('cattle', 'cattle.csv', cattleText),
        PENS_URL: cranTarball('pens', PENS_LICENCE, pd.read_csv(FIXTURES / 'herds.csv'), 'herds'),
    }
    sources = {
        'cap': 40,
        'seed': 0,
        'tiers': {
            'D': {
                'herds': {
                    'kind': 'url',
                    'name': HERDS_URL,
                    'pin': sha(archives[HERDS_URL]),
                    'licence': 'CC0 1.0 Universal',
                }
            },
            'R': {
                'cattle': {
                    'kind': 'url',
                    'name': CATTLE_URL,
                    'pin': sha(archives[CATTLE_URL]),
                    'licence': 'not stated',
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
