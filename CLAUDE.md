# CLAUDE.md

**mixedbench**: see [`README.md`](README.md). metabeta (`~/Code/metabeta-v3`) consumes this
package and is never imported. Read [`CONTEXT.md`](CONTEXT.md) for vocabulary, `docs/adr/` for
every decision with lock-in and [`ROADMAP.md`](ROADMAP.md) for build order.

## Layout

```
pyproject.toml          distribution mixedbench, MIT; registry, suite and references CC BY 4.0
src/mixedbench/
  datasets/             the loader: pinned CRAN, git or url source in, typed DataFrames out
  registry/             paths and readers of the registry files
registry/               the census files the package ships; help/ and cache/ untracked
survey/                 the pipeline that builds registry/ (survey/README.md); archive/ finished
tests/                  mirrors src/; survey/tests run by hand
docs/adr/               the decisions
```

Planned ([`ROADMAP.md`](ROADMAP.md)): `contract/`, `suite/`, `references/`, `metrics/` and
`tracks/` in `src/mixedbench/`; `suite/<version>/`, `lab/` and `experiments/` at the root.

- Nothing in `registry/` is edited by hand; agents write shards, `merge.py` merges.
- A released suite is immutable: its membership, contract hash and references never change.
  A contract change is a new suite version, never a recomputation.
- No R in the loader (ADR 0003): R, brms and cmdstanr only compute references; using the
  suite never needs them.
- The envelope docs of metabeta cite this repository's `SUMMARY.md` and `quantiles.yaml` by
  version; a change to an axis name or a tier breaks their contract test.

## Tooling

- Python 3.14 via `uv` only: `uv run` for everything, `uv sync --extra references` for the
  reference runner. `ruff format`, `pytest`. Run commands from the repository root, without
  `cd`.
- CI: GitHub Actions on the matrix of ADR 0003.
- Ask before adding a heavyweight dependency.

## Code

### Conventions

- Absolute internal imports (`from mixedbench.contract import x`).
- `PascalCase` classes, `camelCase` functions/methods, `snake_case` variables,
  `UPPER_SNAKE_CASE` constants.
- Modern typing: `X | Y`, built-in generics, `from __future__ import annotations` (Python
  3.11 evaluates annotations eagerly, and `-> Row` inside `Row` needs it).
  `Literal[...]` for an argument with a fixed set of options, a type alias when the same
  `Literal` repeats. Config models are Pydantic. f-strings.
