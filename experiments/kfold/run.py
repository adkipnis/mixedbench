"""run.py scores a GLM and a mixed model under the single split and grouped K-fold (#47).

The single split is the contract's, redrawn under other seeds; its first seed is the problem's own,
checked against the problem's `rows` and `groups` columns.
Grouped K-fold deals the same rows or groups into folds, so that each is held out once.
It reruns at the commit that wrote scores.parquet:
once the contract deals K-fold (#87), the copied single split no longer matches a problem.

pipeline:
---------
the suite 1.1 candidates in scope                                 Experiment.ids
-> per problem, every split under every seed                      splits
-> the aliased table and model (Handoff), the splits as folds.csv  Experiment.score
-> per held-out row, both lines' log predictive density            fit.R
-> per problem, regime, scheme and seed: the scores and Δ          summarize
-> scores.parquet                                                  Experiment.collect
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from mixedbench import suite
from mixedbench.contract import Problem
from mixedbench.references.handoff import Handoff

HERE = Path(__file__).parent
CACHE = Path('registry/cache')
ROWS = 10_000  # larger problems hold out at least 1,000 rows
FOLDS = 5  # K = min(FOLDS, G) in the groups regime, FOLDS over the rows

# =====================================================================================
# the splits
# =====================================================================================
# the contract's single split is copied from contract/problem.py and checked against each problem


def splits(problem: Problem, seeds: int) -> pd.DataFrame:
    """Returns one column per regime, scheme and seed: a row's fold, or -1 where it stays seen."""
    factors = [problem.table[factor].to_numpy() for factor in problem.factors]
    first = factors[0]
    groups = first.max() + 1
    n = len(problem.table)
    columns = {}
    for seed in range(seeds):
        rng = _rng(problem.id, 'single', seed)
        columns[f'rows_single_{seed}'] = np.where(_heldRows(rng, factors, n), 0, -1)
        if groups > 2:  # as the contract: holding out one of two groups would leave one
            columns[f'groups_single_{seed}'] = np.where(_heldGroups(rng, first), 0, -1)
        rng = _rng(problem.id, 'kfold', seed)
        columns[f'rows_kfold_{seed}'] = _rowFolds(rng, factors, n)
        if groups > 2:
            columns[f'groups_kfold_{seed}'] = _groupFolds(rng, first)
    table = pd.DataFrame(columns)
    _checkContract(problem, table)
    return table


def _rng(id: str, scheme: str, seed: int) -> np.random.Generator:
    """The single split's seed 0 is the contract's: the first 8 bytes of the id's sha256."""
    key = id if (scheme, seed) == ('single', 0) else f'{id}#{scheme}{seed}'
    digest = hashlib.sha256(key.encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], 'big'))


def _seededOrder(rng: np.random.Generator, n: int) -> np.ndarray:
    return np.argsort(rng.random(n), kind='stable')  # (n,)


def _spare(order: np.ndarray, factors: list[np.ndarray]) -> np.ndarray:
    """Marks the rows, in seeded order, that are not the first of a group of any factor."""
    spare = np.ones(len(order), dtype=bool)  # (n,) in seeded order
    for codes in factors:
        ordered = pd.Series(codes[order])  # (n,) in seeded order
        spare &= ordered.duplicated().to_numpy()
    return spare


def _heldRows(rng: np.random.Generator, factors: list[np.ndarray], n: int) -> np.ndarray:
    order = _seededOrder(rng, n)  # (n,) row positions
    spare = _spare(order, factors)
    count = (n + 5) // 10  # the nearest whole number to 10%
    held = np.zeros(n, dtype=bool)  # (n,)
    held[order[spare][:count]] = True
    return held


def _heldGroups(rng: np.random.Generator, codes: np.ndarray) -> np.ndarray:
    groups = codes.max() + 1
    tenth = (groups + 5) // 10  # the nearest whole number to 10%
    count = min(max(1, tenth), groups - 2)
    held = _seededOrder(rng, groups)[:count]
    return np.isin(codes, held)  # (n,)


def _rowFolds(rng: np.random.Generator, factors: list[np.ndarray], n: int) -> np.ndarray:
    """Deals the spare rows into FOLDS folds in seeded order; a group's first row stays seen."""
    order = _seededOrder(rng, n)  # (n,) row positions
    spare = order[_spare(order, factors)]
    folds = np.full(n, -1)  # (n,)
    folds[spare] = np.arange(len(spare)) % FOLDS
    return folds


def _groupFolds(rng: np.random.Generator, codes: np.ndarray) -> np.ndarray:
    """Deals the groups into min(FOLDS, G) folds in seeded order: one group each where G ≤ FOLDS."""
    groups = codes.max() + 1
    folds = min(FOLDS, groups)
    order = _seededOrder(rng, groups)  # (m,) group codes
    fold_of = np.empty(groups, dtype=int)  # (m,)
    fold_of[order] = np.arange(groups) % folds
    return fold_of[codes]  # (n,)


