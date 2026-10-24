"""flat.py runs the flat pass: the survey's tables filed `no grouping structure`, screened for
the registry's two oversights before they are measured beside the registry as the flat sample.

pipeline:
---------
excluded.csv and candidates.csv
-> the frame: each flat table with its stratum              FlatPass.deriveFrame
-> a read table's filing words and id-like columns          FlatPass.screenTable
-> flat_screen.csv, the second reading's worklist           FlatPass.screen
-> the sample: the screened frame decided by the verdicts   FlatPass._selectSample
-> a table's sizes, design and column statistics            FlatPass.measureTable
-> flat.csv and flat_columns.csv                            FlatPass.measure
-> flat_sample.csv, 50 sample tables in two batches         FlatPass.draw
-> one batch as a prompt with page and download URLs        FlatPass.handoff
-> flat_agreement.csv, the share that stood per stratum     FlatPass.agree

Run a step from the repo root:

    uv run python survey/flat.py screen
    uv run python survey/flat.py measure
    uv run python survey/flat.py draw
    uv run python survey/flat.py handoff --batch 1
    uv run python survey/flat.py agree
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from columns import COLUMN_STATISTICS, measureMaxAbsRho, measureShape
from dimensions import computeConditionIndex, countWidth
from mixedbench.contract import codeCovariate, columnType
from mixedbench.datasets import Loader
from mixedbench.registry.row import readCsv, splitList, writeCsv
from pull import Puller
from schema import FLAT_VERDICTS
from sources import readFrame
from verify import Links, drawSample, renderHelpPage

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
COLUMN_TYPES = ('continuous', 'binary', 'categorical', 'ordered')  # the kinds `columnType` gives
# flat.csv: one row per table of the flat sample, how it got in, its sizes and its design
FLAT_COLUMNS = (
    'source', 'object', 'tier', 'stratum', 'basis', 'evidence', 'n_obs', 'n_columns',
    'n_continuous', 'n_binary', 'n_categorical', 'n_ordered', 'n_id_columns', 'd_all',
    'condition_all',
)  # fmt: skip
# flat_columns.csv: columns.csv's columns less those a registry row's model binds
FLAT_COLUMN_COLUMNS = (
    'source', 'object', 'tier', 'column', 'type', 'K', 'missing_share', *COLUMN_STATISTICS,
)  # fmt: skip
SAMPLE_SIZE = 50
SEED = 2  # the registry's hand samples took 0 and 1
# the hand sample's strata, in the order their ties are allocated; read/integer holds the
# unflagged tables the dropped integer-levels rule alone would have flagged
SAMPLE_STRATA = ('prescreened', 'read/unflagged', 'read/flagged', 'read/integer')
# flat_sample.csv: per drawn table, its stratum and batch, and what its handoff shows as it stood
# at the draw
SAMPLE_COLUMNS = (
    'source', 'object', 'tier', 'file', 'stratum', 'batch', 'basis', 'evidence', 'detail',
    'words', 'id_columns', 'integer_columns',
)  # fmt: skip
# a drawn table's screen columns as its handoff names them
SCREEN_REASONS = {
    'words': 'filing words',
    'id_columns': 'id-like columns',
    'integer_columns': 'integer columns',
}
# a batch's handoff opens with a prompt that a checker who knows neither the survey nor the
# repository can act on
HANDOFF_HEAD = """# Flat tables, hand check, batch {batch}

You check {n} tables from public statistics sources that a survey filed as having no grouping
structure, so that they can serve as a reference sample of flat tables beside a registry of
grouped ones.
A language model read each table once, and read the flagged ones a second time.
Open each table's page and download, read its documentation and its columns, and decide which
verdict holds.

## Verdicts

- **flat:** no documented model fits the table with a random effect, and no column indexes a
  unit the rows repeat within. A design factor of fixed levels (treatment, dose, sex), a field
  coordinate each plot holds once, a count and an id with one row per unit are no grouping
  factor.
