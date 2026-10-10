"""The grouping factors of each registry row against its `formula` (#45): a factor the formula
nests as `a:b` while the row names `b` alone pools unrelated groups when `b`'s codes repeat
across `a` (nlme Wafer's sites 1–8 in every wafer). The audit runs once: it regroups those rows
as the composite, writes a shard of them, and reports every other formula factor the row does
not name for admission (#32) to decide. Run from the repo root:

    uv run python survey/factors.py
    uv run python survey/merge.py survey/shards/registry_factors.csv
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd
from mixedbench.datasets import Loader
from mixedbench.registry import manifest, sources
from mixedbench.registry.row import parseTypes, readCsv, splitList, writeCsv
from schema import REGISTRY
from slopes import BARS, nestedFactors, randomTerms, unique

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
REGISTRY_DIR = HERE.parent / 'registry'
REGROUPED_NOTE = ' Regrouped by #45: the nested factor named as its composite, its codes repeating across its parent.'  # fmt: skip


# =====================================================================================
# the audit
# =====================================================================================
def regroup(
    registry: pd.DataFrame, load: Callable[[pd.Series], pd.DataFrame]
) -> tuple[pd.Series, pd.DataFrame]:
    """`grouping_factors` per registry row, on the registry's index, with every pooled factor
    replaced by the formula's composite, and the report of each formula factor the row does not
    name with its reason; `load` gives a row's typed table and runs only for a reported row."""
    grouping = []
    reported = []
    for _, row in registry.iterrows():
        reader = FactorReader(row, load)
        grouping.append(';'.join(reader.factors))
        key = row[list(REGISTRY.key)].to_dict()
        reported += [key | {'factor': g, 'reason': why} for g, why in reader.reasons]
    report = pd.DataFrame(reported, columns=[*REGISTRY.key, 'factor', 'reason'])
    return pd.Series(grouping, index=registry.index), report


class FactorReader:
    """One registry row's grouping factors against the factors its `formula` groups by: a nested
    `a:b` that the row names by its last part `b`, and the formula never groups by `b` alone,
    pools unrelated groups when `b`'s codes repeat across `a`; the row takes `a:b` instead."""

    def __init__(self, row: pd.Series, load: Callable[[pd.Series], pd.DataFrame]) -> None:
        self.factors = list(splitList(row['grouping_factors']))
        self.formulaFactors = formulaFactors(row['formula'])
        self.reasons = []
        unnamed = [g for g in self.formulaFactors if g not in self.factors]
        if not unnamed:
            return
        self.df = load(row)
        for g in unnamed:
            self.read(g)

    def read(self, g: str) -> None:
        names = g.split(':')
        pooled = self.isColumns(names) and self.namedByLastPart(names) and self.codesRepeat(names)
        self.reasons.append((g, self.reason(g, names, pooled)))
        if pooled:
            self.factors[self.factors.index(names[-1])] = g

    def reason(self, g: str, names: list[str], pooled: bool) -> str:
        if pooled:
            return 'codes repeat: regrouped'
        if not self.isColumns(names):
            return 'no such column'
        if self.namedByLastPart(names):
            return 'codes unique'
        if any(factor.endswith(f':{g}') for factor in self.factors):
            return 'inside a composite of the row'
        if self.df[names].drop_duplicates().shape[0] == len(self.df):
            return 'one row per level'
        return 'not a grouping factor of the row'

    def isColumns(self, names: list[str]) -> bool:
        return all(name in self.df.columns for name in names)

    def namedByLastPart(self, names: list[str]) -> bool:
        last = names[-1]
        return len(names) > 1 and last in self.factors and last not in self.formulaFactors

    def codesRepeat(self, names: list[str]) -> bool:
        """Whether a code of the last factor lies in more than one combination of the others."""
        combinations = self.df[names].dropna().drop_duplicates()
        parents = combinations.groupby(names[-1], observed=True).size()
        return bool((parents > 1).any())


def formulaFactors(formula: str) -> list[str]:
    """Every factor the random terms of `formula` group by, `a/b` expanded, each once."""
    factors = [g for term in randomTerms(formula) for g in nestedFactors(BARS.split(term)[-1])]
    return unique(factors)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    registry = readCsv(REGISTRY_DIR / 'registry.csv')
    pinned = sources()
    loader = Loader(REGISTRY_DIR / 'cache', manifest=manifest())

    def load(row: pd.Series) -> pd.DataFrame:
        return loader.load(pinned[row['source']], row['object'], parseTypes(row['types']))

    grouping, report = regroup(registry, load)
    regrouped = grouping != registry['grouping_factors']
    registry['grouping_factors'] = grouping
    registry.loc[regrouped, 'notes'] += REGROUPED_NOTE
    writeCsv(registry.loc[regrouped, list(REGISTRY.agentColumns)], HERE / 'shards' / 'registry_factors.csv')  # fmt: skip
    print(f'{regrouped.sum()} rows regrouped; every formula factor the row does not name:')
    print(report.to_string(index=False))
