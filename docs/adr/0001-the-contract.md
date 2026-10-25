---
status: accepted, amended 2026-10-09, 2026-10-10, 2026-10-20 and 2026-10-21
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

**Coding and standardization.**

- Decision: continuous covariates are z-scored, binary ones 0/1, a categorical with K levels
  becomes K − 1 treatment-contrast columns in the loaded table's level order (R's factor order
  where the file carries one) with the first level as reference; ordered factors fold into
  categorical; an interaction is the product of the coded columns; the intercept column is
  always present. A continuous response is z-scored.
- Why: every problem is stated and stored on this standardized scale (metabeta's ADR 0001 and
  0002), so one prior serves every problem and nothing is data-adapted by hand.

> Amended 2026-10-09 below: the standardization is computed per regime on the rows a fit
> sees; the coding stays the full table's.

> Amended 2026-10-21 below: an integer covariate is continuous unless the source stores it as
> a factor or `types` declares it categorical.

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

- Decision: on the standardized scale, β_j ~ Normal(0, 2.5), intercept ~ Normal(0, 2.5),
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
- Clarified 2026-10-09 (#29): 10% is rounded to the nearest whole number, halves up. In the
  held-out-rows regime every group of every grouping factor keeps a seen row. A first factor
  of two groups has no held-out-groups regime, since holding one leaves one (10 rows); the
  problem keeps the posterior track and the held-out-rows regime.

> Superseded by the amendment of 2026-10-20 below: each split regime is dealt into folds
> instead of holding out 10% once.

**Oracle track.**

- Decision: `<problem>@oracle-<seed>`: parameters drawn from the contract prior, the response
  simulated on the problem's design, the truth stored beside the reference.

**Identity.**

- Decision: a problem is `<source>/<object>/<model_index>`; its contract hash is the sha256
  over the contract version, the pinned brms and CmdStan versions and the materialized arrays.
- Why: a changed pin or rule is visible as a changed hash.

> Superseded in part by the amendment of 2026-10-09 below: the hash covers the contract
> version and the materialized problem, not the sampler pins.

## Amendment 2026-10-09: the grill of roadmap item 3

**Hash.**

- Decision: the contract hash is the sha256 over a canonical serialization of the
  materialized problem (the JSON with sorted keys, then every column in table order as its
  name, dtype and little-endian bytes, floats as float64) and the contract version, which
  is the package major version. The brms and CmdStan pins leave the hash: they are part
  of a reference, recorded in the suite (ADR 0002), not of a problem.
- Why: item 3 ships before any sampler is pinned, and a problem is a design, a family, a
  prior and the splits. Hashing parquet bytes was rejected because a pyarrow bump would
  become a contract change.

**Standardization and the splits.**

- Decision: the standardization is computed on the rows a fit sees: the full table for the
  posterior track and the seen rows of each predictive regime. The materialized table holds
  the coded columns in raw units and the per-regime means and standard deviations beside it.
  Coding (levels, contrasts) is the full table's; a level that survives only in held-out
  rows leaves an all-zero column in the seen rows, which the prior keeps proper.
- Why: a scaler fit on held-out rows is leakage to a benchmark reviewer, and the predictive
  track refits on the seen rows anyway, so no draws were ever shared across tracks.
  Redrawing a split until every level survives was rejected: it biases toward balanced
  problems and couples the split to the coding.

> Amended 2026-10-20 below: the standardization of a split regime is computed per fold.

**Random slopes.**

- Decision: a `random_slopes` registry column, a `;`-list of `x|g` (correlated with the
  intercept of `g`, Ω_k ~ LKJ(1)) and `x||g` (uncorrelated) terms, filled by a script that
  parses the lme4 syntax of `formula` and hand-checked where it fails. The contract reads
  structured columns only; nothing parses `formula`. Nested factors need nothing new:
  `grouping_factors` already writes `(1|a/b)` as `a;a:b`.
- Why: 97 of 714 documented models carry a slope, and intercept-only would make 14% of the
  problems not their documented model.
- Clarified 2026-10-09 (#27, after an outside review): `x||g` is independent of the intercept
  and of every other slope of `g`. Both kinds of term act on the standardized column, so a
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

## Amendment 2026-10-10: the grill of roadmap item 5

**The intercept's prior.**

- Decision: the intercept's prior, Normal(0, 2.5), is on the intercept at the mean of every
  design column over the rows a fit sees (brms's default centering), not at the zero of the
  binary and contrast columns. The draws report the uncentered intercept, `Intercept`, as
  brms does.
- Why: it is brms's default and current practice; on z-scored covariates the two coincide,
  and only the binary and contrast columns move the intercept. metabeta adopts it separately.
- The contract hash does not move: the materialized problem's prior is unchanged, and this
  states its meaning.

## Amendment 2026-10-20: grouped K-fold (#87)

**Splits.**

- Decision: each split regime is dealt into folds, and a fit per fold sees every row outside
  it. The held-out-groups regime deals the groups of the first grouping factor into
  K = min(5, G) folds in a seeded order, each group whole in one fold, and still needs G > 2.
  The held-out-rows regime deals into 5 folds the rows it may hold, which are all but the
  first row of each group of every grouping factor in a seeded order. The seed stays the
  hash of the problem id, and the row order is drawn before the group order.
- Decision: a method's score in a regime is the mean over its held-out rows, each held out
  once.
- Why: in the experiment of #47 (`experiments/kfold`), a single 10% split was too noisy for
  per-problem scores. Under another seed, the problems' ranking by the log-score gap between
  a mixed model and a GLM reproduced with Spearman ρ of only 0.59 for held-out rows and 0.44
  for held-out groups. Grouped K-fold raised ρ to 0.89 and 0.87, which more than halves
  1 − ρ, the rule fixed before the experiment ran.

**The materialized problem.**

- Decision: the table's `rows` and `groups` columns hold the fold that holds each row out,
  and −1 for a row the held-out-rows regime never holds. The standardization is computed per
  fold on the rows its fit sees, so the record carries a set of scales per fold, and the full
  table counts as one fold that holds nothing out.

**Fits.**

- Decision: a predictive line fits each fold's seen rows, K fits per regime instead of one,
  and so does the reference's posterior predictive from suite 1.2 (ADR 0005).

**Hashes.**

- Decision: every contract hash moves, as a patch, since no suite is frozen before
  release 1.1.

## Amendment 2026-10-21: integer covariates (#108)

**Typing.**

- Decision: an integer covariate is continuous however few its values, unless the source
  stores it as a factor or the row's `types` declares it categorical. A column the documented
  formula wraps in `factor()` is declared categorical.
- Why: the earlier rule made an integer column with at most 10 values categorical. In 49 of the
  608 candidates the source fits such a column as one slope, which the problem replaced by K − 1
  contrasts, and a random slope on it grew a 2 × 2 block into a K × K one. Only four candidates
  wrap an integer column in `factor()`.

**Hashes.**

- Decision: the 49 contract hashes move, as a patch, since no suite is frozen before
  release 1.1.

## Amendment 2026-10-25: constant design columns (#131)

**Coding.**

- Decision: a design column with one value over the kept rows is dropped, as lme4 drops the
  columns of a rank-deficient model matrix, and the materialized problem lists it in
  `dropped_columns`.
- Why: no likelihood identifies the coefficient of such a column. Three candidates had one.
  The width and length of ros Helicopters are fixed over its 20 flights, so z-scoring turned
  them into rounding noise, and Helicopters keeps only its intercept. Empty interaction cells
  in liutu_2026_zenodo_3 and timmer_2024_osf_15 gave all-zero contrasts, whose coefficients
  never met the likelihood.

**Refusals.**

- Decision: a row is refused when a covariate varies only over the rows without a response.
- Why: Stata's copies of Phenobarb and Quinidine put a dose of 0 on each observation row and
  the doses on dosing rows without a concentration. Dropping the constant dose would state a
  model of another quantity. nlme's copies leave the dose missing on observation rows, so no
  row of theirs is complete and they were refused already. The rule reads the rows without a
  response rather than every dropped row, which would also refuse six of the survey's designs
  over every column.

**Hashes.**

- Decision: every contract hash moves, as a patch, since no suite is frozen before
  release 1.1. Every record gains `dropped_columns`.
