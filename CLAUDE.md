# CLAUDE.md

**mixedbench**: a benchmark of posterior approximation and prediction on real grouped data for
generalized linear mixed models (GLMMs). A **registry** of documented problems over public
grouped datasets, fetched from pinned sources with checksums and never redistributed; a frozen,
versioned **suite** with NUTS reference posteriors; metrics, tracks and opponent lines. Born
2026-10-08 from the dimension survey of metabeta-v3 (`packages/glmm/surveys/dimensions`, 712
rows over 642 datasets); its loader and survey pipeline move here with history. metabeta
(`~/Code/metabeta-v3`) is a consumer of this package and is never imported.

Read [`CONTEXT.md`](CONTEXT.md) for vocabulary, `docs/adr/` for every decision with lock-in
(0001 the contract, 0002 registry versus suite, 0003 fetch-only, 0004 the reference sampler,
0005 metrics, tracks and opponents) and [`ROADMAP.md`](ROADMAP.md) for build order.

## Layout

```
pyproject.toml          distribution mixedbench, MIT; registry, suite and references CC BY 4.0
src/mixedbench/
  datasets/             the loader: pinned CRAN, git or url source in, typed DataFrames out
  contract/             a registry row and its table -> a Problem (ADR 0001)
  registry/, suite/     readers of the files below; suite admission; problem ids
  references/           the brms/cmdstanr runner, ladder, bar and draw files (ADR 0004)
  metrics/, tracks/     posterior, predictive and oracle tracks, opponent lines (ADR 0005)
registry/               sources.yaml, registry.csv, excluded.csv, dimensions.csv, columns.csv,
                        quantiles.yaml, SUMMARY.md, manifest.csv, help/ and cache/ untracked
survey/                 the pipeline that builds the registry: pull, merge, measure, summarise,
                        shards/, prompts/; merge.py is the only writer of registry/
suite/<version>/        problems.csv, contract hash, diagnostics per problem; draws on the
                        Hugging Face Hub, a Zenodo DOI per release
tests/                  mirrors src/; survey/tests run by hand
docs/adr/, lab/, experiments/
```

- Nothing in `registry/` is edited by hand; agents write shards, `merge.py` merges.
- A released suite is immutable: its membership, contract hash and references never change.
  A contract change is a new suite version, never a recomputation.
- No R in the loader: every registry object loads in Python (ADR 0003). R, brms and cmdstanr
  are needed only to compute references (the `references` extra), never to use the suite.
- The envelope docs of metabeta cite this repository's `SUMMARY.md` and `quantiles.yaml` by
  version; a change to an axis name or a tier breaks their contract test.

## Tooling

- Python 3.14 via `uv` only: `uv sync --extra references` for the runner stack (brms and
  cmdstanr called in an R subprocess; the runner ticket fixes the mechanics), `uv run` for
  everything else. Formatter `ruff format`, tests `pytest`. Run commands from the repository
  root, without `cd`.
- CI (GitHub Actions): per pull request three operating systems × a seeded 20-problem
  subset; weekly a full fetch on Ubuntu with checksum verification as the link-rot detector;
  at release a full fetch on three operating systems.
- Ask before adding a heavyweight dependency.
- Reference runs are CPU work on the cluster, one problem per job, never GPU.

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
- Linear code: a method is the list of steps it takes, one after another, in the order a
  reader would describe them. A step with its own `if` ladder or loop becomes its own
  method. No `for`/`else`, no `while True` with exits inside, no generator-and-`next`
  searches; a plain loop with an explicit check after it.
- A conditional expression (`a if c else b`) only when the whole line stays short; otherwise
  an `if`/`else` block. Lookup tables are literal dicts or `if` chains, never built from
  `dict.fromkeys`, `|` merges or comprehensions.
- A helper used by one class only is a static method of that class.
- Guard `argparse` blocks with `# fmt: off` / `# fmt: on`.
- File layout: banner comments split a file into sections (`# ====` for globals / classes /
  main, `# ----` for subsections). One pipeline class per script, steps as methods, instead
  of many free functions. A recipe-style `__main__` block instantiates it and reads as the
  run's table of contents.
- Class layout: public methods first, then the private steps in the order the pipeline
  runs them, under a `# ----` banner that names the pipeline, so the class reads top to
  bottom.

### Arrays

- Annotate shapes inline (`# (S, P)` for S draws of P parameters), never mutate a reused
  array in place. Vectorise with broadcasting and advanced indexing, not loops. Draw files
  are parquet with named columns on the standardised scale.

### Tests

