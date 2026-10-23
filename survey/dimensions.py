"""dimensions.py measures dimensions.csv: a row per grouping factor of a registry row.

pipeline:
---------
a measurer
-> the factors' relation                      classifyRelation
-> the documented and the full design's width  countDesignColumns
-> both designs' condition indexes             measureConditions
-> each factor's group sizes                   measureGroupSizes
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
    """Concentration of a symmetric Dirichlet fitted by moment matching to the group-size
    proportions: Var(p) = (1 − 1/m) / (m (m α + 1)) solved for α,
    with the variance taken around the known mean 1/m.
    A balanced allocation has zero variance, hence infinite α."""
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
    shared = {'n_factors': len(measurer.factors), 'relation': classifyRelation(measurer)}
    shared |= countDesignColumns(measurer) | measureConditions(measurer)
    dimensions = []
    for factor in measurer.factors:
        sizes = measureGroupSizes(measurer, factor)
        dimensions.append(measurer.identity | {'factor': factor} | shared | sizes)
    return dimensions


def classifyRelation(measurer: Measurer) -> str:
    """The practice survey's single / nested / crossed / mixed, computed from the data.
    A pair is nested when every level of one factor lies in one level of the other."""
    if len(measurer.factors) == 1:
        return 'single'
    nested = {bool(measurer.findHolders(a, b)) for a, b in combinations(measurer.factors, 2)}
    if nested == {True}:
        return 'nested'
    if nested == {False}:
        return 'crossed'
    return 'mixed'


def countDesignColumns(measurer: Measurer) -> dict:
    """d_doc expands the documented model, d_all every covariate column plus the documented
    interactions, so that d_all is never below d_doc (envelope rule 4).
    Continuous and binary count 1, categorical k − 1, an interaction the product."""
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


def measureConditions(measurer: Measurer) -> dict:
    """The condition index of the contract's design, of the documented model
    and of every measured column with the documented interactions.
    The contract codes, types and drops incomplete rows alike for both.
    Blank where the contract builds no problem."""
    try:
        documented = Problem.build(measurer.row, measurer.table)
    except Refused:
        return {}
    conditions = {'condition_doc': computeConditionIndex(documented)}
    everything = dataclasses.replace(measurer.row, covariates=tuple(measurer.column_names))
    try:
        measured = Problem.build(everything, measurer.table)
    except (Refused, TypeError):  # no complete row, or a column of strings and numbers (#105)
        return conditions
    return conditions | {'condition_all': computeConditionIndex(measured)}


def computeConditionIndex(problem: Problem) -> float:
    """The condition index σ_max / σ_min of the standardized full-regime design,
    intercept included, each column scaled to unit length as Belsley, Kuh and Welsch (1980)
    scale it, inf when rank-deficient.
    Unlike their index, it is taken after the contract centers the continuous columns,
    so their collinearity with the intercept does not count."""
    design = problem.standardized()[list(problem.design)]
    scaled = (design / np.sqrt((design**2).sum())).to_numpy()
    # a constant continuous column standardizes to 0/0, and an interaction's empty cell
    # gives a column of zeros, which scales to 0/0: set to zeros, either leaves the design
    # rank-deficient
    scaled = np.nan_to_num(scaled)
    if np.linalg.matrix_rank(scaled) < scaled.shape[1]:
        return float('inf')
    singular = np.linalg.svd(scaled, compute_uv=False)
    return round(float(singular[0] / singular[-1]), 4)


def measureGroupSizes(measurer: Measurer, factor: str) -> dict:
    sizes = measurer.table[factor].value_counts()
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