- **wide:** grouped data stored wide, its repeated measures as columns (`y1` to `y4` for four
  visits, one column per year), whether or not the source also holds a long form.
- **hidden grouping:** a column indexes a unit the rows repeat within, a subject, plot, school,
  site or wave with two or more rows each, whether or not the documentation fits a model with
  it.

Four rules settle the edge cases:

- **Levels:** a grouping factor no documented model fits needs at least five levels sampled
  from a larger population (Harrison et al. 2018; Bolker et al. 2009). Fewer levels, or a few
  exhaustive ones (a city's boroughs, a country's regions), make a design factor.
- **Plots:** coordinates that identify one plot observed on several occasions on the same land
  group as `row:col`, even where some plots are observed once.
- **Waves:** a wave that a documented model fits as fixed, or separately per wave, keeps the
  table flat.
- **Wide first:** a wide table that also has a grouping column is `wide`.

## Per table

- **page, download:** the source at the version the survey read; the file names the table
  inside an archive.
- **filing:** the first reading's reason for calling the table flat, or `no repeated column`
  where no column repeats a value.
- **screen:** the filing words or id-like columns that flagged the table for the second
  reading. Integer columns of more than ten repeated levels flag nothing yet; this check
  decides whether they should. The screen is a reason to look, never evidence.
- **second reading:** its evidence for `flat`, where the table had one.
- **help page:** the documentation the first reading saw, where one exists, ending with the
  table's column types and first rows; cut at 20,000 characters.

## Answer

One bullet per table in this order, nothing else:

- `<n> · <source> · <object>: stands — <what makes it flat>`
- `<n> · <source> · <object>: wide — <the columns that repeat a measure>`
- `<n> · <source> · <object>: hidden grouping <column or a:b> — <its levels, rows per level,
  the documented model and its link if any>`

