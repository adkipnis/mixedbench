# Contributing

The map of the repository for a contributor. Vocabulary: [`CONTEXT.md`](CONTEXT.md). Every
decision with lock-in: [`docs/adr/`](docs/adr). Build order: [`ROADMAP.md`](ROADMAP.md).

## Layout

### Purpose

mixedbench is a benchmark of posterior approximation and prediction on real grouped data for
generalized linear mixed models (GLMMs). It holds three things. The **registry** is a census of
documented models over public grouped tables, one row per table and model, its dimensions
measured by script; it grows with every survey pass and is never frozen. The **contract** is the
frozen rule set that turns a registry row and its loaded table into a problem: the rows kept,
the coding, the family, the prior, the splits ([ADR 0001](docs/adr/0001-the-contract.md)); a
change to a rule is a new suite, never a recomputation. A **suite** is a frozen, versioned
subset of problems with reference posteriors
([ADR 0002](docs/adr/0002-registry-suite-versioning-licences.md)); release 1.0 ships the
registry, the contract and the candidate list of suite 1.1. Every table is fetched from its
pinned source at first use and verified against its checksum; nothing is redistributed and no R
is needed ([ADR 0003](docs/adr/0003-fetch-only.md)). The survey began in metabeta-v3, which
consumes this package and is never imported by it.

### Blueprint

```
pyproject.toml          distribution mixedbench: the package and the registry files it ships
src/mixedbench/
  registry/             the registry files and the registry row
    __init__.py         the installed files; sources.yaml, manifest.csv and registry.csv as objects
    row.py              the row grammar: dialect, columns, vocabularies, cell grammars
  datasets/             the loader: a pinned source in, a typed DataFrame out, no R
    loader.py           the pipeline url -> archive -> tree -> files -> tables, and the cache
    readers.py          file -> tables by format; which files of a tree hold data
    deparse.py          base R's data/*.R files evaluated without R
    intermediates.pem   TLS intermediates a source's server leaves out of its chain
  contract/             the contract: a registry row and its table in, a problem out
    problem.py          Problem.build: typing, coding, family rule, prior, splits, scales, names
    materialised.py     the materialised problem: two files under the cache, the contract hash
registry/               the registry files, written by survey/merge.py only; help/, cache/ untracked
survey/                 the pipeline that builds registry/ (survey/README.md); shards/ per reading run
suite/
  admit.py              admission: registry rows -> the candidate list of suite 1.1
  1.1/                  candidates.csv and refused.csv of suite 1.1
  tests/                run by hand
tests/                  mirrors src/; fixtures beside the tests; network tests run only in CI
docs/adr/               the decisions
.github/workflows/      ci.yml, the matrix; weekly-fetch.yml, the link-rot detector
```

Each module owns one design decision that no other module depends on. The interface is small;
the decision stays inside.

- **`registry/row.py`**: how a `registry.csv` row is written and read. The CSV dialect (every
  cell a quoted string, the empty cell the empty string), the column order (the fields of
  `Row`), the vocabularies (response types, families, `verified`; column types are the
  loader's `ColumnType`) and the cell grammars (`;`-lists, `a:b` terms, `x|g` and `x||g` slope
  terms, `col=kind` types). `Row.parse` types a row; `Row.refusals` is the grammar the survey's
  merge enforces. Imported by `registry/__init__.py`, `contract/problem.py`, `suite/admit.py`
  and the survey's scripts (`schema.py`, `merge.py`, `measure.py`, `pull.py`, …); nothing else
  parses a cell.
- **`registry/__init__.py`**: where the registry files are once installed (`path`, through the
  distribution, since the wheel carries them as `mixedbench/registry/files/`) and how
  `sources.yaml` becomes a `Source` per label, `manifest.csv` a `Manifest`, `registry.csv` a
  list of `Row`. `Tables` is the one line from a row to its typed table.
- **`datasets/loader.py`**: the pipeline from a pinned source to tables and the cache under it:
  which URLs to try, where a download lands, extraction, checksum verification on every load,
  reading one object's manifest file against enumerating a whole source, and the column
  `types` a row declares for a format that carries none. Formats are not its business.
