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
-> brms's draws and summaries under the contract's names       read, _contractNames
"""

from __future__ import annotations

import hashlib
import json
from functools import cached_property
from itertools import combinations
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
        1: {
            'chains': 4,
            'cores': 4,
            'warmup': 2000,
            'draws': 1000,
            'thin': 1,
            'adapt_delta': 0.9,
            'max_treedepth': 10,
        },
        # 2,000 draws per chain, thinned by 2 after the sampler's checks: 4,000 stored, as at
        # the other levels
        2: {
            'chains': 4,
            'cores': 4,
            'warmup': 4000,
            'draws': 2000,
            'thin': 2,
            'adapt_delta': 0.99,
            'max_treedepth': 12,
        },
    }

    # a factor of more groups keeps per-effect summaries of its random effects, not their draws
    FULL_GROUPS = 1000

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    @cached_property
    def aliases(self) -> dict[str, str]:
        """Per alias, the problem's column: `Intercept` is brms's own, so it has none."""
        aliases = {'y': self.problem.response}
        if self.problem.trials:
            aliases['n'] = self.problem.trials
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
            'summarised': [self._aliasOf[factor] for factor in self._summarised()],
        }
        (dir / 'input.json').write_text(json.dumps(model, indent=2))

    def read(self, dir: Path) -> dict[str, pd.DataFrame]:
        """The draws R left in `dir` under the contract's names, per file they go to:
        `globals`, the global draws in the contract's order after `chain` and `draw` counted
        from 0 (`draw` within its chain); `locals`, the random effects of every factor of at
        most `FULL_GROUPS` groups, beside `chain` and `draw`; `locals_summary`, a row per
        random effect of every larger factor. Both in factor order, slopes after the
        intercept, groups in code order, and each absent where no factor qualifies."""
        names = self._contractNames()
        draws = pyreadr.read_r(dir / 'draws.rds')[None].rename(columns=names)
        draws['chain'] = draws['chain'] - 1
        draws['draw'] = draws.pop('iteration') - 1
        files = {'globals': draws[['chain', 'draw', *self.problem.globalDraws()]]}
        summarised = self._summarised()
        full = [factor for factor in self.problem.factors if factor not in summarised]
        if full:
            files['locals'] = draws[['chain', 'draw', *self._effectsOf(full)]]
        if summarised:
            files['locals_summary'] = self._localsSummary(dir, names)
        return files

    # ---------------------------------------------------------------------------------
    # problem -> formula, prior; brms's names -> the contract's
    # ---------------------------------------------------------------------------------

    def _formula(self) -> str:
        response = 'y | trials(n)' if self.problem.trials else 'y'
        terms = ['1', *[alias for alias in self.aliases if alias.startswith('x')]]
        for factor in self.problem.factors:
            terms += self._randomTerms(factor)
        return f'{response} ~ {" + ".join(terms)}'

    def _randomTerms(self, factor: str) -> list[str]:
        """The intercept with its correlated slopes, `(1 + xa + … | g)`, and where the factor has
        uncorrelated slopes, `(0 + xb + … || g)`: independent of the intercept and of each other."""
        alias = self._aliasOf
        correlated = self.problem.correlations.get(factor, ('Intercept',))[1:]
        uncorrelated = [column for column in self._slopes(factor) if column not in correlated]
        effects = ['1', *[alias[column] for column in correlated]]
        terms = [f'({" + ".join(effects)} | {alias[factor]})']
        if uncorrelated:
            slopes = ' + '.join(alias[column] for column in uncorrelated)
            terms.append(f'(0 + {slopes} || {alias[factor]})')
        return terms

    def _slopes(self, factor: str) -> list[str]:
        """The design columns with a slope on `factor`, correlated or not, in design order."""
        sds = self.problem.parameters
        return [column for column in self.problem.design[1:] if f'sd[{column}|{factor}]' in sds]

    def _effectsOf(self, factors: list[str]) -> list[str]:
        local = self.problem.localDraws()
        return [name for factor in factors for name in local[factor]]

    def _localsSummary(self, dir: Path, names: dict[str, str]) -> pd.DataFrame:
        summary = pyreadr.read_r(dir / 'locals_summary.rds')[None]
        summary.insert(0, 'name', summary.pop('variable').map(names))
        return summary.set_index('name').loc[self._effectsOf(self._summarised())].reset_index()

    def _summarised(self) -> list[str]:
        """The factors above `FULL_GROUPS` groups, in factor order."""
        groups = {factor: len(self.problem.levels[factor]) for factor in self.problem.factors}
        return [factor for factor, count in groups.items() if count > self.FULL_GROUPS]

    @staticmethod
    def _brmsPrior(prior: Prior) -> str:
        parameters = ', '.join(f'{p:g}' for p in prior.parameters)
        return f'{prior.distribution}({parameters})'

    def _contractNames(self) -> dict[str, str]:
        """Per brms variable, its contract name, by the aliases in brms's label."""
        alias = self._aliasOf
        names = {'b_Intercept': 'Intercept', 'sigma': 'sigma'}
        for name in self.problem.parameters:
            if name.startswith('Intercept['):  # an ordinal model's thresholds
                names[f'b_{name}'] = name
        for column in self.problem.design[1:]:
            names[f'b_{alias[column]}'] = column
        for factor in self.problem.factors:
            g = alias[factor]
            names[f'sd_{g}__Intercept'] = f'sd[{factor}]'
            for column in self._slopes(factor):
                names[f'sd_{g}__{alias[column]}'] = f'sd[{column}|{factor}]'
            for j in range(len(self.problem.levels[factor])):  # brms labels a group by its code
                names[f'r_{g}[{j},Intercept]'] = f'r[{factor}][{j}]'
                for column in self._slopes(factor):
                    names[f'r_{g}[{j},{alias[column]}]'] = f'r[{column}|{factor}][{j}]'
            for a, b in combinations(self.problem.correlations.get(factor, ()), 2):
                names[f'cor_{g}__{alias[a]}__{alias[b]}'] = f'cor[{factor}][{a},{b}]'
        return names

    @cached_property
    def _aliasOf(self) -> dict[str, str]:
        """Per column, its alias; `Intercept` is brms's own name in its labels."""
        aliasOf = {'Intercept': 'Intercept'}
        for alias, column in self.aliases.items():
            aliasOf[column] = alias
        return aliasOf
