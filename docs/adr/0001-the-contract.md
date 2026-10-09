---
status: accepted, amended 2026-10-09
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

> Amended 2026-10-09 below: the standardisation is computed per regime on the rows a fit
> sees; the coding stays the full table's.

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

> Superseded in part by the amendment of 2026-10-09 below: the hash covers the contract
> version and the materialised problem, not the sampler pins.

## Amendment 2026-10-09: the grill of roadmap item 3

**Hash.**

- Decision: the contract hash is the sha256 over a canonical serialisation of the
  materialised problem (the JSON with sorted keys, then every column in table order as its
  name, dtype and little-endian bytes, floats as float64) and the contract version, which
  is the package major version. The brms and CmdStan pins leave the hash: they are part
  of a reference, recorded in the suite (ADR 0002), not of a problem.
- Why: item 3 ships before any sampler is pinned, and a problem is a design, a family, a
  prior and the splits. Hashing parquet bytes was rejected because a pyarrow bump would
  become a contract change.

**Standardisation and the splits.**

- Decision: the standardisation is computed on the rows a fit sees: the full table for the
  posterior track and the seen rows of each predictive regime. The materialised table holds
  the coded columns in raw units and the per-regime means and standard deviations beside it.
  Coding (levels, contrasts) is the full table's; a level that survives only in held-out
  rows leaves an all-zero column in the seen rows, which the prior keeps proper.
- Why: a scaler fit on held-out rows is leakage to a benchmark reviewer, and the predictive
  track refits on the seen rows anyway, so no draws were ever shared across tracks.
  Redrawing a split until every level survives was rejected: it biases toward balanced
  problems and couples the split to the coding.

**Random slopes.**

- Decision: a `random_slopes` registry column, a `;`-list of `x|g` (correlated with the
  intercept of `g`, Ω_k ~ LKJ(1)) and `x||g` (uncorrelated) terms, filled by a script that
  parses the lme4 syntax of `formula` and hand-checked where it fails. The contract reads
  structured columns only; nothing parses `formula`. Nested factors need nothing new:
  `grouping_factors` already writes `(1|a/b)` as `a;a:b`.
- Why: 97 of 714 documented models carry a slope, and intercept-only would make 14% of the
  problems not their documented model.
- Clarified 2026-10-09 (#27, after an outside review): `x||g` is independent of the intercept
  and of every other slope of `g`. Both kinds of term act on the standardised column, so a
  zero correlation or a slope without its intercept is set at the sample mean, not at the
  source's zero. This is a benchmark assumption of suite 1.1. A slope that maps the source's structure into another basis is equivalent in structure, not
  in prior. Keeping the source's own blocks is a contract extension (#46).

**Family rule, two cases.**

- Decision: a censored response (`family` `cox` or `weibull`, 7 rows) is outside suite 1.1
  like a categorical one. A Gaussian documented model on a binary, count or ordinal response
  (12 rows) takes the rule's family.
- Why: Gaussian on an uncensored time is a model of a different quantity, and a `cens()`
  term is a contract extension that belongs with suite 1.2's families if ever. The second
  case is what the rule's "by response type" was decided for.
