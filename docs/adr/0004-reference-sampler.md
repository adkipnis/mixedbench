---
status: accepted, amended 2026-10-10, 2026-10-16 and 2026-10-28
date: 2026-10-08
---

# 0004 - brms over Stan is the single reference sampler; ladder, bar and what a reference is not

**Sampler.**

- Decision: every reference posterior is computed by brms (cmdstanr backend) from the
  contract's model and prior, at pinned brms and CmdStan versions.
- Why: one trusted implementation of every family and grouping structure the contract allows,
  and the model code is what the audience already believes.
- Rejected: a hand-written likelihood per family in another framework, which would be a second
  thing to get right for 575 problems (at grilling, 2026-10-08).
- metabeta's own validation sets use PyMC NUTS, and metabeta shows parity with these
  references on a seeded suite subset (metabeta's glmm ADR 0004).

**Ladder.**

- Decision: metabeta v0.5's, four chains. Level 0: warmup 1000, draws 1000, adapt_delta 0.8,
  tree depth 10. Level 1: warmup 2000, draws 1000, adapt_delta 0.9. Level 2: warmup 4000,
  draws 2000, adapt_delta 0.99, tree depth 12.
- Decision: escalate until the bar passes; store the passing level's draws thinned to 4,000; a
  problem that fails at level 2 stays registry-only.

**Bar.**

- Decision: rank-normalized R-hat < 1.01, bulk and tail ESS >= 400 on every global parameter,
  zero divergences.
- Why stricter than v0.5's escalation trigger (1.05, 100): these draws are published, not
  consumed once.

> Amended 2026-10-28 below: every random effect meets a looser R-hat bar and the same ESS.

**Storage.**

- Decision: global draws in full (4,000 × P, parquet, standardized scale); random-effect draws
  in full for factors with at most 1,000 groups, per-group summaries above; diagnostics, ladder
  level and contract hash beside them.

**Not a speed opponent.**

- Decision: wall-clock is not a benchmark metric, and the reference runs are not timed as an
  opponent line. The chain-split null is the floor of every metric on every problem.
- Why: wall-clock is hardware-specific.

## Amendment 2026-10-10: the grill of roadmap item 5

**The runner.**

- Decision: Python writes the regime's standardized table, the brms formula and the prior;
  a thin R script calls `brm()` with the cmdstanr backend, checks the bar and writes the
  draws under brms's names, which Python renames to the contract's parameter names. The Stan
  code and data brms generated are stored beside the draws.
- Why: the contract's logic stays in Python and the naming stays brms's. Generating the Stan
  program with brms and sampling from Python (cmdstanpy) was rejected: mapping Stan's raw
  names to brms's would copy brms's internals a second time. brms also runs the posterior
  opponent lines (Pathfinder, Laplace, mean-field ADVI) on the same program.
- Decision: the runner is the package's `references` module behind the `references` extra,
  with the R script as package data; the cluster driver is a script under `suite/`.
- Decision: the R stack is pinned by an `renv.lock` and `cmdstanr::install_cmdstan(version=)`;
  each draw file records `sessionInfo()`.
- Rejected for now: a container image, kept for the case that the cluster's R toolchain fails.

**What a run leaves.**

- Decision: draws and diagnostics go to `references/<suite>/<id>/`, never committed, and
  reach the Hugging Face Hub and Zenodo with the suite's freeze. The runner writes one
  committed table, `suite/<suite>/references.csv`, a row per problem: the level reached,
  passed or the failure (`bar`, `cap`, `error`), the largest R-hat, the smallest bulk and
  tail ESS, the divergences and the brms and CmdStan pins.
- Why: failures are part of the record, and a script writes every file under `suite/`.

**Only the full table.**

- Decision: suite 1.1's references are fits to the full table (the posterior track). The
  fits to the seen rows of the predictive regimes come with suite 1.2.

## Amendment 2026-10-16: the runner's review (#70)

**The bar in Python.**

- Decision: the R script fits a level and reports its diagnostics; Python checks the bar on
  them, beside the ladder and the cap. An R-hat or ESS that posterior could not compute
  (constant or non-finite draws) fails the bar. This replaces "checks the bar" in the runner
  decision above.
- Why: the bar is tested without R, and the gate sits with the ladder it stops. In R, a missing
  diagnostic made the verdict NA, which Python read as a pass.

**The R stack and the session.**

- Decision: the pins check covers posterior beside brms, cmdstanr and CmdStan, since posterior
  computes the bar's R-hat and ESS.
- Decision: each level prints `sessionInfo()` into the run's `R.log` before it fits, however it
  ends. This replaces "each draw file records `sessionInfo()`" above.
- Decision: the runner ships in the base package, with no `references` extra. This replaces
  "behind the `references` extra" above.
- Why: its stack is R, brms and CmdStan, which no Python extra installs; the extra was empty.

**The run's directory.**

- Decision: `references/<suite>/<the first 16 hex characters of sha256 of the id>/`, since an id
  holds `/`; `run.json` inside carries the id. A rerun replaces the directory, so no file of an
  earlier run sits beside a later record.

## Amendment 2026-10-28: the random effects' bar (#148)

**Bar.**

- Decision: a level passes only if every random effect also has R-hat < 1.05 and bulk and tail
  ESS >= 400; one that misses it climbs the ladder, as a global parameter does. `run.json`
  records the largest R-hat and the smallest bulk and tail ESS over the random effects.
- Why: the random-effect draws are published and used, so a reference needs them converged.
  rstan warns at R-hat > 1.05 and at bulk or tail ESS < 100 per chain over every parameter,
  400 for four chains. R-hat stays looser than the global 1.01, since the largest of thousands
  crosses 1.01 by chance more often than one does. Every random effect of the nine passing
  pilot runs met even the global bar.
