"""materialised.py defines a problem's files on disk and the contract hash over them.

A materialised problem is two files under the loader's cache (ADR 0001, 0003):
a parquet holding the table, and a JSON holding the record a table cannot and the contract hash.
The files are the package's interface to a problem: `load` needs neither the loader nor the network.
The hash is over values, not file bytes: the record as canonical JSON,
then every column's name, dtype and little-endian bytes, so a writer's options do not move it.

pipeline:
---------
a built Problem
-> its record, every field but the table as JSON values      _record
-> its contract hash                                         contractHash
-> the table as parquet, the record and the hash as JSON     materialise
-> the problem read back, refused if its hash moved          load
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields
from pathlib import Path

import numpy as np
import pandas as pd
from mixedbench.contract.problem import Prior, Problem, Scale


# =====================================================================================
# the files
# =====================================================================================
def materialise(problem: Problem, cache: Path) -> str:
    """Write the problem's two files under `cache` and return its contract hash."""
    dir = _problemDir(cache, problem.id)
    dir.mkdir(parents=True, exist_ok=True)
    problem.table.to_parquet(dir / 'table.parquet', index=False)
    written = contractHash(problem)
    stored = _record(problem) | {'hash': written}
    (dir / 'problem.json').write_text(json.dumps(stored, sort_keys=True, indent=2))
    return written


def load(cache: Path, id: str) -> Problem:
    """The problem the files hold; files whose arrays or record no longer give the hash they
    were written with (edited, or stale) are refused."""
    dir = _problemDir(cache, id)
    stored = json.loads((dir / 'problem.json').read_text())
    problem = Problem(
        id=stored['id'],
        table=pd.read_parquet(dir / 'table.parquet'),
        design=tuple(stored['design']),
        response=stored['response'],
        factors=tuple(stored['factors']),
        levels={column: tuple(levels) for column, levels in stored['levels'].items()},
        scales={
            regime: {column: Scale(**scale) for column, scale in columns.items()}
            for regime, columns in stored['scales'].items()
        },
        dropped_share=stored['dropped_share'],
        trials=stored['trials'],
        family=stored['family'],
        link=stored['link'],
        prior={
            name: Prior(prior['distribution'], tuple(prior['parameters']))
            for name, prior in stored['prior'].items()
        },
        parameters=tuple(stored['parameters']),
        correlations={factor: tuple(names) for factor, names in stored['correlations'].items()},
        contract=stored['contract'],
    )
    if contractHash(problem) != stored['hash']:
        raise ValueError(f'{id}: the files in {dir} do not match their contract hash; rebuild them')
    return problem


def _problemDir(cache: Path, id: str) -> Path:
    """Named by the id's sha256: an object name may hold `/`, `!`, commas and spaces, and the
    JSON carries the id itself."""
    return Path(cache) / 'problems' / hashlib.sha256(id.encode()).hexdigest()[:16]


# =====================================================================================
# the record and the contract hash
# =====================================================================================
def _record(problem: Problem) -> dict:
    """Every field but the table, as JSON values: a numpy level as its Python number."""
    values = {f.name: getattr(problem, f.name) for f in fields(Problem) if f.name != 'table'}
    return json.loads(json.dumps(values, default=_jsonValue))


def _jsonValue(value: Scale | Prior | np.generic) -> dict | int | float:
    if isinstance(value, np.generic):
        return value.item()
    return asdict(value)


def contractHash(problem: Problem) -> str:
    """sha256 over the record with sorted keys, then every column in table order as its name,
    dtype and little-endian bytes, floats as float64 (ADR 0001, amended 2026-10-09); the record
    carries the contract version."""
    canonical = json.dumps(_record(problem), sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(canonical.encode())
    for name, column in problem.table.items():
        dtype, values = _columnBytes(column)
        digest.update(f'{name}\0{dtype}\0'.encode())
        digest.update(values)
    return digest.hexdigest()


def _columnBytes(column: pd.Series) -> tuple[str, bytes]:
    """A regime column as its codes, its categories in the dtype; a float as float64; an
    integer in its own width."""
    if isinstance(column.dtype, pd.CategoricalDtype):
        categories = ','.join(column.cat.categories)
        codes = column.cat.codes.to_numpy()
        return f'category[{categories}]', codes.astype(codes.dtype.newbyteorder('<')).tobytes()
    if pd.api.types.is_float_dtype(column.dtype):
        return 'float64', column.to_numpy(dtype='<f8').tobytes()
    values = column.to_numpy()
    return str(values.dtype), values.astype(values.dtype.newbyteorder('<')).tobytes()
