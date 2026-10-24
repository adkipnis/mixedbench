"""dimensions.py measures dimensions.csv: a row per grouping factor of a registry row.

pipeline:
---------
a measurer
-> the grouping factors' relation              classifyRelation
-> the documented and the full design's width  countDesignColumns
-> both designs' condition indexes             measureConditionIndexes
-> each grouping factor's group sizes          measureGroupSizes
"""

from __future__ import annotations

import dataclasses
from itertools import combinations
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from mixedbench.contract import Problem, Refused
from mixedbench.registry.row import parts
from schema import IDENTITY

if TYPE_CHECKING:  # only a type: measure.py imports this module
    from measure import Measurer

# =====================================================================================
# globals
# =====================================================================================
CONDITIONS = ('condition_doc', 'condition_all')
DIMENSION_COLUMNS = (
    *IDENTITY, 'factor', 'n_factors', 'relation', 'd_doc', 'd_all', *CONDITIONS, 'n_obs',
    'n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90',
    'group_size_max', 'singleton_share', 'cv', 'alpha',
)  # fmt: skip


def fitAlpha(sizes: pd.Series) -> float:
    """The concentration of a symmetric Dirichlet matched to the group-size proportions by
    their variance, Var(p) = (1 − 1/m) / (m (m α + 1)) solved for α. Balanced sizes give inf."""
    m = len(sizes)
    p = sizes / sizes.sum()
    variance = float(((p - 1 / m) ** 2).mean())
    if variance == 0:
        return float('inf')
    return ((1 - 1 / m) / (m * variance) - 1) / m


def pickObserved(values: pd.Series, q: float) -> int | float:
    """The observed value at or below the level under p50, at or above from p50 on."""
    v = values.quantile(q, interpolation='higher' if q >= 0.5 else 'lower')
    return int(v) if float(v).is_integer() else float(v)


# =====================================================================================
# dimensions.csv: relation -> design columns -> condition indexes -> group sizes
# =====================================================================================
def measure(measurer: Measurer) -> list[dict]:
    shared = {'n_factors': len(measurer.grouping_factors), 'relation': classifyRelation(measurer)}
    shared |= countDesignColumns(measurer) | measureConditionIndexes(measurer)
    dimensions = []
    for grouping_factor in measurer.grouping_factors:
        sizes = measureGroupSizes(measurer, grouping_factor)
        dimensions.append(measurer.identity | {'factor': grouping_factor} | shared | sizes)
    return dimensions


def classifyRelation(measurer: Measurer) -> str:
    """single, nested, crossed or mixed.
    A pair is nested when every group of one factor lies in one group of the other."""
    if len(measurer.grouping_factors) == 1:
        return 'single'
    nested = {
        bool(measurer.findHolders(a, b)) for a, b in combinations(measurer.grouping_factors, 2)
    }
    if nested == {True}:
        return 'nested'
    if nested == {False}:
        return 'crossed'
    return 'mixed'


def countDesignColumns(measurer: Measurer) -> dict:
    """d_doc counts the documented model's columns, d_all every covariate column plus the
    documented interactions. Continuous and binary count 1, categorical k − 1, an interaction
    the product."""
    width = {c: countWidth(*measurer.column_types[c]) for c in measurer.column_names}
    interactions = measurer.row.interactions
    d_interactions = sum(np.prod([width[c] for c in parts(term)]) for term in interactions)
    d_doc = sum(width[c] for c in measurer.row.covariates) + d_interactions
    d_all = sum(width.values()) + d_interactions
    return {'d_doc': int(d_doc), 'd_all': int(d_all)}


def countWidth(kind: str, levels: int | str) -> int:
    if kind in ('categorical', 'ordered'):
        return levels - 1
    return 1


def measureConditionIndexes(measurer: Measurer) -> dict:
    """The condition index of the documented design and of the design over every column, both
    built by the contract. Blank where the contract refuses the row."""
    try:
        documented = Problem.build(measurer.row, measurer.table)
    except Refused:
        return {}
    design = documented.standardized()[list(documented.design)]
    conditions = {'condition_doc': computeConditionIndex(design)}
    everything = dataclasses.replace(measurer.row, covariates=tuple(measurer.column_names))
    try:
        measured = Problem.build(everything, measurer.table)
    except Refused:  # no complete row
        return conditions
    design = measured.standardized()[list(measured.design)]
    return conditions | {'condition_all': computeConditionIndex(design)}


def computeConditionIndex(design: pd.DataFrame) -> float:
    """σ_max / σ_min of a standardized design with each column scaled to unit length
    (Belsley, Kuh and Welsch 1980), inf when rank-deficient."""
    scaled = (design / np.sqrt((design**2).sum())).to_numpy()
    scaled = np.nan_to_num(scaled)  # a constant or empty-cell column scales to 0/0: zeros
    n, d = scaled.shape
    # more columns than rows are dependent, and the decomposition of so wide a design takes hours
    if d > n or np.linalg.matrix_rank(scaled) < d:
        return float('inf')
    singular = np.linalg.svd(scaled, compute_uv=False)
    return round(float(singular[0] / singular[-1]), 4)


def measureGroupSizes(measurer: Measurer, grouping_factor: str) -> dict:
    sizes = measurer.table[grouping_factor].value_counts()
    sizes = sizes[sizes > 0]  # a categorical may carry unused levels
    return {
        'n_obs': int(sizes.sum()),
        'n_groups': len(sizes),
        'group_size_min': int(sizes.min()),
        'group_size_p10': pickObserved(sizes, 0.1),
        'group_size_p50': pickObserved(sizes, 0.5),
        'group_size_p90': pickObserved(sizes, 0.9),
        'group_size_max': int(sizes.max()),
        'singleton_share': round(float((sizes == 1).mean()), 4),
        'cv': round(float(np.std(sizes) / np.mean(sizes)), 4),
        'alpha': round(fitAlpha(sizes), 4),
    }
