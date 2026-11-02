"""lme4.py defines a mixed model's frequentist fit: a table, a formula and a family in, lme4's fit out.

Python writes the table and the model for R, and `lme4.R` fits the formula as written.
R writes back one fixed set: how the fit ended, the fixed effects with their Wald standard errors,
the random terms, and the variance components of Nakagawa, Johnson and Schielzeth (2017).
`design` reads the same table and formula into the design lme4 fits, without fitting.

pipeline:
---------
a table, a formula and a family
-> table.csv, input.json with the levels for R     _write
-> lme4's fit and its components, output.json      lme4.R fit
-> the fit, lme4 checked against its pin           _read
or
-> lme4's design, design.json                      lme4.R design
-> the design, lme4 checked against its pin        design
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

LME4 = '2.0.6'
_HERE = Path(__file__).parent

Family = Literal['gaussian', 'bernoulli', 'poisson']  # the contract's names
Status = Literal['ok', 'singular', 'warning', 'timeout', 'error', 'no_formula']


@dataclass(frozen=True)
class Term:
    """One random term as lme4 splits the formula's: `(1 + x || g)` is two terms of `g`."""

    factor: str  # as lme4 names it: `herd:region` for `(1 | region/herd)`
    columns: tuple[str, ...]
    variances: tuple[float, ...]
    correlations: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Fit:
    """How a fit ended and what it estimated.
    The estimates and components are empty or `None` where it ended as `timeout`, `error` or
    `no_formula`.

    - `variances`: per factor the mean over rows of z'Σz over its terms (Johnson 2014).
    - `sigma2_fixed`: the variance over rows of the fixed predictor Xβ̂.
    - `sigma2_distribution`: the variance the family adds on the link scale: 0, π²/3, or
      ln(1 + 1/λ) for the Poisson (Nakagawa, Johnson and Schielzeth 2017).
    - the variance partition: properties computed from these, R² and each factor's ICC over
      σ²_f + Σ σ²_g + σ²_ε + σ²_d, the adjusted ICC without σ²_f (the same authors).
    """

    status: Status
    seconds: float | None = None
    message: str = ''  # every warning or the error, joined by `; `
    n_obs: int | None = None
    fixed: dict[str, tuple[float, float]] = field(default_factory=dict)  # estimate, Wald se
    terms: tuple[Term, ...] = ()
    sigma: float | None = None  # gaussian
    variances: dict[str, float] = field(default_factory=dict)
    sigma2_fixed: float | None = None
    sd_eta: float | None = None  # over rows, of the linear predictor with the random effects
    max_abs_eta: float | None = None  # over rows, of the same linear predictor
    sigma2_distribution: float | None = None

    # ---------------------------------------------------------------------------------
    # the variance partition, None or empty where the fit has no estimates
    # ---------------------------------------------------------------------------------

    @property
    def sigma2_random(self) -> float | None:
        if self.sigma2_fixed is None:
            return None
        return sum(self.variances.values())

    @property
    def sigma2_residual(self) -> float | None:
        if self.sigma is None:  # a generalized fit, or none
            return None
        return self.sigma**2

    @property
    def r2_marginal(self) -> float | None:
        if self.sigma2_fixed is None:
            return None
        return self.sigma2_fixed / self._sumVariances()

    @property
    def r2_conditional(self) -> float | None:
        if self.sigma2_fixed is None:
            return None
        return (self.sigma2_fixed + self.sigma2_random) / self._sumVariances()

    @property
    def icc(self) -> dict[str, float]:
        icc = {}
        for factor, variance in self.variances.items():
            icc[factor] = variance / self._sumVariances()
        return icc

    @property
    def icc_adjusted(self) -> dict[str, float]:
        icc = {}
        for factor, variance in self.variances.items():
            icc[factor] = variance / (self._sumVariances() - self.sigma2_fixed)
        return icc

    def _sumVariances(self) -> float:
        residual = self.sigma2_residual or 0
        return self.sigma2_fixed + self.sigma2_random + residual + self.sigma2_distribution


@dataclass(frozen=True)
class Factor:
    """A grouping factor of lme4's design: its terms, its levels and each row's random columns."""

    name: str  # as lme4 names it: `herd:region` for `(1 | region/herd)`
    terms: tuple[tuple[str, ...], ...]  # each term's columns: `(1 + x || g)` is two terms of `g`
    levels: tuple[str, ...]
    Z: np.ndarray  # (n, q) its terms' columns side by side
    codes: np.ndarray  # (n,) each row's level, 0-based


