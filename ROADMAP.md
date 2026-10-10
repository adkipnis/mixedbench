# mixedbench — Roadmap

Grilled 2026-10-08 (metabeta-v3 session; decisions in `docs/adr/0001`–`0005`); releases
regrouped 2026-10-09. Order reflects dependencies. Spec and tickets follow as GitHub Issues on
this repository. Release numbers are package versions (ADR 0002); a suite is named after the
release that freezes it.

## Release 1.0 — the dataset bundle; the repository goes public

- [x] **1 Repository.** Loader and survey moved from metabeta-v3 with history, package and CI
- [x] **2 Registry columns and verification.** Family, prior, licence, readers without R, hand sample (#6)
- [x] **3 Contract and candidate list** (#23). First, the registry module owns the registry row (CSV
  dialect, row grammar, manifest), so `survey/` and the contract share one parser (#16,
  candidate 2). The `random_slopes` and `verified` columns, filled by script. `Problem`
  from a registry row (ADR 0001, amended 2026-10-09): rows, coding, per-regime
  standardisation, family rule, prior, splits, id and hash; the
  materialised problem (parquet and JSON) as the interface; the admission script writes
  suite 1.1's candidate list (membership freezes with the references in 1.1, since admission
  needs a reference that passes the bar, ADR 0002); the weekly fetch CI as the link-rot
  detector before going public
- [x] **4 Going public** (ADR 0002, amended 2026-10-10). A deep review of `src/` and `suite/`
  read together, with `CONTRIBUTING.md`'s layout written first; a demo notebook run in the
  weekly fetch; a short README with badges; `CLAUDE.md` local, the history kept,
  `survey/archive/` behind a tag; Python `>=3.11`; the repository public, then `v1.0.0`, the
  Zenodo DOI and PyPI

## Release 1.1 — suite 1.1 with references; the paper

- [ ] **5 Reference runner.** brms/cmdstanr at pinned versions, the ladder and bar (ADR 0004,
  amended 2026-10-10), draw files, diagnostics, one problem per cluster job, the 12-hour cap
  over the whole ladder; full-table fits only, a pilot on CI's 20-problem subset
- [ ] **6 Cluster run.** Suite 1.1 references on CPU nodes; failures recorded; `suite/1.1/
  problems.csv` frozen from the candidates that passed, once the second hand sample (ADR 0002)
  and the lab note on #47 (ADR 0005) are done; Hub upload and the Zenodo snapshot
- [ ] **7 Metrics and opponent lines.** W1, coverage, C2ST and MMD against the chain-split null,
  the lab note choosing the joint metric; posterior lines (NUTS level 0, Pathfinder, Laplace,
  mean-field ADVI); predictive lines (TabPFN ×2, GPBoost, glmmTMB, GLM) and scores (ADR 0005);
  the demo notebook gains a toy fit scored against the reference draws
- [ ] **8 Paper.** Every number from this repository at a pinned commit:
  frame and method, registry census, contract, suite and diagnostics, opponent lines, usage;
  arXiv, then NeurIPS Datasets & Benchmarks 2027, *Statistics and
  Computing* as fallback

## Release 1.2 — suite 1.2 and the extensions; the last planned release

- [ ] **9 Suite 1.2.** Oracle-track references; predictive references, the fits to each
  regime's seen rows (ADR 0005); negative binomial and probit from the `family`
  column; retirements from the weekly fetch log; random-effect blocks as the source writes
  them (#46, grilled when this item starts). The oracle generator, moved here from item 3
  (#31) and grilled when this item starts: metabeta's simulator draws the parameters and
  the response under any prior it supports, mixedbench turns them into a replicate (new id,
  splits and scales, the truth, the prior) and owns its format, so the simulation exists once
  and the dependency stays one-way (metabeta-v3 ADR 0002)
- [ ] **10 Extensions.** An R loader; an "as published" prior track from `documented_prior`; a
  permitted-mirror fallback for rotted sources (ADR 0003)

No further releases are planned.
