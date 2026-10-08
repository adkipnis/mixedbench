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
from metabeta.glmm.datasets import Loader

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


@pytest.fixture
def merger(tmp_path: Path) -> Merger:
    """A merger over a scratch root whose loader fetches the two zips from memory."""
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
    (tmp_path / 'sources.yaml').write_text(yaml.safe_dump(sources, sort_keys=False))
    (tmp_path / 'shards').mkdir()

    def serve(url: str) -> bytes | None:
        return archives.get(url)

    return Merger(tmp_path, loader=Loader(tmp_path / 'cache', fetch=serve))
