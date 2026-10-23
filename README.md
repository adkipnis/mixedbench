[![Weekly fetch](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml/badge.svg)](https://github.com/adkipnis/mixedbench/actions/workflows/weekly-fetch.yml)
[![CI](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/adkipnis/mixedbench/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mixedbench)](https://pypi.org/project/mixedbench/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23285683.svg)](https://doi.org/10.5281/zenodo.23285683)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/adkipnis/mixedbench/blob/main/examples/demo.ipynb)

# MixedBench

A benchmark of posterior approximation and prediction for generalized linear mixed models
(GLMMs) on real grouped data.

## What and why

- Bayesian methods for GLMMs are hard to compare: each paper and released method tests them on its own few datasets. This benchmark aims to fix that.
- MixedBench lists the documented mixed-effects models of 621 public tabular datasets with grouping structure, each downloaded at a fixed version.
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

## Contributing

Interested in becoming part of `mixedbench`? Check out [`CONTRIBUTING.md`](https://github.com/adkipnis/mixedbench/blob/main/CONTRIBUTING.md).

## Citing

Please cite the release you used: [`CITATION.cff`](https://github.com/adkipnis/mixedbench/blob/main/CITATION.cff), or click "Cite this repository" on
GitHub.

## License

- Code: [Apache-2.0](https://github.com/adkipnis/mixedbench/blob/main/LICENSE). Registry and suite files: [CC BY 4.0](https://github.com/adkipnis/mixedbench/blob/main/docs/LICENSE-CC-BY-4.0).
- The datasets keep their sources' terms and are not redistributed through MixedBench.
