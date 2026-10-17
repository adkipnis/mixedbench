"""The frame of the dimension survey: `sources.yaml` read into labelled pinned sources with
their tier and cap, in frame order. Documented for humans in README.md; the pull and the merge
both read it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from mixedbench import registry
from mixedbench.datasets import Source
from schema import TIERS

Key = tuple[str, str]  # (source label, object name)


@dataclass(frozen=True)
class Frame:
    tiers: dict[str, str]  # label -> tier
    sources: dict[str, Source]  # label -> pinned source
    caps: dict[str, int | None]  # label -> most objects read from it, None for all of them
    licenses: dict[str, str]  # label -> its `license:` key, verbatim, where it has one
    seed: int  # of the per-source draw where a source exceeds its cap
    labels: list[str]  # frame order: tier, then the order of `sources.yaml`

    def rank(self, key: Key) -> tuple[int, str]:
        """Frame order of an object: its source's place in the frame, then its name."""
        return (self.labels.index(key[0]), key[1])


def readFrame(root: Path) -> Frame:
    file = yaml.safe_load((root / 'sources.yaml').read_text())
    tiers, sources, caps, licenses = {}, {}, {}, {}
    for tier, entries in file['tiers'].items():
        for label, entry in (entries or {}).items():
            tiers[label] = tier
            sources[label] = registry.source(label, entry)
            caps[label] = entry.get('cap')
            if 'license' in entry:
                licenses[label] = entry['license']
    labels = sorted(tiers, key=lambda label: TIERS.index(tiers[label]))
    return Frame(tiers, sources, caps, licenses, file['seed'], labels)
