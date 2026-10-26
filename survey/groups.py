"""groups.py measures column_factors.csv: a row per covariate column and grouping factor of a
registry row.

pipeline:
---------
a measurer
-> the rows that observe the column and the factor  measureColumnGroups
-> the share of absent group × level cells          Measurer.measureEmptyCells
-> the between-group share                          measureBetweenGroupShare
-> the size-mean rank correlation                   measureSizeRho
-> the spread of the within-group spreads           measureWithinSdCv
-> the fit on the factor's group-level columns      measureGroupLevelR2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from columns import codeColumn
from schema import IDENTITY

if TYPE_CHECKING:  # only a type: measure.py imports this module
    from measure import Measurer

# =====================================================================================
# globals
# =====================================================================================
COLUMN_FACTOR_STATISTICS = (
    'between_group_share', 'group_level_r2', 'absent_level_share', 'size_rho', 'within_sd_cv',
)  # fmt: skip
COLUMN_FACTOR_COLUMNS = (*IDENTITY, 'column', 'factor', *COLUMN_FACTOR_STATISTICS)


# =====================================================================================
# column_factors.csv: absent levels -> between groups -> sizes -> spreads -> group level
# =====================================================================================
def measure(measurer: Measurer) -> list[dict]:
    column_factors = []
    for column in measurer.column_names:
        for grouping_factor in measurer.grouping_factors:
            key = {'column': column, 'factor': grouping_factor}
            statistics = measureColumnGroups(measurer, column, grouping_factor)
            column_factors.append(measurer.identity | key | statistics)
    return column_factors


def measureColumnGroups(measurer: Measurer, column: str, grouping_factor: str) -> dict:
    """The statistics of a column against a grouping factor's groups. Each is taken over the
    rows where the column and the grouping factor are both observed."""
    table = measurer.table
    both = table[column].notna() & table[grouping_factor].notna()
    if not both.any():
        return {}
    kind, _ = measurer.column_types[column]
    groups = table.loc[both, grouping_factor]
    statistics = {}
    if kind != 'continuous':
        absent = measurer.measureEmptyCells(table.loc[both, [grouping_factor, column]])
        statistics['absent_level_share'] = absent
    if kind == 'categorical':
        return statistics
    values = codeColumn(table[column], kind)[both]
    if values.nunique() < 2:  # a constant column has nothing to share, rank, spread or explain
        return statistics
    statistics |= measureBetweenGroupShare(values, groups) | measureSizeRho(values, groups)
    statistics |= measureWithinSdCv(values, groups)
    statistics |= measureGroupLevelR2(measurer, column, grouping_factor, kind)
    return statistics


def measureBetweenGroupShare(values: pd.Series, groups: pd.Series) -> dict:
    """The adjusted ICC(1), (MSB − MSW) / (MSB + (k₀ − 1) MSW) with
    k₀ = (n − Σ nⱼ² / n) / (m − 1) (Snijders & Bosker 2012, section 3.3.1).
    Blank with one group or all singletons."""
    grouped = values.groupby(groups, observed=True)
    sizes = grouped.size()
    n, m = int(sizes.sum()), len(sizes)
    if m < 2 or n == m:
        return {}
    between = float((sizes * (grouped.mean() - values.mean()) ** 2).sum())
    within = float(((values - grouped.transform('mean')) ** 2).sum())
    msb, msw = between / (m - 1), within / (n - m)
    k0 = (n - float((sizes**2).sum()) / n) / (m - 1)
    return {'between_group_share': round((msb - msw) / (msb + (k0 - 1) * msw), 4)}


def measureSizeRho(values: pd.Series, groups: pd.Series) -> dict:
    """Spearman's ρ of the groups' sizes with their means. Blank when either is constant."""
    grouped = values.groupby(groups, observed=True)
    sizes, means = grouped.size(), grouped.mean()
    if sizes.nunique() < 2 or means.nunique() < 2:
        return {}
    rho = sizes.rank().corr(means.rank())  # by hand: Series.corr's Spearman needs scipy
    return {'size_rho': round(float(rho), 4)}


def measureWithinSdCv(values: pd.Series, groups: pd.Series) -> dict:
    """The population CV of the within-group sample sds over the groups of two or more rows.
    Blank with fewer than two or a zero mean."""
    grouped = values.groupby(groups, observed=True)
    sds = grouped.std()[grouped.size() >= 2]
    if len(sds) < 2 or sds.mean() == 0:
        return {}
    return {'within_sd_cv': round(float(sds.std(ddof=0) / sds.mean()), 4)}


def measureGroupLevelR2(measurer: Measurer, column: str, grouping_factor: str, kind: str) -> dict:
    """The adjusted R² of the column on the factor's other group-level columns,
    1 − (1 − R²)(m − 1) / (m − p − 1) with p the design's rank beyond the intercept.
    Blank when p = 0, m − p − 1 ≤ 0 or the column is constant."""
    table = measurer.table
    # a column with no observed value is constant within groups, but would complete no row
    partners = [
        c for c in measurer.group_level[grouping_factor] if c != column and table[c].notna().any()
    ]
    complete = table[[column, grouping_factor, *partners]].dropna().index
    y = codeColumn(table[column], kind)[complete].to_numpy(float)
    design = codeDesign(measurer, partners, complete)
    m = table.loc[complete, grouping_factor].nunique()
    coefficients, _, rank, _ = np.linalg.lstsq(design, y)
    p = rank - 1
    if p == 0 or m - p - 1 <= 0:
        return {}
    if len(np.unique(y)) < 2:  # a constant column has no variance to explain
        return {}
    total = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(((y - design @ coefficients) ** 2).sum()) / total
    return {'group_level_r2': round(float(1 - (1 - r2) * (m - 1) / (m - p - 1)), 4)}


def codeDesign(measurer: Measurer, columns: list[str], rows: pd.Index) -> np.ndarray:
    """An intercept, a continuous column raw, any other by its level indicators but the first."""
    coded = [pd.DataFrame({'intercept': 1.0}, index=rows)]
    for column in columns:
        values = measurer.table.loc[rows, column]
        kind, _ = measurer.column_types[column]
        if kind == 'continuous':
            coded.append(values.astype(float).to_frame())
        else:
            coded.append(pd.get_dummies(values, drop_first=True, dtype=float))
    return pd.concat(coded, axis=1).to_numpy()