@dataclass(frozen=True)
class Design:
    """The design lme4 builds from a formula before it fits, over the rows it keeps."""

    rows: np.ndarray  # (n,) their 0-based positions in the table
    y: np.ndarray  # (n,) as the fit reads it: a binary text or categorical 0 at its first level
    columns: tuple[str, ...]  # X's, as lme4 names them
    X: np.ndarray  # (n, d)
    offset: np.ndarray  # (n,) 0 without one
    factors: tuple[Factor, ...]  # in lme4's order


def fit(table: pd.DataFrame, formula: str, family: Family, dir: Path, timeout: float) -> Fit:
    """Fits `formula` to `table` by lme4, its files in `dir`, and stops it after `timeout` seconds.
    A formula without a random term is a model documented in words, and runs no fit.
    Raises where R ends without a fit's output or lme4 differs from its pin."""
    if '|' not in formula:
        return Fit('no_formula')
    dir.mkdir(parents=True, exist_ok=True)
    _write(table, {'formula': formula, 'family': family, 'timeout': timeout}, dir)
    _runR('fit', dir)
    return _read(dir)


def design(table: pd.DataFrame, formula: str, family: Family) -> Design:
    """Returns the design lme4 builds from `formula` on `table`, both read as `fit` reads them.
    Raises where lme4 refuses the formula or differs from its pin."""
    with tempfile.TemporaryDirectory() as temporary:
        dir = Path(temporary)
        _write(table, {'formula': formula, 'family': family}, dir)
        _runR('design', dir)
        built = _readOutput(dir / 'design.json')
    factors = []
    for factor in built['factors']:
        terms = tuple(tuple(columns) for columns in factor['terms'])
        z = np.array(factor['Z'], dtype=float)
        codes = np.array(factor['codes']) - 1  # R counts levels from 1
        factors.append(Factor(factor['name'], terms, tuple(factor['levels']), z, codes))
    return Design(
        rows=np.array(built['rows']) - 1,  # R counts rows from 1
        y=np.array(built['y'], dtype=float),
        columns=tuple(built['columns']),
        X=np.array(built['X'], dtype=float),
        offset=np.array(built['offset'], dtype=float),
        factors=tuple(factors),
    )


# =====================================================================================
# table and model -> table.csv, input.json -> R
# =====================================================================================


def _write(table: pd.DataFrame, model: dict, dir: Path) -> None:
    """R reads a categorical column's values as text and applies its levels in order,
    where it would sort them itself."""
    table.to_csv(dir / 'table.csv', index=False)
    levels = {}
    ordered = []
    for column in table.columns:
        dtype = table[column].dtype
        if isinstance(dtype, pd.CategoricalDtype):
            levels[column] = [str(level) for level in dtype.categories]  # as the CSV writes them
            if dtype.ordered:
                ordered.append(column)
    model = model | {'levels': levels, 'ordered': ordered}
    (dir / 'input.json').write_text(json.dumps(model, indent=2))


def _runR(mode: Literal['fit', 'design'], dir: Path) -> None:
    """Raises with R's log where R ends in an error, which a design in a temporary directory
    would otherwise take with it."""
    with open(dir / 'R.log', 'w') as log:
        ended = subprocess.run(
            ['Rscript', _HERE / 'lme4.R', mode, dir], stdout=log, stderr=subprocess.STDOUT
        )
    if ended.returncode != 0:
        raise RuntimeError(f'lme4.R {mode} ended in an error:\n{(dir / "R.log").read_text()}')


# =====================================================================================
# R's output -> the fit
# =====================================================================================


def _readOutput(path: Path) -> dict:
    """Returns R's output without lme4's version, which it checks against the pin."""
    output = json.loads(path.read_text())
    lme4 = output.pop('lme4')
    if lme4 != LME4:
        raise RuntimeError(f'lme4 {lme4} differs from the pin {LME4}')
    return output


def _read(dir: Path) -> Fit:
    output = _readOutput(dir / 'output.json')
    terms = []
    for term in output['terms']:
        correlations = tuple(tuple(row) for row in term['correlations'])
        terms.append(
            Term(term['factor'], tuple(term['columns']), tuple(term['variances']), correlations)
        )
    fixed = {name: tuple(estimate) for name, estimate in output['fixed'].items()}
    return Fit(**output | {'fixed': fixed, 'terms': tuple(terms)})
