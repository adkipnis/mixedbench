# CLAUDE.md

**mixedbench**: a benchmark of posterior approximation and prediction on real grouped data for
generalized linear mixed models (GLMMs). A **registry** of documented problems over public
grouped datasets, fetched from pinned sources with checksums and never redistributed; a frozen,
versioned **suite** with NUTS reference posteriors; metrics, tracks and opponent lines. Born
2026-10-08 from metabeta-v3's dimension survey, whose loader and pipeline moved here with
history. metabeta (`~/Code/metabeta-v3`) consumes this package and is never imported.

Read [`CONTEXT.md`](CONTEXT.md) for vocabulary, `docs/adr/` for every decision with lock-in
(0001 the contract, 0002 registry versus suite, 0003 fetch-only, 0004 the reference sampler,
0005 metrics, tracks and opponents) and [`ROADMAP.md`](ROADMAP.md) for build order.

## Layout

```
pyproject.toml          distribution mixedbench, MIT; registry, suite and references CC BY 4.0
src/mixedbench/
  datasets/             the loader: pinned CRAN, git or url source in, typed DataFrames out
  registry/             paths and readers of the registry files
  contract/             planned: a registry row and its table -> a Problem (ADR 0001)
  suite/                planned: suite admission; problem ids
  references/           planned: the brms/cmdstanr runner, ladder, bar and draw files (ADR 0004)
  metrics/, tracks/     planned: posterior, predictive and oracle tracks, opponent lines (ADR 0005)
registry/               the census files the package ships; help/ and cache/ untracked
survey/                 the pipeline that builds registry/ (survey/README.md); archive/ finished
suite/<version>/        planned: problems.csv, contract hash, diagnostics per problem
tests/                  mirrors src/; survey/tests run by hand
docs/adr/               lab/ and experiments/ planned
```

- Nothing in `registry/` is edited by hand; agents write shards, `merge.py` merges.
- A released suite is immutable: its membership, contract hash and references never change.
  A contract change is a new suite version, never a recomputation.
- No R in the loader: every registry object loads in Python (ADR 0003). R, brms and cmdstanr
  are needed only to compute references (the `references` extra), never to use the suite.
- The envelope docs of metabeta cite this repository's `SUMMARY.md` and `quantiles.yaml` by
  version; a change to an axis name or a tier breaks their contract test.

## Tooling

- Python 3.14 via `uv` only: `uv run` for everything, `uv sync --extra references` for the
  runner stack (brms and cmdstanr in an R subprocess). `ruff format`, `pytest`. Run commands
  from the repository root, without `cd`.
- CI: GitHub Actions on the matrix of ADR 0003.
- Ask before adding a heavyweight dependency.

## Code

### Conventions

- Absolute internal imports (`from mixedbench.contract import x`).
- `PascalCase` classes, `camelCase` functions/methods, `snake_case` variables,
  `UPPER_SNAKE_CASE` constants.
- Modern typing: `X | Y`, built-in generics, `from __future__ import annotations`.
  `Literal[...]` for an argument with a fixed set of options, a type alias when the same
  `Literal` repeats. Config models are Pydantic. f-strings.
- Bind a long inline expression to a variable with a self-explanatory name on the line
  before it. One statement per line. Directory variables are `dir`, not `folder`.
- Linear code: a method lists its steps in the order a reader would describe them; a step
  with its own `if` ladder or loop becomes its own method. A search is a plain loop with an
  explicit check after it (no `for`/`else`, `while True` with exits, generator-and-`next`).
- A conditional expression (`a if c else b`) only when the whole line stays short; otherwise
  an `if`/`else` block. Lookup tables are literal dicts or `if` chains, never built from
  `dict.fromkeys`, `|` merges or comprehensions.
- A helper used by one class only is a static method of that class.
- Guard `argparse` blocks with `# fmt: off` / `# fmt: on`.
- File layout: banners split a file (`# ====` for globals / classes / main, `# ----` for
  subsections). One pipeline class per script, steps as methods; a recipe-style `__main__`
  instantiates it and reads as the run's table of contents.
- Class layout: public methods first, then the private steps in pipeline order under a
  `# ----` banner naming the pipeline.

### Arrays

- Annotate shapes inline (`# (S, P)` for S draws of P parameters), never mutate a reused
  array in place. Vectorise with broadcasting and advanced indexing, not loops. Draw files
  are parquet with named columns on the standardised scale.

### Tests

- Test-driven with the `tdd` skill: agree the seams, write the failing test, then the
  minimal code. Unit tests for the contract, the metrics against known distributions, the
  readers on tiny fixtures; `hypothesis` for property tests. A test that fetches a source is
  marked `network` and runs only in CI.
- Tests live in `tests/`, mirroring `src/`. Each test says in one or two sentences why it
  exists, unless painfully obvious. Bind the object under test, then call it; small named
  helpers instead of lambdas and repeated comprehensions.
- No coverage gate.

### Lab notes versus experiments

- `lab/`: small design choices (C2ST versus MMD), one `YYYY-MM-DD-slug/` folder per note, a
  notebook committed with outputs, indexed in `lab/README.md` with the decision. The package
  never imports from it.
- `experiments/`: rerunnable scripted studies that feed the paper, rerun with flags.

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
  observed on real inputs.
- Design it twice: for a non-trivial interface, name two candidate designs and why one wins
  before writing code.
- Obvious over clever, in code you write, review or rewrite: the simplest form a reader
  guesses right on first read. If 200 lines could be 50, rewrite them.
- Docstrings only for non-obvious functionality or architectural decisions, one or two
  lines; detail goes into inline why-comments, which cite sources (paper link, equation).

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

- Prototyping: MacBook Air M3, 24 GB RAM. Cluster: reference runs on CPU nodes, never GPU,
  one problem per job, a 12-hour cap per problem. Stream or lazily load data that would not
  fit. Suggest cluster commands only when the next step clearly needs the cluster.
- Never overwrite raw data; the cache under `registry/cache/` is rebuilt from pins, never
  edited. Never silently change the contract, a split seed, a pin or a released suite.
- Figures: save as PDF, not PNG/JPG; never rasterise a PDF.

## Working with me

- Responses maximally human-readable and concise; a long one opens with a TL;DR.
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

`CONTEXT.md` at the root, `docs/adr/` beside it. Use the glossary's terms in issue titles,
test names and proposals; flag a contradiction with an ADR instead of overriding it. The
paper's source is `~/LaTeX/mixedbench`, private, every number generated from this
repository's files at a pinned commit.
