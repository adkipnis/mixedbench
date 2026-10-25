"""The contract is documented where agents and readers look: docs/registry.md names every column
and allowed value of the registry's files, README.md those of the survey's own, and the read
and flat prompts speak the glossary (CONTEXT.md)."""

import re
from pathlib import Path
from typing import get_args

import pytest
from columns import COLUMN_COLUMNS
from dimensions import DIMENSION_COLUMNS
from fits import FIT_COLUMNS
from flat import FLAT_COLUMN_COLUMNS, FLAT_COLUMNS, SCREEN_COLUMNS
from groups import COLUMN_FACTOR_COLUMNS
from mixedbench.frequentist import Status
from mixedbench.registry.row import Family, ResponseType, Verified
from pairs import FACTOR_PAIR_COLUMNS
from schema import ALLOWED, CANDIDATE_COLUMNS, SCREENS, TABLES

HERE = Path(__file__).resolve().parents[1]
README = (HERE / 'README.md').read_text()
REGISTRY = (HERE.parent / 'docs' / 'registry.md').read_text()
PROMPT = (HERE / 'prompts' / 'read.md').read_text()
FLAT_PROMPT = (HERE / 'prompts' / 'flat.md').read_text()
HOME = {
    'registry': REGISTRY,
    'excluded': REGISTRY,
    'duplicates': README,
    'dropped': README,
    'flat_verdicts': REGISTRY,  # beside the flat files a verdict decides membership of
    'flat_responses': REGISTRY,  # beside the flat files a response leaves
}
MEASURED_COLUMNS = {
    'dimensions': DIMENSION_COLUMNS,
    'columns': COLUMN_COLUMNS,
    'column_factors': COLUMN_FACTOR_COLUMNS,
    'factor_pairs': FACTOR_PAIR_COLUMNS,
    'fits': FIT_COLUMNS,
    'flat': FLAT_COLUMNS,
    'flat_columns': FLAT_COLUMN_COLUMNS,
}


@pytest.mark.parametrize('table', list(TABLES))
def test_docs_document_every_column(table):
    for column in TABLES[table].columns:
        assert re.search(rf'`{column}`', HOME[table]), f'{table}.{column} undocumented'


@pytest.mark.parametrize('file', list(MEASURED_COLUMNS))
def test_registry_doc_documents_every_measured_column(file):
    for column in MEASURED_COLUMNS[file]:
        assert re.search(rf'`{column}`', REGISTRY), f'{file}.{column} undocumented'


@pytest.mark.parametrize('table', list(TABLES))
def test_docs_document_every_allowed_value(table):
    for column, values in ALLOWED[table].items():
        for value in values:
            assert f'`{value}`' in HOME[table], f'{table}.{column} value {value!r} undocumented'


def test_registry_doc_documents_the_row_vocabularies():
    """The registry's vocabularies are the package's row grammar and fit statuses, not
    schema.py's (#48)."""
    values = (*get_args(ResponseType), *get_args(Family), *get_args(Verified), *get_args(Status))
    for value in values:
        assert f'`{value}`' in REGISTRY, f'registry value {value!r} undocumented'


def test_readme_documents_the_candidates_and_the_frame():
    """The pull's two contracts (#19): every candidates.csv column, and every key of
    sources.yaml a hand edit may touch."""
    for column in CANDIDATE_COLUMNS:
        assert re.search(rf'`{column}`', README), f'candidates.{column} undocumented'
    for key in ('cap', 'seed', 'dropped', 'kind', 'name', 'pin', 'checksum', 'path'):
        assert re.search(rf'`{key}`', REGISTRY), f'sources.yaml key {key!r} undocumented'
    for verdict in SCREENS:
        assert f'`{verdict}`' in README, f'screen verdict {verdict!r} undocumented'


def test_read_prompt_uses_the_glossary_and_forbids_measured_numbers():
    for term in ('grouping factor', 'response', 'family'):
        assert term in PROMPT
    for avoided in ('cluster variable', 'multilevel', 'hierarchical model'):
        assert avoided not in PROMPT
    assert 'never' in PROMPT and 'registry.csv' in PROMPT


def test_readme_documents_the_flat_screen():
    for column in SCREEN_COLUMNS:
        assert re.search(rf'`{column}`', README), f'flat_screen.{column} undocumented'


def test_flat_prompt_uses_the_glossary_and_forbids_measured_numbers():
    """The second reading's brief speaks of flat tables and the three verdicts in the
    glossary's words, and a hidden grouping re-files through the read prompt's shards."""
    for term in ('flat table', 'grouping factor', *ALLOWED['flat_verdicts']['verdict']):
        assert term in FLAT_PROMPT
    for avoided in (
        'i.i.d.',
        'unclustered',
        'cluster variable',
        'multilevel',
        'hierarchical model',
    ):
        assert avoided not in FLAT_PROMPT
    for shard in ('shards/flat_', 'shards/dropped_', 'shards/registry_'):
        assert shard in FLAT_PROMPT
    assert 'never type a measured number' in FLAT_PROMPT
