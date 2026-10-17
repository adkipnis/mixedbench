"""row.py defines the format of a `registry.csv` row.

pipeline:
---------
registry.csv
-> cells as strings                     readCsv
-> typed Row | refused cells            Row.parse | Row.refusals
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, get_args

import pandas as pd
from mixedbench.datasets import ColumnType

# =====================================================================================
# vocabularies
# =====================================================================================
# the legal values per column; `Row.refusals` refuses any other.
ResponseType = Literal['continuous', 'binary', 'count', 'binomial', 'ordinal', 'categorical']
# brms's name of a family that departs from the contract's family rule; '' keeps the rule
Family = Literal[
    'negbinomial', 'bernoulli(probit)', 'cumulative(probit)', 'Gamma(log)', 'lognormal',
    'zero_inflated_poisson', 'zero_inflated_negbinomial', 'hurdle_poisson', 'hurdle_negbinomial',
    'Beta', 'bernoulli(cloglog)', 'Gamma(identity)', 'zero_inflated_beta', 'student', 'gaussian',
    'acat', 'weibull', 'cox',
]  # fmt: skip
Verified = Literal['hand', 'high', 'second-reading']


# =====================================================================================
# csv helpers
# =====================================================================================
# every cell is a quoted string and reads back exactly as written.
def readCsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def writeCsv(table: pd.DataFrame, path: Path) -> None:
    table.to_csv(path, index=False, quoting=csv.QUOTE_ALL)


# =====================================================================================
# cell formats
# =====================================================================================
# a cell holding more than one value writes it as text
# (;-list, an a:b term, an x|g slope, col=kind types).
COLUMN_LIST_COLUMNS = ('covariates', 'ignore')
TERM_COLUMNS = ('grouping_factors', 'interactions')


def splitList(text: str) -> tuple[str, ...]:
    """A `;`-list: `a;b` -> (a, b), the empty cell the empty list."""
    return tuple(t.strip() for t in text.split(';') if t.strip())


def parts(term: str) -> tuple[str, ...]:
    """A term `a:b` names the columns it combines: a grouping factor on their combination
    (`(1|Block:Variety)`) or an interaction; a plain column is a term of one part."""
    return tuple(term.split(':'))


# a `random_slopes` term: covariate `x`, then `|` (correlated with the intercept of `g`) or `||`
# (uncorrelated), then grouping factor `g`; a name may hold spaces (`activity 1`), not at its ends
NAME = r'[^|\s](?:[^|]*[^|\s])?'
SLOPE_TERM = re.compile(rf'(?P<covariate>{NAME})(?P<bars>\|\|?)(?P<factor>{NAME})')


@dataclass(frozen=True)
class SlopeTerm:
    """A random slope as the contract reads it (never the `x|g` text)."""

    covariate: str
    factor: str  # a term of `grouping_factors`, `a:b` for a composite
    correlated: bool

    @classmethod
    def parse(cls, text: str) -> SlopeTerm:
        match = SLOPE_TERM.fullmatch(text)
        return cls(match['covariate'], match['factor'], correlated=match['bars'] == '|')


def parseTypes(text: str) -> dict[str, str]:
    """`col=categorical;col2=continuous` -> {col: kind}."""
    pairs = [entry.partition('=') for entry in splitList(text)]
    return {col.strip(): kind.strip() for col, _, kind in pairs}


# =====================================================================================
# row class
# =====================================================================================
@dataclass(frozen=True)
class Row:
    """One row of `registry.csv`, its fields are the file's columns.
    A scalar cell stays a string, the empty cell is `''`."""

    # identity; `tier`, `sources`, `reader` and `license` are filled by the survey's merge
    source: str
    tier: str
    sources: tuple[str, ...]  # `source:object` of every duplicate folded in, the row's own first
    object: str
    reader: str
    license: str
    model_index: int
    # the documented model, every name a column of the loaded table or a term of them
    response: str
    response_type: ResponseType
    trials: str
    family: Family | Literal['']
    grouping_factors: tuple[str, ...]
    covariates: tuple[str, ...]
    interactions: tuple[str, ...]
    random_slopes: tuple[SlopeTerm, ...]
    ignore: tuple[str, ...]
    types: dict[str, ColumnType]
    formula: str
    documented_prior: str
    published_model: str
    # bookkeeping
    domain: str
    confidence: str
    verified: Verified
    notes: str

    @property
    def id(self) -> str:
        return f'{self.source}/{self.object}/{self.model_index}'

    @classmethod
    def parse(cls, cells: dict[str, str]) -> Row:
        refusals = cls.refusals(cells)
        if refusals:
            key = ' '.join(cells[c] for c in ('source', 'object', 'model_index'))
            raise ValueError('; '.join(f'registry row {key}, column {c}: {r}' for c, r in refusals))
        typed = dict(cells)
        for column in ('sources', *COLUMN_LIST_COLUMNS, *TERM_COLUMNS):
            typed[column] = splitList(cells[column])
        typed['model_index'] = int(cells['model_index'])
        typed['types'] = parseTypes(cells['types'])
        typed['random_slopes'] = tuple(
            SlopeTerm.parse(t) for t in splitList(cells['random_slopes'])
        )
        return cls(**typed)

    @staticmethod
    def refusals(cells: dict[str, str]) -> list[tuple[str, str]]:
        """(column, reason) per refused cell."""
        refusals = []
        if not cells['model_index'].isdigit():
            refusals.append(('model_index', f'not an integer: {cells["model_index"]}'))
        if cells['response_type'] not in get_args(ResponseType):
            refusals.append(('response_type', f'not a response type: {cells["response_type"]}'))
        if cells['family'] not in ('', *get_args(Family)):
            refusals.append(('family', f'not a family: {cells["family"]}'))
        for kind in parseTypes(cells['types']).values():
            if kind not in get_args(ColumnType):
                refusals.append(('types', f'not a column type: {kind}'))
        for column in TERM_COLUMNS:
            for term in splitList(cells[column]):
                if '' in parts(term):
                    refusals.append((column, f'a term with an empty part: {term}'))
        for term in splitList(cells['random_slopes']):
            refusals += Row.slopeRefusals(cells, term)
        covariates = splitList(cells['covariates'])
        for term in splitList(cells['interactions']):
            for part in parts(term):
                if part != '' and part not in covariates:
                    refusals.append(('interactions', f'{part} is not a covariate'))
        # a column is a grouping factor or a covariate, never both;
        # but a part of a composite factor may be a covariate
        for factor in splitList(cells['grouping_factors']):
            if factor in covariates:
                refusals.append(('grouping_factors', f'{factor} is also a covariate'))
        if cells['verified'] not in get_args(Verified):
            refusals.append(('verified', f'not a verification: {cells["verified"]}'))
        return refusals

    @staticmethod
    def slopeRefusals(cells: dict[str, str], term: str) -> list[tuple[str, str]]:
        """A slope term is `x|g` or `x||g`, `x` a covariate and `g` a grouping factor of its
        row."""
        if SLOPE_TERM.fullmatch(term) is None:
            return [('random_slopes', f'not a slope term: {term}')]
        slope = SlopeTerm.parse(term)
        refusals = []
        if slope.covariate not in splitList(cells['covariates']):
            refusals.append(('random_slopes', f'{slope.covariate} is not a covariate'))
        if slope.factor not in splitList(cells['grouping_factors']):
            refusals.append(('random_slopes', f'{slope.factor} is not a grouping factor'))
        return refusals


# the file's ordered columns; the merge writes them in this order (survey/schema.py)
COLUMNS: tuple[str, ...] = tuple(f.name for f in fields(Row))
