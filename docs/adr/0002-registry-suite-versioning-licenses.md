---
status: accepted, amended 2026-10-09, 2026-10-10 and 2026-10-18
date: 2026-10-08
---

# 0002 — Registry and suite are two things; versioning, admission, citation and licenses

The registry is a growing census of documented problems over public grouped data; the suite
is a frozen subset with reference posteriors. Conflating them would make every registry
correction a benchmark change.

**Versioning.**

- Decision: the package version is the registry version (semver: a membership change of a
  released suite never happens, so major bumps are contract changes, minor bumps are registry
  additions, patches are metadata fixes). Suites are named after the release that freezes
  them (`suite-1.1`, `suite-1.2`; release 1.0 ships the registry, the contract and a candidate
  list, no suite) and are immutable; references are tagged by suite version and sampler
  versions.
- Decision: a problem whose source vanishes is retired from the *next* suite, never replaced in
  a released one.

**Admission to a suite.**

- Decision: a row is verified (confidence `high`, or an agreed blind second reading, or
  hand-checked), its reference passes the bar of ADR 0004 within the compute cap (12 hours,
  four chains, one CPU node), and its response type is in the contract's family rule.
  `published_model=no` rows enter with `model_source=reader`.
- Why: the suite tests posterior accuracy on real grouped data, not fidelity to a publication.
- Rejected: an envelope filter. A benchmark defined by one tool's trained ranges is not
  independent; metabeta filters by the problem's dimensions as metadata.

**Verification bar.**

- Decision: a seeded 100-row hand sample, stratified by tier × confidence, gives the per-field
  agreement table; a stratum under 80% agreement on response or grouping factors is re-read.
- Rejected: further agent re-reading, since every medium and low row already had a blind second
  reading with disagreements adjudicated by hand.

**Thin cells.**

- Decision: binomial (16 rows), ordinal (45) and categorical (12) are not padded by new
  sourcing.
- Why: the cell sizes are a finding about public grouped data (63% continuous).

**Citation.**

- Decision: `CITATION.cff`; a Zenodo DOI per release; draws on the Hugging Face Hub for lazy
  access, the Zenodo snapshot for the citation.

**Licenses.**

- Decision: code MIT; registry files, suite files and reference posteriors CC BY 4.0. The data
  themselves keep their sources' terms (ADR 0003).
- Rejected: inheriting metabeta's CC-BY-NC-SA license, since a benchmark under a
  non-commercial license bars companies and most ML groups.

## Amendment 2026-10-09: the grill of roadmap item 3

- Decision: a `verified` registry column records why a row counts as verified: `hand` for
  the hand sample's rows and every Tier D row, `high` for the remaining rows of high
  confidence, `second-reading` for every other row, since the blind second reading was the
  method for all medium and low rows. It is assigned once by script.
- Why: the suite's `problems.csv` and the paper state per problem why it is in; prose
  summarizing it was rejected by the docs rule, and admitting `high` only would discard the
  hand sample's finding that medium rows agree. A second hand sample during item 5 is open.
- Decision: the share of rows dropped for missing values is recorded on the candidate list,
  `suite/<version>/candidates.csv`, and not capped. A cap is a branch for a case not yet
  observed; the admission script prints the top of the distribution.

## Amendment 2026-10-10: going public (roadmap item 4)

- Decision: release 1.0 makes the repository public, tags `v1.0.0`, takes a Zenodo DOI and
  publishes to PyPI by trusted publishing from a GitHub release.
- Why: Zenodo archives only public repositories, and `pip install mixedbench` is what users of
  a benchmark expect; the wheel carries code and registry files only, so ADR 0003 holds.
- Decision: the wheel is licensed `MIT AND CC-BY-4.0`, with both license files, since it
  bundles the registry files.
- Decision: `requires-python = ">=3.11"`; development stays on 3.14, CI tests 3.11 and 3.14.
- Why: no code needs a newer Python, and `>=3.14` would turn away most ML users.
- Decision: the history stays as it is; `CLAUDE.md` leaves the tree and becomes local. Its
  conventions move to a public `docs/conventions.md`, linked from a short `CONTRIBUTING.md`;
  `CLAUDE.md` imports both.
- Why: `CONTRIBUTING.md` is read once by a newcomer deciding whether to help; the conventions
  are read by reviewers and agents, and would bury it.
- Rejected: rewriting the history (`git filter-repo`) or a fresh squashed repository. Nothing
  in the history is secret, and a rewrite breaks every hash cited in issues, PRs and tags.
- Decision: the ADRs, survey shards, prompts, `HISTORY.md` and `VERDICTS.md` stay public as
  the registry's provenance; `survey/archive/` leaves the tree, reachable by tag.
- Why: the shards and prompts rebuild the registry, and the verdicts back the `verified`
  column; the archive is finished and already preserved.

## Amendment 2026-10-10: a suite's list in the wheel (#55)

- Decision: the wheel also carries each suite's list, `suite/<version>/candidates.csv` until
  1.1 freezes `problems.csv`, so `mixedbench.suite.load` builds a problem by its id on first
  use and checks its contract hash against the list.
- Why: the list holds ids and hashes, no data, so ADR 0003 holds; without it a user needs a
  checkout to fetch a suite, and five calls across three modules for one problem.

## Amendment 2026-10-10: the grill of roadmap item 5

- Decision: the compute cap counts the whole ladder. One cluster job per problem runs levels
  0 to 2 in sequence within 12 hours; a job stopped at the cap fails as `cap`.
- Why: admission asks that a reference pass the bar within the cap, and one time limit per
  job is what a scheduler takes.
- Decision: a second hand sample is drawn before suite 1.1 freezes: 100 of the candidates
  not yet hand-checked, seed 1, stratified by tier × `verified` with largest-remainder
  allocation, read in four batches of 25. It compares the first sample's fields and
  `random_slopes`, against the same bar; corrections move hashes as a patch.
- Why: the first sample was drawn from the registry, and it corrected `covariates` in 13 of
  100 rows; the contract reads `covariates`, `interactions` and `random_slopes`, so such
  errors change problems. The suite rests on the candidates.

## Amendment 2026-10-18: code under Apache-2.0

- Decision: the code is licensed Apache-2.0; registry files, suite files and reference
  posteriors stay CC BY 4.0, and the wheel is licensed `Apache-2.0 AND CC-BY-4.0`. Releases up
  to 1.0.3 keep MIT.
- Why: Apache-2.0 adds an explicit patent grant from every contributor, which company legal
  teams look for, and licenses contributions under the same terms without a separate
  agreement.
