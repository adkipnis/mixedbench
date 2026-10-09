---
status: accepted
date: 2026-10-08
---

# 0005 — Three tracks, scale-free metrics, opponent lines that target the same posterior

**Posterior track.**

- Decision: per marginal, Wasserstein-1 against the reference, scaled by the reference SD;
  coverage of the reference's central 50% and 90% intervals for the practitioner.
- Why W1: closed form in one dimension, no kernel, a unit (posterior SDs of mass moved).
- Decision: one joint metric on the standardised global parameters. The classifier two-sample
  test (C2ST, sbibm's primary; fixed small MLP, five-fold; 0.5 means indistinguishable) and MMD
  with the median heuristic are both computed in suite 1.1, and one is chosen empirically in
  the opponent-line ticket, read against the chain-split null.
- Why a joint metric: an approximation with every marginal right and the correlations wrong
  (mean-field VI) is invisible to the first two.
- Rejected: energy distance and rank statistics, as a second kernel metric and a
  metabeta-specific one.
- There is no Gelman-sphere standard for "approximation versus NUTS"; posteriordb compares
  means and SDs against Monte Carlo error, which the scaled W1 subsumes.

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

  > Superseded in part by `ROADMAP.md` (2026-10-09): INLA and MCMCglmm are dropped, not parked
  > on the horizon.

**Opponent lines, predictive track.**

- Decision: TabPFN with the group id as a categorical feature and without it, GPBoost (tree
  boosting with random effects), a glmmTMB plug-in prediction, a GLM ignoring groups
  (OpenClustered's line).
- Rejected: MERF, for want of a maintained package.

**Not measured.**

- Wall-clock (ADR 0004).
