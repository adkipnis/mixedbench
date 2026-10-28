---
status: accepted, amended 2026-10-27
date: 2026-10-20
---

# 0006 - The measurement pass: quirk statistics per column, per column × factor, per factor pair and per row

The registry measures sizes (ADR 0002's census: observations, groups, group sizes, design
columns) and little else about a table's columns. TabDGP ([adkipnis/tabdgp](https://github.com/adkipnis/tabdgp))
fits its default hyperprior to this registry and proves it with a two-sample test and a
containment test over summary statistics of real and generated tables, so the statistics must
be computed here, from the cached tables, and shipped in a pinned release. Grilled on
2026-10-20 ([#71](https://github.com/adkipnis/mixedbench/issues/71)).

**Keys and files.**

- Decision: one file per key, as the registry already does. Per column, `columns.csv` gains
  the marginal statistics; per column × grouping factor, `column_factors.csv`; per pair of
  grouping factors, `factor_pairs.csv`; per registry row, `dimensions.csv` gains the two
  condition numbers beside `d_doc` and `d_all`. Every new column is an axis of
  `quantiles.yaml` under `axes`, counted once per its key, and `SUMMARY.md` shows one pooled
  table per file.
- Why: a consumer reads a wide CSV per key with no pivot, and metabeta's contract test pins
  `quantiles.yaml`'s top-level keys, so new axes go under `axes`.
- Rejected: one long file (key, statistic, value), which hides the keys in a column and needs
  a pivot on every read.
- Decision: every column `columns.csv` lists is measured, with `in_model` kept, over the rows
  with a measured response; the response's documented model is fitted (the amendment below),
  since its R², ICC and sd(η) are what TabDGP's outcome node must cover.
- Why: filtering to the documented covariates is the consumer's one-line choice; the reverse
  is a rerun.

**The statistics.** Defined, with their blanks, in [`docs/registry.md`](../registry.md).

- Per column: `skewness`, `excess_kurtosis` and `outlier_share` for continuous columns;
  `zero_share`, `min_share` and `max_share` for continuous and ordered columns; `unique_share`
  for every type; `rare_level_share` for binary, categorical and ordered columns; `max_abs_rho`,
  the largest |Spearman| with another measured column.
- Per column × factor, every pair uniformly, group-level columns included:
  `between_group_share`, the adjusted ICC(1); `group_level_r2`, the adjusted R² of the column
  on the factor's group-level columns; `absent_level_share`; `size_rho`; `within_sd_cv`.
- Per factor pair: `relation`, `superior` for a nested pair, `empty_cell_share` for a crossed
  one.
- Per row: `condition_doc` and `condition_all`, the condition index of the contract's design,
  documented and over every measured column.
- Why the adjustments: raw η² tends to 1 as the groups approach the rows, and a group-level
  categorical with many levels fakes a full R²; adjusting both by the group count puts the
  gap between them, the share a latent group-level cause must supply, on one scale.
- Why negatives and inf are kept: a clipped value hides a fact the consumer can clip itself.
- Why the contract's design: it is the design the samplers and the amortized posterior face,
  and the coding stays in one home.
- Rejected: a round-value (heaping) share, scale-dependent and a judgment call that
  `unique_share` and `min_share` cover; per-row leverage, which the condition index and
  `outlier_share` cover; irregular-time statistics, since the registry has no time role and
  TabDGP defers time to its outcome node; the pair statistics for categorical columns with
  more than two levels, which `absent_level_share` and the condition index cover.

**Running and releasing.**

- Decision: `survey/measure.py` runs the whole pass as a script and writes the measured
  files and the summary; `merge.py` calls the same function on every merge.
- Decision: the pass ships as a patch release (1.0.8): no row changes, and the next minor
  release names a suite freeze (ADR 0002, amended 2026-10-20).
- Decision: which quirks real tables show strongly enough to earn a generator axis is TabDGP's
  reading of these files, never a decision taken here.

## Amendment 2026-10-23: the response's documented model, fitted

- Decision: a fifth measured file, `fits.csv`, keyed per grouping factor like
  `dimensions.csv`, holds per registry row with a continuous, binary or count response the
  variance components, R² and sd(η) of its documented model, and per factor its random
  variance and ICC, as [`docs/registry.md`](../registry.md) defines them. The model is the
  registry's `formula` as written, offsets and transforms included, fitted by lme4 on the typed
  table with the family the contract's rule gives the response type; the registry's `family`
  departure rides beside the fit as a flag.
- Why the documented model and not the contract's design: the design carries no offset or
  transform, and R², ICC and sd(η) are scale-free, so the documented model is the fact TabDGP's
  outcome node must cover.
- Why lme4 and one grammar: one fitter is one seam. A formula lme4 refuses (an nlme
  heteroscedastic fit, a nonlinear mean, a smooth, a censored likelihood) is recorded as it
  fails, since each would need a fitter of its own with an R² of its own; a model documented in
  words, with no `|` term, is recorded without a fit.
- Decision: one `status` per fit, the worst that applies of `ok`, `singular`, `warning`,
  `timeout`, `error`, `no_formula`, with the messages kept beside it; the components are
  written for the first three. A fit ends at one hour, recorded as `timeout`, never skipped.
- Why one word: the consumer filters on it, and the decision track (ADR 0005) scores the same
  failures, so the vocabulary is shared from the start.
- Decision: the fitter lives in the package, `mixedbench.frequentist`, with its R script beside
  it as `references` keeps brms: one fixed set back per fit (the status, the fixed effects with
  their Wald standard errors, the variance components, the per-factor variance of Johnson 2014,
  the fixed predictor's variance, sd(η) and the distribution variance of Nakagawa, Johnson and
  Schielzeth 2017). The survey computes R² and ICC from it; the decision track fits the
  contract's problems through the same seam.
- Why: the alternative, a fitter in the survey and another in the decision track, repeats the
  status capture, the family map, the control and the pins three times, with the K-fold
  experiment's.
- Decision: the fits are measured by a cluster pass, not by the merge; a merge leaves
  `fits.csv` as it is, and `survey/HISTORY.md` dates each pass with its R and lme4 versions.
- Rejected: fitting the prose rows by hand-written nonlinear models (typed, and the
  decomposition assumes a linear predictor); `sd_eta_fixed`, the root of `sigma2_fixed`.

## Amendment 2026-10-24: the formula cell holds the formula alone

- Decision: a remark in the `formula` cell moves to `notes`, a column is named as the table
  names it, and a variable the source derives from columns is written as its expression
  (`I(age - 12)`, `ave(IQ, class)`), so that the cell is the model lme4 fits. A model part lme4
  cannot express (a residual structure, a censored or zero-inflated likelihood, a pedigree)
  stays in the cell, and its fit is recorded as it fails.
- Why: the first pass ended 54 fits on a remark or a name, not on their model, and 13 more
  cells needed a date, a principal component or a scaling written out.
- Decision: a subset the source fits, or a frequency weight it repeats rows by, is listed in
  `survey/fits_preparation.csv` and applied before the fit, since a formula cannot carry it.
  The registry keeps its columns, and the contract its whole table.
- Decision: 1.0.8 carries these 67 rows, in `formula` and `notes` alone. The contract never
  reads `formula`, so no hash moves.

## Amendment 2026-10-27: the response's marginal

- Decision: a sixth measured file, `responses.csv`, a row per registry row keyed like
  `dimensions.csv`, holds the response's type, `K`, missing share and the quirk statistics
  `columns.csv` defines for its kind, computed by the same functions, as
  [`docs/registry.md`](../registry.md) defines them. Its statistics are axes of their own in
  `quantiles.yaml`, named `response_` and the statistic, and a table of their own in
  `SUMMARY.md`.
- Why: TabDGP's outcome node draws y as a GLM and then as a GLMM, and `fits.csv` covers the
  documented model but not the response's own type, support, zero share or skewness.
- Decision: the row's `response_type` gives the kind, not the loaded column. Continuous, count
  and binomial responses are continuous, a binomial one as its successes' share of the trials;
  binary and categorical ones are measured as loaded, and an ordinal one as ordered, its levels
  in the order the contract codes them.
- Why: 37 ordinal responses load as integers, which the columns rule would measure by their
  moments and without levels, and nine categorical ones load as integers or ordered factors.
- Decision: the missing share counts every loaded row, and the other statistics only the rows
  with a response. A binomial row of zero trials has no share and counts as missing.
- Why: over the rows with a response the share would be zero by construction, but 101 of 692
  registry rows miss the response on some loaded rows, up to 0.79 (Phenobarb's dosing rows).
- Rejected: a row of `columns.csv` flagged as the response, which the covariates'
  `max_abs_rho`, `d_all`, `condition_all`, `column_factors.csv` and the pooled axes would each
  have to filter out, or their numbers move.
- Decision: the file ships as a registry patch, 1.0.11, and the other measured files stay as
  they are, byte for byte.
