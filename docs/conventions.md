# Conventions

The rules a pull request is reviewed against. The words are [`CONTEXT.md`](../CONTEXT.md)'s;
the reasons behind the larger rules are in the [ADRs](adr).

## Tooling

- Python 3.14 through `uv` only, every command from the repository root.
  `uv sync --extra references` adds the reference runner.
- `ruff format` and `pytest`, run by CI on the matrix of [ADR 0003](adr/0003-fetch-only.md).
- Open an issue before adding a heavyweight dependency.

## Modules

Each module owns one design decision that no other module depends on.

| module | owns | imported by |
|---|---|---|
| `registry/row.py` | how a `registry.csv` row is written and read; nothing else parses a cell | `registry`, `contract/problem.py`, `suite`, `suite/admit.py`, the survey |
| `registry/__init__.py` | the installed registry files as objects; `Tables` from a row to its typed table | `suite`, `suite/admit.py`, the survey |
| `datasets/loader.py` | a pinned source to tables: download, checksum on every load, cache, declared column types | `registry`, the survey |
| `datasets/readers.py` | the file formats, a class per format family, and which files are data | `loader.py`, `survey/help.py` |
| `datasets/deparse.py` | base R's `data/*.R` files, read without R | `readers.py` |
| `contract/problem.py` | the contract's rules: typing, coding, family, prior, splits, scales, parameter names | `contract`, through it `suite`, `suite/admit.py` and the survey |
| `contract/materialised.py` | a problem's files on disk and the contract hash over them | `contract`, through it `suite` and `suite/admit.py` |
| `suite/__init__.py` | a suite's problems by id: built and materialised on first use, checked against the suite's list in the wheel | the user |
| `suite/admit.py` | the admission of suite 1.1 and its hand decisions; writes `suite/1.1/` | run as a script |
| `references/handoff.py` | what passes between a problem and `run.R`: the aliased table, the model and a level's settings out; the draws under the contract's names and the diagnostics back | `references` |
| `references/__init__.py` | a problem's reference run: the pinned R stack, the ladder, the bar and the cap, the run's directory and its record | `suite/drive.py` |
| `suite/drive.py` | suite 1.1's reference runs: one candidate by id or index, every record collected into `references.csv` | run as a script, by `suite/drive.sbatch` |

## Design

After Ousterhout, *A Philosophy of Software Design*: complexity is anything that makes code
harder to understand or change.

- **Deep modules.** A small interface over much functionality; an interface as complex as its
  implementation folds into its caller or callee.
- **Information hiding.** Split code by what it knows, not by the order it runs in.
- **No pass-throughs.** A method that forwards its arguments unchanged adds nothing; call the
  target directly.
- **Pull complexity down.** The module absorbs the awkward case so its callers stay simple. A
  fixed sensible behaviour beats a new config parameter.
- **Define errors out of existence.** Shape the interface so the invalid case cannot arise
  (accept the empty set, validate once). The rest fails loudly: no fallbacks, no defensive
  `try`/`except`, no branch for a case not seen on real inputs.
- **Design it twice.** For a non-trivial interface, name two designs and why one wins before
  writing code.
- **Obvious over clever.** The simplest form a reader guesses right on first read.

## Changing code

- Code taken from elsewhere cites its source and is copied verbatim or imported and wrapped.
  A simplified rewrite comes with a test that it matches the original up to numeric noise.
- A task that repeats, or is error-prone by hand, gets a script.

## Names

- British spelling (`standardised`, `licence`), except where an outside standard fixes a
  name: `LICENSE`, `license` in `pyproject.toml`, R's and pandas's own names.
- A module is one lowercase word. A package's `__init__.py` lists its public names in
  `__all__`.
- `PascalCase` for classes and `Literal` aliases, `camelCase` for functions and methods,
  `snake_case` for variables and for fields that mirror a registry column, `UPPER_SNAKE_CASE`
  for constants.
- A directory is `dir`, not `folder`. A DataFrame is a `table`, several are `tables`, never
  `df` or `frame`.
- A leading `_` marks a pipeline step and anything no other module imports.
- Tests live in `tests/<package>/test_<module>.py`, each named as a sentence
  (`test_<what_holds>`), with fixtures in `tests/<package>/fixtures/`.
