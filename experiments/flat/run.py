"""flat/run.py compares the registry's grouped tables with flat tables, one table at a time.

Comparison axes, one number per table each:
- sizes: rows, columns, design columns and the condition index
- type mix: the shares of continuous, binary, categorical and ordered columns, and the median K
  of the categorical and ordered ones
- column statistics: each statistic's median over the table's columns
- the response: its type, as a 0/1 indicator per type, and its statistics, against the flat
  tables that name one

The sets are compared by the two-sided Mann–Whitney U test, which asks whether a table of one set
tends to lie above a table of the other. The rank-biserial correlation quantifies its effect size.
We test against two sets of flat tables: (1) all, and (2) only tables with a documented response.

pipeline:
---------
the measured files of registry/
-> per registry object, its first model's columns and response   summarizeRegistry
-> per flat table, its columns but the id columns and response   summarizeFlat
-> per table: sizes, type shares, each statistic's median        summarizeTables
-> per table: its response's type and statistics                 _joinResponse
-> per flat side and statistic: the U test, rank-biserial r      compareSamples
-> registry_tables.csv, flat_tables.csv and tests.csv

Run from the repo root:

    uv run python experiments/flat/run.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from typing import get_args

import numpy as np
import pandas as pd
from mixedbench.registry.row import ResponseType, readCsv

HERE = Path(__file__).parent
KEY = ['source', 'object']
TYPES = ('continuous', 'binary', 'categorical', 'ordered')  # the column types of columns.csv
LEVELED_TYPES = ('categorical', 'ordered')  # the types whose K levels count K − 1 in d_all
COLUMN_STATISTICS = (
    'missing_share', 'skewness', 'excess_kurtosis', 'outlier_share', 'zero_share', 'min_share',
    'max_share', 'unique_share', 'rare_level_share', 'max_abs_rho',
)  # fmt: skip
STATISTICS = (
    'n_obs', 'n_columns', 'd_all', 'condition_all',
    'continuous_share', 'binary_share', 'categorical_share', 'ordered_share',
    'K', *COLUMN_STATISTICS,
)  # fmt: skip
# a response's statistics, as responses.csv measures them, apart from the columns' medians
RESPONSE_STATISTICS = (
    'response_K', 'response_missing_share', 'response_skewness', 'response_excess_kurtosis',
    'response_outlier_share', 'response_zero_share', 'response_min_share', 'response_max_share',
    'response_unique_share', 'response_rare_level_share', 'response_max_abs_rho',
)  # fmt: skip

# =====================================================================================
# the summary tables
# =====================================================================================


def summarizeRegistry(dir: Path) -> pd.DataFrame:
    """One row per registry object, from its first model."""
    dimensions = _readNumbers(dir / 'dimensions.csv', ('n_obs', 'condition_all'))
    first = dimensions[dimensions['model_index'] == '1']
    tables = first.drop_duplicates(KEY)  # n_obs of the first factor, as quantiles.yaml counts it
    columns = _readNumbers(dir / 'columns.csv', ('K', *COLUMN_STATISTICS))
    columns = columns[columns['model_index'] == '1']
    responses = _readNumbers(dir / 'responses.csv', ('K', *COLUMN_STATISTICS))
    responses = responses[responses['model_index'] == '1']
    return _joinResponse(summarizeTables(tables, columns), responses)


def _readNumbers(path: Path, columns: tuple[str, ...]) -> pd.DataFrame:
    table = readCsv(path)
    converted = {c: pd.to_numeric(table[c].replace('', np.nan)) for c in columns}
    return table.assign(**converted)


def summarizeFlat(dir: Path) -> pd.DataFrame:
    """One row per flat table with its response, from every column but the id columns."""
    tables = _readNumbers(dir / 'flat.csv', ('n_obs', 'condition_all'))
    columns = _readNumbers(dir / 'flat_columns.csv', ('K', *COLUMN_STATISTICS))
    columns = columns[columns['id_column'] == 'no']
    responses = _readNumbers(dir / 'flat_response_statistics.csv', ('K', *COLUMN_STATISTICS))
    summary = _joinResponse(summarizeTables(tables, columns), responses)
    summary.insert(3, 'response', tables['response'])
    return summary


def summarizeTables(tables: pd.DataFrame, columns: pd.DataFrame) -> pd.DataFrame:
    """Each table's sizes, type shares and statistic medians.
    A table without columns gets zero counts and blank shares and medians."""
    summary = tables.set_index(KEY)[['tier', 'n_obs']]
    by_table = columns.groupby(KEY)
    summary['n_columns'] = by_table.size().reindex(summary.index, fill_value=0)
    leveled = columns['type'].isin(LEVELED_TYPES)
    widths = columns.assign(width=np.where(leveled, columns['K'] - 1, 1))
    summary['d_all'] = widths.groupby(KEY)['width'].sum().reindex(summary.index, fill_value=0)
    summary['condition_all'] = tables.set_index(KEY)['condition_all']
    shares = pd.crosstab([columns['source'], columns['object']], columns['type'], normalize='index')
    for kind in TYPES:
        summary[f'{kind}_share'] = shares[kind]
    summary['K'] = columns[leveled].groupby(KEY)['K'].median()
    for statistic in COLUMN_STATISTICS:
        summary[statistic] = by_table[statistic].median()
    return summary.astype({'n_columns': int, 'd_all': int}).reset_index()


def _joinResponse(summary: pd.DataFrame, responses: pd.DataFrame) -> pd.DataFrame:
    """Each table's response type and statistics, blank where it names no response."""
    responses = responses.set_index(KEY)
    statistics = responses[['K', *COLUMN_STATISTICS]].add_prefix('response_')
    return summary.join(responses[['response_type']].join(statistics), on=KEY)


