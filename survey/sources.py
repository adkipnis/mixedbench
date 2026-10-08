"""The frame of the dimension survey: `sources.yaml` read into labelled pinned sources with
their tier and cap. Documented for humans in README.md; the pull and the merge both read it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from mixedbench.datasets import Source


@dataclass(frozen=True)
class Frame:
    tiers: dict[str, str]  # label -> tier
    sources: dict[str, Source]  # label -> pinned source
    caps: dict[str, int | None]  # label -> most objects read from it, None for all of them
    seed: int  # of the per-source draw where a source exceeds its cap


def readFrame(root: Path) -> Frame:
    file = yaml.safe_load((root / 'sources.yaml').read_text())
    tiers, sources, caps = {}, {}, {}
    for tier, entries in file['tiers'].items():
        for label, entry in (entries or {}).items():
            tiers[label] = tier
            sources[label] = Source(
                kind=entry['kind'],
                name=entry.get('name', label),
                pin=str(entry['pin']),
                checksum=entry.get('checksum'),
                path=entry.get('path'),
                file=entry.get('file'),
                layout=layout(entry),
            )
            caps[label] = entry.get('cap', file.get('cap'))
    return Frame(tiers, sources, caps, file['seed'])


def layout(entry: dict) -> tuple[str, ...] | None:
    """The columns of a headerless text file, as the frame lists them."""
    if 'layout' not in entry:
        return None
    return tuple(entry['layout'])
