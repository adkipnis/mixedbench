---
status: accepted
date: 2026-10-20
---

# 0006 — The measurement pass: quirk statistics per column, per column × factor, per factor pair and per row

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
  with a measured response; the response is not, since it is the outcome's business.
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
