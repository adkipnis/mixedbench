"""The census and its tables agree (#14): a re-pull that changes what the loader enumerates
leaves exclusions keyed on objects that are gone and objects no reader saw, and only this
check notices."""

from pathlib import Path

import pandas as pd
from mixedbench.registry.row import readCsv, splitList
from sources import Key

ROOT = Path(__file__).resolve().parents[2]


def keys(rows: pd.DataFrame) -> set[Key]:
    return set(zip(rows['source'], rows['object']))


def registryMembers(registry: pd.DataFrame) -> set[Key]:
    """Every object a registry row stands for, the duplicates folded into it included."""
    members = set()
    for listed in registry['sources']:
        for member in splitList(listed):
            source, object = member.split(':', 1)
            members.add((source, object))
    return members


def sameMembers(duplicates: pd.DataFrame) -> set[Key]:
    """Both objects of a pair confirmed the same: a twin of an excluded object (jing_2020_osf_2's
    copies of jing_2020_osf) is accounted for by its twin's exclusion."""
    same = duplicates[duplicates['verdict'] == 'same']
    first = set(zip(same['source_a'], same['object_a']))
    return first | set(zip(same['source_b'], same['object_b']))


def test_every_exclusion_names_a_census_object():
    census = keys(readCsv(ROOT / 'survey' / 'candidates.csv'))
    excluded = keys(readCsv(ROOT / 'registry' / 'excluded.csv'))
    assert sorted(excluded - census) == []


def test_every_census_object_a_reader_should_see_is_filed():
    """An object a source's cap left out is never read; every other one is a registry row, an
    exclusion, or a confirmed duplicate of either."""
    candidates = readCsv(ROOT / 'survey' / 'candidates.csv')
    read = keys(candidates[candidates['capped'] != 'yes'])
    filed = registryMembers(readCsv(ROOT / 'registry' / 'registry.csv'))
    filed |= keys(readCsv(ROOT / 'registry' / 'excluded.csv'))
    filed |= sameMembers(readCsv(ROOT / 'survey' / 'duplicates.csv'))
    assert sorted(read - filed) == []
