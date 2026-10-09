# mixedbench

A benchmark of posterior approximation and prediction on real grouped data for generalized
linear mixed models: a registry of documented problems over public grouped datasets, fetched
from pinned sources and never redistributed; a frozen, versioned suite with NUTS reference
posteriors; metrics, tracks and opponent lines.

Under construction: see [`ROADMAP.md`](ROADMAP.md), the decisions in `docs/adr/` and the
vocabulary in [`CONTEXT.md`](CONTEXT.md). The registry comes from the dimension survey in
[`survey/`](survey/README.md), begun in [metabeta-v3](https://github.com/adkipnis/metabeta-v3).

## Install

```
pip install git+https://github.com/adkipnis/mixedbench
```

No R is needed: every registry object loads in Python ([ADR 0003](docs/adr/0003-fetch-only.md)).

## Loading one object

```python
from pathlib import Path

import pandas as pd
from mixedbench import registry
from mixedbench.datasets import Loader

rows = pd.read_csv(registry.path('registry.csv'))
row = rows.set_index('object').loc['sleepstudy']  # its documented model: row['formula']

# downloads land in cache/; only the object's file is fetched and checked against its sha256
loader = Loader(Path('cache'), manifest=registry.manifest())
sleepstudy = loader.load(registry.sources()[row['source']], 'sleepstudy')
```

## Loading one problem

A problem is a registry row's documented model on its table, named
`<source>/<object>/<model_index>`; materialised once, it loads from its files alone.

```python
from mixedbench.contract import Problem, load, materialise

[row] = [row for row in registry.rows() if row.source == 'lme4' and row.object == 'sleepstudy']
table = loader.load(registry.sources()[row.source], row.object, row.types)
materialise(Problem.build(row, table), Path('cache'))  # returns the contract hash

# no loader and no network from here on: the table, the column roles, the prior, the scales
problem = load(Path('cache'), 'lme4/sleepstudy/1')
```

## The suite files

- [`suite/1.1/candidates.csv`](suite/1.1/candidates.csv): the problems admitted to suite 1.1
  with their contract hashes, written by `suite/admit.py`.
- [`suite/1.1/refused.csv`](suite/1.1/refused.csv): the rows left out, each with its reason.
- The registry keeps every row; the suite records why a row is out
  ([ADR 0002](docs/adr/0002-registry-suite-versioning-licences.md)).

## The registry files

- The package carries the registry files of the survey's
  [Files table](survey/README.md#files), without the untracked `help/` and `cache/`.
- `mixedbench.registry.path(name)` returns the installed path of one, `path()` their
  directory.
- `manifest.csv` names the file each object loads from, with its sha256 and size.
- In this repository they live in [`registry/`](registry/), written by `survey/merge.py`
  only; start with [`SUMMARY.md`](registry/SUMMARY.md).
