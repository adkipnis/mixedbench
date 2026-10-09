---
status: accepted
date: 2026-10-08
---

# 0001 — The contract: one frozen rule set turns a registry row into a problem

A benchmark of posterior approximation needs every problem's posterior to be one
well-defined distribution that any sampler can target. The contract fixes it; a change to
any rule is a new suite version, never a recomputation.

**Rows.**

- Decision: a row with a missing value in any model column (response, trials, covariates,
  grouping factors) is dropped and the dropped share recorded per problem.
- Why: this is what lme4 and brms do by default; the registry measured missingness but never
  fitted anything.

**Coding and standardisation.**

- Decision: continuous covariates are z-scored, binary ones 0/1, a categorical with K levels
  becomes K − 1 treatment-contrast columns in the loaded table's level order (R's factor order
  where the file carries one) with the first level as reference; ordered factors fold into
  categorical; an interaction is the product of the coded columns; the intercept column is
  always present. A continuous response is z-scored.
- Why: every problem is stated and stored on this standardised scale (metabeta's ADR 0001 and
  0002), so one prior serves every problem and nothing is data-adapted by hand.

**Family rule.**

- Decision: by response type, continuous → Gaussian identity, binary → Bernoulli logit,
  count → Poisson log, binomial → Binomial logit with the trials column, ordinal → cumulative
  logit. Negative binomial and probit, where the registry's `family` column names them,
  replace the rule from suite 1.2 on; Gamma, zero-inflated and hurdle families stay on the
  rule until a lab note settles their scaling. Categorical responses are outside suite 1.1.
- Why Poisson rather than negative binomial as the count default: the benchmark measures
  posterior accuracy, not fit. An overdispersed Poisson posterior is a well-defined target,
  while a negative-binomial shape on equidispersed data is the case that breaks NUTS, and
  practice fits Poisson twice as often (metabeta's practice survey: 4% versus 2% of rows).

**Prior.**

- Decision: on the standardised scale, β_j ~ Normal(0, 2.5), intercept ~ Normal(0, 2.5),
  σ_k ~ half-Student-t(3, 0, 2.5), σ_ε ~ half-Student-t(3, 0, 2.5), Ω_k ~ LKJ(1). Any
  parameter the contract does not name (ordinal thresholds, a shape) takes brms's default at
  the pinned brms version.
- Why: in raw units this is rstanarm's autoscaled default for β and the intercept and brms's
  default for the scales and correlations; metabeta's default prior is this prior by
  construction.
- Rejected: documented priors, since one registry row's notes mention a prior, the Bayesian
  published models would need re-reading for theirs, and those are mostly BUGS-vague normals
  or an author's taste. A `documented_prior` column is recorded for a later "as published"
  track. brms's flat β, since it is improper, and on small binary problems with separation the
  posterior need not exist.

**Splits (predictive track).**

- Decision: two seeded regimes per problem, the seed a hash of the problem id: 10% of rows
  held out uniformly inside seen groups (a single-row group keeps its row); 10% of the groups
  of the first grouping factor held out entirely, at least one and such that at least two
  remain.

**Oracle track.**

- Decision: `<problem>@oracle-<seed>`: parameters drawn from the contract prior, the response
  simulated on the problem's design, the truth stored beside the reference.

**Identity.**

- Decision: a problem is `<source>/<object>/<model_index>`; its contract hash is the sha256
  over the contract version, the pinned brms and CmdStan versions and the materialised arrays.
- Why: a changed pin or rule is visible as a changed hash.
