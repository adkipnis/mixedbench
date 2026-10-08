"""A scratch survey root: `sources.yaml` pins two url sources served from memory by an injected
fetch, `herds` (Tier D) and `cattle` (Tier R), the same hand-made grouped table under two
column namings, so that duplicate flagging has a real pair to find. The table: region > herd
nested, herd `h4` a singleton, `breed` a four-level categorical, `feed` herd-level, `weight`
continuous, `sick` binary, `cases` out of `trials` binomial, `id` a column to ignore.
"""

import hashlib
import io
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # survey scripts are research code outside the package

from merge import Merger
from mixedbench.datasets import Loader

FIXTURES = HERE / 'fixtures'
HERDS_URL = 'https://example.org/herds.zip'
CATTLE_URL = 'https://example.org/cattle.zip'
RENAMED = 'row,area,farm,type,diet,calving,kg,ill,positives,tested'


def zipped(folder: str, filename: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(f'{folder}/{filename}', text)
    return buffer.getvalue()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scratchMerger(registry: Path, survey: Path) -> Merger:
    """A merger over a scratch registry whose loader fetches the two zips from memory."""
    herdsText = (FIXTURES / 'herds.csv').read_text()
    cattleText = RENAMED + herdsText[herdsText.index('\n') :]
    archives = {
        HERDS_URL: zipped('herds', 'herds.csv', herdsText),
        CATTLE_URL: zipped('cattle', 'cattle.csv', cattleText),
    }
    sources = {
        'cap': 40,
        'seed': 0,
        'tiers': {
            'D': {'herds': {'kind': 'url', 'name': HERDS_URL, 'pin': sha(archives[HERDS_URL])}},
            'R': {'cattle': {'kind': 'url', 'name': CATTLE_URL, 'pin': sha(archives[CATTLE_URL])}},
        },
    }
    registry.mkdir(exist_ok=True)
    (registry / 'sources.yaml').write_text(yaml.safe_dump(sources, sort_keys=False))
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
