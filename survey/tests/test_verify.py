"""The verification script at its file seams: registry and help pages in, the scan's hits file
out (#10)."""

import csv
from pathlib import Path

from schema import REGISTRY
from verify import Verifier


def writeRegistry(registry: Path, rows: list[dict]) -> None:
    """A registry.csv of the real shape, every column not given left empty."""
    registry.mkdir(parents=True, exist_ok=True)
    with open(registry / 'registry.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY.columns, restval='', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def writeHelp(registry: Path, source: str, object: str, text: str) -> None:
    dir = registry / 'help' / source
    dir.mkdir(parents=True, exist_ok=True)
    (dir / f'{object}.txt').write_text(text)


def readRows(path: Path) -> list[dict]:
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def hitKey(hit: dict) -> tuple[str, ...]:
    return (hit['source'], hit['object'], hit['model_index'], hit['field'], hit['keyword'])


def test_scan_lists_each_planted_keyword_once_with_its_snippet(tmp_path):
    """A keyword planted in `notes`, in `formula` and in a help page shows up once each, with the
    words around it, so the hand look reads snippets instead of rows. The two spellings of
    negative binomial in one note are two occurrences; `glmer.nb` matching both `glmer.nb` and
    `nb` is one, and "prior to" is not a prior."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    rows = [
        {'source': 'pens', 'object': 'herds', 'model_index': '1', 'formula': 'y ~ x + (1 | herd)',
         'notes': 'Fitted as a negative binomial in the book; the help page says neg. bin. too.'},
        {'source': 'pens', 'object': 'pigs', 'model_index': '1', 'formula': 'glmer.nb(y ~ x + (1 | pen))', 'notes': ''},
        {'source': 'pens', 'object': 'goats', 'model_index': '1', 'formula': 'y ~ x + (1 | farm)', 'notes': ''},
    ]  # fmt: skip
    writeRegistry(registry, rows)
    writeHelp(registry, 'pens', 'herds', 'A plain description of herds.')
    writeHelp(registry, 'pens', 'pigs', 'Weighed prior to slaughter.')
    writeHelp(registry, 'pens', 'goats', 'The authors put a Normal(0, 1) prior\non every slope.')
    verifier = Verifier(registry, survey)

    verifier.scan()

    hits = readRows(survey / 'scan_hits.csv')
    assert sorted(hitKey(h) for h in hits) == [
        ('pens', 'goats', '1', 'help', 'prior'),
        ('pens', 'herds', '1', 'notes', 'negative binomial'),
        ('pens', 'herds', '1', 'notes', 'negative binomial'),
        ('pens', 'pigs', '1', 'formula', 'negative binomial'),
    ]
    snippets = {h['snippet'] for h in hits}
    assert 'The authors put a Normal(0, 1) prior on every slope.' in snippets  # newline collapsed
    assert 'glmer.nb(y ~ x + (1 | pen))' in snippets
