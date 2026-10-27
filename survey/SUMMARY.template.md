# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); the files in
[`docs/registry.md`](../docs/registry.md), the method in [`README.md`](../survey/README.md). Evidence for the envelope in metabeta's
design docs, not the envelope itself.

How to read the tables:

- Every number is filled from the measured files by `merge.py` on each merge, or by
  `measure.py`; edit `SUMMARY.template.md`, never this file.
- Quantiles are observed values, never interpolated: below the median the nearest value at
  or below the level, from the median on the nearest value at or above it.
- Per-factor axes (groups, group sizes, imbalance) count a dataset once per grouping factor;
  dataset axes (observations, grouping factors, design columns) once per registry row; `K`
  once per categorical covariate of a documented model.
- A quirk statistic counts once per row of its file that defines it: a column, a column and
  grouping factor, a crossed pair of factors or a registry row. Its table shows the pooled
  quantiles, `quantiles.yaml` also those per tier and without agridat. Definitions are in the
  [`docs/registry.md`](../docs/registry.md).
- The last column of an axis table, `practice`, is the practice survey's upper decile, the
  maximum over the v1 families in [`practice_quantiles.yaml`](../survey/practice_quantiles.yaml)
  (the minimum for the smallest group size), read at merge time; `–` where the practice survey
  has no such axis.

**Corpus.** ${n_rows} registry rows over ${n_objects} datasets and ${n_factor_rows} grouping
factors; per tier ${tiers}. Excluded: ${n_excluded} objects (${excluded_reasons}).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

${table_n_obs}

## Grouping factors

${table_n_grouping_factors}

${table_relation}

## Groups per factor

${table_n_groups}

## Group size

${table_group_size_min}

${table_group_size_lower}

${table_group_size_median}

${table_group_size_upper}

${table_group_size_max}

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: ${balanced_share}). Singleton share and the
coefficient of variation are readable companions.

${table_alpha}

${table_singleton_share}

${table_cv}

## Covariates of the documented models

${table_covariate_type}

${table_level}

Levels of the categorical covariates:

${table_K}

${table_k_distribution}

Implied design columns of a model under the observed categorical share
(${categorical_share}) and mean columns per categorical (${mean_columns_per_categorical}):
${implied_columns}.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

${table_d_doc}

${table_d_all}

The condition index of the documented design and of the design over every column.

${table_conditions}

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

${table_column_statistics}

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

${table_column_factor_statistics}

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

${table_pair_statistics}

${table_pair_relation}

${table_superior}

## Quirk statistics per response

Every registry row's response, by the statistics its type defines: a binomial one as its
successes' share of the trials, an ordinal one by its levels.

${table_response_statistics}

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

${table_fit_statistics}

${table_status}

## Response, reader and published model

${table_response_type}

${table_reader}

${table_published_model}

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

${tier_d}

## Flat sample

The survey's tables filed `no grouping structure`, screened, read again and measured beside the
registry by `flat.py`, every column by the statistics `columns.csv` defines; the files and the
sample's rule are in [`docs/registry.md`](../docs/registry.md). An axis both samples share ends
its table above with the flat sample's row.

${flat_corpus}

${table_flat_column_type}

${table_flat_statistics}
