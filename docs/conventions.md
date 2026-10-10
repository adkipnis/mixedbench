# Conventions

The rules a pull request is reviewed against. The words are [`CONTEXT.md`](../CONTEXT.md)'s;
why a rule holds is in [`docs/adr/`](adr).

## Modules

Each module owns one design decision that no other module depends on; its docstring states
the decision and its pipeline.

| module | owns | imported by |
|---|---|---|
| `registry/row.py` | how a `registry.csv` row is written and read: dialect, column order, vocabularies, cell grammars; nothing else parses a cell | `registry`, `contract/problem.py`, `suite/admit.py`, the survey |
| `registry/__init__.py` | where the installed registry files are, each file as objects, `Tables` from a row to its typed table | `suite/admit.py`, the survey |
| `datasets/loader.py` | a pinned source to tables: URLs, download, checksum on every load, the cache, a row's declared column types; not the formats | `registry`, the survey |
| `datasets/readers.py` | the file formats, a class per format family, and which files of a tree are data | `loader.py`, `survey/help.py` |
| `datasets/deparse.py` | base R's `data/*.R` files read without R | `readers.py` |
| `contract/problem.py` | the contract's rules: typing, coding, family, prior, splits, scales, parameter names | `contract`, through it `suite/admit.py` and the survey |
| `contract/materialised.py` | a problem's files on disk and the contract hash over them | `contract`, through it `suite/admit.py` |
| `suite/admit.py` | the admission of suite 1.1 and its hand decisions; writes `suite/1.1/` | run as a script |

## Names in code

- A module is one lowercase word. A package's `__init__.py` lists its public names in
  `__all__`.
- `PascalCase` classes and `Literal` aliases, `camelCase` functions and methods, `snake_case`
  variables and the fields that mirror a registry column, `UPPER_SNAKE_CASE` constants.
- A directory variable is `dir`, not `folder`; a DataFrame is a `table`, several by name
  `tables`, never `df` or `frame`.
- One pipeline class per module, its steps as methods in run order under a `# ----` banner
  naming the pipeline (`url -> archive -> tree -> files -> tables`). A step, and anything no
  other module imports, carries a leading `_`.
- Tests: `tests/<package>/test_<module>.py`, a test named as a sentence (`test_<what_holds>`),
  fixtures in `tests/<package>/fixtures/`.

## Names elsewhere

