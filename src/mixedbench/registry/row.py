"""The format of a `registry.csv` row: the CSV dialect, the columns, the vocabularies of the
columns the package reads and the cell grammars. The survey's merge writes the file through
this module; the contract reads it through `Row`."""

from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, get_args

import pandas as pd

# =====================================================================================
# vocabularies
# =====================================================================================
ResponseType = Literal['continuous', 'binary', 'count', 'binomial', 'ordinal', 'categorical']
# A departure from the contract's family rule as brms names it (ADR 0001, 0004); empty on the
# rule. A value is added when a documented model needs it, not in advance.
Family = Literal[
    'negbinomial', 'bernoulli(probit)', 'cumulative(probit)', 'Gamma(log)', 'lognormal',
    'zero_inflated_poisson', 'zero_inflated_negbinomial', 'hurdle_poisson', 'hurdle_negbinomial',
    'Beta', 'bernoulli(cloglog)', 'Gamma(identity)', 'zero_inflated_beta', 'student', 'gaussian',
    'acat', 'weibull', 'cox',
]  # fmt: skip
ColumnType = Literal['categorical', 'ordered', 'continuous']  # what `types` may declare

RESPONSE_TYPES: tuple[str, ...] = get_args(ResponseType)
FAMILIES: tuple[str, ...] = get_args(Family)
COLUMN_TYPES: tuple[str, ...] = get_args(ColumnType)


# =====================================================================================
# csv dialect: every cell a quoted string, an empty cell the empty string
# =====================================================================================
def readCsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def writeCsv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, quoting=csv.QUOTE_ALL)


# =====================================================================================
# cell grammars
# =====================================================================================
# `;`-separated lists of column names of the loaded table
COLUMN_LIST_COLUMNS = ('covariates', 'ignore')
# `;`-separated lists of terms, a term a column name or `a:b` with every part a column name: a
# grouping factor on the combination of two columns (`(1|Block:Variety)`) or an interaction
TERM_COLUMNS = ('grouping_factors', 'interactions')


def splitList(text: str) -> tuple[str, ...]:
    """A `;`-list: `a;b` -> (a, b), the empty cell the empty list."""
    return tuple(t.strip() for t in text.split(';') if t.strip())


def parts(term: str) -> tuple[str, ...]:
    """A term `a:b` names the columns it combines: a grouping factor on their combination
    (`(1|Block:Variety)`) or an interaction; a plain column is a term of one part."""
    return tuple(term.split(':'))


def parseTypes(text: str) -> dict[str, str]:
    """`col=categorical;col2=continuous` -> {col: kind}."""
    pairs = [entry.partition('=') for entry in splitList(text)]
    return {col.strip(): kind.strip() for col, _, kind in pairs}


# =====================================================================================
# the row
# =====================================================================================
@dataclass(frozen=True)
class Row:
    """One row of `registry.csv`, its fields the file's columns in file order. A scalar cell
    stays a string, the empty cell `''`."""

    # identity; `tier`, `sources`, `reader` and `licence` are filled by the survey's merge
    source: str
    tier: str
    sources: tuple[str, ...]  # `source:object` of every duplicate folded in, the row's own first
    object: str
    reader: str
    licence: str
    model_index: int
    # the documented model, every name a column of the loaded table or a term of them
    response: str
    response_type: ResponseType
    trials: str
    family: Family | Literal['']
    grouping_factors: tuple[str, ...]
    covariates: tuple[str, ...]
    interactions: tuple[str, ...]
    ignore: tuple[str, ...]
    types: dict[str, ColumnType]
    formula: str
    documented_prior: str
    published_model: str
    # bookkeeping
    domain: str
    confidence: str
    notes: str

    @classmethod
    def parse(cls, cells: dict[str, str]) -> Row:
        """A row of cells as the dialect reads them, typed; a cell the grammar or a vocabulary
        refuses raises naming the row and the column."""
        refusals = cls.refusals(cells)
        if refusals:
            key = ' '.join(cells[c] for c in ('source', 'object', 'model_index'))
            raise ValueError('; '.join(f'registry row {key}, column {c}: {r}' for c, r in refusals))
        typed = dict(cells)
        for column in ('sources', *COLUMN_LIST_COLUMNS, *TERM_COLUMNS):
            typed[column] = splitList(cells[column])
        typed['model_index'] = int(cells['model_index'])
        typed['types'] = parseTypes(cells['types'])
        return cls(**typed)

    @staticmethod
    def refusals(cells: dict[str, str]) -> list[tuple[str, str]]:
        """(column, reason) per refused cell."""
        refusals = []
        if not cells['model_index'].isdigit():
            refusals.append(('model_index', f'not an integer: {cells["model_index"]}'))
        if cells['response_type'] not in RESPONSE_TYPES:
            refusals.append(('response_type', f'not a response type: {cells["response_type"]}'))
        if cells['family'] not in ('', *FAMILIES):
            refusals.append(('family', f'not a family: {cells["family"]}'))
        for kind in parseTypes(cells['types']).values():
            if kind not in COLUMN_TYPES:
                refusals.append(('types', f'not a column type: {kind}'))
        for column in TERM_COLUMNS:
            for term in splitList(cells[column]):
                if '' in parts(term):
                    refusals.append((column, f'a term with an empty part: {term}'))
        return refusals


COLUMNS: tuple[str, ...] = tuple(f.name for f in fields(Row))
