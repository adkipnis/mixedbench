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

**Corpus.** 75 registry rows over 70 datasets and 102 grouping
factors; per tier R 75. Excluded: 169 objects (no grouping structure 156, unreadable format 9, simulated data 3, derived or duplicated table 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 75 | 18 | 30 | 40 | 234 | 7185 | 24613 | 73421 | 23025 |
| tier R | 75 | 18 | 30 | 40 | 234 | 7185 | 24613 | 73421 |  |
| without agridat | 75 | 18 | 30 | 40 | 234 | 7185 | 24613 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 75 | 1 | 1 | 1 | 1 | 2 | 2 | 3 | 3 |
| tier R | 75 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| without agridat | 75 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 50 | 49% |
| nested | 28 | 27% |
| crossed | 18 | 18% |
| mixed | 6 | 6% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 2 | 4 | 5 | 21 | 316 | 1595 | 10767 | 414 |
| tier R | 102 | 2 | 4 | 5 | 21 | 316 | 1595 | 10767 |  |
| without agridat | 102 | 2 | 4 | 5 | 21 | 316 | 1595 | 10767 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 1 | 1 | 1 | 6 | 30 | 54 | 316 | 1 |
| tier R | 102 | 1 | 1 | 1 | 6 | 30 | 54 | 316 |  |
| without agridat | 102 | 1 | 1 | 1 | 6 | 30 | 54 | 316 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 1 | 1 | 2 | 8 | 40 | 56 | 316 | – |
| tier R | 102 | 1 | 1 | 2 | 8 | 40 | 56 | 316 |  |
| without agridat | 102 | 1 | 1 | 2 | 8 | 40 | 56 | 316 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 1 | 3 | 3 | 10 | 60 | 160 | 351 | – |
| tier R | 102 | 1 | 3 | 3 | 10 | 60 | 160 | 351 |  |
| without agridat | 102 | 1 | 3 | 3 | 10 | 60 | 160 | 351 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 2 | 3 | 4 | 12 | 90 | 257 | 510 | – |
| tier R | 102 | 2 | 3 | 4 | 12 | 90 | 257 | 510 |  |
| without agridat | 102 | 2 | 3 | 4 | 12 | 90 | 257 | 510 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 2 | 3 | 4 | 13 | 188 | 351 | 969 | 300 |
| tier R | 102 | 2 | 3 | 4 | 13 | 188 | 351 | 969 |  |
| without agridat | 102 | 2 | 3 | 4 | 13 | 188 | 351 | 969 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.48). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 0.6747 | 1.2852 | 1.9306 | 261.2424 | inf | inf | inf | – |
| tier R | 102 | 0.6747 | 1.2852 | 1.9306 | 261.2424 | inf | inf | inf |  |
| without agridat | 102 | 0.6747 | 1.2852 | 1.9306 | 261.2424 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 | – |
| tier R | 102 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 |  |
| without agridat | 102 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 102 | 0 | 0 | 0 | 0.0636 | 0.7106 | 0.8761 | 1.2161 | – |
| tier R | 102 | 0 | 0 | 0 | 0.0636 | 0.7106 | 0.8761 | 1.2161 |  |
| without agridat | 102 | 0 | 0 | 0 | 0.0636 | 0.7106 | 0.8761 | 1.2161 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 68 | 44% |
| categorical | 42 | 27% |
| binary | 37 | 24% |
| ordered | 9 | 6% |

| level | n | share |
|---|---|---|
| within | 91 | 58% |
| group | 65 | 42% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 51 | 2 | 3 | 3 | 4 | 6 | 7 | 56 | – |
| tier R | 51 | 2 | 3 | 3 | 4 | 6 | 7 | 56 |  |
| without agridat | 51 | 2 | 3 | 3 | 4 | 6 | 7 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 23 | 45% |
| 4 | 17 | 33% |
| 6 | 4 | 8% |
| 5 | 2 | 4% |
| 2 | 2 | 4% |
| 14 | 1 | 2% |
| 7 | 1 | 2% |
| 56 | 1 | 2% |

Implied design columns of a model under the observed categorical share
(0.327) and mean columns per categorical (3.941):
9 terms 17.65 columns, 14 terms 27.46 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 75 | 0 | 0 | 1 | 3 | 13 | 21 | 55 | 11 |
| tier R | 75 | 0 | 0 | 1 | 3 | 13 | 21 | 55 |  |
| without agridat | 75 | 0 | 0 | 1 | 3 | 13 | 21 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 75 | 0 | 0 | 1 | 4 | 15 | 31 | 55 | – |
| tier R | 75 | 0 | 0 | 1 | 4 | 15 | 31 | 55 |  |
| without agridat | 75 | 0 | 0 | 1 | 4 | 15 | 31 | 55 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 59 | 79% |
| binary | 8 | 11% |
| count | 5 | 7% |
| binomial | 2 | 3% |
| categorical | 1 | 1% |

| reader | n | share |
|---|---|---|
| pyreadr | 75 | 100% |

| published | n | share |
|---|---|---|
| yes | 68 | 91% |
| no | 7 | 9% |