- **`datasets/readers.py`**: which file formats exist and how each becomes tables, a class per
  format family: `RFile` (.rda, .RData, .rds through pyreadr, else rdata), `DataFolder` (a
  CRAN package's `data/` folder as `utils::data()` reads it), `PandasFile` (every other format,
  a workbook's data sheets) and `JsonFile` (records, or a Stan data dict as a table). `isData`
  decides what in a tree is data against documentation; the R routes agree on pyreadr's types.
  Imported by `loader.py` and the survey's `help.py`.
- **`datasets/deparse.py`**: base R's `data/*.R` files read without R: only the functions they
  call, R's types, and what pyreadr drops dropped too; a construct outside that subset raises
  naming the file and the construct. Imported by `readers.DataFolder` only.
- **`contract/problem.py`**: the rules of ADR 0001 in code: the one typing rule (`columnType`,
  shared with the survey's measures), the coding, the family rule, the prior, the seeded
  splits, the per-regime scales and the parameter names. `_Builder` is the pipeline, `Problem`
  the frozen result, `Refused` the rows the contract does not cover.
- **`contract/materialised.py`**: the layout of a materialised problem on disk and the contract
  hash over it (canonical JSON, then every column's name, dtype and little-endian bytes).
  `load` needs neither the loader nor the network and refuses files whose hash moved.
- **`suite/admit.py`**: the admission of suite 1.1: the hand decisions by problem id
  (`REFUSED`, `FIDELITY`), the columns of the candidate list, registry order. It writes
  `suite/1.1/`.

### Naming conventions

**Code**

- A module is one lowercase word (`loader.py`, `row.py`). A package's `__init__.py` lists its
  public names in `__all__`: it re-exports them (`datasets`, `contract`) or is the module
  (`registry`).
- `PascalCase` classes and `Literal` aliases (`ResponseType`, `Reader`), `camelCase` functions
  and methods, `snake_case` variables and the dataclass fields that mirror a registry column
  or a file field, `UPPER_SNAKE_CASE` constants.
- One pipeline class per module, its steps as methods in run order under a `# ----` banner
  that names the pipeline (`url -> archive -> tree -> files -> tables`). A step, and any
  function or class no other module imports, carries a leading `_`.
- Tests: `tests/<package>/test_<module>.py`; a test function is a sentence,
  `test_<what_holds>`; fixtures under `tests/<package>/fixtures/`; a test that fetches a
  source is marked `network`.

**Registry files and the survey** (contents: [survey/README.md](survey/README.md#file-contracts))

- Columns are `snake_case`. A list is `;`-separated; a term is `a:b`; a slope term is `x|g`
  or `x||g`; a `types` entry is `col=kind`.
- `source` is the label in `sources.yaml`: lowercase, a package or collection name; a Tier D
  file is `<paper_id>_<repository>`, with `_2`, `_3` for further files. `kind` is `cran`,
  `git` or `url`; tiers are `R`, `E`, `T`, `D`, `O` in frame order.
- `object` is the name the loader enumerates: an R object name, a file path relative to the
  source tree, or `<path>!<sheet>` for a workbook of several data sheets.
- A help page is `registry/help/<source>/<object>.txt`; a shard is
  `survey/shards/<table>_<label>.csv` with `table` one of `registry`, `excluded`,
  `duplicates`, `dropped`.
- The cache: a source under `registry/cache/cran/<name>_<pin>`,
  `git/<owner>_<repo>_<revision>` or `url/<sha256>`, its download beside `tree/` (the
  extracted archive) or `files/` (a git source's manifest files); a materialised problem under
  `registry/cache/problems/<16 hex of sha256(id)>/` as `table.parquet` and `problem.json`.

**Problems**

- A problem id is `<source>/<object>/<model_index>`: `1` the documented model, `2` and `3`
  further ones. An oracle replicate is `<problem>@oracle-<seed>` (ADR 0001, suite 1.2).
- The materialised table: `Intercept`, then the design columns in the row's order, a
  continuous or binary covariate under its own name, a contrast `<column>[<level>]`, an
  interaction `<a>:<b>`; the response and a binomial's trials under their names; a grouping
  factor under its name as 0-based codes; the regime columns `rows` and `groups` with values
  `seen` and `held`. Scales are keyed `full`, `rows`, `groups`.
- Parameters take brms's names in its block order: `Intercept` (an ordinal model's thresholds
  `Intercept[k]`), the design columns, `sd[<factor>]`, `sd[<x>|<factor>]`, `cor[<factor>]`,
  `sigma`. Prior classes are brms's: `Intercept`, `b`, `sd`, `cor`, `sigma`.
- The contract hash is a sha256 in hex; the contract version is the package's major version.

**Suites, releases, tags, issues**

- A suite lives in `suite/<major>.<minor>/`, named after the release that freezes it
  (ADR 0002): `candidates.csv` and `refused.csv` now, `problems.csv` once the references are
  in. In prose it is suite 1.1.
- A release is the tag `v<major>.<minor>.<patch>`; the package version is the registry version,
  a major bump a contract change (ADR 0002).
- Other tags: `mirror-<n>`, a release whose assets are the mirrored CC0 files (ADR 0003);
  `survey-archive`, `survey-archive-2`, the finished survey scripts.
- A branch is `<area>/<slug>` off `main`, one per spec (`suite/contract`,
  `public/going-public`). An issue carries one area label (`registry`, `suite`, `references`,
  `tracks`, `paper`, `release`), plus `spec` for a spec and `ready-for-agent` once triaged.
