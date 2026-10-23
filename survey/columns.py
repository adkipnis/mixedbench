"""columns.py measures columns.csv: a row per covariate column of a registry row.

pipeline:
---------
a measurer
-> each column's largest rank correlation         measureMaxAbsRho
-> its type, level, missing share and membership  measureColumn
-> the quirk statistics its kind defines          measureShape
"""

from __future__ import annotations

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
# columns.csv: rank correlations -> type, level and missing share -> quirk statistics
# =====================================================================================
def measure(measurer: Measurer) -> list[dict]:
    rho = measureMaxAbsRho(measurer)
    columns = []
    for column in measurer.column_names:
        key = {'column': column}
        measured = measureColumn(measurer, column) | {'max_abs_rho': rho[column]}
        columns.append(measurer.identity | key | measured)
    return columns


def measureMaxAbsRho(measurer: Measurer) -> pd.Series:
    """Each column's largest |Spearman| with another, pairwise complete. A categorical column
    has no order to rank, so it takes no part. Blank with no partner or when constant."""
    ranked = {}
    for column in measurer.column_names:
        kind, _ = measurer.column_types[column]
        if kind != 'categorical':
            ranked[column] = measurer.codeColumn(column, kind)
    rho = pd.DataFrame(ranked, index=measurer.table.index).corr(method='spearman').abs()
    partners = rho.where(~np.eye(len(rho), dtype=bool))
    return partners.max().round(4).reindex(measurer.column_names)


def measureColumn(measurer: Measurer, column: str) -> dict:
    values = measurer.table[column]
    kind, levels = measurer.column_types[column]
    constant_within = [g for g in measurer.grouping_factors if column in measurer.group_level[g]]
    return {
        'type': kind,
        'K': levels,
        'level': 'group' if constant_within else 'within',
        'constant_within': ';'.join(constant_within),
        'missing_share': round(float(values.isna().mean()), 4),
        'in_model': 'yes' if column in measurer.row.covariates else 'no',
    } | measureShape(values.dropna(), kind)


def measureShape(values: pd.Series, kind: str) -> dict:
    """The statistics the column's kind defines, over its present values."""
    if values.empty:
        return {}
    shape = {'unique_share': round(values.nunique() / len(values), 4)}
    if kind == 'continuous':
        shape |= measureMoments(values)
    if kind in ('continuous', 'ordered'):
        shape |= measureBounds(values, kind)
    if kind != 'continuous':
        counts = values.value_counts()
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
