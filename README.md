# mixedbench

A benchmark of posterior approximation and prediction on real grouped data for generalized
linear mixed models: a registry of documented problems over public grouped datasets, fetched
from pinned sources and never redistributed; a frozen, versioned suite with NUTS reference
posteriors; metrics, tracks and opponent lines.

Under construction: see [`ROADMAP.md`](ROADMAP.md), the decisions in `docs/adr/` and the
vocabulary in [`CONTEXT.md`](CONTEXT.md). The registry comes from the dimension survey of
[metabeta-v3](https://github.com/adkipnis/metabeta-v3) (`packages/glmm/surveys/dimensions`).

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

## The registry files

The package carries the eight registry files; `mixedbench.registry.path(name)` returns the
installed path of one (`sources.yaml`, `registry.csv`, `excluded.csv`, `dimensions.csv`,
`columns.csv`, `quantiles.yaml`, `SUMMARY.md`, `manifest.csv`) and `path()` their directory;
`manifest.csv` names the file each object loads from, with its sha256 and size. In this repository
they live in [`registry/`](registry/), written by `survey/merge.py` only; start with
[`SUMMARY.md`](registry/SUMMARY.md).