Take the evidence from the source, not from the filing or the screen alone.
"""


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
        screened = self._screenFrame()
        writeCsv(screened[list(SCREEN_COLUMNS)], self.survey / 'flat_screen.csv')

    def measure(self) -> None:
        """flat.csv and flat_columns.csv: every table of the flat sample, measured. Refuses,
        naming them, while a flagged table has no verdict."""
        tables, columns = [], []
        for _, row in self._selectSample().iterrows():
            table = self.loader.load(self.sources[row['source']], row['object'])
            measured, measured_columns = self.measureTable(table)
            identity = {c: row[c] for c in ('source', 'object', 'tier')}
            tables.append(identity | {'stratum': row['stratum']} | self._findBasis(row) | measured)
            for column in measured_columns:
                columns.append(identity | column)
        writeCsv(pd.DataFrame(tables, columns=FLAT_COLUMNS), self.registry / 'flat.csv')
        flat_columns = pd.DataFrame(columns, columns=FLAT_COLUMN_COLUMNS)
        writeCsv(flat_columns, self.registry / 'flat_columns.csv')

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

    def _screenFrame(self) -> pd.DataFrame:
        """The frame with each read table's screen; a prescreened table stays unscreened."""
        frame = self.deriveFrame()
        screenings = []
        for _, row in frame.iterrows():
            screening = UNSCREENED
            if row['stratum'] == 'read':
                table = self.loader.load(self.sources[row['source']], row['object'])
                screening = self.screenTable(row['detail'], table)
            screenings.append(screening)
        return frame.join(pd.DataFrame(screenings, index=frame.index, columns=list(UNSCREENED)))

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

    # ---------------------------------------------------------------------------------
    # pipeline: screened frame -> sample -> a table's rows of the two flat files
    # ---------------------------------------------------------------------------------

    def _selectSample(self) -> pd.DataFrame:
        """The screened frame's tables in the flat sample: a verdict decides its table whatever
        the screen said; without one, a prescreened or unflagged table is in."""
        screened = self._screenFrame().merge(
            self._readVerdicts(), on=['source', 'object'], how='left'
        )
        screened[['verdict', 'evidence']] = screened[['verdict', 'evidence']].fillna('')
        unread = screened[(screened['flagged'] == 'yes') & (screened['verdict'] == '')]
        if not unread.empty:
            names = '\n'.join(unread['source'] + ' ' + unread['object'])
            raise ValueError(f'{len(unread)} flagged tables without a verdict:\n{names}')
        return screened[screened['verdict'].isin(['', 'flat'])]

    @staticmethod
    def _findBasis(row: pd.Series) -> dict[str, str]:
        """How a sample table got in: the second reading's verdict, else the pre-screen's, else
        the first reading's filing line."""
        if row['verdict'] != '':
            return {'basis': 'second reading', 'evidence': row['evidence']}
        if row['stratum'] == 'prescreened':
            return {'basis': 'prescreen', 'evidence': row['screen']}
        return {'basis': 'first reading', 'evidence': row['detail']}

    def _readVerdicts(self) -> pd.DataFrame:
        path = self.survey / 'flat_verdicts.csv'
        if not path.exists():  # until the merge of the first verdict shard
            return pd.DataFrame(columns=FLAT_VERDICTS.agentColumns)
        return readCsv(path)[list(FLAT_VERDICTS.agentColumns)]

    @staticmethod
    def measureTable(table: pd.DataFrame) -> tuple[dict, list[dict]]:
        """A flat table's sizes and design statistics, and each column's statistics by the
        functions that measure the registry's."""
        column_types = {c: columnType(table[c]) for c in table.columns}
        rho = measureMaxAbsRho(table, column_types)
        columns, designed = [], []
        for column, (kind, levels) in column_types.items():
            typed = {'column': column, 'type': kind, 'K': levels}
            shape = measureShape(table[column], kind) | {'max_abs_rho': rho[column]}
            columns.append(typed | shape)
            if not FlatPass._isIdColumn(table[column], kind, levels):
                designed.append(column)
        sizes = FlatPass._countColumns(table, column_types, designed)
        return sizes | FlatPass._measureCondition(table[designed]), columns

    @staticmethod
    def _isIdColumn(values: pd.Series, kind: str, levels: int | str) -> bool:
        """Whether a column labels its rows: a categorical whose present values are all
        distinct, a design column per row."""
        return kind == 'categorical' and levels == values.notna().sum()

    @staticmethod
    def _countColumns(
        table: pd.DataFrame, column_types: dict[str, tuple], designed: list[str]
    ) -> dict:
        """Every row and column, the columns of each kind, the id columns, and d_all over the
        designed columns."""
        sizes = {'n_obs': len(table), 'n_columns': len(column_types)}
        kinds = [kind for kind, _ in column_types.values()]
        for kind in COLUMN_TYPES:
            sizes[f'n_{kind}'] = kinds.count(kind)
        sizes['n_id_columns'] = len(column_types) - len(designed)
        sizes['d_all'] = int(sum(countWidth(*column_types[c]) for c in designed))
        return sizes

    @staticmethod
    def _measureCondition(table: pd.DataFrame) -> dict:
        """condition_all over the rows complete in every column: the intercept and each column
        coded as the contract codes it, a continuous one standardized as the contract's full
        regime standardizes it. Blank when no row is complete."""
        complete = table.dropna()
        if complete.empty:
            return {}
        design = {'Intercept': pd.Series(1.0, index=complete.index)}
        for column in complete.columns:
            values = complete[column]
            kind, _ = columnType(values)
            coded = codeCovariate(values)
            if kind == 'continuous':
                raw = coded[column]
                coded = {column: (raw - raw.mean()) / raw.std()}
            design |= coded
        return {'condition_all': computeConditionIndex(pd.DataFrame(design))}

    # ---------------------------------------------------------------------------------
    # the hand sample: sample -> drawn tables -> a batch's prompt -> the share that stood
    # ---------------------------------------------------------------------------------

    def draw(self) -> None:
        """flat_sample.csv: 50 tables of the flat sample over four strata, in two batches."""
        population = []
        for _, row in self._selectSample().iterrows():
            stratum = {'stratum': self._findSampleStratum(row)}
            population.append(row.to_dict() | self._findBasis(row) | stratum)
        sample = drawSample(pd.DataFrame(population), SAMPLE_STRATA, SAMPLE_SIZE, SEED)
        writeCsv(sample[list(SAMPLE_COLUMNS)], self.survey / 'flat_sample.csv')

    @staticmethod
    def _findSampleStratum(row: pd.Series) -> str:
        if row['stratum'] == 'prescreened':
            return 'prescreened'
        if row['flagged'] == 'yes':
            return 'read/flagged'
        if row['integer_columns'] != '':
            return 'read/integer'
        return 'read/unflagged'

    def handoff(self, batch: int) -> str:
        """One batch as a prompt for a check in the browser: page and download URLs, never a
        local path."""
        sample = readCsv(self.survey / 'flat_sample.csv')
        drawn = sample[sample['batch'] == str(batch)]
        links = Links(self.registry, self.survey)
        sections = []
        for number, (_, row) in enumerate(drawn.iterrows(), start=1):
            sections.append(self._renderSection(number, row, links))
        return HANDOFF_HEAD.format(batch=batch, n=len(sections)) + ''.join(sections)

    def _renderSection(self, number: int, row: pd.Series, links: Links) -> str:
        page, download = links.resolveUrls(row['source'], row['object'], row['file'])
        second_reading = row['evidence'] if row['basis'] == 'second reading' else '—'
        lines = [
            f'- page: {page}',
            f'- download: {download} (file `{row["file"]}`)',
            f'- filing: {row["detail"]}',
            f'- screen: {self._renderScreen(row)}',
            f'- second reading: {second_reading}',
        ]
        heading = f'## {number}. {row["source"]} · {row["object"]}'
        help_page = renderHelpPage(self.registry, row['source'], row['object'])
        return f'\n{heading}\n\n' + '\n'.join(lines) + f'\n\n{help_page}'

    @staticmethod
    def _renderScreen(row: pd.Series) -> str:
        reasons = []
        for column, name in SCREEN_REASONS.items():
            names = [f'`{c}`' for c in splitList(row[column])]
            if names:
                reasons.append(f'{name} {", ".join(names)}')
        return '; '.join(reasons) or '—'

    def agree(self) -> None:
        """flat_agreement.csv: the share of drawn tables still in the flat sample, per stratum
        and overall. A table the check took out of the frame or the sample did not stand."""
        drawn = readCsv(self.survey / 'flat_sample.csv')
        kept = self._selectSample()[['source', 'object']]
        joined = drawn.merge(kept, on=['source', 'object'], how='left', indicator=True)
        stood = joined['_merge'] == 'both'
        rows = []
        for stratum in (*SAMPLE_STRATA, 'all'):
            within = stood if stratum == 'all' else stood[joined['stratum'] == stratum]
            rows.append(
                {'stratum': stratum, 'tables': len(within), 'stood': round(within.mean(), 3)}
            )
        writeCsv(pd.DataFrame(rows), self.survey / 'flat_agreement.csv')


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=['screen', 'measure', 'draw', 'handoff', 'agree'], help='the step to run')
    parser.add_argument('--batch', type=int, help='handoff: the batch to render')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding candidates.csv and the bookkeeping tables')
    args = parser.parse_args()
    # fmt: on
    flat = FlatPass(args.registry, args.survey)
    match args.step:
        case 'screen':
            flat.screen()
        case 'measure':
            flat.measure()
        case 'draw':
            flat.draw()
        case 'handoff':
            print(flat.handoff(args.batch))
        case 'agree':
            flat.agree()
