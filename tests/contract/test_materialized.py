"""The materialized problem at its seam (#30): `materialize` writes one parquet and one JSON
under the cache and returns the contract hash, `load` reads them back into the `Problem`
(ADR 0001, 0003). The JSON is the package's interface, so a test may read it.

The fixture is one small grouped table: a continuous and a categorical covariate, a numeric
binary, a correlated slope, two crossed factors, and a binomial and an ordinal response beside
the continuous one.
"""

from __future__ import annotations

import json
import random
import socket
import tempfile
from dataclasses import fields, replace
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from mixedbench.contract import Problem, contractHash, load, materialize
from mixedbench.registry.row import Row, SlopeTerm

ROW = Row(
    source='fixture', tier='R', sources=('fixture:trial',), object='data/trial, 1.csv!a',
    reader='pandas', license='MIT', model_index=2, response='y', response_type='continuous',
    trials='', family='', grouping_factors=('g', 'h'), covariates=('x', 'diet', 'dose'),
    interactions=(), random_slopes=(SlopeTerm('x', 'g', correlated=True),), ignore=(),
    types={'diet': 'categorical'}, formula='y ~ x + diet + dose + (x | g) + (1 | h)',
    documented_prior='', published_model='yes', domain='test', confidence='high',
    verified='hand', notes='',
)  # fmt: skip


def fixtureTable() -> pd.DataFrame:
    n = 40
    return pd.DataFrame(
        {
            'g': [f'g{i % 8}' for i in range(n)],
            'h': [f'h{i % 3}' for i in range(n)],
            'x': [0.25 * i - 3 for i in range(n)],
            'diet': pd.Categorical(['a', 'b', 'c', 'b'] * 10, categories=['a', 'b', 'c']),
            'dose': [0.5, 2.0] * 20,  # numeric binary: levels (0.5, 2.0)
            'y': [((i * 7) % 11) / 3 for i in range(n)],
            'wins': [i % 5 for i in range(n)],
            'games': [5 + i % 3 for i in range(n)],
            'rating': [[1, 3, 5][i % 3] for i in range(n)],
        }
    )


RESPONSES = {
    'continuous': {},
    'binomial': {'response': 'wins', 'response_type': 'binomial', 'trials': 'games'},
    'ordinal': {'response': 'rating', 'response_type': 'ordinal'},
}


def fixtureProblem(response_type: str = 'continuous') -> Problem:
    return Problem.build(replace(ROW, **RESPONSES[response_type]), fixtureTable())


def assertSameProblem(loaded: Problem, built: Problem) -> None:
    """Field by field: a `Problem` holds a DataFrame, whose `==` is elementwise."""
    for field in fields(Problem):
        if field.name == 'table':
            pd.testing.assert_frame_equal(loaded.table, built.table)
        else:
            assert getattr(loaded, field.name) == getattr(built, field.name), field.name


def storedHash(cache: Path) -> str:
    [record] = cache.glob('problems/*/problem.json')
    return json.loads(record.read_text())['hash']


# ==============================================================================================
# the round trip
# ==============================================================================================


@pytest.mark.parametrize('response_type', RESPONSES)
def test_a_loaded_problem_equals_the_built_one_and_carries_the_written_hash(
    tmp_path: Path, response_type: str
) -> None:
    """The files are the package's interface (ADR 0003): what metabeta loads must be the
    problem the contract built, numeric levels, trials and ordinal thresholds included, and its
    hash the one the suite lists."""
    built = fixtureProblem(response_type)
    written = materialize(built, tmp_path)
    loaded = load(built.id, tmp_path)
    assertSameProblem(loaded, built)
    assert written == storedHash(tmp_path) == contractHash(loaded)


def refuseNetwork(*args, **kwargs) -> None:
    raise AssertionError('load opened a socket')


def test_loading_needs_only_the_two_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A suite user needs the loader once per machine (ADR 0003): a cache holding nothing but
    the problem's files loads with every socket refused, no source tree and no `Loader`."""
    built = fixtureProblem()
    materialize(built, tmp_path)
    assert {p.name for p in tmp_path.rglob('*') if p.is_file()} == {'table.parquet', 'problem.json'}
    monkeypatch.setattr(socket, 'socket', refuseNetwork)
    assertSameProblem(load(built.id, tmp_path), built)


# ==============================================================================================
# the contract hash
# ==============================================================================================
PROBLEM = fixtureProblem()


def problemFiles(cache: Path) -> tuple[Path, Path]:
    [dir] = cache.glob('problems/*')
    return dir / 'table.parquet', dir / 'problem.json'


def shuffled(value: object, rng: random.Random) -> object:
    """The JSON with every object's keys in a random order; a list's order is its meaning."""
    if not isinstance(value, dict):
        return value
    keys = list(value)
    rng.shuffle(keys)
    return {key: shuffled(value[key], rng) for key in keys}


