[![CI](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml)
[![Weekly fetch](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml/badge.svg)](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml)
[![PyPI](https://img.shields.io/pypi/v/mixedbench)](https://pypi.org/project/mixedbench/)
[![Python](https://img.shields.io/pypi/pyversions/mixedbench)](https://github.com/adkipnis/mixedbench/blob/main/pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache--2.0%20%C2%B7%20CC%20BY%204.0-blue)](https://github.com/adkipnis/mixedbench#license)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23285683.svg)](https://doi.org/10.5281/zenodo.23285683)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/adkipnis/mixedbench/blob/main/examples/demo.ipynb)

# mixedbench

A benchmark of posterior approximation and prediction for generalized linear mixed models
(GLMMs) on real grouped data.

## What and why

- Bayesian methods for GLMMs are hard to compare: each paper and released method tests them on its own few datasets. This benchmark aims to fix that.
- mixedbench lists the documented mixed-effects models of 637 public tabular datasets with grouping structure, each downloaded at a fixed version.
- A fixed set of rules turns each dataset into an inference problem ready to fit. Results of different methods are comparable.
- From release 1.1, suites add reference posteriors to score against.

## Install

```
pip install mixedbench
```

No R needed: every dataset loads in Python.

## Quickstart

```python
from pathlib import Path
from mixedbench import suite

# fetched from CRAN at its pin and checked against suite 1.1's list; later calls are offline
problem = suite.load('lme4/sleepstudy/1', Path('cache'))
```

Check out the [demo](https://colab.research.google.com/github/adkipnis/mixedbench/blob/main/examples/demo.ipynb) for a friendly introduction.

## Contents

- The package `mixedbench`: `suite` (a problem by its id, in one call), `registry` (the registry files, summarized in
  [`SUMMARY.md`](https://github.com/adkipnis/mixedbench/blob/main/registry/SUMMARY.md)), `datasets` (the loader) and `contract`
  (`Problem`, `materialize`, `load`).
- [`suite/1.1/candidates.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/candidates.csv): the candidate problems of
  suite 1.1 with their contract hashes;
  [`refused.csv`](https://github.com/adkipnis/mixedbench/blob/main/suite/1.1/refused.csv): the rows left out, each with its reason.
- [`survey/`](https://github.com/adkipnis/mixedbench/blob/main/survey/README.md): the pipeline that built the registry and its record;
  provenance, not needed to use the package.

## Planned

- Release 1.1: suite 1.1 with reference posteriors, the metrics that score a method against them, and the scores of standard methods.
- Release 1.2: references for the oracle and predictive tracks, more families, and the retirement of sources that went offline.
- Later: an R loader, an "as published" prior track, and a mirror fallback for sources that go offline.

Progress is tracked in the [issues](https://github.com/adkipnis/mixedbench/issues).

## Contributing

Interested in becoming part of `mixedbench`? Check out [`CONTRIBUTING.md`](https://github.com/adkipnis/mixedbench/blob/main/CONTRIBUTING.md).

## Citing

Please cite the release you used: [`CITATION.cff`](https://github.com/adkipnis/mixedbench/blob/main/CITATION.cff), or click "Cite this repository" on
GitHub. All versions share the DOI [10.5281/zenodo.23285683](https://doi.org/10.5281/zenodo.23285683).

## License

- Code: [Apache-2.0](https://github.com/adkipnis/mixedbench/blob/main/LICENSE). Registry and suite files: [CC BY 4.0](https://github.com/adkipnis/mixedbench/blob/main/docs/LICENSE-CC-BY-4.0).
- The data keep their sources' terms: they are fetched at first use, not redistributed.
