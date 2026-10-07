# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); frame and
method in [`README.md`](README.md). Every number below is filled by `merge.py` from
`dimensions.csv` and `columns.csv` on each merge; edit `SUMMARY.template.md`, never this file.
Quantiles are observed values, at or below the level in the lower half and at or above it in
the upper half. Per-factor axes count a dataset once per grouping factor, dataset axes once per
registry row. The last column of each axis table is the practice survey's upper quantile, the
maximum over the v1 families' values in [`../practice/quantiles.yaml`](../practice/quantiles.yaml)
(the minimum for the smallest group size), read at merge time; `–` where the practice survey
has no such axis. These are evidence for `docs/design/envelope.md`, not the envelope itself.

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
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

${table_d_doc}

${table_d_all}

## Response, reader and published model

${table_response_type}

${table_reader}

${table_published_model}
