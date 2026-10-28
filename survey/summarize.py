"""Quantiles and summary of the dimension survey from the measured files (#18):
`quantiles.yaml` from `registry.csv` and the measured files, every axis pooled,
per tier and with agridat removed, and an axis the flat sample shares over its two files too;
`SUMMARY.md` from the digit-free template, the practice
survey's p90 read at merge time from `practice_quantiles.yaml`, a snapshot of the practice
survey's `quantiles.yaml`, which stays in metabeta-v3.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

import pandas as pd
import yaml
from columns import COLUMN_STATISTICS
from dimensions import CONDITIONS, pickObserved
from fits import FACTOR_STATISTICS, FIT_STATISTICS, ROW_STATISTICS
from flat import CHECKS, NOT_FLAT, HandCheck
from groups import COLUMN_FACTOR_STATISTICS
from mixedbench.registry.row import readCsv
from pairs import FACTOR_PAIR_STATISTICS
from schema import TIERS

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
TEMPLATE = HERE / 'SUMMARY.template.md'
PRACTICE = HERE / 'practice_quantiles.yaml'
# the v1 families of the stage table (metabeta-v3's packages/glmm/docs/design/stages.md): the
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
# per-factor axes count once per grouping factor, dataset axes once per registry row.
FACTOR_AXES = (
    'n_groups', 'group_size_min', 'group_size_p10', 'group_size_p50', 'group_size_p90',
    'group_size_max', 'singleton_share', 'cv', 'alpha',
)  # fmt: skip
ROW_AXES = {'n_obs': 'n_obs', 'n_grouping_factors': 'n_factors', 'd_doc': 'd_doc', 'd_all': 'd_all'}  # fmt: skip
FLAT_TABLE_AXES = ('n_obs', 'd_all', 'condition_all')  # the axes flat.csv measures once per table
CATEGORICAL_TYPES = ('categorical', 'ordered')
TERMS = (9, 14)  # the practice survey's p90 and p95 of fixed-effect terms (envelope rule 4)
K_TAIL = 10  # the summary's K table pools the levels above this (the columns rule's integer cap)


# =====================================================================================
# pipeline: measured files -> axes -> shares -> K -> implied columns -> summary
# =====================================================================================
class Summarizer:
    def __init__(self, root: Path, survey: Path) -> None:
        self.root, self.survey = Path(root), Path(survey)  # the registry folder, the survey's
        self.registry = readCsv(self.root / 'registry.csv')
        self.excluded = readCsv(self.root / 'excluded.csv')
        measured = FACTOR_AXES + tuple(ROW_AXES.values()) + CONDITIONS
        self.dimensions = self.numeric(readCsv(self.root / 'dimensions.csv'), measured)
        self.columns = self.numeric(readCsv(self.root / 'columns.csv'), ('K', *COLUMN_STATISTICS))
        column_factors = readCsv(self.root / 'column_factors.csv')
        self.column_factors = self.numeric(column_factors, COLUMN_FACTOR_STATISTICS)
        self.pairs = self.numeric(readCsv(self.root / 'factor_pairs.csv'), FACTOR_PAIR_STATISTICS)
        self.fits = self.numeric(readCsv(self.root / 'fits.csv'), FIT_STATISTICS)
        self.fitted = self.fits.drop_duplicates(['source', 'object', 'model_index'])  # per row
        self.rows = self.dimensions.drop_duplicates(['source', 'object', 'model_index'])
        self.modeled = self.columns[self.columns['in_model'] == 'yes']
        self.categoricals = self.modeled[self.modeled['type'].isin(CATEGORICAL_TYPES)]
        self.flat = self.numeric(readCsv(self.root / 'flat.csv'), FLAT_TABLE_AXES)
        flat_columns = readCsv(self.root / 'flat_columns.csv')
        self.flat_columns = self.numeric(flat_columns, ('K', *COLUMN_STATISTICS))
        self.flat_categoricals = self.flat_columns[
            self.flat_columns['type'].isin(CATEGORICAL_TYPES)
        ]

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
        axes |= {axis: self.axis(self.columns, axis) for axis in COLUMN_STATISTICS}
        axes |= {axis: self.axis(self.column_factors, axis) for axis in COLUMN_FACTOR_STATISTICS}
        axes |= {axis: self.axis(self.pairs, axis) for axis in FACTOR_PAIR_STATISTICS}
        axes |= {axis: self.axis(self.rows, axis) for axis in CONDITIONS}
        axes |= {axis: self.axis(self.fitted, axis) for axis in ROW_STATISTICS}
        axes |= {axis: self.axis(self.fits, axis) for axis in FACTOR_STATISTICS}
        for axis, values in self.collectFlatValues().items():
            axes[axis]['flat'] = self.quantilesOf(values)
        return {
            'n_rows': len(self.registry),
            'n_objects': len(self.registry.drop_duplicates(['source', 'object'])),
            'n_factor_rows': len(self.dimensions),
            'axes': axes,
            'imbalance': {'balanced_share': self.balancedShare()},
            'shares': {
                'covariate_type': self.shares(self.modeled['type']),
                'level': self.shares(self.modeled['level']),
                'relation': self.shares(self.dimensions['relation']),
                'pair_relation': self.shares(self.pairs['relation']),
                'superior': self.shares(self.findSuperiorSides()),
                'response_type': self.shares(self.registry['response_type']),
                'reader': self.shares(self.registry['reader']),
                'published_model': self.shares(self.registry['published_model']),
                'status': self.shares(self.fitted['status']),
                'flat_column_type': self.shares(self.flat_columns['type']),
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
            'pooled': Summarizer.quantilesOf(frame[column]),
            'tiers': {
                t: Summarizer.quantilesOf(frame.loc[frame['tier'] == t, column]) for t in tiers
            },
            'without_agridat': Summarizer.quantilesOf(without_agridat),
        }

    def collectFlatValues(self) -> dict[str, pd.Series]:
        """The flat sample's values of each axis both samples share: a size or design axis once
        per flat table, K once per categorical flat column, a column statistic once per flat
        column."""
        values = {axis: self.flat[axis] for axis in FLAT_TABLE_AXES}
        values['K'] = self.flat_categoricals['K']
        values |= {axis: self.flat_columns[axis] for axis in COLUMN_STATISTICS}
        return values

    @staticmethod
    def quantilesOf(values: pd.Series) -> dict:
        values = pd.Series(values).dropna()
        out = {'n': len(values), 'min': Summarizer.quantile(values, 0)}
        out |= {k: Summarizer.quantile(values, q) for k, q in LEVELS.items()}
        out['max'] = Summarizer.quantile(values, 1)
        return out

    @staticmethod
    def quantile(values: pd.Series, q: float) -> int | float:
        v = pickObserved(values, q)
        return v if isinstance(v, int) else round(v, 4)

    def balancedShare(self) -> float:
        """Share of grouping factors whose allocation is balanced (α infinite)."""
        return round(float((self.dimensions['alpha'] == float('inf')).mean()), 3)

    def findSuperiorSides(self) -> pd.Series:
        """Which factor of each nested pair holds whole groups of the other:
        `factor_a`, `factor_b`, or `none` when the two partition the rows alike."""
        nested = self.pairs[self.pairs['relation'] == 'nested']
        sides = pd.Series('none', index=nested.index)
        sides[nested['superior'] == nested['factor_a']] = 'factor_a'
        sides[nested['superior'] == nested['factor_b']] = 'factor_b'
        return sides

    @staticmethod
    def shares(values: pd.Series) -> dict:
        counts = values.value_counts()
        return {k: round(n / len(values), 3) for k, n in counts.items()}

    def impliedColumns(self) -> dict:
        """Expected design columns of a model with T terms under the observed categorical share c
        and mean k − 1: T (c (k − 1) + (1 − c)), one column per non-categorical term."""
        share = float(self.modeled['type'].isin(CATEGORICAL_TYPES).mean())
        per_categorical = float((self.categoricals['K'] - 1).mean())
        per_term = share * per_categorical + (1 - share)
        return {
            'categorical_share': round(share, 3),
            'mean_columns_per_categorical': round(per_categorical, 3),
            **{f'terms_{t}': round(t * per_term, 2) for t in TERMS},
        }

    # ---------------------------------------------------------------------------------
    # summary
    # ---------------------------------------------------------------------------------
    def summary(self, quantiles: dict) -> str:
        practice = yaml.safe_load(PRACTICE.read_text())['families']
        implied = quantiles['implied_columns']
        implied_text = ', '.join(f'{t} terms {implied[f"terms_{t}"]} columns' for t in TERMS)
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
            'implied_columns': implied_text,
        }
        axes = quantiles['axes']
        for axis in (*FACTOR_AXES, *ROW_AXES, 'K'):
            placeholder = f'table_{PLACEHOLDERS.get(axis, axis)}'
            fields[placeholder] = self.renderAxisTable(axis, axes[axis], practice)
        fields |= {
            'table_conditions': self.renderStatisticTable(CONDITIONS, axes),
            'table_column_statistics': self.renderStatisticTable(COLUMN_STATISTICS, axes),
            'table_column_factor_statistics': self.renderStatisticTable(
                COLUMN_FACTOR_STATISTICS, axes
            ),
            'table_pair_statistics': self.renderStatisticTable(FACTOR_PAIR_STATISTICS, axes),
            'table_fit_statistics': self.renderStatisticTable(FIT_STATISTICS, axes),
            'table_status': self.renderShareTable(self.fitted['status'], 'status'),
            'table_pair_relation': self.renderShareTable(self.pairs['relation'], 'pair relation'),
            'table_superior': self.renderShareTable(self.findSuperiorSides(), 'superior'),
            'table_relation': self.renderShareTable(self.dimensions['relation'], 'relation'),
            'table_covariate_type': self.renderShareTable(self.modeled['type'], 'covariate type'),
            'table_level': self.renderShareTable(self.modeled['level'], 'level'),
            'table_k_distribution': self.renderShareTable(self.kBucketed(), 'K'),
            'table_response_type': self.renderShareTable(
                self.registry['response_type'], 'response type'
            ),
            'table_reader': self.renderShareTable(self.registry['reader'], 'reader'),
            'table_published_model': self.renderShareTable(
                self.registry['published_model'], 'published'
            ),
            'tier_d': self.tierD(),
            'flat_corpus': self.renderFlatCorpus(),
            'table_flat_column_type': self.renderShareTable(
                self.flat_columns['type'], 'column type'
            ),
            'table_flat_statistics': self.renderStatisticTable(
                ('condition_all', *COLUMN_STATISTICS), axes, 'flat'
            ),
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

    def renderFlatCorpus(self) -> str:
        """The flat sample's tables by stratum and tier, the frame's read tables the screen
        flagged, the tables the response reading found not flat, the verdicts by kind, the share
        of the hand sample that stood, the tables that name a response and the shares of the
        response check and its recheck."""
        screen = readCsv(self.survey / 'flat_screen.csv')
        read = screen[screen['stratum'] == 'read']
        flagged = read[read['flagged'] == 'yes']
        responses = readCsv(self.survey / 'flat_responses.csv')
        not_flat = responses['evidence'].str.startswith(NOT_FLAT).sum()
        verdicts = self.counted(readCsv(self.survey / 'flat_verdicts.csv')['verdict'])
        hand = self.readAgreement(CHECKS['verdict'])
        check = self.readAgreement(CHECKS['response'])
        recheck = self.readAgreement(CHECKS['recheck'])
        named = (self.flat['response'] != 'none').sum()
        strata = self.counted(self.flat['stratum'])
        tiers = self.counted(self.flat['tier'])
        return '\n'.join([
            f'**Corpus.** {len(self.flat)} flat tables; per stratum {strata}; per tier {tiers}.',
            f"The screen flagged {len(flagged)} of the frame's {len(read)} read tables for a second reading and the response reading found {not_flat} not flat; verdicts {verdicts}.",
            f'The hand sample of {hand["tables"]} tables stood at {hand["stood"]}.',
            f'{named} of the {len(self.flat)} tables name a response; the response check of {check["tables"]} tables stood at {check["stood"]}, its recheck of {recheck["tables"]} `none` tables at {recheck["stood"]}.',
        ])  # fmt: skip

    def readAgreement(self, check: HandCheck) -> pd.Series:
        """A hand check's tables and the share of them that stood, over all its strata."""
        return readCsv(self.survey / check.AGREEMENT).set_index('stratum').loc['all']

    @staticmethod
    def renderAxisTable(axis: str, block: dict, practice: dict) -> str:
        """Rows pooled, per tier, without agridat and, where the axis has one, the flat sample's;
        the pooled row ends with the practice column."""
        head = f'| {axis} | ' + ' | '.join(QUANTILE_KEYS) + ' | practice |'
        rows = {'pooled': block['pooled']}
        rows |= {f'tier {t}': q for t, q in block['tiers'].items()}
        rows['without agridat'] = block['without_agridat']
        if 'flat' in block:
            rows['flat'] = block['flat']
        last = {'pooled': Summarizer.cell(Summarizer.practiceP90(axis, practice))}
        lines = [head, '|' + '---|' * (len(QUANTILE_KEYS) + 2)]
        for name, q in rows.items():
            cells = Summarizer.renderQuantileCells(q)
            lines.append(f'| {name} | {cells} | {last.get(name, "")} |')
        return '\n'.join(lines)

    @staticmethod
    def renderQuantileCells(quantiles: dict) -> str:
        return ' | '.join(Summarizer.cell(quantiles[k]) for k in QUANTILE_KEYS)

    @staticmethod
    def renderStatisticTable(statistics: tuple[str, ...], axes: dict, split: str = 'pooled') -> str:
        """One row per statistic, the quantiles of one split as columns, pooled unless named."""
        head = '| statistic | ' + ' | '.join(QUANTILE_KEYS) + ' |'
        lines = [head, '|' + '---|' * (len(QUANTILE_KEYS) + 1)]
        for statistic in statistics:
            cells = Summarizer.renderQuantileCells(axes[statistic][split])
            lines.append(f'| {statistic} | {cells} |')
        return '\n'.join(lines)

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
    def renderShareTable(values: pd.Series, label: str) -> str:
        counts = values.value_counts()
        rows = [f'| {k} | {n} | {n / len(values):.0%} |' for k, n in counts.items()]
        return '\n'.join([f'| {label} | n | share |', '|---|---|---|', *rows])

    @staticmethod
    def counted(values: pd.Series) -> str:
        """`D 12, R 3` from a column of labels; `none` when empty."""
        return ', '.join(f'{k} {n}' for k, n in values.value_counts().items()) or 'none'

    @staticmethod
    def cell(value: float | None) -> str:
        return '-' if value is None else str(value)
