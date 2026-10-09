---
status: accepted
date: 2026-10-08
---

# 0004 — brms over Stan is the single reference sampler; ladder, bar and what a reference is not

**Sampler.**

- Decision: every reference posterior is computed by brms (cmdstanr backend) from the
  contract's model and prior, at pinned brms and CmdStan versions.
- Why: one trusted implementation of every family and grouping structure the contract allows,
  and the model code is what the audience already believes.
- Rejected: a hand-written likelihood per family in another framework, which would be a second
  thing to get right for 575 problems (at grilling, 2026-10-08).
- metabeta's own validation sets use PyMC NUTS, and metabeta shows parity with these
  references on a seeded suite subset (metabeta's glmm ADR 0004); the benchmark paper makes no
  independent-implementation claim of its own unless that parity lands first.

**Ladder.**

- Decision: metabeta v0.5's, four chains. Level 0: warmup 1000, draws 1000, adapt_delta 0.8,
  tree depth 10. Level 1: warmup 2000, draws 1000, adapt_delta 0.9. Level 2: warmup 4000,
  draws 2000, adapt_delta 0.99, tree depth 12.
- Decision: escalate until the bar passes; store the passing level's draws thinned to 4,000; a
  problem that fails at level 2 stays registry-only.

**Bar.**

- Decision: rank-normalised R-hat < 1.01, bulk and tail ESS ≥ 400 on every global parameter,
  zero divergences.
- Why stricter than v0.5's escalation trigger (1.05, 100): these draws are published, not
  consumed once.

**Storage.**

- Decision: global draws in full (4,000 × P, parquet, standardised scale); random-effect draws
  in full for factors with at most 1,000 groups, per-group summaries above; diagnostics, ladder
  level and contract hash beside them.

**Not a speed opponent.**

- Decision: wall-clock is not a benchmark metric, and the reference runs are not timed as an
  opponent line. The chain-split null is the floor of every metric on every problem.
- Why: wall-clock is hardware-specific.
