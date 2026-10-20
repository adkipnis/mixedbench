"""handoff.py defines what passes between a problem and the R script that fits its reference.

Python writes the standardized table and the model for R.
The table's columns take aliases brms never rewrites (`y`, `x1`, `g1`, ...).
The model is written in JSON format: the formula, family and link, the prior per class,
a level's settings, the seed and the factors R summarizes.
Python reads back the draws by the aliases in brms's labels and the diagnostics of the fit.

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
    """A problem's handoff to the R script and back.

    brms rewrites column names such as `x[level]` or `a:b`, so R sees aliases instead:
    `y` for the response, `n` for a binomial model's trials,
    `x1`, `x2`, ... for the design columns after `Intercept`,
    `g1`, `g2`, ... for the grouping factors.
    Each grouping factor takes its intercept with the correlated slopes, `(1 + x1 | g1)`.
    Uncorrelated slopes go in a term of their own, `(0 + x2 || g1)`.
    brms labels a variable by its class and aliases, such as `sd_g1__x1` or `r_g1[j,x1]`,
    where `j` is a group's code. The draws are renamed by these labels.
    Random effects for more than `FULL_GROUPS` groups are summarized instead of saving the draws.
    """

    FULL_GROUPS = 1000

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    # ---------------------------------------------------------------------------------
    # problem -> aliases
    # ---------------------------------------------------------------------------------

    @cached_property
    def aliases(self) -> dict[str, str]:
        """Returns each alias's column."""
        aliases = {'y': self.problem.response}
        if self.problem.trials:
            aliases['n'] = self.problem.trials
        for i, column in enumerate(self.problem.design[1:], start=1):
            aliases[f'x{i}'] = column
        for i, factor in enumerate(self.problem.factors, start=1):
            aliases[f'g{i}'] = factor
        return aliases

    @cached_property
    def _aliasOf(self) -> dict[str, str]:
        """Returns each column's alias."""
        alias_of = {'Intercept': 'Intercept'}
        for alias, column in self.aliases.items():
            alias_of[column] = alias
        return alias_of

    # ---------------------------------------------------------------------------------
    # aliases -> table.csv, input.json
    # ---------------------------------------------------------------------------------

    def write(self, dir: Path, settings: dict) -> None:
        """Writes `table.csv` and `input.json` for the R script into `dir`.
        `settings` are a level's arguments to `brm()`."""
        standardized = self.problem.standardized('full')
        table = standardized[list(self.aliases.values())]
        table.columns = list(self.aliases)
        table.to_csv(dir / 'table.csv', index=False)
        priors = {name: self._brmsPrior(prior) for name, prior in self.problem.prior.items()}
        summarized = [self._aliasOf[factor] for factor in self._summarized()]
        model = {
            'formula': self._formula(),
            'family': self.problem.family,
            'link': self.problem.link,
            'prior': priors,
            'settings': settings,
            'seed': self.seed,
            'summarized': summarized,
        }
        (dir / 'input.json').write_text(json.dumps(model, indent=2))

    def _formula(self) -> str:
        response = 'y | trials(n)' if self.problem.trials else 'y'
        covariates = [self._aliasOf[column] for column in self.problem.design[1:]]
        terms = ['1', *covariates]
        for factor in self.problem.factors:
            terms += self._randomTerms(factor)
        predictors = ' + '.join(terms)
        return f'{response} ~ {predictors}'

    def _randomTerms(self, factor: str) -> list[str]:
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

    @property
    def seed(self) -> int:
        """Returns the first 4 bytes of the id's sha256, modulo 2³¹ (R's integer range)."""
        digest = hashlib.sha256(self.problem.id.encode()).digest()
        return int.from_bytes(digest[:4], 'big') % 2**31

    def _summarized(self) -> list[str]:
        summarized = []
        for factor in self.problem.factors:
            if len(self.problem.levels[factor]) > self.FULL_GROUPS:
                summarized.append(factor)
        return summarized

    # ---------------------------------------------------------------------------------
    # draws.rds, locals_summary.rds -> the contract's names
    # ---------------------------------------------------------------------------------

    def read(self, dir: Path) -> dict[str, pd.DataFrame]:
        """Returns the draws R left in `dir` under the contract's names, per file they go to:
        `globals`, `locals` for the factors kept in full, `locals_summary` for the summarized."""
        raw = pyreadr.read_r(dir / 'draws.rds')[None]  # as brms named them
        names = self._contractNames()
        draws = raw.rename(columns=names)
        draws['chain'] = draws['chain'] - 1
        draws['draw'] = draws.pop('iteration') - 1  # within its chain
        files = {'globals': draws[['chain', 'draw', *self.problem.globalDraws()]]}
        summarized = self._summarized()
        full = [factor for factor in self.problem.factors if factor not in summarized]
        if full:
            files['locals'] = draws[['chain', 'draw', *self._effectsOf(full)]]
        if summarized:
            files['locals_summary'] = self._localsSummary(dir, names, summarized)
        return files

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
        for j in range(len(self.problem.levels[factor])):
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
        self, dir: Path, names: dict[str, str], summarized: list[str]
    ) -> pd.DataFrame:
        summary = pyreadr.read_r(dir / 'locals_summary.rds')[None]  # a row per random effect
        summary['variable'] = summary['variable'].map(names)
        summary = summary.rename(columns={'variable': 'name'})
        order = self._effectsOf(summarized)
        return summary.set_index('name').loc[order].reset_index()

    # ---------------------------------------------------------------------------------
    # summary.rds, chains.rds, meta.rds -> diagnostics
    # ---------------------------------------------------------------------------------

    def diagnostics(self, dir: Path) -> dict:
        """Returns what R reported of a level it ran to its end,
        with each global parameter's R-hat and ESS under the contract's names.
        An R-hat or ESS that R could not compute stays NaN, so the bar fails on it."""
        summary = pyreadr.read_r(dir / 'summary.rds')[None]  # per global parameter
        summary['variable'] = summary['variable'].map(self._contractNames())
        summary = summary.set_index('variable').loc[list(self.problem.globalDraws())]
        chains = pyreadr.read_r(dir / 'chains.rds')[None]  # per chain, over every iteration
        meta = pyreadr.read_r(dir / 'meta.rds')[None]  # the largest R-hat over the random effects
        return {
            'rhat': float(summary['rhat'].max(skipna=False)),
            'ess_bulk': float(summary['ess_bulk'].min(skipna=False)),
            'ess_tail': float(summary['ess_tail'].min(skipna=False)),
            'divergences': int(chains['divergences'].sum()),
            'treedepth_hits': int(chains['treedepth_hits'].sum()),
            'ebfmi': chains['ebfmi'].tolist(),
            'rhat_locals': float(meta['rhat_locals'].iloc[0]),
            'globals': summary.to_dict(orient='index'),
        }
