"""Why each registry row counts as verified (ADR 0002, #26): `hand` for a row of the archived
hand sample or of Tier D, `high` for the other rows of confidence `high`, `second-reading` for
the rest, since every medium and low row had a blind second reading. The rule runs once over
the current registry and writes a shard of every row with `verified` filled; the merge fills
the column. Run from the repo root:

    uv run python survey/verify.py
    uv run python survey/merge.py survey/shards/registry_verified.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from mixedbench.registry.row import readCsv, writeCsv
from schema import REGISTRY

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
SAMPLE = HERE / 'archive' / 'sample.csv'  # the seeded hand sample of spec #6


# =====================================================================================
# the rule
# =====================================================================================
def verification(registry: pd.DataFrame, sample: pd.DataFrame) -> pd.Series:
    """`verified` per registry row, on the registry's index."""
    key = list(REGISTRY.key)
    sampled = pd.MultiIndex.from_frame(registry[key]).isin(pd.MultiIndex.from_frame(sample[key]))
    hand = sampled | (registry['tier'] == 'D')
    high = registry['confidence'] == 'high'
    verified = np.select([hand, high], ['hand', 'high'], 'second-reading')
    return pd.Series(verified, index=registry.index)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    registry = readCsv(HERE.parent / 'registry' / 'registry.csv')
    registry['verified'] = verification(registry, readCsv(SAMPLE))
    writeCsv(registry[list(REGISTRY.agentColumns)], HERE / 'shards' / 'registry_verified.csv')
    print(registry['verified'].value_counts().to_string())
