"""The random slopes of each registry row's documented model (ADR 0001, #27): the parser reads
the random terms `(lhs | rhs)` of `formula` and fills `random_slopes` where every term is a sum
of covariates over a grouping factor; every other shape is reported with its row and formula
for Alex to decide. Run from the repo root:

    uv run python survey/slopes.py
    uv run python survey/merge.py survey/shards/registry_slopes.csv
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from mixedbench.registry.row import parseTypes, readCsv, splitList, writeCsv
from schema import REGISTRY

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
BARS = re.compile(r'(\|\|?)')  # `|` correlated with the intercept of the factor, `||` not


# =====================================================================================
# the parser
# =====================================================================================
def randomSlopes(registry: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """`random_slopes` per registry row, on the registry's index, and the report of the rows
    left empty for a shape the parser does not fill, one reason per offending term, with the
    terms it recognised as candidates for Alex's decision."""
    slopes = []
    reported = []
    for _, row in registry.iterrows():
        reader = SlopeReader(row)
        reasons = unique(reader.reasons)
        if reasons:
            reported.append(
                {
                    **row[list(REGISTRY.key)].to_dict(),
                    'formula': row['formula'],
                    'reason': '; '.join(reasons),
                    'candidates': ';'.join(reader.slopes),
                }
            )
            slopes.append('')
        else:
            slopes.append(';'.join(reader.slopes))
    report = pd.DataFrame(reported, columns=[*REGISTRY.key, 'formula', 'reason', 'candidates'])
    return pd.Series(slopes, index=registry.index), report


class SlopeReader:
    """The random terms of one registry row's `formula`, read against the row's covariates,
    grouping factors and declared categorical columns: the slope terms, and why a term is no
    plain sum of covariates over a grouping factor of the row."""

    def __init__(self, row: pd.Series) -> None:
        self.covariates = splitList(row['covariates'])
        self.factors = splitList(row['grouping_factors'])
        types = parseTypes(row['types'])
        self.categorical = [column for column, kind in types.items() if kind in ('categorical', 'ordered')]  # fmt: skip
        self.slopes = []
        self.reasons = []
        for term in randomTerms(row['formula']):
            self.read(term)

    def read(self, term: str) -> None:
        pieces = BARS.split(term)  # 5 pieces for brms's `(1 + x | c | g)`
        lhs, bars, rhs = pieces[0], pieces[1], pieces[-1]
        parts = [part.strip() for part in lhs.split('+')]
        named = [part for part in parts if part not in ('0', '1')]
        nested = nestedFactors(rhs)
        if not named:  # an intercept-only term has no slope, whatever its factor or id
            return
        if len(pieces) != 3:
            self.reasons.append('not a random term')
            return
        if '0' in parts:
            self.reasons.append('no random intercept')
        for x in named:
            self.readSlope(x, bars)
        for g in nested:
            if g not in self.factors:
                self.reasons.append(f'{g} is not a grouping factor')
        held = [x for x in mainEffects(named) if self.holds(x, bars)]
        factors = [g for g in nested if g in self.factors]
        self.slopes += [f'{x}{bars}{g}' for x in held for g in factors]

    def readSlope(self, x: str, bars: str) -> None:
        interaction = ('*' in x or ':' in x) and '(' not in x  # not `sin(2*pi*Time)`
        if interaction:
            self.reasons.append('interaction in the slope')
        elif x not in self.covariates:
            self.reasons.append(f'{x} is not a covariate')
        elif bars == '||' and x in self.categorical:
            # lme4 keeps a factor's indicator columns correlated under `||`, brms does not
            self.reasons.append(f'double bar on categorical {x}')

    def holds(self, x: str, bars: str) -> bool:
        """Whether `random_slopes` can hold the slope on `x`."""
        return x in self.covariates and not (bars == '||' and x in self.categorical)


def unique(reasons: list[str]) -> list[str]:
    """`reasons` in order, each once."""
    kept = []
    for reason in reasons:
        if reason not in kept:
            kept.append(reason)
    return kept


def mainEffects(named: list[str]) -> list[str]:
    """The columns of a left side's slopes: `a * b` expands to `a + b + a:b` (R's formula
    semantics), so its main effects are slopes; an interaction-only `a:b` names none."""
    effects = []
    for part in named:
        if '*' in part and '(' not in part:
            effects += [name.strip() for name in part.split('*')]
        elif ':' not in part:
            effects.append(part)
    return effects


def nestedFactors(rhs: str) -> list[str]:
    """`a/b` is `a` and `a:b` (lme4); a plain factor is itself."""
    levels = [name.strip() for name in rhs.split('/')]
    return [':'.join(levels[: i + 1]) for i in range(len(levels))]


def randomTerms(formula: str) -> list[str]:
    """The text inside each top-level bracket of `formula` that holds a `|` outside any inner
    bracket: `(x + I(x^2) | g)` is a random term, `(a + b)` and `f(a, b)` are not."""
    terms = []
    depth = 0
    for i, char in enumerate(formula):
        if char == '(':
            depth += 1
            if depth == 1:
                start = i + 1
                bar = False
        elif char == ')':
            depth -= 1
            if depth == 0 and bar:
                terms.append(formula[start:i])
        elif char == '|' and depth == 1:
            bar = True
    return terms


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    registry = readCsv(HERE.parent / 'registry' / 'registry.csv')
    registry['random_slopes'], report = randomSlopes(registry)
    writeCsv(registry[list(REGISTRY.agentColumns)], HERE / 'shards' / 'registry_slopes.csv')
    print(f'{(registry["random_slopes"] != "").sum()} rows filled, {len(report)} reported:')
    print(report.to_string(index=False))
