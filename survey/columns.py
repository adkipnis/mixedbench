"""columns.py measures columns.csv: a row per covariate column of a registry row.

pipeline:
---------
a measurer
-> each column's largest rank correlation                       measureMaxAbsRho
-> its type, level and membership                               measureColumn
-> its missing share and the quirk statistics its kind defines  measureShape
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from schema import IDENTITY

if TYPE_CHECKING:  # only a type: measure.py imports this module
    from measure import Measurer

# =====================================================================================
# globals
# =====================================================================================
COLUMN_STATISTICS = (
    'skewness', 'excess_kurtosis', 'outlier_share', 'zero_share', 'min_share', 'max_share',
    'unique_share', 'rare_level_share', 'max_abs_rho',
)  # fmt: skip
COLUMN_COLUMNS = (
    *IDENTITY, 'column', 'type', 'K', 'level', 'constant_within', 'missing_share', 'in_model',
    *COLUMN_STATISTICS,
)  # fmt: skip


# =====================================================================================
# columns.csv: rank correlations -> type and level -> missing share and quirk statistics
# =====================================================================================
def measure(measurer: Measurer) -> list[dict]:
    rho = measureMaxAbsRho(measurer.table, measurer.column_types)
    columns = []
    for column in measurer.column_names:
        key = {'column': column}
        measured = measureColumn(measurer, column) | {'max_abs_rho': rho[column]}
        columns.append(measurer.identity | key | measured)
    return columns


def measureMaxAbsRho(table: pd.DataFrame, column_types: dict[str, tuple]) -> pd.Series:
    """Each typed column's largest |Spearman| with another, pairwise complete. A categorical
    column has no order to rank, so it takes no part. Blank with no partner or when constant."""
    ranked = {}
    for column, (kind, _) in column_types.items():
        if kind != 'categorical':
            ranked[column] = codeColumn(table[column], kind)
    codes = pd.DataFrame(ranked, index=table.index).to_numpy(dtype=float)  # (n, d)
    observed = np.isfinite(codes)  # (n, d); pandas leaves an infinity out too
    largest = np.full(codes.shape[1], np.nan)  # (d,), nan only without a partner
    # a pair ranks over the rows both columns observe, so columns observing the same rows rank
    # together, and each pair of their patterns takes one matrix product, not one per pair;
    # positions, not labels, since a table may hold hundreds of patterns
    for a, b in itertools.combinations_with_replacement(_groupByPattern(observed), 2):
        rows = observed[:, a[0]] & observed[:, b[0]]  # (n,)
        rho = _rankCorrelations(codes[np.ix_(rows, a)], codes[np.ix_(rows, b)])  # (|a|, |b|)
        if a is b:
            np.fill_diagonal(rho, np.nan)  # a column is no partner of itself
        largest[a] = np.fmax(largest[a], np.fmax.reduce(rho, axis=1, initial=np.nan))
        largest[b] = np.fmax(largest[b], np.fmax.reduce(rho, axis=0, initial=np.nan))
    return pd.Series(largest, index=list(ranked)).round(4).reindex(list(column_types))


def _groupByPattern(observed: np.ndarray) -> list[list[int]]:
    """The column positions by the rows they observe, one list per pattern of gaps."""
    patterns = {}
    for position in range(observed.shape[1]):
        pattern = np.packbits(observed[:, position]).tobytes()  # eight rows a byte
        patterns.setdefault(pattern, []).append(position)
    return list(patterns.values())


def _rankCorrelations(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """|Spearman| of each column of x with each of y over their rows, as pandas computes it:
    Pearson's r of average ranks, centered on their mean, (n + 1) / 2. Blank where constant."""
    middle = (len(x) + 1) / 2
    ranks_x = pd.DataFrame(x).rank().to_numpy() - middle  # (n, |x|)
    ranks_y = pd.DataFrame(y).rank().to_numpy() - middle  # (n, |y|)
    rho = ranks_x.T @ ranks_y  # (|x|, |y|)
    # pandas' divisor, sqrt(sxx * syy), applied in place: a flat table's |x| reaches the tens of
    # thousands
    divisor = np.outer((ranks_x**2).sum(axis=0), (ranks_y**2).sum(axis=0))  # (|x|, |y|)
    np.sqrt(divisor, out=divisor)
    with np.errstate(divide='ignore', invalid='ignore'):  # 0 / 0 for a constant column
        rho /= divisor
    return np.abs(rho, out=rho)


def codeColumn(values: pd.Series, kind: str) -> pd.Series:
    """A continuous column as loaded, a binary or ordered one by the codes of its present
    levels. A missing value stays missing."""
    if kind == 'continuous':
        return values.astype(float)
    levels = pd.Categorical(values).remove_unused_categories()
    codes = pd.Series(levels.codes, index=values.index)
    return codes.where(codes >= 0)  # -1 codes a missing value


def measureColumn(measurer: Measurer, column: str) -> dict:
    values = measurer.table[column]
    kind, levels = measurer.column_types[column]
    constant_within = [g for g in measurer.grouping_factors if column in measurer.group_level[g]]
    return {
        'type': kind,
        'K': levels,
        'level': 'group' if constant_within else 'within',
        'constant_within': ';'.join(constant_within),
        'in_model': 'yes' if column in measurer.row.covariates else 'no',
    } | measureShape(values, kind)


def measureShape(values: pd.Series, kind: str) -> dict:
    """The missing share, then the statistics the column's kind defines over its present values."""
    shape = {'missing_share': round(float(values.isna().mean()), 4)}
    observed = values.dropna()
    if observed.empty:
        return shape
    shape['unique_share'] = round(observed.nunique() / len(observed), 4)
    if kind == 'continuous':
        shape |= measureMoments(observed)
    if kind in ('continuous', 'ordered'):
        shape |= measureBounds(observed, kind)
    if kind != 'continuous':
        counts = observed.value_counts()
        present = counts[counts > 0]  # a categorical may carry unused levels
        shape['rare_level_share'] = round(float(present.min() / present.sum()), 4)
    return shape


def measureMoments(values: pd.Series) -> dict:
    """Fisher's G1 and G2 and the share beyond four sample standard deviations.
    None for a constant column."""
    if values.nunique() < 2:
        return {}
    z = (values - values.mean()) / values.std()
    return {
        'skewness': round(float(values.skew()), 4),  # blank under three values
        'excess_kurtosis': round(float(values.kurt()), 4),  # blank under four
        'outlier_share': round(float((z.abs() > 4).mean()), 4),
    }


def measureBounds(values: pd.Series, kind: str) -> dict:
    """The shares at the minimum, the maximum and zero; zero only for numeric values or levels."""
    bounds = {
        'min_share': round(float((values == values.min()).mean()), 4),
        'max_share': round(float((values == values.max()).mean()), 4),
    }
    loaded = values.cat.categories if kind == 'ordered' else values
    if pd.api.types.is_numeric_dtype(loaded):
        bounds['zero_share'] = round(float((values == 0).mean()), 4)
    return bounds
