"""copies.py names the pairs of registry tables that may be copies of each other, for an agent to
confirm or reject through a duplicates shard.

A copy can rename, reorder, recode, add or drop columns and store its numbers at another
precision, so two tables may be copies when most of the smaller one's distinctive values appear
in the other. A distinctive value survives all of that: a non-integer number to four significant
digits, a large integer of a sparse column, a text label. A copy of codes and small integers has
none, so two tables of equal row count and column cardinalities may be copies too. The value
scan of #168 set the rule.

pipeline:
---------
a table
-> its row count, cardinalities and distinctive values  profileTable
the profiles of every registry object
-> pairs of equal row count and cardinalities           _matchSignatures
-> pairs that share enough rare values                  _shareRareValues
-> of them, pairs of similar row counts                 _haveSimilarRows
-> and most distinctive values shared                   _shareMostValues
-> the pairs that may be copies, in the profiles' order copyPairs
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
from sources import Key

# =====================================================================================
# the rule
# =====================================================================================
# the value scan of #168 calibrated these over the registry and #162's new tables: every copy
# group it found stays connected through the pairs they flag.
MIN_CONTAINMENT = 0.9  # share of the smaller table's distinctive values the other holds
MIN_SHARED = 10  # distinctive values two tables share; fewer tell no copy apart
MIN_ROW_RATIO = 0.8  # the smaller table's rows over the larger's
COMMON = 50  # a value held by more objects proposes no pair
CAP = 20_000  # distinctive values a profile keeps, a sample by hash above it


def _cut(rate: float) -> np.uint64:
    """The largest hash a sample at this rate keeps, so two samples compare at the lower rate."""
    return np.uint64(min(2**64 - 1, int(rate * 2**64)))


@dataclass(frozen=True)
class Profile:
    """What a table offers the comparison:
    - cardinalities: its columns' numbers of distinct values, sorted
    - values: the hashes of its distinctive values, sorted, those at or below the rate's cut
    - rate: the share of all hashes the sample keeps, 1 for a table of at most CAP values
    """

    rows: int
    cardinalities: tuple[int, ...]
    values: np.ndarray
    rate: float


# =====================================================================================
# profileTable: table -> cardinalities and distinctive values -> sample
# =====================================================================================
def profileTable(table: pd.DataFrame) -> Profile:
    values = _hashValues(table)
    rate = min(1.0, CAP / max(len(values), 1))
    cardinalities = tuple(sorted(table.nunique()))
    return Profile(len(table), cardinalities, values[values <= _cut(rate)], rate)


def _hashValues(table: pd.DataFrame) -> np.ndarray:
    """Each kind of value hashes under its own tag, so the label '1001' never meets 1001."""
    parts = [np.empty(0, np.uint64)]
    for name in table.columns:
        column = table[name]
        if pd.api.types.is_bool_dtype(column) or pd.api.types.is_datetime64_any_dtype(column):
            continue
        if pd.api.types.is_numeric_dtype(column):
            values = column.to_numpy(dtype=float, na_value=np.nan)
            values = values[np.isfinite(values)]
            parts += [_hashFloats(values), _hashIntegers(values)]
        else:
            parts.append(_hashLabels(column))
    return np.unique(np.concatenate(parts))


def _hashFloats(values: np.ndarray) -> np.ndarray:
    """Non-integer numbers to four significant digits, the fourth nonzero: float32 storage keeps
    them, and a number written to fewer digits is too common to tell tables apart."""
    fractional = values[(values != np.rint(values)) & (values != 0)]
    exponent = np.floor(np.log10(np.abs(fractional))).astype(np.int64)
    mantissa = np.rint(fractional / 10.0 ** (exponent - 3)).astype(np.int64)
    rounded_up = np.abs(mantissa) >= 10_000  # 9999.6 rounds to a fifth digit
    mantissa[rounded_up] //= 10
    exponent[rounded_up] += 1
    four_digits = mantissa % 10 != 0
    codes = (mantissa[four_digits] * 1000 + exponent[four_digits] + 500) * 4 + 1
    return pd.util.hash_array(np.unique(codes))


def _hashIntegers(values: np.ndarray) -> np.ndarray:
    """Integers of 1000 or more from a column whose integers fill less than half their range,
    as identifiers and years do; a dense run of counts or codes is in every table."""
    integers = np.unique(values[values == np.rint(values)])
    if len(integers) < 2:
        return np.empty(0, np.uint64)
    sparse = len(integers) / (integers.max() - integers.min() + 1) < 0.5
    large = integers[np.abs(integers) >= 1000]
    if not sparse or len(large) == 0:
        return np.empty(0, np.uint64)
    return pd.util.hash_array(large.astype(np.int64) * 4 + 2)


def _hashLabels(column: pd.Series) -> np.ndarray:
    """Labels of four or more characters, case and padding ignored."""
    labels = column.dropna().astype(str).str.strip().str.lower().unique()
    labels = np.array([f's:{label}' for label in labels if len(label) >= 4], dtype=object)
    if len(labels) == 0:
        return np.empty(0, np.uint64)
    return pd.util.hash_array(labels)


# =====================================================================================
# copyPairs: profiles -> signatures or shared values -> pairs
# =====================================================================================
def copyPairs(profiles: dict[Key, Profile]) -> list[tuple[Key, Key]]:
    """The pairs that may be copies, each in the profiles' order and sorted by it."""
    rank = {key: i for i, key in enumerate(profiles)}
    pairs = set(_matchSignatures(profiles))
    for a, b in _shareRareValues(profiles):
        first, second = profiles[a], profiles[b]
        if _haveSimilarRows(first, second) and _shareMostValues(first, second):
            pairs.add((a, b))
    return sorted(pairs, key=lambda pair: (rank[pair[0]], rank[pair[1]]))


def _matchSignatures(profiles: dict[Key, Profile]) -> list[tuple[Key, Key]]:
    groups = defaultdict(list)  # (rows, cardinalities) -> its objects in the profiles' order
    for key, profile in profiles.items():
        groups[profile.rows, profile.cardinalities].append(key)
    return [pair for keys in groups.values() for pair in combinations(keys, 2)]


def _shareRareValues(profiles: dict[Key, Profile]) -> list[tuple[Key, Key]]:
    """Pairs that share MIN_SHARED values held by at most COMMON objects: comparing every pair
    of a thousand tables in full would take too long."""
    holders = defaultdict(list)
    for key, profile in profiles.items():
        for value in profile.values.tolist():
            holders[value].append(key)
    shared = Counter()
    for owners in holders.values():
        if 2 <= len(owners) <= COMMON:
            for pair in combinations(owners, 2):
                shared[pair] += 1
    return [pair for pair, count in shared.items() if count >= MIN_SHARED]


def _haveSimilarRows(a: Profile, b: Profile) -> bool:
    """A table much larger than another holds most of its distinctive values by chance."""
    return min(a.rows, b.rows) >= MIN_ROW_RATIO * max(a.rows, b.rows)


def _shareMostValues(a: Profile, b: Profile) -> bool:
    cut = _cut(min(a.rate, b.rate))
    left = a.values[a.values <= cut]
    right = b.values[b.values <= cut]
    shared = len(np.intersect1d(left, right, assume_unique=True))
    smaller = min(len(left), len(right))
    return shared >= MIN_SHARED and shared >= MIN_CONTAINMENT * smaller
