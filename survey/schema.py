"""File contract of the GLMM dimension survey: what a writer knows of `registry.csv`,
`excluded.csv`, `duplicates.csv`, `dropped.csv`, `flat_verdicts.csv` and `flat_responses.csv`
(agent and script columns, allowed values, row keys) and the shape of `sources.yaml`.
The registry row's dialect, columns, vocabularies and grammars are the package's
(`mixedbench.registry.row`).
The merge script enforces it, and agents write shards with exactly the agent columns.
Documented for humans in `docs/registry.md` and `README.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import get_args

from mixedbench.registry.row import COLUMNS, ResponseType


# =====================================================================================
# tables
# =====================================================================================
@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[str, ...]  # in file order
    scriptColumns: tuple[str, ...]  # filled by the merge; an agent writes the others
    key: tuple[str, ...]

    @property
    def agentColumns(self) -> tuple[str, ...]:
        return tuple(c for c in self.columns if c not in self.scriptColumns)


# One row per dataset and documented model, the documented model first, at most three.
REGISTRY = Table(
    name='registry',
    columns=COLUMNS,
    # tier from sources.yaml; sources: `source:object` of every confirmed duplicate folded into
    # this row, the row's own first; reader: the loader's route; license: the source's, through
    # LICENSES
    scriptColumns=('tier', 'sources', 'reader', 'license'),
    key=('source', 'object', 'model_index'),
)

EXCLUDED = Table(
    name='excluded',
    columns=('source', 'tier', 'object', 'reason', 'detail'),
    scriptColumns=('tier',),
    key=('source', 'object'),
)

# The merge writes `flagged` pairs; an agent's shard answers `same` or `different`.
DUPLICATES = Table(
    name='duplicates',
    columns=('source_a', 'object_a', 'source_b', 'object_b', 'verdict', 'notes'),
    scriptColumns=(),
    key=('source_a', 'object_a', 'source_b', 'object_b'),
)

# A dropped object leaves registry.csv and excluded.csv, so that a later shard can re-file it.
DROPPED = Table(
    name='dropped',
    columns=('source', 'tier', 'object', 'reason'),
    scriptColumns=('tier',),
    key=('source', 'object'),
)

# The second reading's verdict on a flat table the screen flagged, or a hand sample's correction.
FLAT_VERDICTS = Table(
    name='flat_verdicts',
    columns=('source', 'tier', 'object', 'verdict', 'evidence'),
    scriptColumns=('tier',),
    key=('source', 'object'),
)

# A flat table's response, the outcome of its first documented model, or `none`; a named one
# with its type, and a binomial one with its trials, as a registry row records them.
FLAT_RESPONSES = Table(
    name='flat_responses',
    columns=('source', 'tier', 'object', 'response', 'evidence', 'response_type', 'trials'),
    scriptColumns=('tier',),
    key=('source', 'object'),
)

TABLES = {
    'registry': REGISTRY,
    'excluded': EXCLUDED,
    'duplicates': DUPLICATES,
    'dropped': DROPPED,
    'flat_verdicts': FLAT_VERDICTS,
    'flat_responses': FLAT_RESPONSES,
}
# a shard `<prefix>_<label>.csv` -> the table it merges into
SHARDS = {
    'registry': REGISTRY,
    'excluded': EXCLUDED,
    'duplicates': DUPLICATES,
    'dropped': DROPPED,
    'flat': FLAT_VERDICTS,
    'response': FLAT_RESPONSES,
}
IDENTITY = (
    'source',
    'object',
    'model_index',
    'tier',
)  # a measured file's key: the registry row's, with its tier

# One row per data object the pull script enumerates in a kept source. `screen` is the
# mechanical pre-screen's verdict; `capped` is `yes` for the passing objects a source's cap
# left out. Both stay listed as the screening denominator; agents read `pass` and `no` rows.
CANDIDATE_COLUMNS = (
    'tier', 'source', 'pin', 'object', 'file', 'n_rows', 'n_cols',
    'n_numeric', 'n_categorical', 'n_string', 'n_other', 'reader', 'screen', 'capped',
)  # fmt: skip
# What a table needs before an agent reads it: a frame, a response and a possible grouping
# column. The discards go to `shards/excluded_prescreen.csv` under the reason given here.
SCREENS = {
    'pass': None,
    'no frame': 'unreadable format',
    'under 3 rows': 'no grouping structure',
    'one column': 'no grouping structure',
    'no repeated column': 'no grouping structure',
}


# =====================================================================================
# allowed values
# =====================================================================================
TIERS = ('R', 'E', 'T', 'D', 'O')  # frame order; a duplicate keeps the earliest
YES_NO = ('yes', 'no')
DOMAINS = (
    'ecology_biology', 'psychology_neuroscience', 'biomedicine', 'social_humanities',
    'agriculture', 'education', 'economics', 'industry', 'other',
)  # fmt: skip
EXCLUSION_REASONS = (
    'no grouping structure', 'time series without replication', 'fewer than two groups',
    'response missing or undocumented', 'derived or duplicated table', 'simulated data',
    'unreadable format', 'license forbids redistribution', 'too large', 'not the paper\'s data',
)  # fmt: skip

ALLOWED: dict[str, dict[str, tuple[str, ...]]] = {
    'registry': {  # the package's vocabularies are its row grammar (`Row.refusals`)
        'published_model': YES_NO,
        'domain': DOMAINS,
        'confidence': ('high', 'medium', 'low'),
    },
    'excluded': {'reason': EXCLUSION_REASONS},
    'duplicates': {'verdict': ('same', 'different')},
    'dropped': {},
    'flat_verdicts': {'verdict': ('flat', 'wide', 'hidden grouping')},
    'flat_responses': {'response_type': get_args(ResponseType)},
}

REQUIRED = {
    'registry': (  # an empty `model_index`, `response_type` or `verified` the grammar refuses
        'source', 'object', 'response', 'grouping_factors', 'formula', 'published_model',
        'domain', 'confidence',
    ),
    'excluded': ('source', 'object', 'reason'),
    'duplicates': ('source_a', 'object_a', 'source_b', 'object_b', 'verdict'),
    'dropped': ('source', 'object', 'reason'),
    'flat_verdicts': ('source', 'object', 'verdict', 'evidence'),
    'flat_responses': ('source', 'object', 'response', 'evidence'),
}  # fmt: skip
MAX_MODELS_PER_OBJECT = 3
MIN_ORDINAL_LEVELS = 3  # an ordinal response with fewer distinct values is binary
MAX_ORDINAL_LEVELS = 10  # an ordinal response with more distinct values is refused

# A source's license as `sources.yaml` or its CRAN DESCRIPTION states it, verbatim -> the
# registry's vocabulary. A string not listed refuses the merge, so a new spelling is classified
# on sight (ADR 0003).
LICENSES = {
    'CC0 1.0 Universal': 'CC0-1.0',
    'https://spdx.org/licenses/CC0-1.0.html': 'CC0-1.0',
    'CC0: Public Domain': 'CC0-1.0',
    'Kaggle, CC0: Public Domain': 'CC0-1.0',
    'CC-By Attribution 4.0 International': 'CC-BY-4.0',
    'CC BY 4.0': 'CC-BY-4.0',
    'cc-by-4.0': 'CC-BY-4.0',
    'Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)': 'CC-BY-NC-4.0',
    'CC_BY-NC-SA': 'CC-BY-NC-SA-4.0',  # OpenML names no version
    'Database: Open Database, Contents: Database Contents': 'ODbL-1.0',  # Kaggle's ODbL/DbCL
    'GPL (>= 2)': 'GPL-2.0-or-later',
    'GPL': 'GPL-2.0-or-later',  # R's reading of an unversioned GPL: any version
    'GPL-2 | GPL-3': 'GPL-2.0-or-later',  # the nearest value
    'Part of R 4.6.1': 'GPL-2.0-or-later',  # R is GPL-2 | GPL-3 (r-project.org/Licenses)
    'GPL-2': 'GPL-2.0',
    'GPL 2': 'GPL-2.0',
    'GPL (>= 3)': 'GPL-3.0-or-later',
    'GPL-3.0': 'GPL-3.0',
    'AGPL-3': 'AGPL-3.0',
    'MIT': 'MIT',
    'mit-license': 'MIT',
    'MIT + file LICENSE': 'MIT',
    'BSD-3-Clause': 'BSD-3-Clause',
    'Unlimited': 'public-domain',  # R: no restriction beyond the law
    'Public': 'other',  # OpenML: access, not a license
    'Publicly available': 'other',
    'other-open': 'other',
    'Kaggle and Federal University of Espirito Santo, Brazil': 'not stated',  # an attribution
    'not stated': 'not stated',
}
