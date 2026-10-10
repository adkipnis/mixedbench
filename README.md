[![CI](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml)
[![Weekly fetch](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml/badge.svg)](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml)
[![PyPI](https://img.shields.io/pypi/v/mixedbench)](https://pypi.org/project/mixedbench/)
[![Python](https://img.shields.io/pypi/pyversions/mixedbench)](https://pypi.org/project/mixedbench/)
[![Licence](https://img.shields.io/badge/licence-MIT%20%C2%B7%20CC%20BY%204.0-blue)](https://github.com/adkipnis/mixedbench#licence)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)](https://github.com/adkipnis/mixedbench#citing)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/adkipnis/mixedbench/blob/main/examples/demo.ipynb)

# mixedbench

A benchmark of posterior approximation and prediction for generalized linear mixed models
(GLMMs) on real grouped data.

## What and why

- Bayesian methods for GLMMs are each tested on their own few datasets.
- mixedbench lists the documented models of public grouped datasets, each fetched from a
  pinned source.
- One frozen contract turns each into a problem ready to fit; suites add reference posteriors
  to score against, from release 1.1.

## Install

```
pip install mixedbench
```

No R is needed: every registry object loads in Python.

## Quickstart

```python
from pathlib import Path

from mixedbench import registry
from mixedbench.contract import Problem, load, materialise

cache = Path('cache')
[row] = [row for row in registry.rows() if row.id == 'lme4/sleepstudy/1']
table = registry.Tables(cache).load(row)  # fetched from CRAN at its pin
materialise(Problem.build(row, table), cache)
problem = load('lme4/sleepstudy/1', cache)
```

The [demo](https://github.com/adkipnis/mixedbench/blob/main/examples/demo.ipynb) walks the same path with its outputs.

## Contents

- The package `mixedbench`: `registry` (the registry files, summarised in
  [`SUMMARY.md`](https://github.com/adkipnis/mixedbench/blob/main/registry/SUMMARY.md)), `datasets` (the loader) and `contract`
  (`Problem`, `materialise`, `load`).
- [`suite/1.1/candidates.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/candidates.csv): the problems admitted to
  suite 1.1 with their contract hashes;
  [`refused.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/refused.csv): the rows left out, each with its reason.
- [`survey/`](https://github.com/adkipnis/mixedbench/blob/main/survey/README.md): the pipeline that built the registry and its record;
  provenance, not needed to use the package.

## Contributing

The layout, the conventions and the vocabulary are in
[`CONTRIBUTING.md`](https://github.com/adkipnis/mixedbench/blob/main/CONTRIBUTING.md).

## Citing

Cite the release you used: [`CITATION.cff`](https://github.com/adkipnis/mixedbench/blob/main/CITATION.cff), or "Cite this repository" on
GitHub. The Zenodo DOI follows with release 1.0.

## Licence

- Code: [MIT](https://github.com/adkipnis/mixedbench/blob/main/LICENSE). Registry and suite files: [CC BY 4.0](https://github.com/adkipnis/mixedbench/blob/main/LICENSE-CC-BY-4.0).
- The data keep their sources' terms: they are fetched at first use and never redistributed,
  except CC0 files whose host refuses scripts, mirrored with the same checksum.
