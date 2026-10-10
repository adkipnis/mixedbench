# Contributing to mixedbench

Thank you for your interest. mixedbench is early stage and help is welcome.

## Ways to help

- **A dataset is missing, or a row is wrong.** Open an issue with a link to the dataset and one
  to the documentation that fits its model: a help page, a tutorial or a paper. The registry
  files are written by script, so we add it in the next survey pass.
- **A bug in the loader or the contract.** Open an issue with the smallest example that shows
  it, or a pull request with a failing test and the fix.
- **A method to benchmark.** Scoring arrives with suite 1.1 (see the [roadmap](ROADMAP.md));
  until then, open an issue describing the method.

For anything bigger than a small fix, open an issue before writing code, so we can agree on
the approach first.

## Set up

You need [uv](https://docs.astral.sh/uv/), R is not required.

```
git clone https://github.com/adkipnis/mixedbench
cd mixedbench
uv sync
uv run pytest               # the offline tests, about ten seconds
uv run pytest -m network    # the tests that download sources, as CI runs them
```

## Find your way

```
src/mixedbench/
  registry/     the registry files as Python objects
  datasets/     the loader: a pinned source in, typed tables out
  contract/     the rules that turn a registry row and its table into a problem
registry/       the registry files, written by survey/merge.py
suite/          the admission script and each suite's candidate list
survey/         the pipeline that built the registry
tests/          mirrors src/
docs/adr/       the design decisions and why they were taken
examples/       the demo notebook
```

Each module's docstring says what it defines and how. [`CONTEXT.md`](CONTEXT.md) defines the
words (source, table, registry, contract, problem, suite).

## Pull requests

- Branch off `main`, one change per pull request, linked to its issue.
- Add a test with each change; mark a test that downloads with `@pytest.mark.network`.
- Run `uv run ruff format .` and `uv run pytest`. CI runs the tests on Linux, macOS and Windows.
- Please follow the style [conventions](docs/conventions.md).

Three rules keep results comparable:

- **The contract does not move.** A change in `src/` leaves every contract hash as it is. CI
  checks a sample of `suite/1.1/candidates.csv`; `uv run python suite/admit.py` checks all of
  them (it downloads every source, a few GB), after which `git diff suite/` must be empty. A change that moves a hash is a new
  contract version: discuss it in an issue first.
- **The registry is written by script.** Nothing in `registry/` or `suite/<version>/` is edited
  by hand.
- **No R in the loader.** Every table loads in Python alone; R may only computes reference posteriors.

## Licence

By contributing, you agree that your code is released under [MIT](LICENSE) and your changes to
the registry and suite files under [CC BY 4.0](LICENSE-CC-BY-4.0).