- Other names have one home each: registry columns in the
  [file contracts](../survey/README.md#file-contracts); problem ids in `CONTEXT.md`; table
  columns and parameter names in `contract/problem.py`; the cache layout in `loader.py` and
  `materialised.py`; the draw files' directory in `references/__init__.py`, their names and
  columns in `references/handoff.py`; versions and suite folders in
  [ADR 0002](adr/0002-registry-suite-versioning-licences.md); mirror and archive tags in the
  [survey README](../survey/README.md).

## Code

- Absolute imports: `from mixedbench.contract import x`.
- Modern typing: `X | Y`, built-in generics, `from __future__ import annotations`.
  `Literal[...]` for an argument with a fixed set of options, a type alias once it repeats.
  Config models are Pydantic.
- f-strings, one statement per line, a long expression named on the line before.
- A method lists its steps in the order you would describe them; a step with its own `if`
  ladder or loop becomes a method. A search is a plain loop with an explicit check after it,
  not `for`/`else`, `while True` or `next()` on a generator.
- `a if c else b` only on a short line. Lookup tables are literal dicts or `if` chains, not
  built with comprehensions, `dict.fromkeys` or `|`.
- A class per concept a reader should hold apart (a format family, a pipeline), static
  methods where it holds no state. A helper used by one class lives on it; module functions
  are for what spans classes.
- Arrays: annotate shapes inline (`# (S, P)` for S draws of P parameters), vectorise instead
  of looping, never mutate a reused array in place. Draw files follow
  [ADR 0004](adr/0004-reference-sampler.md).
- Wrap `argparse` blocks in `# fmt: off` / `# fmt: on`.

## File layout

```python
"""loader.py defines how a pinned source becomes typed tables and where it is cached.

pipeline:
---------
a pinned Source
-> the download from the first URL that answers (verified)     _urls, _download
-> its tree (the source's files on disk)                       tree
"""

# =====================================================================================
# where sources are fetched
# =====================================================================================
# the hosts behind every pin and the default fetch.
```

- The module docstring: one sentence on what the module defines, optionally a short paragraph
  on how, then the pipeline, one `-> result` line per step with its function on the right.
  Who imports the module is the [map](#modules)'s.
- `# ====` banners separate globals, classes and main, `# ----` banners subsections. Each is
  named in plain words, with one comment line on why the section exists unless a class
  docstring below says it.
- One pipeline class per module: public methods first, then its steps in run order under a
  `# ----` banner naming the pipeline (`url -> archive -> tree -> files -> tables`).
- A script's `__main__` creates its pipeline class and reads as the run's table of contents.

## Comments and docstrings

- Comments start in lower case; docstrings are capitalised sentences. Break the lines of both
  at sentence or clause boundaries, not at the column limit.
- Short, plain sentences, one idea each, with a subject and a verb. A docstring starts with
  what the function does or returns.
- A docstring only where the behaviour or design is not obvious: one or two plain sentences.
  Detail goes into inline comments that say why and cite sources (a paper, an equation).
- A comment explains the code, not its history: the case behind a rule goes to the test that
  pins it, a definition to `CONTEXT.md`, how it was decided to a dated history
  (`survey/HISTORY.md`).
- Code in `src/` and `suite/` states its rules without citing an ADR; the ADR keeps the
  reason. A string written into a released suite file stays as released.

## Tests

- Test first: the failing test, then the minimal code. `hypothesis`
  for property tests.
- A test that downloads a source is marked `network` and runs only in CI.
- Each test says in a sentence or two why it exists, unless obvious. Bind the object under
  test, then call it; small named helpers, not lambdas.
- No coverage gate.

## Docs

Markdown meets the same bar as code: simple, and read top to bottom.

- Short bullets, the essentials first, detail in an appendix or a linked file.
- One home per fact, links everywhere else; a living rule sits with the method it governs.
  Counts live in generated files (`SUMMARY.md`), never in prose; the one exception, the
  README's dataset count, is pinned by an offline test against `quantiles.yaml`.
- `README.md` is for users and fits one screen: badges, a short what and why, install, one
  quickstart box, contents, contributing, citing, licence. Its links are absolute to `main`,
  so PyPI renders them.

## Data

- A released suite is immutable: its membership, contract hash and references never change.
  A contract change is a new suite version, never a recomputation.
- Never overwrite raw data. The cache under `registry/cache/` is rebuilt from pins, never
  edited.
- Stream or lazily load data that would not fit in memory.
- Figures are PDFs, never rasterised.

## Lab notes and experiments

- `lab/YYYY-MM-DD-slug/`: one small design choice, its notebook committed with outputs and
  indexed in `lab/README.md` with the decision. Never imported.
- `experiments/`: rerunnable scripted studies that feed the paper.
