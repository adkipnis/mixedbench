"""File contract of the GLMM dimension survey: columns, allowed values and row keys of
`registry.csv`, `excluded.csv`, `duplicates.csv` and `dropped.csv`, and the shape of
`sources.yaml`. The merge script enforces it; agents write shards with exactly the agent
columns. Documented for humans in README.md. The practice survey's schema is the model;
nothing is imported across surveys.
"""

from __future__ import annotations

from dataclasses import dataclass


# =====================================================================================
# tables
# =====================================================================================
@dataclass(frozen=True)
class Table:
    name: str
    agentColumns: tuple[str, ...]
    scriptColumns: dict[str, str]  # column -> inserted after which agent column
    key: tuple[str, ...]

    @property
    def columns(self) -> list[str]:
        cols = list(self.agentColumns)
        for col, after in self.scriptColumns.items():
            cols.insert(cols.index(after) + 1, col)
        return cols


# One row per dataset and documented model, the documented model first, at most three.
REGISTRY = Table(
    name='registry',
    agentColumns=(
        # identity: the source label of sources.yaml, the object as the loader enumerates it
        'source', 'object', 'model_index',
        # the documented model, every entry a column name of the loaded table
        'response', 'response_type', 'trials', 'grouping_factors', 'covariates', 'interactions',
        'ignore', 'types', 'formula', 'published_model',
        # bookkeeping
        'domain', 'confidence', 'notes',
    ),
    # tier from sources.yaml; sources: `source:object` of every confirmed duplicate folded into
    # this row, the row's own first; reader: the loader's route
    scriptColumns={'tier': 'source', 'sources': 'tier', 'reader': 'object'},
    key=('source', 'object', 'model_index'),
)  # fmt: skip

EXCLUDED = Table(
    name='excluded',
    agentColumns=('source', 'object', 'reason', 'detail'),
    scriptColumns={'tier': 'source'},
    key=('source', 'object'),
)

# The merge writes `flagged` pairs; an agent's shard answers `same` or `different`.
DUPLICATES = Table(
    name='duplicates',
    agentColumns=('source_a', 'object_a', 'source_b', 'object_b', 'verdict', 'notes'),
    scriptColumns={},
    key=('source_a', 'object_a', 'source_b', 'object_b'),
)

# A dropped object leaves registry.csv and excluded.csv, so that a later shard can re-file it.
DROPPED = Table(
    name='dropped',
    agentColumns=('source', 'object', 'reason'),
    scriptColumns={'tier': 'source'},
    key=('source', 'object'),
)

TABLES = {t.name: t for t in (REGISTRY, EXCLUDED, DUPLICATES, DROPPED)}

# One row per data object the pull script enumerates in a kept source; `capped` is `yes` for
# the objects a source's cap left out, which stay listed as the screening denominator.
CANDIDATE_COLUMNS = (
    'tier', 'source', 'pin', 'object', 'file', 'n_rows', 'n_cols',
    'n_numeric', 'n_categorical', 'n_string', 'n_other', 'reader', 'capped',
)  # fmt: skip
MAX_MODELS_PER_OBJECT = 3

# =====================================================================================
# allowed values
# =====================================================================================
TIERS = ('R', 'E', 'T', 'D', 'O')  # frame order; a duplicate keeps the earliest
YES_NO = ('yes', 'no')
RESPONSE_TYPES = ('continuous', 'binary', 'count', 'binomial', 'ordinal', 'categorical')
DOMAINS = (
    'ecology_biology', 'psychology_neuroscience', 'biomedicine', 'social_humanities',
    'agriculture', 'education', 'economics', 'industry', 'other',
)  # fmt: skip
EXCLUSION_REASONS = (
    'no grouping structure', 'time series without replication', 'fewer than two groups',
    'response missing or undocumented', 'derived or duplicated table', 'unreadable format',
    'licence forbids redistribution', 'too large',
)  # fmt: skip
COLUMN_TYPES = ('categorical', 'ordered', 'continuous')  # what `types` may declare: `col=ordered`  # fmt: skip

ALLOWED: dict[str, dict[str, tuple[str, ...]]] = {
    'registry': {
        'response_type': RESPONSE_TYPES,
        'published_model': YES_NO,
        'domain': DOMAINS,
        'confidence': ('high', 'medium', 'low'),
    },
    'excluded': {'reason': EXCLUSION_REASONS},
    'duplicates': {'verdict': ('same', 'different')},
    'dropped': {},
}

# `;`-separated lists of column names of the loaded table
COLUMN_LIST_COLUMNS = ('grouping_factors', 'covariates', 'ignore')
# `a:b;a:c`, every part a column name
INTERACTION_COLUMN = 'interactions'
# `col=categorical;col2=continuous`
TYPES_COLUMN = 'types'

REQUIRED = {
    'registry': (
        'source', 'object', 'model_index', 'response', 'response_type', 'grouping_factors',
        'formula', 'published_model', 'domain', 'confidence',
    ),
    'excluded': ('source', 'object', 'reason'),
    'duplicates': ('source_a', 'object_a', 'source_b', 'object_b', 'verdict'),
    'dropped': ('source', 'object', 'reason'),
}  # fmt: skip

# What the loaded table must show for each declared response type. A binomial response also
# names its trials column; ordinal and categorical responses are checked on distinct values.
MAX_ORDINAL_LEVELS = 10
