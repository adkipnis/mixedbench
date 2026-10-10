# mixedbench

A benchmark of posterior approximation and prediction for generalized linear mixed models
(GLMMs) on real grouped data: documented models over public datasets, each turned into a
problem ready to fit by one frozen contract.

[![CI](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml)
[![Weekly fetch](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml/badge.svg)](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml)
[![PyPI](https://img.shields.io/pypi/v/mixedbench)](https://pypi.org/project/mixedbench/)
[![Python](https://img.shields.io/pypi/pyversions/mixedbench)](https://pypi.org/project/mixedbench/)
[![Licence](https://img.shields.io/badge/licence-MIT%20%C2%B7%20CC%20BY%204.0-blue)](https://github.com/adkipnis/mixedbench#licence)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)](https://github.com/adkipnis/mixedbench#citing)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/adkipnis/mixedbench/blob/main/examples/demo.ipynb)

[Demo](https://github.com/adkipnis/mixedbench/blob/main/examples/demo.ipynb) ·
[Registry summary](https://github.com/adkipnis/mixedbench/blob/main/registry/SUMMARY.md) ·
[Contributing](https://github.com/adkipnis/mixedbench/blob/main/CONTRIBUTING.md) ·
[Citing](https://github.com/adkipnis/mixedbench#citing)

## What and why

- Bayesian inference methods for GLMMs are hard to compare: each paper tests on its own
  handful of datasets.
- The **registry** lists the documented models of public grouped tables, one row per table and
  model; each table is fetched from a pinned source and checked against its sha256.
- The **contract** turns a row and its table into a **problem**: the design, the response and
  the grouping codes, the family and link, one prior, the held-out splits and the scales, named
  by a hash that is the same on every machine.
- A **suite** is a frozen subset of problems with reference posteriors; suite 1.1 brings the
  references, the metrics and the scores of standard methods
  ([roadmap](https://github.com/adkipnis/mixedbench/blob/main/ROADMAP.md)).

<!-- corpus: written by survey/merge.py from registry/SUMMARY.md -->
**Corpus.** 714 registry rows over 641 datasets and 941 grouping
factors; per tier R 252, T 244, D 104, E 101, O 13. Excluded: 2133 objects (no grouping structure 1164, derived or duplicated table 622, unreadable format 192, not the paper's data 46, simulated data 44, response missing or undocumented 36, time series without replication 28, fewer than two groups 1).
<!-- /corpus -->

## Install

```
pip install mixedbench
```

No R is needed: every registry object loads in Python.

## Quickstart

### Loading one object

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

### Loading one problem

A problem is a registry row's documented model on its table, named
`<source>/<object>/<model_index>`; materialised once, it loads from its files alone.

```python
from mixedbench.contract import Problem, load, materialise

[row] = [row for row in registry.rows() if row.id == 'lme4/sleepstudy/1']
table = registry.Tables(Path('cache')).load(row)  # its `types` declared
materialise(Problem.build(row, table), Path('cache'))  # returns the contract hash

# no loader and no network from here on: the table, the column roles, the prior, the scales
problem = load('lme4/sleepstudy/1', Path('cache'))
```

The [demo](https://github.com/adkipnis/mixedbench/blob/main/examples/demo.ipynb) walks the same path with its outputs.

## Contents

- The package `mixedbench`: `registry` (the registry files and their readers), `datasets` (the
  loader) and `contract` (`Problem`, `materialise`, `load`).
- [`suite/1.1/candidates.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/candidates.csv): the problems admitted to
  suite 1.1 with their contract hashes;
  [`refused.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/refused.csv): the rows left out, each with its reason.
- [`survey/`](https://github.com/adkipnis/mixedbench/blob/main/survey/README.md): the pipeline that built the registry and its record,
  begun in metabeta-v3; provenance, not needed to use the package.

## Data and licences

- The data are fetched from their sources at first use and never redistributed; the one
  exception is CC0 files whose host refuses scripts, mirrored with the same checksum
  ([ADR 0003](https://github.com/adkipnis/mixedbench/blob/main/docs/adr/0003-fetch-only.md)).
- Code: MIT. Registry and suite files: CC BY 4.0. The data: their sources' terms, recorded per
  row in the registry's `licence` column.

## Versioning

- The package version is the registry version: a major bump is a contract change, a minor one
  adds registry rows, a patch fixes metadata.
- A suite is named after the release that freezes it (`suite-1.1`) and never changes; release
  1.0 ships the registry, the contract and the candidate list of suite 1.1, no suite
  ([ADR 0002](https://github.com/adkipnis/mixedbench/blob/main/docs/adr/0002-registry-suite-versioning-licences.md)).

## Contributing

The layout, the conventions and the vocabulary are in
[`CONTRIBUTING.md`](https://github.com/adkipnis/mixedbench/blob/main/CONTRIBUTING.md).

## Citing

Cite the release you used: [`CITATION.cff`](https://github.com/adkipnis/mixedbench/blob/main/CITATION.cff), or "Cite this repository" on
GitHub. The Zenodo DOI follows with release 1.0.

## Licence

The code under the [MIT License](https://github.com/adkipnis/mixedbench/blob/main/LICENSE); the registry and suite files under
[CC BY 4.0](https://github.com/adkipnis/mixedbench/blob/main/LICENSE-CC-BY-4.0).
