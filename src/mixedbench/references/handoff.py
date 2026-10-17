"""handoff.py defines what passes between a problem and the R script that fits its reference.

Python writes the standardised table and the model for R.
The table's columns take aliases brms never rewrites (`y`, `x1`…, `g1`…).
The model is JSON: the formula, family and link, the prior per class, a level's settings,
the seed and the factors R summarises.
Python reads back the draws by the aliases in brms's labels, never by position,
and the diagnostics of the fit.

pipeline:
---------
a Problem
-> the aliases of its response, design columns and factors     aliases
-> the aliased table as CSV, the model as JSON                 write
-> brms's draws and summaries under the contract's names       read, _contractNames
-> the diagnostics R reported                                  diagnostics
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
    # a factor of more groups keeps per-effect summaries of its random effects, not their draws
    FULL_GROUPS = 1000

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    @cached_property
    def aliases(self) -> dict[str, str]:
        """Returns each alias's column in the problem.
        `Intercept` has no alias: brms names it itself."""
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
        """Returns the first 4 bytes of the id's sha256, modulo 2³¹ (R's integer range)."""
        digest = hashlib.sha256(self.problem.id.encode()).digest()
        return int.from_bytes(digest[:4], 'big') % 2**31

    def write(self, dir: Path, settings: dict) -> None:
        """Writes `table.csv` and `input.json` for the R script into `dir`.
        `settings` are a level's arguments to `brm()`."""
        standardised = self.problem.standardised('full')
        table = standardised[list(self.aliases.values())]
        table.columns = list(self.aliases)
        table.to_csv(dir / 'table.csv', index=False)
        priors = {name: self._brmsPrior(prior) for name, prior in self.problem.prior.items()}
        summarised = [self._aliasOf[factor] for factor in self._summarised()]
        model = {
            'formula': self._formula(),
            'family': self.problem.family,
            'link': self.problem.link,
            'prior': priors,
            'settings': settings,
            'seed': self.seed,
            'summarised': summarised,
        }
        (dir / 'input.json').write_text(json.dumps(model, indent=2))

    def read(self, dir: Path) -> dict[str, pd.DataFrame]:
        """Returns the draws R left in `dir` under the contract's names, per file they go to.
        `globals` holds the global draws.
        `locals` holds the random effects of each factor of at most `FULL_GROUPS` groups.
        `locals_summary` holds a row per random effect of each larger factor.
        A file is absent where no factor qualifies.
        The draws come after `chain` and `draw`; `draw` counts within its chain."""
        raw = pyreadr.read_r(dir / 'draws.rds')[None]  # as brms named them
        names = self._contractNames()
        draws = raw.rename(columns=names)
        draws['chain'] = draws['chain'] - 1
        draws['draw'] = draws.pop('iteration') - 1
        files = {'globals': draws[['chain', 'draw', *self.problem.globalDraws()]]}
        summarised = self._summarised()
        full = [factor for factor in self.problem.factors if factor not in summarised]
        if full:
            files['locals'] = draws[['chain', 'draw', *self._effectsOf(full)]]
        if summarised:
            files['locals_summary'] = self._localsSummary(dir, names, summarised)
        return files

    @staticmethod
    def diagnostics(dir: Path) -> dict:
        """Returns what R reported of a level it ran to its end.
        R-hat and ESS are the worst over the global parameters,
        `rhat_locals` the largest R-hat over the random effects.
        A global one R could not compute stays NaN, so the bar fails on it.
        Divergences and tree-depth hits count every iteration."""
        summary = pyreadr.read_r(dir / 'summary.rds')[None]  # per global parameter
        chains = pyreadr.read_r(dir / 'chains.rds')[None]
        meta = pyreadr.read_r(dir / 'meta.rds')[None]
        return {
            'rhat': float(summary['rhat'].max(skipna=False)),
            'ess_bulk': float(summary['ess_bulk'].min(skipna=False)),
            'ess_tail': float(summary['ess_tail'].min(skipna=False)),
            'divergences': int(chains['divergences'].sum()),
            'treedepth_hits': int(chains['treedepth_hits'].sum()),
            'ebfmi': chains['ebfmi'].tolist(),
            'rhat_locals': float(meta['rhat_locals'].iloc[0]),
        }

    # ---------------------------------------------------------------------------------
    # problem -> formula, prior, summarised factors
    # ---------------------------------------------------------------------------------

    @cached_property
    def _aliasOf(self) -> dict[str, str]:
        """Returns each column's alias.
        `Intercept` keeps its name, as brms's labels do."""
        alias_of = {'Intercept': 'Intercept'}
        for alias, column in self.aliases.items():
            alias_of[column] = alias
        return alias_of

    def _formula(self) -> str:
        response = 'y | trials(n)' if self.problem.trials else 'y'
        covariates = [self._aliasOf[column] for column in self.problem.design[1:]]
        terms = ['1', *covariates]
        for factor in self.problem.factors:
            terms += self._randomTerms(factor)
        predictors = ' + '.join(terms)
        return f'{response} ~ {predictors}'

    def _randomTerms(self, factor: str) -> list[str]:
        """Returns the intercept with its correlated slopes, `(1 + xa + … | g)`.
        Uncorrelated slopes take a term of their own, `(0 + xb + … || g)`:
        independent of the intercept and of each other."""
        alias = self._aliasOf
        g = alias[factor]
        correlated = self.problem.correlations.get(factor, ())[1:]  # after `Intercept`
        uncorrelated = [
            column for column in self.problem.slopes(factor) if column not in correlated
        ]
        slopes = [alias[column] for column in correlated]
        effects = ' + '.join(['1', *slopes])
        terms = [f'({effects} | {g})']
        if uncorrelated:
            independent = ' + '.join(alias[column] for column in uncorrelated)
            terms.append(f'(0 + {independent} || {g})')
        return terms

    @staticmethod
    def _brmsPrior(prior: Prior) -> str:
        parameters = ', '.join(f'{p:g}' for p in prior.parameters)
        return f'{prior.distribution}({parameters})'

    def _summarised(self) -> list[str]:
        summarised = []
        for factor in self.problem.factors:
            if len(self.problem.levels[factor]) > self.FULL_GROUPS:
                summarised.append(factor)
        return summarised

    # ---------------------------------------------------------------------------------
    # brms's labels -> the contract's names
    # ---------------------------------------------------------------------------------

    def _contractNames(self) -> dict[str, str]:
        """Returns each brms variable's contract name, by the aliases in its label."""
        names = {'b_Intercept': 'Intercept', 'sigma': 'sigma'}
        for name in self.problem.parameters:
            if name.startswith('Intercept['):  # an ordinal model's thresholds
                names[f'b_{name}'] = name
        for column in self.problem.design[1:]:
            names[f'b_{self._aliasOf[column]}'] = column
        for factor in self.problem.factors:
            names.update(self._factorNames(factor))
        return names

    def _factorNames(self, factor: str) -> dict[str, str]:
        """Returns the contract names of `factor`'s sds, correlations and random effects."""
        alias = self._aliasOf
        g = alias[factor]
        slopes = self.problem.slopes(factor)
        names = {f'sd_{g}__Intercept': f'sd[{factor}]'}
        for column in slopes:
            names[f'sd_{g}__{alias[column]}'] = f'sd[{column}|{factor}]'
        for a, b in combinations(self.problem.correlations.get(factor, ()), 2):
            names[f'cor_{g}__{alias[a]}__{alias[b]}'] = f'cor[{factor}][{a},{b}]'
        for j in range(len(self.problem.levels[factor])):  # brms labels a group by its code
            names[f'r_{g}[{j},Intercept]'] = f'r[{factor}][{j}]'
            for column in slopes:
                names[f'r_{g}[{j},{alias[column]}]'] = f'r[{column}|{factor}][{j}]'
        return names

    def _effectsOf(self, factors: list[str]) -> list[str]:
        local = self.problem.localDraws()
        names = []
        for factor in factors:
            names += local[factor]
        return names

    def _localsSummary(
        self, dir: Path, names: dict[str, str], summarised: list[str]
    ) -> pd.DataFrame:
        summary = pyreadr.read_r(dir / 'locals_summary.rds')[None]  # a row per random effect
        summary['variable'] = summary['variable'].map(names)
        summary = summary.rename(columns={'variable': 'name'})
        order = self._effectsOf(summarised)
        return summary.set_index('name').loc[order].reset_index()
