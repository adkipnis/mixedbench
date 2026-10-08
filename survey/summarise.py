"""Quantiles and summary of the dimension survey from the measured files (#18):
`quantiles.yaml` from `dimensions.csv`, `columns.csv` and `registry.csv`, every axis pooled,
per tier and with agridat removed; `SUMMARY.md` from the digit-free template, the practice
survey's p90 read at merge time from `practice_quantiles.yaml`, a snapshot of the practice
survey's `quantiles.yaml`, which stays in metabeta-v3.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

import pandas as pd
import yaml
from measure import observed
from schema import TIERS

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
TEMPLATE = HERE / 'SUMMARY.template.md'
PRACTICE = HERE / 'practice_quantiles.yaml'
# The v1 families of the stage table (docs/design/stages.md): the practice column takes the
# maximum of their p90 (envelope rule 1), the minimum for the smallest group size.
PRACTICE_FAMILIES = ('Normal', 'Bernoulli', 'Poisson', 'negative binomial', 'binomial', 'Gamma', 'log-normal')  # fmt: skip
PRACTICE_AXES = {
    'n_obs': 'n_obs',
    'n_grouping_factors': 'n_grouping_factors',
    'n_groups': 'n_groups_per_factor',
    'group_size_min': 'group_size_min',
    'group_size_max': 'group_size_max',
    'd_doc': 'n_fixed_effects',  # terms, not columns: the gap this survey's K closes
}
QUANTILE_KEYS = ('n', 'min', 'p5', 'p10', 'p50', 'p90', 'p95', 'max')
# placeholder names of the template carry no digit (asserted by a test)
PLACEHOLDERS = {'group_size_p10': 'group_size_lower', 'group_size_p50': 'group_size_median', 'group_size_p90': 'group_size_upper'}  # fmt: skip
HEAVY_SOURCE = 'agridat'  # the one capped census source large enough to pull the quantiles
LEVELS = {'p5': 0.05, 'p10': 0.1, 'p50': 0.5, 'p90': 0.9, 'p95': 0.95}
# Per-factor axes count once per grouping factor, dataset axes once per registry row.
FACTOR_AXES = (
    'n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90',
    'group_size_max', 'singleton_share', 'cv', 'alpha',
)  # fmt: skip
ROW_AXES = {'n_obs': 'n_obs', 'n_grouping_factors': 'n_factors', 'd_doc': 'd_doc', 'd_all': 'd_all'}  # fmt: skip
CATEGORICAL_TYPES = ('categorical', 'ordered')
TERMS = (9, 14)  # the practice survey's p90 and p95 of fixed-effect terms (envelope rule 4)
K_TAIL = 10  # the summary's K table pools the levels above this (the columns rule's integer cap)


def readCsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def numeric(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    converted = {c: pd.to_numeric(frame[c], errors='coerce') for c in columns}
    return frame.assign(**converted)


def quantile(values: pd.Series, q: float) -> int | float | None:
    if values.empty:
        return None
    v = observed(values, q)
    return v if isinstance(v, int) else round(v, 4)


def quantiles(values: pd.Series) -> dict:
    values = pd.Series(values).dropna()
    out = {'n': len(values), 'min': quantile(values, 0)}
    out |= {k: quantile(values, q) for k, q in LEVELS.items()}
    out['max'] = quantile(values, 1)
    return out


def shares(values: pd.Series) -> dict:
    counts = values.value_counts()
    return {k: round(n / len(values), 3) for k, n in counts.items()}


def shareTable(values: pd.Series, label: str) -> str:
    counts = values.value_counts()
    rows = [f'| {k} | {n} | {n / len(values):.0%} |' for k, n in counts.items()]
    return '\n'.join([f'| {label} | n | share |', '|---|---|---|', *rows])


def cell(value: float | None) -> str:
    return '–' if value is None else str(value)


def counted(values: pd.Series) -> str:
    """`D 12, R 3` from a column of labels; `none` when empty."""
    return ', '.join(f'{k} {n}' for k, n in values.value_counts().items()) or 'none'


# =====================================================================================
# pipeline: measured files -> axes -> shares -> K -> implied columns -> summary
# =====================================================================================
class Summariser:
    def __init__(
        self, root: Path, survey: Path, registry: pd.DataFrame, excluded: pd.DataFrame
    ) -> None:
        self.root, self.survey = Path(root), Path(survey)  # the registry folder, the survey's
        self.registry = registry
        self.excluded = excluded
        measured = FACTOR_AXES + tuple(ROW_AXES.values())
        self.dimensions = numeric(readCsv(self.root / 'dimensions.csv'), measured)
        self.columns = numeric(readCsv(self.root / 'columns.csv'), ('K',))
        self.rows = self.dimensions.drop_duplicates(['source', 'object', 'model_index'])
        self.modelled = self.columns[self.columns['in_model'] == 'yes']
        self.categoricals = self.modelled[self.modelled['type'].isin(CATEGORICAL_TYPES)]

    def quantiles(self) -> dict:
        axes = {axis: self.axis(self.dimensions, axis) for axis in FACTOR_AXES}
        axes |= {axis: self.axis(self.rows, column) for axis, column in ROW_AXES.items()}
        axes['K'] = self.axis(self.categoricals, 'K')
        return {
            'n_rows': len(self.registry),
            'n_objects': len(self.registry.drop_duplicates(['source', 'object'])),
            'n_factor_rows': len(self.dimensions),
            'axes': axes,
            'imbalance': {'balanced_share': self.balancedShare()},
            'shares': {
                'covariate_type': shares(self.modelled['type']),
                'level': shares(self.modelled['level']),
                'relation': shares(self.dimensions['relation']),
                'response_type': shares(self.registry['response_type']),
                'reader': shares(self.registry['reader']),
                'published_model': shares(self.registry['published_model']),
            },
            'k_distribution': {int(k): v for k, v in shares(self.categoricals['K']).items()},
            'implied_columns': self.impliedColumns(),
        }

    # ---------------------------------------------------------------------------------
    # axes
    # ---------------------------------------------------------------------------------
    @staticmethod
    def axis(frame: pd.DataFrame, column: str) -> dict:
        """One axis pooled, per tier present, and without the heavy source."""
        tiers = [t for t in TIERS if (frame['tier'] == t).any()]
        return {
            'pooled': quantiles(frame[column]),
            'tiers': {t: quantiles(frame.loc[frame['tier'] == t, column]) for t in tiers},
            'without_agridat': quantiles(frame.loc[frame['source'] != HEAVY_SOURCE, column]),
        }

    def balancedShare(self) -> float:
        """Share of grouping factors whose allocation is balanced (α infinite)."""
        if self.dimensions.empty:
            return 0.0
        return round(float((self.dimensions['alpha'] == float('inf')).mean()), 3)

    def impliedColumns(self) -> dict:
        """Expected design columns of a model with T terms under the observed categorical share c
        and mean K − 1: T (c (K − 1) + (1 − c)), one column per non-categorical term."""
        if self.modelled.empty:
            empty = {f'terms_{t}': None for t in TERMS}
            return {'categorical_share': None, 'mean_columns_per_categorical': None} | empty
        share = float(self.modelled['type'].isin(CATEGORICAL_TYPES).mean())
        perCategorical = (
            float((self.categoricals['K'] - 1).mean()) if len(self.categoricals) else 0.0
        )
        perTerm = share * perCategorical + (1 - share)
        return {
            'categorical_share': round(share, 3),
            'mean_columns_per_categorical': round(perCategorical, 3),
            **{f'terms_{t}': round(t * perTerm, 2) for t in TERMS},
        }

    # ---------------------------------------------------------------------------------
    # summary
    # ---------------------------------------------------------------------------------
    def summary(self, quantiles: dict) -> str:
        practice = yaml.safe_load(PRACTICE.read_text())['families']
        implied = quantiles['implied_columns']
        impliedText = ', '.join(f'{t} terms {implied[f"terms_{t}"]} columns' for t in TERMS)
        fields = {
            'n_rows': quantiles['n_rows'],
            'n_objects': quantiles['n_objects'],
            'n_factor_rows': quantiles['n_factor_rows'],
            'tiers': counted(self.registry['tier']),
            'n_excluded': len(self.excluded),
            'excluded_reasons': counted(self.excluded['reason']),
            'balanced_share': quantiles['imbalance']['balanced_share'],
            'categorical_share': implied['categorical_share'],
            'mean_columns_per_categorical': implied['mean_columns_per_categorical'],
            'implied_columns': impliedText,
        }
        for axis, block in quantiles['axes'].items():
            fields[f'table_{PLACEHOLDERS.get(axis, axis)}'] = self.axisTable(axis, block, practice)
        fields |= {
            'table_relation': shareTable(self.dimensions['relation'], 'relation'),
            'table_covariate_type': shareTable(self.modelled['type'], 'covariate type'),
            'table_level': shareTable(self.modelled['level'], 'level'),
            'table_k_distribution': shareTable(self.kBucketed(), 'K'),
            'table_response_type': shareTable(self.registry['response_type'], 'response type'),
            'table_reader': shareTable(self.registry['reader'], 'reader'),
            'table_published_model': shareTable(self.registry['published_model'], 'published'),
            'tier_d': self.tierD(),
        }
        return Template(TEMPLATE.read_text()).substitute(fields)

    def kBucketed(self) -> pd.Series:
        """K as the summary table shows it: every level count up to the columns rule's 10, the
        long tail (declared factors of dozens of levels) as one `11+` row."""
        k = self.categoricals['K'].astype(int)
        return k.astype(str).where(k <= K_TAIL, f'{K_TAIL + 1}+')

    def tierD(self) -> str:
        """The deposit-level loss of Tier D (#26) as bullets: the links of `deposits.csv` by
        status, the listed files by role, the data files not pulled by reason, the objects
        excluded by reason, and the papers that reached the registry."""
        file = self.survey / 'deposit_files.csv'
        if not file.exists():
            return 'Tier D not pulled.'
        files = readCsv(file)
        links = files.drop_duplicates(['paper_id', 'link'])
        listed = files[files['file'] != '']
        data = listed[listed['role'] == 'data']
        unpulled = data[data['reason'] != '']
        excluded = self.excluded[self.excluded['tier'] == 'D']
        registered = self.registry[self.registry['tier'] == 'D']
        labels = registered['source'].str.replace(
            r'_(dryad|osf|zenodo|figshare)(_\d+)?$', '', regex=True
        )
        return '\n'.join([
            f'- Links: {len(links)} of {links["paper_id"].nunique()} papers; by status {counted(links["status"])}.',
            f'- Listed files: {len(listed)}; by role {counted(listed["role"])}; data files not pulled: {counted(unpulled["reason"])}.',
            f'- Objects excluded: {len(excluded)} ({counted(excluded["reason"])}).',
            f'- Papers with a registry row: {labels.nunique()}, over {len(registered)} rows.',
        ])  # fmt: skip

    @staticmethod
    def axisTable(axis: str, block: dict, practice: dict) -> str:
        """Rows pooled, per tier and without agridat; the pooled row ends with the practice p90."""
        head = f'| {axis} | ' + ' | '.join(QUANTILE_KEYS) + ' | practice p90 |'
        rows = {'pooled': block['pooled']}
        rows |= {f'tier {t}': q for t, q in block['tiers'].items()}
        rows['without agridat'] = block['without_agridat']
        last = {'pooled': cell(Summariser.practiceP90(axis, practice))}
        lines = [
            f'| {name} | '
            + ' | '.join(cell(q[k]) for k in QUANTILE_KEYS)
            + f' | {last.get(name, "")} |'
            for name, q in rows.items()
        ]
        return '\n'.join([head, '|' + '---|' * (len(QUANTILE_KEYS) + 2), *lines])

    @staticmethod
    def practiceP90(axis: str, practice: dict) -> int | float | None:
        if axis not in PRACTICE_AXES:
            return None
        values = [practice[f]['p90'][PRACTICE_AXES[axis]] for f in PRACTICE_FAMILIES]
        values = [v for v in values if v is not None]
        if axis == 'group_size_min':
            return min(values)
        return max(values)

    def flush(self) -> None:
        quantiles = self.quantiles()
        (self.root / 'quantiles.yaml').write_text(yaml.safe_dump(quantiles, sort_keys=False))
        (self.root / 'SUMMARY.md').write_text(self.summary(quantiles))
