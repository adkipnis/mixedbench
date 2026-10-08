"""Merge one agent-written shard into the dimension survey's canonical CSVs.

A shard is `shards/<table>_<label>.csv` with exactly the agent columns of its table
(schema.py). The script loads every named object through the package's dataset loader,
validates the shard against the table it returns, refuses a failing shard printing the
offending rows, and otherwise upserts on the table's row key, so merging the same shard twice
changes nothing and a corrected shard replaces its earlier rows. The census tables land in
`registry/`, the survey's bookkeeping tables (duplicates, dropped) in `survey/`. Run from the
repo root:

    uv run python survey/merge.py survey/shards/registry_lme4.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd
from measure import (
    COLUMN_COLUMNS,
    DIMENSION_COLUMNS,
    Measurer,
    parseTypes,
    splitList,
    withComposites,
)
from mixedbench.datasets import DataObject, Loader
from schema import (
    ALLOWED,
    COLUMN_LIST_COLUMNS,
    COLUMN_TYPES,
    MAX_MODELS_PER_OBJECT,
    MAX_ORDINAL_LEVELS,
    REQUIRED,
    TABLES,
    TERM_COLUMNS,
    TIERS,
    TYPES_COLUMN,
    Table,
)
from sources import readFrame
from summarise import Summariser

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
# An object is in the registry or in the exclusions, never both: the second shard is refused.
RIVALS = {'registry': 'excluded', 'excluded': 'registry'}
# A dropped object leaves both files; re-filing it leaves dropped.csv. The later merge wins.
SUPERSEDES = {
    'registry': ('dropped',),
    'excluded': ('dropped',),
    'dropped': ('registry', 'excluded'),
    'duplicates': (),
}
RECONCILED = ('registry', 'duplicates', 'dropped')  # merges that can change the duplicate fold
CENSUS = ('registry', 'excluded')  # the tables the package ships; the others stay in the survey
Key = tuple[str, str]  # (source label, object name)


def isNumeric(values: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(values)


def isCount(values: pd.Series) -> bool:
    if not isNumeric(values):
        return False
    return bool(((values >= 0) & (values == values.round())).all())


def isBinary(values: pd.Series) -> bool:
    return values.nunique() == 2


def isOrdinal(values: pd.Series) -> bool:
    return values.nunique() <= MAX_ORDINAL_LEVELS


def isCategorical(values: pd.Series) -> bool:
    return not pd.api.types.is_float_dtype(values)


# What the response column must show for its declared type, and the complaint if it does not.
RESPONSE_CHECKS = {
    'continuous': (isNumeric, 'is not numeric'),
    'binary': (isBinary, 'does not have two distinct values'),
    'count': (isCount, 'is not integer-valued'),
    'binomial': (isCount, 'is not integer-valued'),
    'ordinal': (isOrdinal, f'has more than {MAX_ORDINAL_LEVELS} levels'),
    'categorical': (isCategorical, 'is not categorical'),
}


class ShardRefused(Exception):
    """Carries the offending rows as a DataFrame (line, key, column, value, problem)."""

    def __init__(self, problems: pd.DataFrame) -> None:
        self.problems = problems
        super().__init__(
            f'shard refused, {len(problems)} problems:\n{problems.to_string(index=False)}'
        )


def readCsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def writeCsv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, quoting=csv.QUOTE_ALL)


# =====================================================================================
# pipeline: shard -> validate -> upsert -> reconcile duplicates -> measure -> summarise
# =====================================================================================
class Merger:
    def __init__(self, registry: Path, survey: Path, loader: Loader | None = None) -> None:
        self.registry, self.survey = Path(registry), Path(survey)
        self.loader = loader or Loader(self.registry / 'cache')
        frame = readFrame(self.registry)
        self.tiers, self.sources = frame.tiers, frame.sources
        self.order = {label: i for i, label in enumerate(frame.tiers)}  # sources.yaml order

    def canonical(self, table: Table) -> pd.DataFrame:
        path = self.file(table.name)
        return readCsv(path) if path.exists() else pd.DataFrame(columns=table.columns)

    def file(self, name: str) -> Path:
        dir = self.registry if name in CENSUS else self.survey
        return dir / f'{name}.csv'

    def objects(self, label: str) -> dict[str, DataObject]:
        return {o.name: o for o in self.loader.objects(self.sources[label])}

    def rank(self, key: Key) -> tuple[int, int, str]:
        """Frame order of an object: its tier, its source's place in `sources.yaml`, its name."""
        return (TIERS.index(self.tiers[key[0]]), self.order[key[0]], key[1])

    # ---------------------------------------------------------------------------------
    # load
    # ---------------------------------------------------------------------------------
    def load(self, shard: Path) -> None:
        shard = Path(shard)
        self.table = TABLES[shard.stem.split('_')[0]]
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
            ordered.append(sorted([a, b], key=self.rank))
        self.shard[['source_a', 'object_a']] = [a for a, _ in ordered]
        self.shard[['source_b', 'object_b']] = [b for _, b in ordered]

    # ---------------------------------------------------------------------------------
    # validate
    # ---------------------------------------------------------------------------------
    def validate(self) -> None:
        self.validateHeader()
        problems = self.validateValues()
        if self.table.name == 'registry':
            problems += self.validateAgainstTables()
        if self.table.name in RIVALS:
            problems += self.rivalProblems()
        if self.table.name == 'dropped':
            problems += self.unknownObjects()
        if problems:
            raise ShardRefused(pd.DataFrame(problems))
        self.fillScriptColumns()

    def validateHeader(self) -> None:
        present = set(self.shard.columns)
        expected = set(self.table.agentColumns)
        if present == expected:
            return
        problems = [('header', '', 'missing', c) for c in sorted(expected - present)]
        problems += [('header', '', 'unknown', c) for c in sorted(present - expected)]
        raise ShardRefused(pd.DataFrame(problems, columns=['line', 'column', 'problem', 'value']))

    def validateValues(self) -> list[dict]:
        name = self.table.name
        problems = []
        for col in REQUIRED[name]:
            problems += self.flag(self.shard[col] == '', col, 'required')
        for col, allowed in ALLOWED[name].items():
            bad = ~self.shard[col].isin(allowed) & (self.shard[col] != '')
            problems += self.flag(bad, col, 'not allowed')
        if name == 'registry':
            problems += self.modelIndexProblems()
        return problems

    def modelIndexProblems(self) -> list[dict]:
        index = self.shard['model_index']
        problems = self.flag(~index.str.fullmatch(r'\d+'), 'model_index', 'not an integer')
        number = pd.to_numeric(index, errors='coerce')
        outside = number.notna() & ~number.between(1, MAX_MODELS_PER_OBJECT)
        problems += self.flag(outside, 'model_index', f'at most {MAX_MODELS_PER_OBJECT} models per object')  # fmt: skip
        return problems

    def rivalProblems(self) -> list[dict]:
        rival = TABLES[RIVALS[self.table.name]]
        taken = self.objectsIn(rival)
        return self.flag(self.shardObjects().isin(taken), 'object', f'also in {rival.name}.csv')

    def unknownObjects(self) -> list[dict]:
        """A dropped object must be somewhere to drop it from."""
        known = self.objectsIn(TABLES['registry']) | self.objectsIn(TABLES['excluded'])
        unknown = ~self.shardObjects().isin(known)
        return self.flag(unknown, 'object', 'not in registry.csv or excluded.csv')

    def objectsIn(self, table: Table) -> set[Key]:
        rows = self.canonical(table)
        return set(zip(rows['source'], rows['object']))

    def shardObjects(self) -> pd.Series:
        keys = list(zip(self.shard['source'], self.shard['object']))
        return pd.Series(keys, index=self.shard.index)

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
        every named column exists, the grouping factors group, the response is what it says."""
        problems = []
        for line, row in self.shard.iterrows():
            problems += self.validateRow(line, row)
        return problems

    def validateRow(self, line: int, row: pd.Series) -> list[dict]:
        if row['source'] not in self.sources:
            return [self.problem(line, 'source', 'not in sources.yaml')]
        if row['object'] not in self.objects(row['source']):
            return [self.problem(line, 'object', f'not an object of {row["source"]}')]
        source = self.sources[row['source']]
        types = parseTypes(row[TYPES_COLUMN])
        problems = []
        for kind in types.values():
            if kind not in COLUMN_TYPES:
                problems.append(self.problem(line, TYPES_COLUMN, f'not a column type: {kind}'))
        untyped = self.loader.load(source, row['object'])
        problems += self.missingColumns(line, row, set(untyped.columns), types)
        if problems:
            return problems
        loaded = self.loader.load(source, row['object'], types)
        df = withComposites(loaded, splitList(row['grouping_factors']))
        problems += self.groupingProblems(line, row, df)
        problems += self.roleProblems(line, row)
        problems += self.responseProblems(line, row, df)
        return problems

    def missingColumns(
        self, line: int, row: pd.Series, columns: set[str], types: dict[str, str]
    ) -> list[dict]:
        """Every column a row names, with the shard column it was named in."""
        named = [('response', row['response']), ('trials', row['trials'])]
        for col in COLUMN_LIST_COLUMNS:
            named += [(col, name) for name in splitList(row[col])]
        for col in TERM_COLUMNS:
            for term in splitList(row[col]):
                named += [(col, name) for name in term.split(':')]
        named += [(TYPES_COLUMN, name) for name in types]
        return [
            self.problem(line, col, f'no such column: {name}')
            for col, name in named
            if name != '' and name not in columns
        ]

    def groupingProblems(self, line: int, row: pd.Series, df: pd.DataFrame) -> list[dict]:
        """A grouping factor has at least two levels and a level with two or more rows."""
        problems = []
        for factor in splitList(row['grouping_factors']):
            sizes = df[factor].value_counts()
            if len(sizes) < 2:
                problems.append(self.problem(line, 'grouping_factors', f'{factor} has one level'))
            elif sizes.max() < 2:
                problems.append(
                    self.problem(line, 'grouping_factors', f'{factor} has no level with two rows')
                )
        return problems

    def roleProblems(self, line: int, row: pd.Series) -> list[dict]:
        """A column is a grouping factor or a covariate, never both (SASmixed Cultivation's
        `(1|Cult)` next to `Inoc * Cult` reads as the whole-plot term `Block:Cult`); a part of a
        composite factor may be a covariate."""
        covariates = set(splitList(row['covariates']))
        for term in splitList(row['interactions']):
            covariates |= set(term.split(':'))
        return [
            self.problem(line, 'grouping_factors', f'{factor} is also a covariate')
            for factor in splitList(row['grouping_factors'])
            if factor in covariates
        ]

    def responseProblems(self, line: int, row: pd.Series, df: pd.DataFrame) -> list[dict]:
        """The response column shows what its declared type says."""
        response, kind = row['response'], row['response_type']
        fits, complaint = RESPONSE_CHECKS[kind]
        problems = []
        if not fits(df[response].dropna()):
            problems.append(self.problem(line, 'response_type', f'{response} {complaint}'))
        if kind == 'binomial':
            problems += self.trialsProblems(line, row, df)
        return problems

    def trialsProblems(self, line: int, row: pd.Series, df: pd.DataFrame) -> list[dict]:
        """A binomial response names integer trials it never exceeds."""
        response, trials = row['response'], row['trials']
        if trials == '':
            return [self.problem(line, 'trials', 'binomial names its trials')]
        if not isCount(df[trials].dropna()):
            return [self.problem(line, 'trials', f'{trials} is not integer-valued')]
        if (df[response] > df[trials]).any():
            return [self.problem(line, 'trials', f'{response} exceeds {trials}')]
        return []

    def fillScriptColumns(self) -> None:
        if 'tier' in self.table.scriptColumns:
            self.shard['tier'] = self.shard['source'].map(self.tiers)
        if 'reader' in self.table.scriptColumns:
            self.shard['reader'] = [self.objects(s)[o].reader for s, o in self.shardObjects()]
        if 'sources' in self.table.scriptColumns:
            self.shard['sources'] = self.shard['source'] + ':' + self.shard['object']

    # ---------------------------------------------------------------------------------
    # append
    # ---------------------------------------------------------------------------------
    def append(self) -> None:
        """Upsert on the row key: existing keys are replaced in place, new rows appended."""
        old = self.canonical(self.table)
        new = self.shard[self.table.columns].reset_index(drop=True)
        key = list(self.table.key)
        merged = pd.concat([old, new]).drop_duplicates(subset=key, keep='last')
        self.replaced = len(old) + len(new) - len(merged)
        self.merged = merged.reset_index(drop=True)
        writeCsv(self.merged, self.file(self.table.name))
        self.supersede()
        self.flagged = 0
        if self.table.name in RECONCILED:
            self.reconcile()
        self.measure()

    def supersede(self) -> None:
        """The shard's objects leave the files this merge wins over."""
        objects = set(self.shardObjects()) if 'source' in self.shard else set()
        for name in SUPERSEDES[self.table.name]:
            path = self.file(name)
            if not path.exists():
                continue
            rows = readCsv(path)
            keys = pd.Series(list(zip(rows['source'], rows['object'])), index=rows.index)
            writeCsv(rows[~keys.isin(objects)], path)

    # ---------------------------------------------------------------------------------
    # reconcile duplicates: fold confirmed groups, flag new candidates
    # ---------------------------------------------------------------------------------
    def reconcile(self) -> None:
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
        keys = pd.Series(list(zip(registry['source'], registry['object'])), index=registry.index)
        sources = registry['source'] + ':' + registry['object']
        keep = pd.Series(True, index=registry.index)
        for group in groups:
            members = sorted(group, key=self.rank)
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
        objects = sorted(set(zip(registry['source'], registry['object'])), key=self.rank)
        signatures = {key: self.signature(key) for key in objects}
        first = zip(duplicates['source_a'], duplicates['object_a'])
        second = zip(duplicates['source_b'], duplicates['object_b'])
        decided = set(zip(first, second))  # pairs are stored earliest tier first too
        flagged = []
        for a, b in combinations(objects, 2):
            if signatures[a] == signatures[b] and (a, b) not in decided:
                flagged.append({'source_a': a[0], 'object_a': a[1], 'source_b': b[0], 'object_b': b[1], 'verdict': 'flagged', 'notes': ''})  # fmt: skip
        return flagged

    def signature(self, key: Key) -> tuple[int, tuple[int, ...]]:
        df = self.loader.load(self.sources[key[0]], key[1])
        return (len(df), tuple(sorted(df.nunique())))

    # ---------------------------------------------------------------------------------
    # measure: registry rows -> dimensions.csv, columns.csv
    # ---------------------------------------------------------------------------------
    def measure(self) -> None:
        """Every merge measures the whole registry from the loaded tables; nothing is typed."""
        registry = self.canonical(TABLES['registry'])
        dimensions, columns = [], []
        for _, row in registry.iterrows():
            types = parseTypes(row['types'])
            df = self.loader.load(self.sources[row['source']], row['object'], types)
            measurer = Measurer(df, row.to_dict())
            dimensions += measurer.dimensions()
            columns += measurer.columns()
        writeCsv(pd.DataFrame(dimensions, columns=DIMENSION_COLUMNS), self.registry / 'dimensions.csv')  # fmt: skip
        writeCsv(pd.DataFrame(columns, columns=COLUMN_COLUMNS), self.registry / 'columns.csv')
        Summariser(self.registry, self.survey, registry, self.canonical(TABLES['excluded'])).flush()

    def flush(self) -> None:
        new = len(self.shard) - self.replaced
        print(f'{self.table.name}: {new} rows added, {self.replaced} replaced, {len(self.merged)} total')  # fmt: skip
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
    merger.append()
    merger.flush()
