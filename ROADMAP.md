# mixedbench — Roadmap

Grilled 2026-10-08 (metabeta-v3 session; decisions in `docs/adr/0001`–`0005`); releases
regrouped 2026-10-09. Order reflects dependencies. Spec and tickets follow as GitHub Issues on
this repository. Release numbers are package versions (ADR 0002); a suite is named after the
release that freezes it.

## Release 1.0 — the dataset bundle; the repository goes public

- [x] **1 Repository.** Loader and survey moved from metabeta-v3 with history, package and CI
- [x] **2 Registry columns and verification.** Family, prior, licence, readers without R, hand sample (#6)
- [ ] **3 Contract and candidate list.** First, the registry module owns the registry row (CSV
  dialect, row grammar, manifest), so `survey/` and the contract share one parser (#16,
  candidate 2). `Problem` from a registry row (ADR 0001): rows, coding,
  standardisation, family rule, prior, splits, oracle generator, id and hash; `materialise` to
  parquet; the admission script writes suite 1.1's candidate list (membership freezes with the
  references in 1.1, since admission needs a reference that passes the bar, ADR 0002); the
  weekly fetch CI as the link-rot detector before going public

## Release 1.1 — suite 1.1 with references; the paper

- [ ] **4 Reference runner.** brms/cmdstanr at pinned versions, the ladder and bar (ADR 0004),
  draw files, diagnostics, one problem per cluster job, the 12-hour cap
- [ ] **5 Cluster run.** Suite 1.1 references on CPU nodes; failures recorded; `suite/1.1/
  problems.csv` frozen from the candidates that passed; Hub upload and the Zenodo snapshot
- [ ] **6 Metrics and opponent lines.** W1, coverage, C2ST and MMD against the chain-split null,
  the lab note choosing the joint metric; posterior lines (NUTS level 0, Pathfinder, Laplace,
  mean-field ADVI); predictive lines (TabPFN ×2, GPBoost, glmmTMB, GLM) and scores (ADR 0005)
- [ ] **7 Paper.** `~/LaTeX/mixedbench`, every number from this repository at a pinned commit:
  frame and method, registry census, contract, suite and diagnostics, opponent lines, usage;
  arXiv, then NeurIPS Datasets & Benchmarks 2027 (deadline about May 2027), *Statistics and
  Computing* as fallback

## Release 1.2 — suite 1.2 and the extensions; the last planned release

- [ ] **8 Suite 1.2.** Oracle-track references; negative binomial and probit from the `family`
  column; retirements from the weekly fetch log
- [ ] **9 Extensions.** An R loader; an "as published" prior track from `documented_prior`; a
  permitted-mirror fallback for rotted sources (ADR 0003)

No further releases are planned.