- Registry columns and cell grammars: the [file contracts](../survey/README.md#file-contracts).
- Problem ids: [`CONTEXT.md`](../CONTEXT.md); the materialised table's columns and the
  parameter names: `contract/problem.py`; the cache layout: `loader.py` and `materialised.py`.
- Versions and suite folders: [ADR 0002](adr/0002-registry-suite-versioning-licences.md); the
  mirror and archive tags: the [survey README](../survey/README.md).

## Tooling

- Python 3.14 via `uv` only: `uv run` for everything, `uv sync --extra references` for the
  reference runner. `ruff format`, `pytest`. Run commands from the repository root, without
  `cd`.
- CI: GitHub Actions on the matrix of [ADR 0003](adr/0003-fetch-only.md).
- Open an issue before adding a heavyweight dependency.

## Code

- Absolute internal imports (`from mixedbench.contract import x`).
- Modern typing: `X | Y`, built-in generics, `from __future__ import annotations` (Python
  3.11 evaluates annotations eagerly, and `-> Row` inside `Row` needs it).
  `Literal[...]` for an argument with a fixed set of options, a type alias when the same
  `Literal` repeats. Config models are Pydantic. f-strings.
- Bind a long inline expression to a variable with a self-explanatory name on the line
  before it. One statement per line.
- Linear code: a method lists its steps in the order a reader would describe them; a step
  with its own `if` ladder or loop becomes its own method. A search is a plain loop with an
  explicit check after it (no `for`/`else`, `while True` with exits, generator-and-`next`).
- A conditional expression (`a if c else b`) only when the whole line stays short; otherwise
  an `if`/`else` block. Lookup tables are literal dicts or `if` chains, never built from
  `dict.fromkeys`, `|` merges or comprehensions.
- A class per concept a reader should hold apart (a format family, a pipeline), its methods
  static where it holds no state; module functions only for what spans the classes.
  A helper or constant used by one class only lives on that class: a static method, a class
  attribute.
- Guard `argparse` blocks with `# fmt: off` / `# fmt: on`.
- Module docstring: one sentence on what the module defines (who imports it is the
  [module map](#modules)'s), optionally a short paragraph on how (its high-level decisions in
  plain words, the details left to the functions' docstrings), then a `pipeline:` section:
  the input on its own line, then one `-> result` line per step with the function that does
  it in a column on the right.
- File layout: banners split a file (`# ====` for globals / classes / main, `# ----` for
  subsections), each named in words a new reader understands and followed by one comment
  line on why the section exists, unless a class docstring right below says it. Comments
  start in lower case; docstrings are capitalised sentences; the lines of both are broken at
  sentence or clause boundaries, not at the column limit. A script's recipe-style `__main__`
  instantiates its pipeline class and reads as the run's table of contents.
- Class layout: public methods first, then the private steps in pipeline order under the
  pipeline's banner.

## Arrays

- Annotate shapes inline (`# (S, P)` for S draws of P parameters), never mutate a reused
  array in place. Vectorise with broadcasting and advanced indexing, not loops. Draw files
  follow [ADR 0004](adr/0004-reference-sampler.md).

## Tests

- Test-first: agree the seams, write the failing test, then the minimal code; `hypothesis`
  for property tests. A test that fetches a source is marked `network` and runs only in CI.
- Each test says in one or two sentences why it exists, unless painfully obvious. Bind the
  object under test, then call it; small named helpers instead of lambdas and repeated
  comprehensions.
- No coverage gate.

## Design

Directives after Ousterhout, *A Philosophy of Software Design*: complexity is anything that
makes code harder to understand or change.

- Deep modules: a small interface over much functionality. An interface as complex as its
  implementation is a red flag; fold it into its caller or callee.
- Information hiding: each module owns one design decision (a file format, the draw layout,
  the contract's coding rule) no other module depends on. Split code by what it knows, not
  by the order it runs in.
- Different layer, different abstraction: a method that forwards its arguments unchanged
  adds nothing; call the target directly.
- Pull complexity downwards: the module absorbs the awkward case so callers stay simple. A
  fixed sensible behaviour beats a new config parameter.
- Define errors out of existence: shape the interface so the invalid case cannot arise
  (accept the empty set, validate once at construction). What remains fails loudly: no
  fallbacks, no defensive `try`/`except`, no speculative generality. Branch only for cases
  observed on real inputs; add the next branch when use hits it.
- Design it twice: for a non-trivial interface, name two candidate designs and why one wins
  before writing code.
- Obvious over clever, in code you write, review or rewrite: the simplest form a reader
  guesses right on first read. If 200 lines could be 50, rewrite them.
- Docstrings only for non-obvious functionality or architectural decisions, one or two
  lines: none on a method its name and body already explain, otherwise a plain sentence on
  what is not obvious, never a chain of `;` clauses; detail goes into inline why-comments,
  which cite sources (paper link, equation).
- A comment explains the code, not its bookkeeping: the case that prompted a rule goes to
  the test that pins it, a definition to `CONTEXT.md`, how it was decided to a history.
- Code in `src/` and `suite/` cites no ADR: a comment or docstring states the rule itself,
  the ADR keeps why. A string written into a released suite file stays as released.

## Changing code

- Smallest change that solves the problem and meets the design bar, no unrequested
  extras. Leave adjacent code, comments and formatting untouched.
- Reproducing external code: cite the source in the docstring; copy verbatim or import
  and wrap. If the original is needlessly complex, write a simplified version and test
  that behaviour is identical up to numeric noise.
- Write a .py or .sh script for a task that repeats or that is error-prone by hand.

## Lab notes and experiments

- `lab/`: a small design choice per `YYYY-MM-DD-slug/` folder, its notebook committed with
  outputs, indexed in `lab/README.md` with the decision; never imported.
- `experiments/`: rerunnable scripted studies that feed the paper.

## Docs

The same bar as code: simplicity and a linear read, for every Markdown file.

- Short bullets, the essentials first, detail in appendices or a linked file.
- One home per fact; elsewhere a link to it. A count lives in a generated file (`SUMMARY.md`),
  never typed into prose; the one exception, the README's dataset count, is pinned by an
  offline test against `quantiles.yaml`.
- `README.md` is for users and reads in one screen: badges on top, a short what and why,
  install, one quickstart box, contents, contributing, citing, licence. Links are absolute to
  `main`, so PyPI renders them; decisions, provenance and detail stay one link away.
- A living rule sits with the method it governs; the record of how it was decided goes to a
  dated history (`survey/HISTORY.md`).

## Data

- A released suite is immutable: its membership, contract hash and references never change.
  A contract change is a new suite version, never a recomputation.
- Never overwrite raw data; the cache under `registry/cache/` is rebuilt from pins, never
  edited. Never silently change the contract, a split seed, a pin or a released suite.
- Stream or lazily load data that would not fit in memory.
- Figures: save as PDF, not PNG/JPG; never rasterise a PDF.
