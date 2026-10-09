---
status: accepted
date: 2026-10-08
---

# 0002 — Registry and suite are two things; versioning, admission, citation and licences

The registry is a growing census of documented problems over public grouped data; the suite
is a frozen subset with reference posteriors. Conflating them would make every registry
correction a benchmark change.

- **Versioning.** The package version is the registry version (semver: a membership change of
  a released suite never happens, so major bumps are contract changes, minor bumps are
  registry additions, patches are metadata fixes). Suites are named after the release that
  freezes them (`suite-1.1`, `suite-1.2`; release 1.0 ships the registry, the contract and a
  candidate list, no suite) and are immutable; references are tagged by suite version and
  sampler versions. A problem whose source vanishes is retired from the *next* suite, never
  replaced in a released one.
- **Admission to a suite.** A row is verified (confidence `high`, or an agreed blind second
  reading, or hand-checked), its reference passes the bar of ADR 0004 within the compute cap
  (12 hours, four chains, one CPU node), and its response type is in the contract's family
  rule. No envelope filter: a benchmark defined by one tool's trained ranges is not
  independent; metabeta filters by the problem's dimensions as metadata. `published_model=no`
  rows enter with `model_source=reader`: the suite tests posterior accuracy on real grouped
  data, not fidelity to a publication.
- **Verification bar.** No further agent re-reading: every medium and low row already had a
  blind second reading with disagreements adjudicated by hand. A seeded 100-row hand sample,
  stratified by tier × confidence, gives the per-field agreement table; a stratum under 80%
  agreement on response or grouping factors is re-read.
- **Thin cells.** Binomial (16 rows), ordinal (45) and categorical (12) are not padded by new
  sourcing; the cell sizes are a finding about public grouped data (63% continuous).
- **Citation.** `CITATION.cff`; a Zenodo DOI per release; draws on the Hugging Face Hub for
  lazy access, the Zenodo snapshot for the citation.
- **Licences.** Code MIT; registry files, suite files and reference posteriors CC BY 4.0. The
  data themselves keep their sources' terms (ADR 0003). metabeta's CC-BY-NC-SA licence was not
  inherited: a benchmark under a non-commercial licence bars companies and most ML groups.
