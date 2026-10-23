"""pairs.py measures factor_pairs.csv: a row per pair of grouping factors of a registry row.

pipeline:
---------
a measurer
-> each pair's holders                              Measurer.findHolders
-> a nested pair's superior, a crossed pair's empty cells  measureFactorPair
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from schema import IDENTITY

if TYPE_CHECKING:  # only a type: measure.py imports this module
    from measure import Measurer

# =====================================================================================
# globals
# =====================================================================================
FACTOR_PAIR_STATISTICS = ('empty_cell_share',)
FACTOR_PAIR_COLUMNS = (
    *IDENTITY, 'factor_a', 'factor_b', 'relation', 'superior', *FACTOR_PAIR_STATISTICS,
)  # fmt: skip


# =====================================================================================
# factor_pairs.csv: holders -> superior or empty cells
# =====================================================================================
def measure(measurer: Measurer) -> list[dict]:
    pairs = []
    for a, b in combinations(measurer.factors, 2):
        key = {'factor_a': a, 'factor_b': b}
        pairs.append(measurer.identity | key | measureFactorPair(measurer, a, b))
    return pairs


def measureFactorPair(measurer: Measurer, a: str, b: str) -> dict:
    """A nested pair's superior factor, blank when each holds the other's groups,
    or a crossed pair's share of empty group × group cells."""
    holders = measurer.findHolders(a, b)
    if not holders:
        empty = measurer.measureEmptyCells(measurer.table[[a, b]])
        return {'relation': 'crossed', 'empty_cell_share': empty}
    if len(holders) == 2:
        return {'relation': 'nested'}
    return {'relation': 'nested', 'superior': holders[0]}