def _checkContract(problem: Problem, table: pd.DataFrame) -> None:
    """Checks that seed 0 of the single split reproduces the problem's own regimes."""
    for regime in ('rows', 'groups'):
        if regime not in problem.table:
            assert f'{regime}_single_0' not in table, problem.id
            continue
        own = (problem.table[regime] == 'held').to_numpy()
        copied = table[f'{regime}_single_0'].to_numpy() == 0
        assert (own == copied).all(), f'{problem.id}: {regime} differs from the contract'


# =====================================================================================
# the summary
# =====================================================================================


def summarize(id: str, problem: Problem, scores: pd.DataFrame, fits: pd.DataFrame) -> pd.DataFrame:
    """Returns per split the mean log scores of both lines over the held-out rows and their Δ.
    Δ's standard error is clustered by held-out unit: a group in the groups regime, a row in
    the rows regime. A failed fit leaves the split's scores NaN."""
    first = problem.table[problem.factors[0]].to_numpy()
    records = []
    for split, rows in scores.groupby('split', sort=False):
        regime, scheme, seed = split.split('_')
        delta = (rows['mixed'] - rows['glm']).to_numpy()  # (rows,)
        units = first[rows['row']] if regime == 'groups' else rows['row'].to_numpy()
        attempts = fits[fits['split'] == split]
        records.append(
            {
                'id': id,
                'family': problem.family,
                'n': len(problem.table),
                'G': int(first.max()) + 1,
                'regime': regime,
                'scheme': scheme,
                'seed': int(seed),
                'rows': len(rows),
                'units': len(np.unique(units)),
                'glm': rows['glm'].mean(skipna=False),
                'mixed': rows['mixed'].mean(skipna=False),
                'delta': delta.mean(),
                'delta_se': _clusteredSe(delta, units),
                'failed': int((attempts['error'].fillna('') != '').sum()),
                'singular': int(attempts['singular'].fillna(False).astype(bool).sum()),
                'warned': int((attempts['warning'].fillna('') != '').sum()),
                'seconds': float(attempts['seconds'].sum()),
            }
        )
    return pd.DataFrame(records)


def _clusteredSe(delta: np.ndarray, units: np.ndarray) -> float:
    """The standard error of the mean of `delta` over clusters of rows (Cameron & Miller 2015)."""
    clusters = len(np.unique(units))
    if clusters < 2:
        return float('nan')
    residuals = pd.Series(delta - delta.mean()).groupby(units).sum()
    variance = clusters / (clusters - 1) * (residuals**2).sum() / len(delta) ** 2
    return float(np.sqrt(variance))


# =====================================================================================
# the experiment
# =====================================================================================


class Experiment:
    """A run over the problems in scope, one directory per problem under `work`.
    A problem whose summary.csv exists is not run again."""

    def __init__(self, work: Path, seeds: int) -> None:
        self.work = work
        self.seeds = seeds

    def ids(self) -> list[str]:
        """Returns the candidates with at most ROWS rows and a family lme4 fits, largest first."""
        sizes = {}
        for id, problem in suite.problems('1.1', CACHE):
            if len(problem.table) <= ROWS and problem.family != 'cumulative':
                sizes[id] = len(problem.table)
        return sorted(sizes, key=sizes.get, reverse=True)

    def score(self, id: str) -> pd.DataFrame:
        dir = self.work / hashlib.sha256(id.encode()).hexdigest()[:16]
        summary = dir / 'summary.csv'
        if summary.exists():
            return pd.read_csv(summary)
        dir.mkdir(parents=True, exist_ok=True)
        problem = suite.load(id, CACHE)
        Handoff(problem).write(dir, settings={})
        splits(problem, self.seeds).to_csv(dir / 'folds.csv', index=False)
        single = {
            'VECLIB_MAXIMUM_THREADS': '1',
            'OPENBLAS_NUM_THREADS': '1',
            'OMP_NUM_THREADS': '1',
        }
        with open(dir / 'R.log', 'w') as log:
            subprocess.run(
                ['Rscript', HERE / 'fit.R', dir],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=os.environ | single,
                check=True,
            )
        scores = pd.read_csv(dir / 'scores.csv')
        fits = pd.read_csv(dir / 'fits.csv', keep_default_na=False, na_values=['NA'])
        table = summarize(id, problem, scores, fits)
        table.to_csv(summary, index=False)
        return table

    def collect(self, ids: list[str], workers: int) -> pd.DataFrame:
        with ThreadPoolExecutor(workers) as pool:
            tables = list(pool.map(self.score, ids))
        return pd.concat(tables, ignore_index=True)


# =====================================================================================
# main
# =====================================================================================

if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--work', type=Path, default=HERE / 'work', help='the directory of the per-problem runs')
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--pilot', type=int, default=0, help='run every n-th problem only, e.g. 26 for 21')
    parser.add_argument('--out', type=Path, default=HERE / 'scores.parquet')
    args = parser.parse_args()
    # fmt: on
    experiment = Experiment(args.work, args.seeds)
    ids = experiment.ids()
    if args.pilot:
        ids = ids[:: args.pilot]
    print(f'{len(ids)} problems')
    scores = experiment.collect(ids, args.workers)
    scores.to_parquet(args.out, index=False)
    print(f'{len(scores)} splits written to {args.out}')