@settings(max_examples=25, deadline=None)
@given(rng=st.randoms(use_true_random=False))
def test_the_hash_ignores_the_json_key_order(rng: random.Random) -> None:
    """The hash is over the record with sorted keys (ADR 0001), so a JSON rewritten by another
    tool, its keys in another order, is the same problem."""
    with tempfile.TemporaryDirectory() as cache:
        written = materialize(PROBLEM, Path(cache))
        _, record = problemFiles(Path(cache))
        record.write_text(json.dumps(shuffled(json.loads(record.read_text()), rng)))
        assert contractHash(load(PROBLEM.id, Path(cache))) == written


WRITER_OPTIONS = st.fixed_dictionaries(
    {
        'compression': st.sampled_from(['snappy', 'gzip', 'zstd', 'brotli', 'lz4', None]),
        'row_group_size': st.integers(1, 50),
        'use_dictionary': st.booleans(),
        'data_page_version': st.sampled_from(['1.0', '2.0']),
        'write_statistics': st.booleans(),
    }
)


@settings(max_examples=25, deadline=None)
@given(options=WRITER_OPTIONS)
def test_the_hash_ignores_the_parquet_writers_options(options: dict) -> None:
    """Hashing parquet bytes was rejected because a pyarrow bump would be a contract change
    (ADR 0001): the hash reads the arrays, so a table rewritten with other writer options, as a
    newer writer's defaults would, is the same problem."""
    with tempfile.TemporaryDirectory() as cache:
        written = materialize(PROBLEM, Path(cache))
        table, _ = problemFiles(Path(cache))
        pd.read_parquet(table).to_parquet(table, index=False, **options)
        assert contractHash(load(PROBLEM.id, Path(cache))) == written


def perturbedCell(table: pd.DataFrame, column: str, row: int) -> pd.DataFrame:
    """One cell changed: a number plus one, a fold among them."""
    changed = table.copy()
    changed.at[row, column] += 1
    return changed


MISMATCH = 'do not match their contract hash'


@settings(max_examples=50, deadline=None)
@given(
    column=st.sampled_from(list(PROBLEM.table.columns)),
    row=st.integers(0, len(PROBLEM.table) - 1),
)
def test_a_changed_array_fails_to_load(column: str, row: int) -> None:
    """A changed array is a changed problem: a cache file edited or stale, in any column
    including the factor codes and the regimes, fails loudly instead of loading as the problem
    the suite lists."""
    with tempfile.TemporaryDirectory() as cache:
        materialize(PROBLEM, Path(cache))
        table, _ = problemFiles(Path(cache))
        perturbedCell(pd.read_parquet(table), column, row).to_parquet(table, index=False)
        with pytest.raises(ValueError, match=MISMATCH):
            load(PROBLEM.id, Path(cache))


def leafPaths(value: object, path: tuple = ()) -> list[tuple]:
    """The path of every scalar in the JSON: keys of objects, indices of lists."""
    if isinstance(value, dict):
        children = value.items()
    elif isinstance(value, list):
        children = enumerate(value)
    else:
        return [path]
    paths = []
    for key, child in children:
        paths += leafPaths(child, (*path, key))
    return paths


def perturbedLeaf(stored: dict, path: tuple) -> dict:
    """The scalar at `path` changed: a string or null gains a character, a number one."""
    changed = json.loads(json.dumps(stored))
    parent = changed
    for key in path[:-1]:
        parent = parent[key]
    value = parent[path[-1]]
    if isinstance(value, int | float):
        parent[path[-1]] = value + 1
    else:
        parent[path[-1]] = f'{value or ""}~'
    return changed


@settings(max_examples=50, deadline=None)
@given(data=st.data())
def test_a_changed_json_value_fails_to_load(data: st.DataObject) -> None:
    """Every value of the record is part of the problem: a changed family, prior parameter,
    level, scale or name fails loudly on load."""
    with tempfile.TemporaryDirectory() as cache:
        materialize(PROBLEM, Path(cache))
        _, record = problemFiles(Path(cache))
        stored = json.loads(record.read_text())
        paths = [path for path in leafPaths(stored) if path != ('hash',)]
        path = data.draw(st.sampled_from(paths))
        record.write_text(json.dumps(perturbedLeaf(stored, path)))
        with pytest.raises(ValueError, match=MISMATCH):
            load(PROBLEM.id, Path(cache))


def test_another_contract_version_is_another_hash() -> None:
    """A contract change is a new suite version, never a recomputation (docs/conventions.md):
    the same arrays and record under the next major version hash differently."""
    next_version = replace(PROBLEM, contract=PROBLEM.contract + 1)
    assert contractHash(next_version) != contractHash(PROBLEM)
