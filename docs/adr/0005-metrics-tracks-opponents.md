---
status: accepted, amended 2026-10-10 and 2026-11-19
date: 2026-10-08
---

# 0005 - Three tracks, scale-free metrics, opponent lines that target the same posterior

**Posterior track.**

- Decision: per marginal, Wasserstein-1 against the reference, scaled by the reference SD;
  coverage of the reference's central 50% and 90% intervals for the practitioner.
- Why W1: closed form in one dimension, no kernel, a unit (posterior SDs of mass moved).
- Decision: one joint metric on the standardized global parameters. The classifier two-sample
  test (C2ST, sbibm's primary; fixed small MLP, five-fold; 0.5 means indistinguishable) and MMD
  with the median heuristic are both computed in suite 1.1, and one is chosen empirically in
  the opponent-line ticket, read against the chain-split null.
- Why a joint metric: an approximation with every marginal right and the correlations wrong
  (mean-field VI) is invisible to the first two.
- Rejected: energy distance and rank statistics, as a second kernel metric and a
  metabeta-specific one.
- There is no Gelman-sphere standard for "approximation versus NUTS"; posteriordb compares
  means and SDs against Monte Carlo error, which the scaled W1 subsumes.

> Amended 2026-11-19 below: coverage leaves this track, a rank statistic and the signed
> comparisons of means and SDs join W1, and C2ST alone is the joint metric.

**Predictive track.**

- Decision: the two seeded regimes of ADR 0001; log score where a predictive density exists,
  CRPS for continuous and Brier for binary and binomial responses as the universal pair, RMSE
  and AUC secondary for the ML reader.
- Decision: the reference's posterior predictive is the ceiling; the group-held-out regime
  integrates over a new group's random effects.

**Oracle track.**

- Decision: defined in ADR 0001, references shipped from suite 1.2; SBC-scale replication is
  the user's compute.

**Opponent lines, posterior track.**

- Decision: all from the one brms-generated Stan model, so prior and target are identical:
  NUTS at ladder level 0 (the hurried user), Pathfinder, Laplace (CmdStan's `laplace`),
  mean-field ADVI.
- Why mean-field ADVI: cheap, expected, and its failure on hierarchical geometry is a result to
  state rather than omit.
- Rejected: full-rank ADVI; glmmTMB (a flat-prior point estimate muddles a posterior
  benchmark); INLA and MCMCglmm (priors cannot be made to match; Horizon).

  > Superseded in part by the releases regrouped on 2026-10-09: INLA and MCMCglmm are dropped,
  > not parked on the horizon.

**Opponent lines, predictive track.**

- Decision: TabPFN with the group id as a categorical feature and without it, GPBoost (tree
  boosting with random effects), a glmmTMB plug-in prediction, a GLM ignoring groups
  (OpenClustered's line).
- Rejected: MERF, for want of a maintained package.

> Amended 2026-11-19 below: lme4 replaces glmmTMB, and a decision track joins the three.

**Not measured.**

- Wall-clock (ADR 0004).

## Amendment 2026-10-10: the grill of roadmap item 5

- Decision: the predictive track's ceiling, the reference's posterior predictive on each
  regime's seen rows, ships with suite 1.2; suite 1.1's predictive track carries the
  opponent lines without it.
- Decision: whether the regimes stay one seeded 10% split or become grouped K-fold (#47) is
  settled before suite 1.1 freezes, by a lab note scoring cheap predictive lines (a GLM, a
  REML mixed model) under both. After the freeze, a change of the splits is a new contract.
- Why: the splits are in the materialized problem and so in the contract hash.

> Settled 2026-10-20 by #47: grouped K-fold in both regimes (ADR 0001's amendment of that
> date).

> Superseded in part by the amendment of 2026-11-19 below: the predictive track's opponent
> lines ship with suite 1.2, beside the ceiling.

## Amendment 2026-11-19: the posterior track's metrics, and which release scores what

**Releases.**

- Decision: release 1.1.0 freezes suite 1.1 with its references and the code that scores draws
  against them. The opponent lines' scores follow in a later 1.1 patch, as added files.
- Why: a suite is its membership, its hashes and its references, and a user can score a method
  once these and the metrics exist.
- Decision: no opponent line is scored before the rule that combines the per-problem scores
  across the suite is published.
- Why: a threshold chosen after the lines' scores are known can be tuned to them.
- Decision: the whole predictive track ships with suite 1.2, its opponent lines beside the
  ceiling.
- Why: a line's score is read against the ceiling, and suite 1.1 has none.

**Per parameter.**

- Decision: four numbers per parameter, each beside its chain-split null:
  - W1 against the reference, in reference SDs;
  - the method's posterior mean minus the reference's, in reference SDs;
  - the method's posterior SD over the reference's;
  - a rank statistic: the rank of each reference draw within the method's draws, and how far
    those ranks are from uniform.
- Decision: they are computed for every global parameter and every random effect whose draws
  the reference holds in full. A factor stored as summaries (ADR 0004) is not scored.
- Decision: each number carries its parameter's class, and no reduction pools across classes.
- Why: a problem with five fixed effects and a thousand random effects has one pooled number,
  which the random effects decide by count.
- Why W1 stays the distance: in one dimension it is the area between the two distribution
  functions, with no kernel or bandwidth to choose. It bounds the error of the posterior mean
  and of every other 1-Lipschitz summary (Kantorovich-Rubinstein), it equals the mean error over
  all quantiles, and it grows with a shift where a bounded kernel levels off.
- Why the mean and the SD beside it: they are signed, so they show which way a method is off
  and whether it is too narrow.
- Why a rank statistic, which this ADR rejected as metabeta-specific: it compares the shapes of
  two posteriors on the probability scale, where a skewed SD does not set the unit, and ranks of
  one sample within another are the construction of simulation-based calibration
  ([Talts et al. 2018](https://arxiv.org/abs/1804.06788)).
- Decision: coverage leaves the posterior track and stays on the oracle track.
- Why: coverage is read against a true parameter, and the reference is one prior's posterior.
- Rejected: the RMSE or the Pearson correlation of the posterior means, which are computed
  across a problem's parameters and so pool them.

**Joint.**

- Decision: C2ST over the global parameters is the one joint metric, and MMD is dropped.
  scikit-learn becomes a dependency.
- Why: MMD's bandwidth is computed from the pooled draws, so the method moves its own yardstick,
  and its value has no unit a reader knows. It adds nothing C2ST does not show
  ([TabDGP's ADR 0008](https://github.com/adkipnis/tabdgp/blob/main/docs/adr/0008-summary-vectors-compared-on-ranks.md)).
- C2ST costs a dependency, a seed and a training budget.

**Draws and the null.**

- Decision: a method hands in exactly 4,000 draws, a column per parameter under the contract's
  names on the standardized scale, as the reference's files are. Every global parameter is
  required; random effects are optional, whole per factor. More draws are thinned and weighted
  ones resampled by the method, and fewer are refused.
- Why 4,000: it is the reference's count. The effective sample size is what matters, and the
  count is the pragmatic line. With fewer draws a perfect method scores above the null.
- Decision: the chain-split null scores two of the reference's chains against the other two,
  averaged over the three ways to split four chains. It is a conservative floor, since 2,000
  draws carry more noise than 4,000.
- Decision: the nulls are frozen: a script computes them once per problem, they are stored
  beside the problem's draws, and they are recomputed only when the code of a metric changes.
- Why: every user reads the same floor, and it is published before any method is scored.

**The experiment that settles two forms.**

- Decision: the classifier and the rank statistic's form are chosen by an experiment over the
  reference draws of every problem of suite 1.1, with its rules fixed here before it runs.
- Two of a problem's chains are perturbed in a known way and scored against the other two: a
  shifted mean, an inflated and a deflated scale, a marginal replaced by a Gaussian of its mean
  and SD, the correlations broken by permuting each column, each over a grid of sizes. A
  perturbation is detected on a problem when its score exceeds the largest of the problem's
  three null scores.
- Classifier: scikit-learn's random forest with its defaults, as TabDGP's ADR 0008 chose it,
  unless sbibm's MLP detects the broken correlations on at least 10 points more of the problems.
  The forest grows the same trees under any monotone transform, so its inputs need no scale.
- Form: the area between the ranks' distribution function and the diagonal, doubled, so that 0
  is the same shape and 1 is disjoint, unless metabeta's form (the 10, 25, 50, 75 and 90%
  quantiles of the ranks against uniform) detects some perturbation on at least 10 points more
  of the problems.
- The rank statistic is named after the experiment. It is dropped if it detects no perturbation
  on at least 10 points more of the problems than W1 and its curves read no more clearly.

**Decision track.**

- Decision: a fourth track scores a method that reports a point estimate and an interval
  (e.g. lme4). On a problem it scores the method's failures and its agreement with the
  reference; on an oracle replicate its errors against the truth. What agreement measures is
  settled with the track's lines.
- Why agreement and not error: the reference holds one prior's answer, which a method without
  that prior does not target.

**Opponent lines.**

- Decision: lme4 replaces glmmTMB on the predictive track.
- Why: `mixedbench.frequentist` already fits it, and `experiments/kfold` checked its prediction
  for a new group. glmmTMB would be a second R fitter for the same estimate.
