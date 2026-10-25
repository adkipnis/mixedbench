"""Pull every kept source of `sources.yaml` and list its data objects in `candidates.csv`.

Each source is fetched once into the untracked `registry/cache/` through the package's dataset loader
and enumerated. Every object is pre-screened mechanically for what a grouped table needs (a
data frame, three rows, two columns, one column whose values could index groups); the discards
are written as the shard `survey/shards/excluded_prescreen.csv` for the merge. A source with more
passing objects than its cap keeps a seeded draw of them. Objects screened out or left out by
the cap stay listed, so that the screening denominator is known. The help page of every object
to read lands in the untracked `registry/help/<source>/<object>.txt` for the reading agents, with the
table's dtypes and first rows appended. Rerunning
downloads nothing and rewrites the same files. `--tiers` pulls only those tiers (a ticket's
pull; the others keep their rows, shard rows and help pages). Run from the repo root:

    uv run python survey/pull.py [--tiers E O]
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

import pandas as pd
from help import HelpPage
from mixedbench.datasets import DataObject, Loader
from mixedbench.registry.row import readCsv, writeCsv
from schema import CANDIDATE_COLUMNS, EXCLUDED, SCREENS, TIERS
from sources import readFrame

HERE = Path(__file__).parent
MIN_ROWS = 3  # two groups, one of them with two observations
MIN_COLS = 2  # a response and a grouping factor
HEAD_ROWS = 8  # appended to each help page with the dtypes
HEAD_COLUMNS = 60  # a genotype matrix's thousands of columns are not read column by column


# =====================================================================================
# puller
# =====================================================================================
class Puller:
    def __init__(
        self,
        registry: Path,
        survey: Path,
        loader: Loader | None = None,
        tiers: tuple[str, ...] = TIERS,
    ) -> None:
        self.registry, self.survey = Path(registry), Path(survey)
        self.loader = loader or Loader(self.registry / 'cache')
        self.help = HelpPage(self.loader)
        self.frame = readFrame(self.registry)
        self.tiers = tiers
        self.labels = [label for label in self.frame.labels if self.frame.tiers[label] in tiers]
        self.rows: list[dict] = []
        self.depositPages: dict[str, Path] = {}  # Tier D label -> the page of its deposit
        if 'D' in tiers:
            self.depositPages = self._depositPages(self.registry, self.survey)

    def enumerate(self) -> None:
        """One row per data object of every source of the pulled tiers, in frame order,
        screened, the cap drawn per source among the passing objects."""
        for label in self.labels:
            objects = sorted(self.loader.objects(self.frame.sources[label]), key=lambda o: o.name)
            rows = [self._row(label, obj) for obj in objects]
            passing = [row['object'] for row in rows if row['screen'] == 'pass']
            kept = self._draw(passing, self.frame.caps[label])
            for row in rows:
                row['capped'] = 'no'
                if row['screen'] == 'pass' and row['object'] not in kept:
                    row['capped'] = 'yes'
            self.rows.extend(rows)

    def copyHelp(self) -> None:
        """One page per object to read, and per object stopped at `no repeated column`, which
        the flat sample reads for its response; a source's folder is rewritten, so a changed
        cap or frame leaves no stale page behind."""
        for label in self.labels:
            shutil.rmtree(self.registry / 'help' / label, ignore_errors=True)
        to_read = [row for row in self.rows if row['screen'] == 'pass' and row['capped'] == 'no']
        to_read += [row for row in self.rows if row['screen'] == 'no repeated column']
        for row in to_read:
            source = self.frame.sources[row['source']]
            file = self.registry / 'help' / row['source'] / f'{row["object"]}.txt'
            file.parent.mkdir(parents=True, exist_ok=True)
            page = self.help.page(source, row['object'])
            if row['source'] in self.depositPages:  # one page per deposit, read once per deposit
                deposit = self.depositPages[row['source']].relative_to(self.registry.parent)
                page = f'# deposit page: {deposit}\n\n{page}'
            table = self.loader.load(source, row['object'])
            file.write_text(f'{page}\n\n{self._firstRows(table)}\n')

    def flush(self) -> None:
        """`candidates.csv` whole, and the screened-out objects as an exclusion shard; the rows
        of tiers not pulled are kept from the existing file, everything in frame order."""
        rows = self._kept() + self.rows
        rows.sort(key=lambda row: self.frame.rank((row['source'], row['object'])))
        candidates = pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)
        writeCsv(candidates, self.survey / 'candidates.csv')
        excluded = [self._exclusion(row) for row in rows if row['screen'] != 'pass']
        (self.survey / 'shards').mkdir(exist_ok=True)
        shard = self.survey / 'shards' / 'excluded_prescreen.csv'
        writeCsv(pd.DataFrame(excluded, columns=EXCLUDED.agentColumns), shard)

    @staticmethod
    def screen(table: pd.DataFrame | None) -> str:
        """The pre-screen verdict, one of SCREENS: what a grouped table needs before an agent
        reads its documentation."""
        if table is None:
            return 'no frame'
        if table.shape[0] < MIN_ROWS:
            return 'under 3 rows'
        if table.shape[1] < MIN_COLS:
            return 'one column'
        for column in table.columns:
            if Puller.canGroup(table[column]):
                return 'pass'
        return 'no repeated column'

    @staticmethod
    def canGroup(values: pd.Series) -> bool:
        """Whether a column's values could index groups: not fractional (R stores integer codes
        as doubles), two or more distinct values, and some value repeated."""
        if pd.api.types.is_float_dtype(values):
            present = values.dropna()
            if len(present) == 0 or not (present == present.round()).all():
                return False
        distinct = values.nunique(dropna=True)
        return 2 <= distinct < len(values)

    # ---------------------------------------------------------------------------------
    # pipeline: deposit pages -> object -> row -> draw -> kept rows -> shard row -> csv
    # ---------------------------------------------------------------------------------

    @staticmethod
    def _depositPages(registry: Path, survey: Path) -> dict[str, Path]:
        """Tier D label -> the page of its deposit, as the archived `resolve.py` (tag
        `survey-archive`) named it; none before the listing ran."""
        pages = {}
        file = survey / 'deposit_files.csv'
        if not file.exists():
            return pages
        files = readCsv(file)
        rows = files[files['label'] != ''].to_dict('records')
        for row in rows:
            deposit = row['deposit'].split('.')[-1].replace('/', '_')
            name = f'{row["paper_id"]}_{row["repository"]}_{deposit}.txt'
            pages[row['label']] = registry / 'help' / 'deposits' / name
        return pages

    def _row(self, label: str, obj: DataObject) -> dict:
        source = self.frame.sources[label]
        table = None
        counts = {'n_numeric': '', 'n_categorical': '', 'n_string': '', 'n_other': ''}
        if obj.n_rows is not None:
            table = self.loader.load(source, obj.name)
            counts = self._countDtypes(table)
        return {
            'tier': self.frame.tiers[label],
            'source': label,
            'pin': source.pin,
            'object': obj.name,
            'file': obj.file,
            'n_rows': '' if obj.n_rows is None else obj.n_rows,
            'n_cols': '' if obj.n_cols is None else obj.n_cols,
            **counts,
            'reader': obj.reader,
            'screen': self.screen(table),
        }

    @staticmethod
    def _countDtypes(table: pd.DataFrame) -> dict[str, int]:
        counts = {'n_numeric': 0, 'n_categorical': 0, 'n_string': 0, 'n_other': 0}
        for dtype in table.dtypes:
            if isinstance(dtype, pd.CategoricalDtype):
                counts['n_categorical'] += 1
            elif pd.api.types.is_bool_dtype(dtype):
                counts['n_other'] += 1
            elif pd.api.types.is_numeric_dtype(dtype):
                counts['n_numeric'] += 1
            elif pd.api.types.is_string_dtype(dtype):
                counts['n_string'] += 1
            else:
                counts['n_other'] += 1
        return counts

    @staticmethod
    def _firstRows(table: pd.DataFrame) -> str:
        """What the read prompt promises next to the documentation: the dtypes and the first
        rows, so that an agent sees the columns as loaded and runs nothing."""
        shown = table.iloc[:, :HEAD_COLUMNS]
        dtypes = '\n'.join(f'{column}: {dtype}' for column, dtype in shown.dtypes.items())
        if shown.shape[1] < table.shape[1]:
            dtypes += f'\n... and {table.shape[1] - shown.shape[1]} more columns'
        head = shown.head(HEAD_ROWS).to_string(index=False)
        return f'# first rows (of {len(table)})\n{dtypes}\n\n{head}'

    def _draw(self, names: list[str], cap: int | None) -> set[str]:
        """The names to read: all of them without a cap or under it, else a seeded sample."""
        if cap is None or len(names) <= cap:
            return set(names)
        return set(random.Random(self.frame.seed).sample(names, cap))

    def _kept(self) -> list[dict]:
        """The rows of the tiers this run does not pull, as the last run wrote them."""
        file = self.survey / 'candidates.csv'
        if not file.exists():
            return []
        rows = readCsv(file)
        return rows[~rows['tier'].isin(self.tiers)].to_dict('records')

    @staticmethod
    def _exclusion(row: dict) -> dict:
        """The screened-out object as a row of the exclusion shard, verdict kept as detail."""
        return {
            'source': row['source'],
            'object': row['object'],
            'reason': SCREENS[row['screen']],
            'detail': row['screen'],
        }


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml, cache/ and help/')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder of candidates.csv and shards/')
    parser.add_argument('--tiers', nargs='+', choices=TIERS, default=TIERS, help='tiers to pull; the others keep their rows')
    args = parser.parse_args()
    # fmt: on
    puller = Puller(args.registry, args.survey, tiers=tuple(args.tiers))
    puller.enumerate()
    puller.copyHelp()
    puller.flush()
