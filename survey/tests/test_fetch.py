"""The weekly fetch (#25): every source a registry object loads from, fetched through the loader
with checksum verification, each failing source reported once by its label (ADR 0003)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fetch import WeeklyFetch
from mixedbench.datasets import Loader, ManifestRow, Source

TABLE = b'group,y\na,1\nb,2\n'


class Server:
    """Answers the URLs it holds and None to any other, as the loader tests' server."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files

    def __call__(self, url: str) -> bytes | None:
        return self.files.get(url)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def url(label: str) -> str:
    return f'https://example.org/{label}.csv'


def urlSource(label: str, checksum: str) -> Source:
    """A url source as `registry.sources()` reads one: the file's sha256 is pin and checksum."""
    return Source(kind='url', name=url(label), pin=checksum, checksum=checksum)


def test_the_wrong_checksum_and_the_missing_source_are_reported_and_nothing_else(tmp_path):
    """The script's verdict: a served file whose digest differs from its pin and a file the
    host no longer has fail; a good source passes, and a pinned source no registry object
    loads from is never fetched, so its absence opens no issue."""
    sources = {
        'good': urlSource('good', sha(TABLE)),
        'tampered': urlSource('tampered', '0' * 64),
        'gone': urlSource('gone', sha(TABLE)),
        'unused': urlSource('unused', sha(TABLE)),
    }
    registered = ['good', 'tampered', 'gone']
    manifest = {}
    for label in registered:
        manifest[sources[label], f'{label}.csv'] = ManifestRow(f'{label}.csv', sha(TABLE))
    server = Server({url('good'): TABLE, url('tampered'): TABLE})
    weekly = WeeklyFetch(sources, Loader(tmp_path, fetch=server, manifest=manifest))
    failures = weekly.failures()
    assert set(failures) == {'tampered', 'gone'}
    assert 'checksum' in failures['tampered']
    assert 'not at' in failures['gone']
