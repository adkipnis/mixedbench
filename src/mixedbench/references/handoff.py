"""handoff.py defines what passes between a problem and the R script that fits its reference.

Python writes the standardised table under aliases brms never rewrites (`y`, `x1`…, `g1`…)
and the model as JSON: the formula, family and link, the prior per class, a level's settings
and the seed.
It reads the draws R wrote back by the aliases in brms's labels, never by position.

pipeline:
---------
a Problem
-> the aliases of its response, design columns and factors     aliases
-> the aliased table as CSV, the model as JSON                 write
-> brms's draws under the contract's names                     read, _contractNames
"""

from __future__ import annotations

import hashlib
import json
from functools import cached_property
from pathlib import Path

import pandas as pd
import pyreadr
from mixedbench.contract import Prior, Problem

# =====================================================================================
# the handoff
# =====================================================================================


class Handoff:
    # the ladder: per level, the settings of `brm()`; four chains in parallel, no threading
    LEVELS = {
        0: {
            'chains': 4,
            'cores': 4,
            'warmup': 1000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.8,
            'max_treedepth': 10,
        },
    }

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    @cached_property
    def aliases(self) -> dict[str, str]:
        """Per alias, the problem's column: `Intercept` is brms's own, so it has none."""
        aliases = {'y': self.problem.response}
        for i, column in enumerate(self.problem.design[1:], start=1):
            aliases[f'x{i}'] = column
        for i, factor in enumerate(self.problem.factors, start=1):
            aliases[f'g{i}'] = factor
        return aliases

    @property
    def seed(self) -> int:
        """The first 4 bytes of sha256 of the id, modulo 2³¹ (R's integer range)."""
        digest = hashlib.sha256(self.problem.id.encode()).digest()
        return int.from_bytes(digest[:4], 'big') % 2**31

    def write(self, dir: Path, level: int) -> None:
        """`table.csv` and `input.json` for the R script, into `dir`."""
        table = self.problem.standardised('full')[list(self.aliases.values())]
        table.columns = list(self.aliases)
        table.to_csv(dir / 'table.csv', index=False)
        model = {
            'formula': self._formula(),
            'family': self.problem.family,
            'link': self.problem.link,
            'prior': {name: self._brmsPrior(prior) for name, prior in self.problem.prior.items()},
            'settings': self.LEVELS[level],
            'seed': self.seed,
        }
        (dir / 'input.json').write_text(json.dumps(model, indent=2))

    def read(self, dir: Path) -> pd.DataFrame:
        """The global draws in `dir/draws.rds` under the contract's names, in its order, after
        `chain` and `draw` counted from 0 (`draw` within its chain)."""
        draws = pyreadr.read_r(dir / 'draws.rds')[None]
        draws = draws.rename(columns=self._contractNames())
        draws['chain'] = draws['chain'] - 1
        draws['draw'] = draws.pop('iteration') - 1
        return draws[['chain', 'draw', *self.problem.globalDraws()]]

    # ---------------------------------------------------------------------------------
    # problem -> formula, prior; brms's names -> the contract's
    # ---------------------------------------------------------------------------------

    def _formula(self) -> str:
        covariates = [alias for alias in self.aliases if alias.startswith('x')]
        factors = [alias for alias in self.aliases if alias.startswith('g')]
        terms = ['1', *covariates, *[f'(1 | {g})' for g in factors]]
        return f'y ~ {" + ".join(terms)}'

    @staticmethod
    def _brmsPrior(prior: Prior) -> str:
        parameters = ', '.join(f'{p:g}' for p in prior.parameters)
        return f'{prior.distribution}({parameters})'

    def _contractNames(self) -> dict[str, str]:
        """Per brms variable, its contract name, by the alias in brms's label."""
        names = {'b_Intercept': 'Intercept', 'sigma': 'sigma'}
        for alias, column in self.aliases.items():
            if alias.startswith('x'):
                names[f'b_{alias}'] = column
            if alias.startswith('g'):
                names[f'sd_{alias}__Intercept'] = f'sd[{column}]'
        return names
