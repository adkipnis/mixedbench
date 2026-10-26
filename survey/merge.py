"""Merge one agent-written shard into the dimension survey's canonical CSVs.

A shard is `shards/<table>_<label>.csv` with exactly the agent columns of its table
(schema.py). The script loads every named object through the package's dataset loader,
validates the shard against the table it returns, refuses a failing shard printing the
offending rows, and otherwise upserts on the table's row key, so merging the same shard twice
changes nothing and a corrected shard replaces its earlier rows. Every merge then folds
confirmed duplicates, measures the whole registry and rewrites the manifest and the summary;
a merge about the flat sample measures nothing.
The census tables land in `registry/`, the survey's bookkeeping tables (duplicates, dropped,
flat verdicts and responses) in `survey/`. Run from the repo root:

    uv run python survey/merge.py survey/shards/registry_lme4.csv
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd
from measure import measureRegistry
from mixedbench.contract import withComposites
from mixedbench.datasets import DataObject, Loader
from mixedbench.registry.row import (
    COLUMN_LIST_COLUMNS,
    TERM_COLUMNS,
    Row,
    parts,
    readCsv,
    writeCsv,
)
from schema import (
    ALLOWED,
    LICENSES,
    MAX_MODELS_PER_OBJECT,
    MAX_ORDINAL_LEVELS,
    REQUIRED,
    SHARDS,
    TABLES,
    Table,
)
from sources import Key, readFrame
from summarize import Summarizer

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
# An object is in the registry or in the exclusions, never both: the second shard is refused.
RIVALS = {'registry': 'excluded', 'excluded': 'registry'}
ON_CENSUS = ('dropped', 'flat_verdicts', 'flat_responses')  # about an object the census holds
# A dropped object leaves both files; re-filing it leaves dropped.csv. The later merge wins.
SUPERSEDES = {
    'registry': ('dropped',),
    'excluded': ('dropped',),
    'dropped': ('registry', 'excluded'),
    'duplicates': (),
    'flat_verdicts': (),
    'flat_responses': (),
}
RECONCILED = ('registry', 'duplicates', 'dropped')  # merges that can change the duplicate fold
FLAT = ('flat_verdicts', 'flat_responses')  # merges about the flat sample, never a registry row
CENSUS = ('registry', 'excluded')  # shard tables in registry/; the others in survey/
MANIFEST_COLUMNS = ['source', 'object', 'file', 'sha256', 'size']


class ShardRefused(Exception):
    """Carries the offending rows as a DataFrame (line, key, column, value, problem)."""

    def __init__(self, problems: pd.DataFrame) -> None:
        self.problems = problems
        super().__init__(
            f'shard refused, {len(problems)} problems:\n{problems.to_string(index=False)}'
        )


# =====================================================================================
# pipeline: shard -> validate -> upsert -> supersede -> reconcile duplicates -> measure
# -> manifest -> summary -> report
# =====================================================================================
class Merger:
    def __init__(self, registry: Path, survey: Path, loader: Loader | None = None) -> None:
        self.registry, self.survey = Path(registry), Path(survey)
        self.loader = loader or Loader(self.registry / 'cache')
        self.frame = readFrame(self.registry)

    # ---------------------------------------------------------------------------------
    # load
    # ---------------------------------------------------------------------------------
    def load(self, shard: Path) -> None:
        shard = Path(shard)
        self.table = SHARDS[shard.stem.split('_')[0]]
        self.shard = readCsv(shard)
        self.shard.columns = [c.strip() for c in self.shard.columns]
        self.shard = self.shard.apply(lambda col: col.str.strip())
        self.shard.index = range(2, len(self.shard) + 2)  # line numbers in the shard file
        self.shard.index.name = 'line'
        if self.table.name == 'duplicates':
            self.orderPairs()

    def orderPairs(self) -> None:
        """A pair is keyed earliest tier first, whichever way the agent wrote it."""
        ordered = []
        for _, row in self.shard.iterrows():
            a = (row['source_a'], row['object_a'])
            b = (row['source_b'], row['object_b'])
            ordered.append(sorted([a, b], key=self.frame.rank))
        self.shard[['source_a', 'object_a']] = [a for a, _ in ordered]
        self.shard[['source_b', 'object_b']] = [b for _, b in ordered]

    # ---------------------------------------------------------------------------------
    # validate
    # ---------------------------------------------------------------------------------
    def validate(self) -> None:
        self.refuse(self.validateHeader())  # the checks below index every agent column
        problems = self.validateValues()
        if self.table.name == 'registry':
            problems += self.validateAgainstTables()
            problems += self.licenseProblems()
        if self.table.name in RIVALS:
            problems += self.rivalProblems()
        if self.table.name in ON_CENSUS:
            problems += self.unknownObjects()
        self.refuse(problems)
        if self.table.name == 'flat_responses':  # every object loads, the census holds it
            self.refuse(self.flatResponseProblems())

    @staticmethod
    def refuse(problems: list[dict]) -> None:
        if problems:
            raise ShardRefused(pd.DataFrame(problems))

    def validateHeader(self) -> list[dict]:
        """The shard's header is the table's agent columns; line 1 is the header line."""
        present = set(self.shard.columns)
        expected = set(self.table.agentColumns)
        problems = [self.headerProblem(c, 'missing') for c in sorted(expected - present)]
        problems += [self.headerProblem(c, 'unknown') for c in sorted(present - expected)]
        return problems

    @staticmethod
    def headerProblem(column: str, text: str) -> dict:
        return {'line': 1, 'key': '', 'column': column, 'value': '', 'problem': text}

    def validateValues(self) -> list[dict]:
        name = self.table.name
        problems = []
        for col in REQUIRED[name]:
            problems += self.flag(self.shard[col] == '', col, 'required')
        for col, allowed in ALLOWED[name].items():
            bad = ~self.shard[col].isin(allowed) & (self.shard[col] != '')
            problems += self.flag(bad, col, 'not allowed')
        if name == 'registry':
            problems += self.grammarProblems()
            problems += self.modelIndexProblems()
            prior = self.shard['documented_prior'] != ''
            unpublished = self.shard['published_model'] == 'no'
            problems += self.flag(prior & unpublished, 'documented_prior', 'only on a published model')  # fmt: skip
        return problems

    def grammarProblems(self) -> list[dict]:
        """The package's row grammar, in its words (`Row.refusals`)."""
        problems = []
        for line, cells in self.shard.iterrows():
            refusals = Row.refusals(cells.to_dict())
            problems += [self.problem(line, column, reason) for column, reason in refusals]
        return problems

    def modelIndexProblems(self) -> list[dict]:
        number = pd.to_numeric(self.shard['model_index'], errors='coerce')
        outside = number.notna() & ~number.between(1, MAX_MODELS_PER_OBJECT)
        return self.flag(outside, 'model_index', f'at most {MAX_MODELS_PER_OBJECT} models per object')  # fmt: skip

    def licenseProblems(self) -> list[dict]:
        """Every registry source's license is in the lookup, the shard's and those merged
        earlier, since the merge rewrites every row's license."""
        merged = set(self.canonical(TABLES['registry'])['source'])
        named = merged | set(self.shard['source'])
        # a label not in sources.yaml is flagged by its row
        labels = named & set(self.frame.sources)
        problems = []
        for label in sorted(labels):
            verbatim = self.verbatimLicense(label)
            problem = {'line': '', 'key': label, 'column': 'license', 'value': verbatim or ''}
            if verbatim is None:
                problems.append(problem | {'problem': 'no license: key in sources.yaml'})
            elif verbatim not in LICENSES:
                problems.append(problem | {'problem': 'not in the license lookup'})
        return problems

    def verbatimLicense(self, label: str) -> str | None:
        """The source's `license:` key, else the `License` field of its CRAN package's
        DESCRIPTION, verbatim (base R's has none, so `datasets` carries a key); None for a git
        or url source nobody has looked at."""
        source = self.frame.sources[label]
        if label in self.frame.licenses:
            return self.frame.licenses[label]
        if source.kind == 'cran':
            description = (self.loader.tree(source) / 'DESCRIPTION').read_text()
            return re.search(r'^License:\s*(.+)$', description, re.MULTILINE).group(1)
        return None

    def rivalProblems(self) -> list[dict]:
        rival = TABLES[RIVALS[self.table.name]]
        taken = self.objectsIn(rival)
        return self.flag(self.keysOf(self.shard).isin(taken), 'object', f'also in {rival.name}.csv')

    def unknownObjects(self) -> list[dict]:
        """An object is dropped or given a verdict only where the census holds it."""
        known = self.objectsIn(TABLES['registry']) | self.objectsIn(TABLES['excluded'])
        unknown = ~self.keysOf(self.shard).isin(known)
        return self.flag(unknown, 'object', 'not in registry.csv or excluded.csv')

    def flatResponseProblems(self) -> list[dict]:
        """A flat table's response is a column of its loaded table, or `none`."""
        problems = []
        for line, row in self.shard.iterrows():
            if row['response'] == 'none':
                continue
            table = self.loader.load(self.frame.sources[row['source']], row['object'])
            if row['response'] not in table.columns:
                problems.append(self.problem(line, 'response', 'not a column of the table'))
        return problems

    def objectsIn(self, table: Table) -> set[Key]:
        return set(self.keysOf(self.canonical(table)))

    @staticmethod
    def keysOf(rows: pd.DataFrame) -> pd.Series:
        """Each row's (source, object), on the rows' index."""
        return pd.Series(list(zip(rows['source'], rows['object'])), index=rows.index)

    def canonical(self, table: Table) -> pd.DataFrame:
        """The table's file in its current columns: a file of an older shape gains the new
        columns empty (#7)."""
        path = self.file(table.name)
        if not path.exists():
            return pd.DataFrame(columns=table.columns)
        return readCsv(path).reindex(columns=table.columns, fill_value='')

    def file(self, name: str) -> Path:
        dir = self.registry if name in CENSUS else self.survey
        return dir / f'{name}.csv'

    def flag(self, mask: pd.Series, column: str, text: str) -> list[dict]:
        return [self.problem(line, column, text) for line in self.shard.index[mask]]

    def problem(self, line: int, column: str, text: str) -> dict:
        key = ' '.join(self.shard.loc[line, list(self.table.key)])
        return {
            'line': line,
            'key': key,
            'column': column,
            'value': self.shard.at[line, column],
            'problem': text,
        }

    # ---------------------------------------------------------------------------------
    # validate against the loaded tables
    # ---------------------------------------------------------------------------------
    def validateAgainstTables(self) -> list[dict]:
        """Every reading the data can contradict, row by row: the source and object exist,
        every named column exists, the grouping factors group, the response is what it says. A
        row the grammar refuses is read again at the next merge."""
        blank = {c: '' for c in self.table.scriptColumns}
        problems = []
        for line, cells in self.shard.iterrows():
            if not Row.refusals(cells.to_dict()):
                problems += self.validateRow(line, Row.parse(blank | cells.to_dict()))
        return problems

    def validateRow(self, line: int, row: Row) -> list[dict]:
        if row.source not in self.frame.sources:
            return [self.problem(line, 'source', 'not in sources.yaml')]
        if row.object not in self.objects(row.source):
            return [self.problem(line, 'object', f'not an object of {row.source}')]
        source = self.frame.sources[row.source]
        untyped = self.loader.load(source, row.object)
        problems = self.missingColumns(line, row, set(untyped.columns))
        if problems:
            return problems
        loaded = self.loader.load(source, row.object, row.types)
        table = withComposites(loaded, row.grouping_factors)
        problems += self.groupingProblems(line, row, table)
        problems += self.responseProblems(line, row, table)
        return problems

    def objects(self, label: str) -> dict[str, DataObject]:
        return {o.name: o for o in self.loader.objects(self.frame.sources[label])}

    def missingColumns(self, line: int, row: Row, columns: set[str]) -> list[dict]:
        """Every column a row names, with the shard column it was named in."""
        named = [('response', row.response), ('trials', row.trials)]
        for col in COLUMN_LIST_COLUMNS:
            named += [(col, name) for name in getattr(row, col)]
        for col in TERM_COLUMNS:
            for term in getattr(row, col):
                named += [(col, name) for name in parts(term)]
        named += [('types', name) for name in row.types]
        return [
            self.problem(line, col, f'no such column: {name}')
            for col, name in named
            if name != '' and name not in columns
        ]

    def groupingProblems(self, line: int, row: Row, table: pd.DataFrame) -> list[dict]:
        """A grouping factor has at least two levels and a level with two or more rows."""
        problems = []
        for factor in row.grouping_factors:
            sizes = table[factor].value_counts()
            if len(sizes) < 2:
                problems.append(self.problem(line, 'grouping_factors', f'{factor} has one level'))
            elif sizes.max() < 2:
                problems.append(
                    self.problem(line, 'grouping_factors', f'{factor} has no level with two rows')
                )
        return problems

    def responseProblems(self, line: int, row: Row, table: pd.DataFrame) -> list[dict]:
        """The response column shows what its declared type says."""
        response, kind = row.response, row.response_type
        complaint = self.responseComplaint(kind, table[response].dropna())
        problems = []
        if complaint is not None:
            problems.append(self.problem(line, 'response_type', f'{response} {complaint}'))
        if kind == 'binomial':
            problems += self.trialsProblems(line, row, table)
        return problems

    @staticmethod
    def responseComplaint(kind: str, values: pd.Series) -> str | None:
        """What the response column fails to show of its declared type; None when it fits."""
        if kind == 'continuous' and not pd.api.types.is_numeric_dtype(values):
            return 'is not numeric'
        if kind == 'binary' and values.nunique() != 2:
            return 'does not have two distinct values'
        if kind in ('count', 'binomial') and not Merger.isCount(values):
            return 'is not integer-valued'
        if kind == 'ordinal' and values.nunique() > MAX_ORDINAL_LEVELS:
            return f'has more than {MAX_ORDINAL_LEVELS} levels'
        if kind == 'categorical' and pd.api.types.is_float_dtype(values):
            return 'is not categorical'
        return None

    @staticmethod
    def isCount(values: pd.Series) -> bool:
        if not pd.api.types.is_numeric_dtype(values):
            return False
        return bool(((values >= 0) & (values == values.round())).all())

    def trialsProblems(self, line: int, row: Row, table: pd.DataFrame) -> list[dict]:
        """A binomial response names integer trials it never exceeds."""
        response, trials = row.response, row.trials
        if trials == '':
            return [self.problem(line, 'trials', 'binomial names its trials')]
        if not self.isCount(table[trials].dropna()):
            return [self.problem(line, 'trials', f'{trials} is not integer-valued')]
        if (table[response] > table[trials]).any():
            return [self.problem(line, 'trials', f'{response} exceeds {trials}')]
        return []

    # ---------------------------------------------------------------------------------
    # upsert
    # ---------------------------------------------------------------------------------
    def upsert(self) -> None:
        """Upsert on the row key: existing keys are replaced in place, new rows appended."""
        self.fillScriptColumns()
        old = self.canonical(self.table)
        shard = self.shard
        if self.table.name == 'dropped':
            shard = shard[self.inCensus()]
        new = shard.reindex(columns=self.table.columns).reset_index(drop=True)
        key = list(self.table.key)
        # groups in order of first appearance: a replaced key keeps its place
        merged = pd.concat([old, new]).groupby(key, sort=False).last().reset_index()[old.columns]
        if self.table.name == 'registry':
            merged = self.withLicenses(merged)
        self.replaced = len(old) + len(new) - len(merged)
        self.added = len(new) - self.replaced
        self.merged = merged.reset_index(drop=True)
        writeCsv(self.merged, self.file(self.table.name))

    def fillScriptColumns(self) -> None:
        if 'tier' in self.table.scriptColumns:
            self.shard['tier'] = self.shard['source'].map(self.frame.tiers)
        if 'reader' in self.table.scriptColumns:
            self.shard['reader'] = [self.objects(s)[o].reader for s, o in self.keysOf(self.shard)]
        if 'sources' in self.table.scriptColumns:
            self.shard['sources'] = self.shard['source'] + ':' + self.shard['object']

    def inCensus(self) -> pd.Series:
        """A dropped object the loader no longer enumerates can never be re-filed, so its key
        leaves every file instead of waiting in dropped.csv (#14)."""
        present = [o in self.objects(s) for s, o in self.keysOf(self.shard)]
        return pd.Series(present, index=self.shard.index)

    def withLicenses(self, registry: pd.DataFrame) -> pd.DataFrame:
        """Every row's license, rows merged earlier too: a license is its source's, so a
        corrected key reaches every row of the source at the next merge."""
        licenses = {
            label: LICENSES[self.verbatimLicense(label)] for label in set(registry['source'])
        }
        return registry.assign(license=registry['source'].map(licenses))

    def supersede(self) -> None:
        """The shard's objects leave the files this merge wins over."""
        objects = set(self.keysOf(self.shard)) if 'source' in self.shard else set()
        for name in SUPERSEDES[self.table.name]:
            path = self.file(name)
            if not path.exists():
                continue
            rows = readCsv(path)
            writeCsv(rows[~self.keysOf(rows).isin(objects)], path)

    # ---------------------------------------------------------------------------------
    # reconcile duplicates: fold confirmed groups, flag new candidates
    # ---------------------------------------------------------------------------------
    def reconcile(self) -> None:
        """Only a merge that changes the registry or the verdicts can change the fold."""
        self.flagged = 0
        if self.table.name not in RECONCILED:
            return
        registry = self.canonical(TABLES['registry'])
        duplicates = self.canonical(TABLES['duplicates'])
        registry = self.fold(registry, self.sameGroups(duplicates))
        flagged = self.flagCandidates(registry, duplicates)
        writeCsv(registry, self.file('registry'))
        if len(duplicates) + len(flagged) > 0:
            duplicates = pd.concat([duplicates, pd.DataFrame(flagged)]).reset_index(drop=True)
            writeCsv(duplicates, self.file('duplicates'))
        self.flagged = len(flagged)

    @staticmethod
    def sameGroups(duplicates: pd.DataFrame) -> list[set[Key]]:
        """Connected components of the `same` pairs (radon in three sources is one group)."""
        groups: list[set[Key]] = []
        same = duplicates[duplicates['verdict'] == 'same']
        for _, row in same.iterrows():
            pair = {(row['source_a'], row['object_a']), (row['source_b'], row['object_b'])}
            touching = [g for g in groups if g & pair]
            for g in touching:
                groups.remove(g)
                pair |= g
            groups.append(pair)
        return groups

    def fold(self, registry: pd.DataFrame, groups: list[set[Key]]) -> pd.DataFrame:
        """Each confirmed group becomes the row(s) of its earliest member in the registry,
        `sources` listing every member of the group, present or already folded away; the
        other present members' rows leave the registry."""
        keys = self.keysOf(registry)
        sources = registry['source'] + ':' + registry['object']
        keep = pd.Series(True, index=registry.index)
        for group in groups:
            members = sorted(group, key=self.frame.rank)
            present = [m for m in members if m in set(keys)]
            if not present:
                continue
            keep &= ~keys.isin(present[1:])
            listed = ';'.join(f'{s}:{o}' for s, o in members)
            sources = sources.where(keys != present[0], listed)
        return registry.assign(sources=sources)[keep].reset_index(drop=True)

    def flagCandidates(self, registry: pd.DataFrame, duplicates: pd.DataFrame) -> list[dict]:
        """Pairs of registry objects with equal row count and sorted column cardinalities that
        no verdict row covers yet, earliest tier first."""
        objects = sorted(set(self.keysOf(registry)), key=self.frame.rank)
        groups: dict[tuple, list[Key]] = {}  # signature -> its objects in frame order
        for key in objects:
            groups.setdefault(self.signature(key), []).append(key)
        first = zip(duplicates['source_a'], duplicates['object_a'])
        second = zip(duplicates['source_b'], duplicates['object_b'])
        decided = set(zip(first, second))  # pairs are stored earliest tier first too
        pairs = [pair for group in groups.values() for pair in combinations(group, 2)]
        undecided = [(a, b) for a, b in pairs if (a, b) not in decided]
        return [
            {'source_a': a[0], 'object_a': a[1], 'source_b': b[0], 'object_b': b[1], 'verdict': 'flagged', 'notes': ''}
            for a, b in undecided
        ]  # fmt: skip

    def signature(self, key: Key) -> tuple[int, tuple[int, ...]]:
        table = self.loader.load(self.frame.sources[key[0]], key[1])
        return (len(table), tuple(sorted(table.nunique())))

    # ---------------------------------------------------------------------------------
    # measure: registry -> measured files -> manifest.csv
    # ---------------------------------------------------------------------------------
    def measure(self) -> None:
        """A flat verdict or response changes no registry row, so its merge measures nothing."""
        if self.table.name in FLAT:
            return
        measureRegistry(self.registry, self.loader)
        self.writeManifest()

    def writeManifest(self) -> None:
        """The file each registry object loads from, with its digest and size (#4)."""
        registry = self.canonical(TABLES['registry'])
        rows = []
        for label, name in registry[['source', 'object']].drop_duplicates().itertuples(index=False):  # fmt: skip
            file = self.objects(label)[name].file
            data = (self.loader.tree(self.frame.sources[label]) / file).read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            rows.append({'source': label, 'object': name, 'file': file, 'sha256': sha256, 'size': len(data)})  # fmt: skip
        manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
        writeCsv(manifest, self.registry / 'manifest.csv')

    # ---------------------------------------------------------------------------------
    # report
    # ---------------------------------------------------------------------------------
    def report(self) -> None:
        print(f'{self.table.name}: {self.added} rows added, {self.replaced} replaced, {len(self.merged)} total')  # fmt: skip
        if self.flagged:
            print(f'duplicates: {self.flagged} candidate pairs flagged, confirm through a duplicates shard')  # fmt: skip


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('shard', type=Path, help='survey/shards/<table>_<label>.csv')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding the duplicates and dropped tables')
    args = parser.parse_args()
    # fmt: on
    merger = Merger(args.registry, args.survey)
    merger.load(args.shard)
    try:
        merger.validate()
    except ShardRefused as e:
        sys.exit(str(e))
    merger.upsert()
    merger.supersede()
    merger.reconcile()
    merger.measure()
    Summarizer(args.registry, args.survey).flush()
    merger.report()
