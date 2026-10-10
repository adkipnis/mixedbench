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
