"""lme4.py defines a mixed model's frequentist fit: a table, a formula and a family in, lme4's fit out.

Python writes the table and the model for R, and `lme4.R` fits the formula as written.
R writes back one fixed set: how the fit ended, the fixed effects with their Wald standard errors,
the random terms, and the variance components of Nakagawa, Johnson and Schielzeth (2017).

pipeline:
---------
a table, a formula and a family
-> table.csv, input.json with the levels for R     _write
-> lme4's fit and its components, output.json      lme4.R
-> the fit, lme4 checked against its pin           _read
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

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
    sigma2_distribution: float | None = None


def fit(table: pd.DataFrame, formula: str, family: Family, dir: Path, timeout: float) -> Fit:
    """Fits `formula` to `table` by lme4, its files in `dir`, and stops it after `timeout` seconds.
    A formula without a random term is a model documented in words, and runs no fit.
    Raises where R ends without a fit's output or lme4 differs from its pin."""
    if '|' not in formula:
        return Fit('no_formula')
    dir.mkdir(parents=True, exist_ok=True)
    _write(table, formula, family, dir, timeout)
    with open(dir / 'R.log', 'w') as log:
        subprocess.run(
            ['Rscript', _HERE / 'lme4.R', dir], stdout=log, stderr=subprocess.STDOUT, check=True
        )
    return _read(dir)


# =====================================================================================
# table and model -> table.csv, input.json
# =====================================================================================


def _write(table: pd.DataFrame, formula: str, family: Family, dir: Path, timeout: float) -> None:
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
    model = {
        'formula': formula,
        'family': family,
        'timeout': timeout,
        'levels': levels,
        'ordered': ordered,
    }
    (dir / 'input.json').write_text(json.dumps(model, indent=2))


# =====================================================================================
# output.json -> the fit
# =====================================================================================


def _read(dir: Path) -> Fit:
    output = json.loads((dir / 'output.json').read_text())
    lme4 = output.pop('lme4')
    if lme4 != LME4:
        raise RuntimeError(f'lme4 {lme4} differs from the pin {LME4}')
    terms = []
    for term in output['terms']:
        correlations = tuple(tuple(row) for row in term['correlations'])
        terms.append(
            Term(term['factor'], tuple(term['columns']), tuple(term['variances']), correlations)
        )
    fixed = {name: tuple(estimate) for name, estimate in output['fixed'].items()}
    return Fit(**output | {'fixed': fixed, 'terms': tuple(terms)})