- Test-driven: use the `tdd` skill. Agree the seams, write the failing test, then the
  minimal code. Unit tests for the contract (coding, standardisation, splits, the hash),
  the metrics against known distributions, the loader's readers on tiny fixtures;
  `hypothesis` for property tests. A test that fetches a source is marked `network` and
  runs only in the CI matrix.
- Tests live in `tests/`, mirroring `src/`. Each test says in one or two sentences why it
  exists, unless painfully obvious. Bind the object under test, then call it; small named
  helpers instead of lambdas and repeated comprehensions.
- No coverage gate.

### Lab notes versus experiments

- `lab/`: documented experimentation on small design choices (C2ST versus MMD, the
  classifier for C2ST). One folder per note, `YYYY-MM-DD-slug/`, a notebook committed with
  outputs plus any PDFs, indexed in `lab/README.md` with the decision taken. The package
  never imports from `lab/`.
- `experiments/`: rerunnable scripted studies (the opponent lines, the predictive track)
  that feed the paper. Rerun with flags; never one-off.

### Design

Directives after Ousterhout, *A Philosophy of Software Design*. Complexity is anything
that makes code harder to understand or change; it accrues one small edit at a time.

- Deep modules: a small interface hiding a lot of functionality. A class or function
  whose interface is as complex as its implementation is a red flag; fold it into its
  caller or callee.
- Information hiding: each module owns one design decision (a file format, the draw
  layout, the contract's coding rule) that no other module depends on. Split code by
  what it knows, not by the order it runs in.
- Different layer, different abstraction: a method that forwards its arguments unchanged
  adds nothing; call the target directly.
- Pull complexity downwards: the module absorbs the awkward case so every caller stays
  simple. A fixed sensible behaviour beats a new config parameter.
- Define errors out of existence: shape the interface so the invalid case cannot arise
  (accept the empty set, validate once at construction). What remains fails loudly: no
  fallbacks, no defensive `try`/`except`, no speculative generality. Branch only for
  cases observed on real inputs; add the next branch when use hits it.
- Design it twice: for a non-trivial interface, name two candidate designs and why one
  wins before writing code.
- Obvious over clever: code you write, or code I ask you to review or rewrite, takes the
  simplest form a reader guesses right on first read. If 200 lines could be 50, rewrite
  them.
- Docstrings only for non-obvious functionality or architectural decisions, one or two
  lines; detail goes into inline why-comments. Comments cite sources (paper link,
  equation number).

### Changing code

- Smallest change that solves the problem and meets the Design bar, no unrequested
  extras. Leave adjacent code, comments and formatting untouched.
- Reproducing external code: cite the source in the docstring; copy verbatim or import
  and wrap. If the original is needlessly complex, write a simplified version and test
  that behaviour is identical up to numeric noise.
- Prefer writing .py or .sh scripts to execute tasks, if (a) the task is a repetitive one
  or (b) the task is error prone when directly performed by a Claude agent.

## Data and compute

- Prototyping: MacBook Air M3, 24 GB RAM. Cluster: CPU nodes for the reference runs, one
  problem per job, a 12-hour cap per problem. Stream or lazily load data that would not
  fit. Suggest cluster commands only when the next step clearly needs the cluster.
- Never overwrite raw data; the cache under `registry/cache/` is rebuilt from pins, never
  edited. Never silently change the contract, a split seed, a pin or a released suite.
- Figures: save as PDF, not PNG/JPG; never rasterise a PDF.

## Working with me

- Your responses should be maximally human-readable and concise.
- When you write a long response nonetheless, preface it with a TL;DR.
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
  local paths; my verdicts come back as bullets per row and are recorded in the survey's
  README.

## Agent skills

### Funnel

Per roadmap item: `/grill-me` (decision only) or `/grill-with-docs` (decision that changes
`CONTEXT.md` or needs an ADR), then `/to-spec`, `/to-tickets` only if the spec spans
several sessions, then `/tdd` or `/implement` per ticket, then tick the `ROADMAP.md`. One
funnel stage per session.

### Issue tracker

Specs and tickets are GitHub Issues on this repo, via `gh`, one area label per issue
(`registry`, `suite`, `references`, `tracks`, `paper`).

### Domain docs

Single context: `CONTEXT.md` at the root, `docs/adr/` beside it. Use the glossary's terms in
issue titles, test names and proposals; flag any contradiction with an ADR instead of
silently overriding it. The paper's source lives in `~/LaTeX/mixedbench`, private, with
every number generated from this repository's files at a pinned commit.
