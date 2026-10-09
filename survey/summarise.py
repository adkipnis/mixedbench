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
from schema import TIERS, readCsv

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
TEMPLATE = HERE / 'SUMMARY.template.md'
PRACTICE = HERE / 'practice_quantiles.yaml'
# The v1 families of the stage table (metabeta-v3's packages/glmm/docs/design/stages.md): the
# practice column takes the maximum of their p90 (envelope rule 1), the minimum for the smallest
# group size.
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


# =====================================================================================
# pipeline: measured files -> axes -> shares -> K -> implied columns -> summary
# =====================================================================================
class Summariser:
    def __init__(self, root: Path, survey: Path) -> None:
        self.root, self.survey = Path(root), Path(survey)  # the registry folder, the survey's
        self.registry = readCsv(self.root / 'registry.csv')
        self.excluded = readCsv(self.root / 'excluded.csv')
        measured = FACTOR_AXES + tuple(ROW_AXES.values())
        self.dimensions = self.numeric(readCsv(self.root / 'dimensions.csv'), measured)
        self.columns = self.numeric(readCsv(self.root / 'columns.csv'), ('K',))
        self.rows = self.dimensions.drop_duplicates(['source', 'object', 'model_index'])
        self.modelled = self.columns[self.columns['in_model'] == 'yes']
        self.categoricals = self.modelled[self.modelled['type'].isin(CATEGORICAL_TYPES)]

    def flush(self) -> None:
        quantiles = self.quantiles()
        (self.root / 'quantiles.yaml').write_text(yaml.safe_dump(quantiles, sort_keys=False))
        (self.root / 'SUMMARY.md').write_text(self.summary(quantiles))

    @staticmethod
    def numeric(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
        converted = {c: pd.to_numeric(frame[c], errors='coerce') for c in columns}
        return frame.assign(**converted)

    # ---------------------------------------------------------------------------------
    # quantiles
    # ---------------------------------------------------------------------------------
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
                'covariate_type': self.shares(self.modelled['type']),
                'level': self.shares(self.modelled['level']),
                'relation': self.shares(self.dimensions['relation']),
                'response_type': self.shares(self.registry['response_type']),
                'reader': self.shares(self.registry['reader']),
                'published_model': self.shares(self.registry['published_model']),
            },
            'k_distribution': {int(k): v for k, v in self.shares(self.categoricals['K']).items()},
            'implied_columns': self.impliedColumns(),
        }

    @staticmethod
    def axis(frame: pd.DataFrame, column: str) -> dict:
        """One axis pooled, per tier present, and without the heavy source."""
        tiers = [t for t in TIERS if (frame['tier'] == t).any()]
        without_agridat = frame.loc[frame['source'] != HEAVY_SOURCE, column]
        return {
            'pooled': Summariser.quantilesOf(frame[column]),
            'tiers': {
                t: Summariser.quantilesOf(frame.loc[frame['tier'] == t, column]) for t in tiers
            },
            'without_agridat': Summariser.quantilesOf(without_agridat),
        }

    @staticmethod
    def quantilesOf(values: pd.Series) -> dict:
        values = pd.Series(values).dropna()
        out = {'n': len(values), 'min': Summariser.quantile(values, 0)}
        out |= {k: Summariser.quantile(values, q) for k, q in LEVELS.items()}
        out['max'] = Summariser.quantile(values, 1)
        return out

    @staticmethod
    def quantile(values: pd.Series, q: float) -> int | float:
        v = observed(values, q)
        return v if isinstance(v, int) else round(v, 4)

    def balancedShare(self) -> float:
        """Share of grouping factors whose allocation is balanced (α infinite)."""
        return round(float((self.dimensions['alpha'] == float('inf')).mean()), 3)

    @staticmethod
    def shares(values: pd.Series) -> dict:
        counts = values.value_counts()
        return {k: round(n / len(values), 3) for k, n in counts.items()}

    def impliedColumns(self) -> dict:
        """Expected design columns of a model with T terms under the observed categorical share c
        and mean K − 1: T (c (K − 1) + (1 − c)), one column per non-categorical term."""
        share = float(self.modelled['type'].isin(CATEGORICAL_TYPES).mean())
        perCategorical = float((self.categoricals['K'] - 1).mean())
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
            'tiers': self.counted(self.registry['tier']),
            'n_excluded': len(self.excluded),
            'excluded_reasons': self.counted(self.excluded['reason']),
            'balanced_share': quantiles['imbalance']['balanced_share'],
            'categorical_share': implied['categorical_share'],
            'mean_columns_per_categorical': implied['mean_columns_per_categorical'],
            'implied_columns': impliedText,
        }
        for axis, block in quantiles['axes'].items():
            fields[f'table_{PLACEHOLDERS.get(axis, axis)}'] = self.axisTable(axis, block, practice)
        fields |= {
            'table_relation': self.shareTable(self.dimensions['relation'], 'relation'),
            'table_covariate_type': self.shareTable(self.modelled['type'], 'covariate type'),
            'table_level': self.shareTable(self.modelled['level'], 'level'),
            'table_k_distribution': self.shareTable(self.kBucketed(), 'K'),
            'table_response_type': self.shareTable(self.registry['response_type'], 'response type'),
            'table_reader': self.shareTable(self.registry['reader'], 'reader'),
            'table_published_model': self.shareTable(self.registry['published_model'], 'published'),
            'tier_d': self.tierD(),
        }
        return Template(TEMPLATE.read_text()).substitute(fields)

    def kBucketed(self) -> pd.Series:
        """K as the summary table shows it: every level count up to the columns rule's 10, the
        long tail (declared factors of dozens of levels) as one `11+` row."""
        k = self.categoricals['K'].astype(int)
        return k.astype(str).where(k <= K_TAIL, f'{K_TAIL + 1}+')

    def tierD(self) -> str:
        """The deposit-level loss of Tier D (#26) as bullets: the links of `deposit_files.csv`
        by status, the listed files by role, the data files not pulled by reason, the objects
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
        papers = files.loc[files['label'].isin(registered['source']), 'paper_id']
        return '\n'.join([
            f'- Links: {len(links)} over {links["paper_id"].nunique()} papers; by status {self.counted(links["status"])}.',
            f'- Listed files: {len(listed)}; by role {self.counted(listed["role"])}; data files not pulled: {self.counted(unpulled["reason"])}.',
            f'- Objects excluded: {len(excluded)} ({self.counted(excluded["reason"])}).',
            f'- Papers with a registry row: {papers.nunique()}, over {len(registered)} rows.',
        ])  # fmt: skip

    @staticmethod
    def axisTable(axis: str, block: dict, practice: dict) -> str:
        """Rows pooled, per tier and without agridat; the pooled row ends with the practice column."""
        head = f'| {axis} | ' + ' | '.join(QUANTILE_KEYS) + ' | practice |'
        rows = {'pooled': block['pooled']}
        rows |= {f'tier {t}': q for t, q in block['tiers'].items()}
        rows['without agridat'] = block['without_agridat']
        last = {'pooled': Summariser.cell(Summariser.practiceP90(axis, practice))}
        lines = [
            f'| {name} | '
            + ' | '.join(Summariser.cell(q[k]) for k in QUANTILE_KEYS)
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

    @staticmethod
    def shareTable(values: pd.Series, label: str) -> str:
        counts = values.value_counts()
        rows = [f'| {k} | {n} | {n / len(values):.0%} |' for k, n in counts.items()]
        return '\n'.join([f'| {label} | n | share |', '|---|---|---|', *rows])

    @staticmethod
    def counted(values: pd.Series) -> str:
        """`D 12, R 3` from a column of labels; `none` when empty."""
        return ', '.join(f'{k} {n}' for k, n in values.value_counts().items()) or 'none'

    @staticmethod
    def cell(value: float | None) -> str:
        return '–' if value is None else str(value)
