"""The contract is documented where agents and readers look: README.md names every column
and allowed value of schema.py, and the read prompt speaks the glossary (CONTEXT.md)."""

import re
from pathlib import Path
from typing import get_args

import pytest
from columns import COLUMN_COLUMNS
from dimensions import DIMENSION_COLUMNS
from groups import COLUMN_FACTOR_COLUMNS
from mixedbench.registry.row import Family, ResponseType, Verified
from pairs import FACTOR_PAIR_COLUMNS
from schema import ALLOWED, CANDIDATE_COLUMNS, SCREENS, TABLES

HERE = Path(__file__).resolve().parents[1]
README = (HERE / 'README.md').read_text()
PROMPT = (HERE / 'prompts' / 'read.md').read_text()


@pytest.mark.parametrize('table', list(TABLES))
def test_readme_documents_every_column(table):
    for column in TABLES[table].columns:
        assert re.search(rf'`{column}`', README), f'{table}.{column} undocumented'


@pytest.mark.parametrize('columns', [DIMENSION_COLUMNS, COLUMN_COLUMNS, COLUMN_FACTOR_COLUMNS, FACTOR_PAIR_COLUMNS], ids=['dimensions', 'columns', 'column_factors', 'factor_pairs'])  # fmt: skip
def test_readme_documents_every_measured_column(columns):
    for column in columns:
        assert re.search(rf'`{column}`', README), f'{column} undocumented'


@pytest.mark.parametrize('table', list(TABLES))
def test_readme_documents_every_allowed_value(table):
    for column, values in ALLOWED[table].items():
        for value in values:
            assert f'`{value}`' in README, f'{table}.{column} value {value!r} undocumented'


def test_readme_documents_the_row_vocabularies():
    """The registry's vocabularies are the package's row grammar, not schema.py's (#48)."""
    values = (*get_args(ResponseType), *get_args(Family), *get_args(Verified))
    for value in values:
        assert f'`{value}`' in README, f'registry value {value!r} undocumented'


def test_readme_documents_the_candidates_and_the_frame():
    """The pull's two contracts (#19): every candidates.csv column, and every key of
    sources.yaml a hand edit may touch."""
    for column in CANDIDATE_COLUMNS:
        assert re.search(rf'`{column}`', README), f'candidates.{column} undocumented'
    for key in ('cap', 'seed', 'dropped', 'kind', 'name', 'pin', 'checksum', 'path'):
        assert re.search(rf'`{key}`', README), f'sources.yaml key {key!r} undocumented'
    for verdict in SCREENS:
        assert f'`{verdict}`' in README, f'screen verdict {verdict!r} undocumented'


def test_read_prompt_uses_the_glossary_and_forbids_measured_numbers():
    for term in ('grouping factor', 'response', 'family'):
        assert term in PROMPT
    for avoided in ('cluster variable', 'multilevel', 'hierarchical model'):
        assert avoided not in PROMPT
    assert 'never' in PROMPT and 'registry.csv' in PROMPT
