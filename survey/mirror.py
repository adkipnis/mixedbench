"""Mirror the CC0 files of the registry's Dryad sources as assets of a GitHub release.

Dryad answers a scripted download with 401, so a user's loader could not fetch them; their
CC0 license permits a copy (ADR 0003). Each file is taken from the survey's cache, checked
against its pin, uploaded as `<label>__<file>`, and its URL written into the entry's
`mirror:` in `sources.yaml`; the Dryad URL stays the source and is asked first. Run from the
repo root:

    uv run python survey/mirror.py --tag mirror-1
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from mixedbench.datasets import Source
from mixedbench.registry.row import readCsv
from sources import readFrame

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
REPOSITORY = 'adkipnis/mixedbench'
HOST = 'datadryad.org'
CC0 = 'https://spdx.org/licenses/CC0-1.0.html'
NOTES = """CC0 copies of the files of the registry's Dryad sources, which Dryad refuses to a
script (HTTP 401). Each asset is `<source label>__<file>`; its sha256 is the source's pin in
`registry/sources.yaml`, where the Dryad URL stays the source and is asked first (ADR 0003)."""


# =====================================================================================
# pipeline: registry's Dryad sources -> verified copies -> release -> sources.yaml
# =====================================================================================
class Mirror:
    def __init__(self, registryDir: Path, tag: str) -> None:
        self.registryDir, self.tag = Path(registryDir), tag
        self.frame = readFrame(self.registryDir)

    def run(self) -> None:
        labels = self.dryadLabels()
        if not labels:  # a rerun after every Dryad source is mirrored creates no empty release
            print('every Dryad source of the registry has a mirror')
            return
        with tempfile.TemporaryDirectory() as staging:
            assets = [self.stage(label, Path(staging)) for label in labels]
            self.upload(assets)
        self.writeMirrors(labels)

    # ---------------------------------------------------------------------------------
    # pipeline
    # ---------------------------------------------------------------------------------
    def dryadLabels(self) -> list[str]:
        """The Dryad sources a registry object loads from that have no mirror yet, so that a
        rerun adds no second `mirror:` key; each must be CC0."""
        rows = readCsv(self.registryDir / 'registry.csv')
        sources = self.frame.sources
        labels = sorted({label for label in rows['source'] if HOST in sources[label].name})
        unmirrored = [label for label in labels if sources[label].mirror is None]
        for label in unmirrored:
            if self.frame.licenses[label] != CC0:
                raise ValueError(f'{label} is not CC0: no mirror')
        return unmirrored

    def stage(self, label: str, staging: Path) -> Path:
        """The cached download, checked against its pin, under its asset name."""
        source = self.frame.sources[label]
        cached = self.registryDir / 'cache' / 'url' / source.pin / source.file
        digest = hashlib.sha256(cached.read_bytes()).hexdigest()
        if digest != source.pin:
            raise ValueError(f'{cached} checksum {digest} differs from pinned {source.pin}')
        asset = staging / self.assetName(label, source)
        shutil.copyfile(cached, asset)
        return asset

    def upload(self, assets: list[Path]) -> None:
        title = 'Mirror of CC0 files the hosts refuse to scripts'
        command = ['gh', 'release', 'create', self.tag, '--repo', REPOSITORY]
        command += ['--title', title, '--notes', NOTES, *map(str, assets)]
        subprocess.run(command, check=True)

    def writeMirrors(self, labels: list[str]) -> None:
        """`mirror:` appended to each entry's flow mapping; the rest of the file untouched."""
        file = self.registryDir / 'sources.yaml'
        frame = file.read_text()
        for label in labels:
            line = self.entryLine(frame, label)
            url = f'https://github.com/{REPOSITORY}/releases/download/{self.tag}/{self.assetName(label, self.frame.sources[label])}'  # fmt: skip
            mirrored = line.replace('}', f', mirror: "{url}"}}', 1)
            frame = frame.replace(line, mirrored, 1)
        file.write_text(frame)

    @staticmethod
    def entryLine(frame: str, label: str) -> str:
        match = re.search(rf'^ +{re.escape(label)}: \{{.*$', frame, re.MULTILINE)
        if match is None:
            raise KeyError(f'{label}: no flow-mapping entry in sources.yaml')
        return match.group(0)

    @staticmethod
    def assetName(label: str, source: Source) -> str:
        return f'{label}__{source.file}'


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tag', required=True, help='the release to create, e.g. mirror-1')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml, registry.csv and cache/')
    args = parser.parse_args()
    # fmt: on
    mirror = Mirror(args.registry, args.tag)
    mirror.run()
