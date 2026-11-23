---
status: accepted, amended 2026-10-08, 2026-10-09, 2026-11-18 and 2026-11-23
date: 2026-10-08
---

# 0003 - Fetch-only: pins and checksums, no redistribution, no R in the loader

The package ships pins, checksums, the registry and the reference posteriors; a user's
first use fetches each source and verifies its digest. Nothing is mirrored.

> Superseded in part by the amendment of 2026-10-08 below: the CC0 files of Dryad sources are
> mirrored.

## Why

- About 280 registry rows (Stata Press's "not stated", textbook companion sites) grant no
  redistribution right at all, so a mirroring package would carry two regimes anyway.
- CRAN data sit under GPL, whose copyleft on data is unsettled (the Rdatasets mirror
  redistributes 2,000 CRAN tables under GPL-3 unchallenged, so this is the weaker reason).
- Every mirrored file is a derivative-work question, and the package would weigh gigabytes (a
  full fetch is 4.5 GB).
- Rejected: OpenClustered's way. It bundled all 19 of its datasets, lme4's and MASS's
  included, and its paper never mentions a license; we do not follow it.
- The permanent loss is link rot. Each release records a fetch status per problem from the
  weekly CI fetch; a rotted source retires its problems from the next suite (ADR 0002).

## Consequences

- A per-row `license` column, filled by script (CRAN from the package DESCRIPTION, git and
  url sources from `sources.yaml`, companion sites `not stated`), so that a permitted-mirror
  fallback for rotted links can be added in a later version without re-reading.
- No R in the loader. The 36 objects that the survey read through an Rscript dump (27 agridat
  `data/*.txt` files, 7 base R `datasets` objects, 2 `.rda`/`.RData` files pyreadr rejects) get
  a Python reader for CRAN's text format and a pinned fetch of the R source tarball for the
  base R objects; what no Python reader takes is retired from the suite, not the registry.

  > Superseded in part by the amendment of 2026-10-09 below: the two files pyreadr rejects
  > load through `rdata`, and none is retired.
- CI loads every problem: per pull request three operating systems × a seeded 20-problem
  subset, weekly a full fetch with checksum verification, at release a full fetch on three
  operating systems. A problem materializes to one parquet file per problem for R and Julia
  users.

## Amendment 2026-10-08: a mirror where a CC0 host refuses scripts (#4)

Dryad answers a scripted download with 401, so the 15 registry objects of its 11 sources
could not be fetched by a user's loader. Their data are CC0, which permits a copy: the
package mirrors exactly those files as assets of the release `mirror-1` of this repository
(`survey/mirror.py`), recorded as `mirror:` in their `sources.yaml` entries. The host stays
the source and is asked first; the mirror is asked on a 404 or a refusal (401, 403), and its
file must carry the same pinned sha256. Nothing under another license is mirrored; a rotted
non-CC0 source still retires its problems.

## Amendment 2026-10-09: rdata for the R files librdata rejects (#9)

The two registry objects whose files librdata rejects, geepack's `muscatine.rda` and
plonsky_2019_osf's `.RData` (`dd1`), are not retired: the pure-Python `rdata` package reads
both, and its frames equal the Rscript dump's on columns, dtypes, levels and values. With
that, the Rscript route leaves the loader; `reader` is `pyreadr`, `rdata`, `pandas` or
`deparse`. A file neither pyreadr nor rdata parses (a model fit's bytecode) is one object
without a table, as an object pyreadr cannot frame is.

## Amendment 2026-10-09: materialized problems are a cache; the weekly fetch opens issues

A materialized problem (one parquet and one JSON, ADR 0001) is derived from a pin, a
registry row and the contract, so it lives under `registry/cache/` like the fetched files:
never committed, never uploaded, rebuilt from the pins. Committing or hosting the arrays
would be redistribution with another file extension. The suite commits ids and contract
hashes only, and a test rebuilds a sample and compares them. The materialized files are the
package's interface to a problem: `Problem` loads from them, and metabeta never fetches a
source. The weekly fetch opens one GitHub issue per failing source, labeled `registry`, and
closes it when the source returns; item 9's retirements read that history. A committed log
was rejected because it would make a bot the author of registry commits.

## Amendment 2026-11-18: a 403 is a burst limit (#231)

OSF answers a burst of scripted downloads with a 403 or a stalled read, so the weekly fetch of
2026-11-18 opened 15 issues for files that matched their pins. `fetch` retries a 403 and a
stalled read as it does a 429, and raises one that persists. A refusal is a 401 (Dryad's) or
a 404, on which the mirror is asked.

## Amendment 2026-11-23: a row declares its table's missing codes ([#210](https://github.com/adkipnis/mixedbench/issues/210))

Five tables write a missing value as an ordinary one (`-10`, `-9`, `-1`, `?`, `destroyed`).
The loader kept it as a value, so each was excluded as `unreadable format`.

- Decision: a registry row declares its table's missing codes in a `missing` column of
  `registry.csv` beside `types` and `stack`, one `column=code` per code, on the long form's
  columns. The loader reads each as missing after the stack and before the types.
- Why: the codes are read off the documentation the types are read off, so one reading, one
  shard and one merge check cover them.
- Rejected: `sources.yaml`, which pins sources and holds nothing per column, and the manifest,
  which the merge rewrites from the files.
- Decision: a code belongs to a column, never to the whole table.
- Why: a table-wide `-9` would turn another column's measured -9 missing, with no one having
  read that column.
- Decision: a reader declares only a code the source documents, a text among a column's
  numbers, or a value outside the range the source documents for the column. A value that only
  looks like a code stays a value, and the row's `notes` open `MISSING SUSPECTED:`.
- Why: a rule on the loaded values deletes measurements where it guesses wrong. A documented
  range is the source's own word on what a measurement can be: Rouault et al. (2020) rate
  confidence from 1 to 6, and 19 responses hold 999.
- Decision: the merge refuses a code whose column the table lacks, and one that no value of
  its column equals.
- Why: a typo, or a code the pinned file does not write, would otherwise declare nothing
  unseen.
