"""materialized.py defines a problem's files on disk and the contract hash over them.

A materialized problem is two files under the loader's cache:
`table.parquet` holding the table, `problem.json` the record a table cannot and the contract hash.
Three decisions guide them:
- the files are the interface: `load` needs neither the loader nor the network,
  so a suite user fetches the sources once per machine;
- the hash is over values, not file bytes: a parquet writer's options or version do not move it;
- the hash covers every field and every cell, the contract version among them,
  so `load` refuses files that were edited or are stale.

pipeline:
---------
a built Problem
-> its record, every field but the table as JSON values     _serializeRecord
-> its contract hash                                        contractHash
-> the table as parquet, the record and the hash as JSON    materialize
-> the problem read back, refused if its hash moved         load
-> the hash its files were written with, if any             storedHash
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
# the package's interface to a problem: written once, loaded anywhere
def materialize(problem: Problem, cache: Path) -> str:
    """Write the problem's two files under `cache` and return its contract hash."""
    dir = _locateProblem(problem.id, cache)
    dir.mkdir(parents=True, exist_ok=True)
    problem.table.to_parquet(dir / 'table.parquet', index=False)
    written = contractHash(problem)
    stored = _serializeRecord(problem) | {'hash': written}
    (dir / 'problem.json').write_text(json.dumps(stored, sort_keys=True, indent=2))
    return written


def load(id: str, cache: Path) -> Problem:
    """Raises where the files no longer give the hash they were written with (edited, or stale)."""
    dir = _locateProblem(id, cache)
    stored = json.loads((dir / 'problem.json').read_text())
    problem = Problem(
        id=stored['id'],
        table=pd.read_parquet(dir / 'table.parquet'),
        design=tuple(stored['design']),
        response=stored['response'],
        factors=tuple(stored['factors']),
        levels={column: tuple(levels) for column, levels in stored['levels'].items()},
        scales=_readScales(stored['scales']),
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


def _readScales(stored: dict[str, list[dict]]) -> dict[str, tuple[dict[str, Scale], ...]]:
    """Returns each regime's scales, one dict of `Scale`s per fold."""
    scales = {}
    for regime, folds in stored.items():
        fold_scales = []
        for columns in folds:
            fold_scales.append({column: Scale(**scale) for column, scale in columns.items()})
        scales[regime] = tuple(fold_scales)
    return scales


def storedHash(id: str, cache: Path) -> str | None:
    """None where the problem has no files under `cache`."""
    record = _locateProblem(id, cache) / 'problem.json'
    if not record.exists():
        return None
    return json.loads(record.read_text())['hash']


def _locateProblem(id: str, cache: Path) -> Path:
    """Named by the id's sha256: an object name may hold `/`, `!`, commas and spaces,
    and the JSON carries the id itself."""
    return Path(cache) / 'problems' / hashlib.sha256(id.encode()).hexdigest()[:16]


# =====================================================================================
# the contract hash
# =====================================================================================
# over values, so that a problem is the same whatever wrote its files
def contractHash(problem: Problem) -> str:
    """sha256 over the record with sorted keys,
    then every column in table order as its name, dtype and little-endian bytes."""
    canonical = json.dumps(_serializeRecord(problem), sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(canonical.encode())
    for name, column in problem.table.items():
        dtype, values = _serializeColumn(column)
        digest.update(f'{name}\0{dtype}\0'.encode())
        digest.update(values)
    return digest.hexdigest()


def _serializeRecord(problem: Problem) -> dict:
    """Every field but the table, as JSON values: a numpy level as its Python number."""
    values = {f.name: getattr(problem, f.name) for f in fields(Problem) if f.name != 'table'}
    return json.loads(json.dumps(values, default=_serializeValue))


def _serializeValue(value: Scale | Prior | np.generic) -> dict | int | float:
    if isinstance(value, np.generic):
        return value.item()
    return asdict(value)


def _serializeColumn(column: pd.Series) -> tuple[str, bytes]:
    """Returns a float column as float64, an integer column in its own width."""
    if pd.api.types.is_float_dtype(column.dtype):
        return 'float64', column.to_numpy(dtype='<f8').tobytes()
    values = column.to_numpy()
    return str(values.dtype), values.astype(values.dtype.newbyteorder('<')).tobytes()