- Bind a long inline expression to a variable with a self-explanatory name on the line
  before it. One statement per line. Directory variables are `dir`, not `folder`; a
  DataFrame is a `table` (CONTEXT.md's word), several by name `tables`, never `df` or `frame`.
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
  `CONTRIBUTING.md` map's), optionally a short paragraph on how (its high-level decisions in
  plain words, the details left to the functions' docstrings), then a `pipeline:` section:
  the input on its own line, then one `-> result` line per step with the function that does
  it in a column on the right.
- File layout: banners split a file (`# ====` for globals / classes / main, `# ----` for
  subsections), each named in words a new reader understands and followed by one comment
  line on why the section exists, unless a class docstring right below says it. Comments
  start in lower case; docstrings are capitalised sentences, their lines broken at sentence
  or clause boundaries, not at the column limit. One pipeline class per script, steps as
  methods; a recipe-style `__main__` instantiates it and reads as the run's table of contents.
- Class layout: public methods first, then the private steps in pipeline order under a
  `# ----` banner naming the pipeline by its arrows alone (`# url -> archive -> tree`).

### Arrays

- Annotate shapes inline (`# (S, P)` for S draws of P parameters), never mutate a reused
  array in place. Vectorise with broadcasting and advanced indexing, not loops. Draw files
  follow [ADR 0004](docs/adr/0004-reference-sampler.md).

### Tests

- Test-driven with the `tdd` skill: agree the seams, write the failing test, then the
  minimal code; `hypothesis` for property tests. A test that fetches a source is marked
  `network` and runs only in CI.
- Tests live in `tests/`, mirroring `src/`. Each test says in one or two sentences why it
  exists, unless painfully obvious. Bind the object under test, then call it; small named
  helpers instead of lambdas and repeated comprehensions.
- No coverage gate.

### Lab notes versus experiments

- `lab/`: a small design choice per `YYYY-MM-DD-slug/` folder, its notebook committed with
  outputs, indexed in `lab/README.md` with the decision; never imported.
- `experiments/`: rerunnable scripted studies that feed the paper.

### Design

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

### Changing code

- Smallest change that solves the problem and meets the Design bar, no unrequested
  extras. Leave adjacent code, comments and formatting untouched.
- Reproducing external code: cite the source in the docstring; copy verbatim or import
  and wrap. If the original is needlessly complex, write a simplified version and test
  that behaviour is identical up to numeric noise.
- Write a .py or .sh script for a task that repeats or that an agent does error-prone by
  hand.

## Docs

The same bar as code: simplicity and a linear read, for every Markdown file.

- Short bullets, the essentials first, detail in appendices or a linked file.
- One home per fact; elsewhere a link to it. A count lives in a generated file (`SUMMARY.md`),
  never typed into prose.
- A living rule sits with the method it governs; the record of how it was decided goes to a
  dated history (`survey/HISTORY.md`).
- Issue numbers of metabeta-v3 carry the prefix `m3#`.

## Data and compute

- Prototyping: MacBook Air M3, 24 GB RAM. Reference runs go to the cluster's CPU nodes, never
  GPU, one problem per job, within the compute cap of
  [ADR 0002](docs/adr/0002-registry-suite-versioning-licences.md). Stream or lazily load data
  that would not fit. Suggest cluster commands only when the next step clearly needs them.
- Never overwrite raw data; the cache under `registry/cache/` is rebuilt from pins, never
  edited. Never silently change the contract, a split seed, a pin or a released suite.
- Figures: save as PDF, not PNG/JPG; never rasterise a PDF.

## Working with me

- Responses maximally human-readable and concise; a long one closes with a TL;DR.
- State assumptions for routine calls. When readings lead to materially different work,
  present at most four options with a recommendation; if still unclear, stop and ask.
- Propose a short plan before non-trivial edits.
- Push back when I am wrong: one sentence, then the reasoning.
- Spell out every acronym at its first use in a session: "generalized linear mixed model
  (GLMM)", then GLMM.
- Report in order: what you did, the result, what you did not verify, the next step.
- Commit each file separately, unless a small bundled change happened in multiple files.
- Commit messages end with the body text itself: no `Co-Authored-By` or generated-with
  trailers.
- Rows handed to me for a spot check carry the source's page and download URLs, never
  local paths; my verdicts come back as bullets per row and are recorded unchanged in
  `survey/VERDICTS.md`.

## Agent skills

### Funnel

Per roadmap item, one stage per session: `/grill-me` (a decision) or `/grill-with-docs` (one
that changes `CONTEXT.md` or needs an ADR); `/to-spec`; `/to-tickets` only if the spec spans
several sessions; `/tdd` or `/implement` per ticket; tick `ROADMAP.md`. A spec's ticket table
gives per ticket the skill, the model (Sonnet 5.5, Opus 5.5 or Fable 5.1) and the expected
tokens.

### Issue tracker

Specs and tickets are GitHub Issues on this repo, via `gh`, one area label per issue
(`registry`, `suite`, `references`, `tracks`, `paper`). From roadmap item 3 on, each spec
opens its own branch off `main`; its tickets commit there, and the branch is merged into
`main` when the spec issue closes.

### Domain docs

Use the glossary's terms in issue titles, test names and proposals; flag a contradiction with
an ADR instead of overriding it. The paper's private source: [`ROADMAP.md`](ROADMAP.md) item 8.
