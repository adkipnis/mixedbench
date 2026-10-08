---
status: accepted
date: 2026-10-08
---

# 0003 — Fetch-only: pins and checksums, no redistribution, no R in the loader

The package ships pins, checksums, the registry and the reference posteriors; a user's
first use fetches each source and verifies its digest. Nothing is mirrored.

## Why

- About 280 registry rows (Stata Press's "not stated", textbook companion sites) grant no
  redistribution right at all, so a mirroring package would carry two regimes anyway; CRAN
  data sit under GPL, whose copyleft on data is unsettled (the Rdatasets mirror redistributes
  2,000 CRAN tables under GPL-3 unchallenged, so this is the weaker reason); every mirrored
  file is a derivative-work question and the package would weigh gigabytes (a full fetch is
  4.5 GB). OpenClustered bundled all 19 of its datasets, lme4's and MASS's included, and its
  paper never mentions a licence; we do not follow it.
- The permanent loss is link rot. Each release records a fetch status per problem from the
  weekly CI fetch; a rotted source retires its problems from the next suite (ADR 0002).

## Consequences

- A per-row `licence` column, filled by script (CRAN from the package DESCRIPTION, git and
  url sources from `sources.yaml`, companion sites `not stated`), so that a permitted-mirror
  fallback for rotted links can be added in a later version without re-reading.
- No R in the loader. The 36 objects that the survey read through an Rscript dump (27 agridat
  `data/*.txt` files, 7 base R `datasets` objects, 2 `.rda`/`.RData` files pyreadr rejects) get
  a Python reader for CRAN's text format and a pinned fetch of the R source tarball for the
  base R objects; what no Python reader takes is retired from the suite, not the registry.
- CI loads every problem: per pull request three operating systems × a seeded 20-problem
  subset, weekly a full fetch with checksum verification, at release a full fetch on three
  operating systems. A problem materialises to one parquet file per problem for R and Julia
  users.

## Amendment 2026-10-08: a mirror where a CC0 host refuses scripts (#4)

Dryad answers a scripted download with 401, so the 15 registry objects of its 11 sources
could not be fetched by a user's loader. Their data are CC0, which permits a copy: the
package mirrors exactly those files as assets of the release `mirror-1` of this repository
(`survey/mirror.py`), recorded as `mirror:` in their `sources.yaml` entries. The host stays
the source and is asked first; the mirror is asked on a 404 or a refusal (401, 403), and its
file must carry the same pinned sha256. Nothing under another licence is mirrored; a rotted
non-CC0 source still retires its problems.