# =====================================================================================
# the tests
# =====================================================================================


def compareSamples(registry: pd.DataFrame, flat: pd.DataFrame) -> pd.DataFrame:
    """Tests every statistic against both flat sets, and the response's type and statistics
    against the flat tables that name one, leaving out blanks but keeping inf."""
    named = flat[flat['response'] != 'none']
    records = []
    for statistic in STATISTICS:
        records.append(_compareStatistic('all', statistic, registry[statistic], flat[statistic]))
    for statistic in (*STATISTICS, *RESPONSE_STATISTICS):
        records.append(
            _compareStatistic('response', statistic, registry[statistic], named[statistic])
        )
    for response_type in get_args(ResponseType):
        x = (registry['response_type'] == response_type).astype(float)
        y = (named['response_type'] == response_type).astype(float)
        records.append(_compareStatistic('response', f'response_{response_type}_share', x, y))
    return pd.DataFrame(records)


def _compareStatistic(side: str, statistic: str, x: pd.Series, y: pd.Series) -> dict:
    x = x.dropna()
    y = y.dropna()
    sizes = {'n_registry': len(x), 'n_flat': len(y)}
    medians = {'median_registry': x.median(), 'median_flat': y.median()}
    return {'flat': side, 'statistic': statistic} | sizes | medians | _testMannWhitney(x, y)


def _testMannWhitney(x: pd.Series, y: pd.Series) -> dict:
    """The Mann–Whitney U test as scipy's `mannwhitneyu(method='asymptotic')` computes it, and the
    rank-biserial r = 2U / (n_x n_y) − 1, the probability that x lies above y minus the reverse
    (Kerby 2014, https://doi.org/10.2466/11.IT.3.1)."""
    n_x = len(x)
    n_y = len(y)
    n = n_x + n_y
    pooled = pd.concat([x, y])
    ranks = pooled.rank().to_numpy()  # average ranks over ties, inf above every finite value
    u = ranks[:n_x].sum() - n_x * (n_x + 1) / 2  # the pairs where x is larger, a tie half
    ties = pooled.value_counts().to_numpy()  # the size of each group of equal values
    variance = n_x * n_y / 12 * (n + 1 - (ties**3 - ties).sum() / (n * (n - 1)))
    z = (abs(u - n_x * n_y / 2) - 0.5) / math.sqrt(variance)
    return {'U': u, 'p': math.erfc(z / math.sqrt(2)), 'rank_biserial': 2 * u / (n_x * n_y) - 1}


# =====================================================================================
# main
# =====================================================================================

if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--registry', type=Path, default=Path('registry'), help='the directory of the measured files')
    parser.add_argument('--out', type=Path, default=HERE, help='the directory of the three tables')
    args = parser.parse_args()
    # fmt: on
    registry = summarizeRegistry(args.registry)
    flat = summarizeFlat(args.registry)
    tests = compareSamples(registry, flat)
    registry.round(4).to_csv(args.out / 'registry_tables.csv', index=False)
    flat.round(4).to_csv(args.out / 'flat_tables.csv', index=False)
    rounded = {'median_registry': 4, 'median_flat': 4, 'rank_biserial': 4}
    tests.round(rounded).to_csv(args.out / 'tests.csv', index=False)
    print(f'{len(registry)} registry objects, {len(flat)} flat tables, {len(tests)} tests')
