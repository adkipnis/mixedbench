"""flat.py runs the flat pass: the survey's tables filed `no grouping structure`, screened for
the registry's two oversights before they are measured beside the registry as the flat sample.

pipeline:
---------
excluded.csv and candidates.csv
-> the frame: each flat table with its stratum       FlatPass.deriveFrame
-> a read table's filing words and id-like columns   FlatPass.screenTable
-> flat_screen.csv, the second reading's worklist    FlatPass.screen

Run from the repo root:

    uv run python survey/flat.py screen
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from mixedbench.datasets import Loader
from mixedbench.registry.row import readCsv, writeCsv
from pull import Puller
from sources import readFrame

HERE = Path(__file__).parent

# =====================================================================================
# globals
# =====================================================================================
# the pre-screen's verdict -> the stratum of a table filed `no grouping structure`; a table
# stopped at `one column`, `under 3 rows` or `no frame` cannot be measured
STRATA = {'pass': 'read', 'no repeated column': 'prescreened'}
# The screen's two rules flag a read table for the second reading; their stems are those of the
# prototype that ADR 0007's counts rest on. A false positive costs one second reading.
FILING_WORDS = re.compile(r'\b(?:wide|repeat|occasion|visit)\w*', re.IGNORECASE)
ID_STEMS = (
    'subj', 'participant', 'patient', 'person', 'site', 'school', 'plot', 'block', 'unit',
    'household', 'cluster', 'animal', 'family', 'pair', 'group', 'country', 'region', 'state',
    'county', 'city', 'team', 'firm', 'cow', 'rat', 'litter', 'tree', 'field', 'farm', 'herd',
    'clinic', 'hospital', 'center', 'centre', 'ward', 'class', 'student', 'pupil', 'teacher',
    'judge', 'rater', 'item', 'word', 'trial', 'session', 'wave', 'year', 'time', 'day', 'week',
    'month', 'date',
)  # fmt: skip
MANY_LEVELS = 10  # a repeated integer column with more levels is recorded for the hand sample
# flat_screen.csv: one row per frame table; a list of words or columns is `;`-separated
SCREEN_COLUMNS = (
    'source', 'object', 'tier', 'stratum', 'words', 'id_columns', 'integer_columns', 'flagged',
)  # fmt: skip
# a prescreened table's filing line is the pre-screen's verdict, and it holds no repeated column
UNSCREENED = {'words': '', 'id_columns': '', 'integer_columns': '', 'flagged': 'no'}


# =====================================================================================
# flat pass
# =====================================================================================
class FlatPass:
    def __init__(self, registry: Path, survey: Path, loader: Loader | None = None) -> None:
        self.registry, self.survey = Path(registry), Path(survey)
        self.loader = loader or Loader(self.registry / 'cache')
        self.sources = readFrame(self.registry).sources

    def screen(self) -> None:
        """flat_screen.csv: every frame table with its stratum, a read one with its screen."""
        rows = []
        for _, row in self.deriveFrame().iterrows():
            screening = UNSCREENED
            if row['stratum'] == 'read':
                table = self.loader.load(self.sources[row['source']], row['object'])
                screening = self.screenTable(row['detail'], table)
            rows.append({c: row[c] for c in ('source', 'object', 'tier', 'stratum')} | screening)
        writeCsv(pd.DataFrame(rows, columns=SCREEN_COLUMNS), self.survey / 'flat_screen.csv')

    # ---------------------------------------------------------------------------------
    # pipeline: merged files -> frame -> a read table's screen
    # ---------------------------------------------------------------------------------

    def deriveFrame(self) -> pd.DataFrame:
        """The exclusions filed `no grouping structure` joined to their candidates rows, with
        their stratum, in frame order."""
        excluded = readCsv(self.registry / 'excluded.csv')
        flat = excluded[excluded['reason'] == 'no grouping structure']
        candidates = readCsv(self.survey / 'candidates.csv')
        frame = candidates.merge(flat, on=['tier', 'source', 'object'])
        frame = frame[frame['screen'].isin(STRATA)].reset_index(drop=True)
        return frame.assign(stratum=frame['screen'].map(STRATA))

    @staticmethod
    def screenTable(detail: str, table: pd.DataFrame) -> dict[str, str]:
        """A read table's screen: the words of its filing line that say grouped data stored wide
        or repeated, its columns that could index groups and are named like an id, and those of
        many integer levels, which flag nothing."""
        words = sorted({word.lower() for word in FILING_WORDS.findall(detail)})
        id_columns, integer_columns = [], []
        for column in table.columns:
            values = table[column]
            if not Puller.canGroup(values):
                continue
            if FlatPass._isIdLike(str(column)):
                id_columns.append(str(column))
            if FlatPass._isInteger(values) and values.nunique() > MANY_LEVELS:
                integer_columns.append(str(column))
        return {
            'words': ';'.join(words),
            'id_columns': ';'.join(id_columns),
            'integer_columns': ';'.join(integer_columns),
            'flagged': 'yes' if words or id_columns else 'no',
        }

    @staticmethod
    def _isIdLike(name: str) -> bool:
        name = name.lower()
        return name.endswith('id') or name == 'idx' or name.startswith(ID_STEMS)

    @staticmethod
    def _isInteger(values: pd.Series) -> bool:
        """Whether a column that could index groups holds integers: `canGroup` refused a
        fractional float."""
        return pd.api.types.is_integer_dtype(values) or pd.api.types.is_float_dtype(values)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=['screen'], help='the step to run')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding candidates.csv and the bookkeeping tables')
    args = parser.parse_args()
    # fmt: on
    flat = FlatPass(args.registry, args.survey)
    flat.screen()
