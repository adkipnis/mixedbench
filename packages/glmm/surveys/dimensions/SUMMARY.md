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

**Corpus.** 76 registry rows over 71 datasets and 98 grouping
factors; per tier R 76. Excluded: 168 objects (no grouping structure 157, unreadable format 9, derived or duplicated table 1, response missing or undocumented 1).

## Observations

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 76 | 18 | 30 | 36 | 237 | 7185 | 26796 | 73421 | 23025 |
| tier R | 76 | 18 | 30 | 36 | 237 | 7185 | 26796 | 73421 |  |
| without agridat | 76 | 18 | 30 | 36 | 237 | 7185 | 26796 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 76 | 1 | 1 | 1 | 1 | 2 | 2 | 3 | 3 |
| tier R | 76 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| without agridat | 76 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 55 | 56% |
| nested | 22 | 22% |
| crossed | 18 | 18% |
| mixed | 3 | 3% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 2 | 3 | 5 | 21 | 437 | 1721 | 11598 | 414 |
| tier R | 98 | 2 | 3 | 5 | 21 | 437 | 1721 | 11598 |  |
| without agridat | 98 | 2 | 3 | 5 | 21 | 437 | 1721 | 11598 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 1 | 1 | 1 | 6 | 32 | 56 | 316 | 1 |
| tier R | 98 | 1 | 1 | 1 | 6 | 32 | 56 | 316 |  |
| without agridat | 98 | 1 | 1 | 1 | 6 | 32 | 56 | 316 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 1 | 1 | 2 | 8 | 50 | 63 | 316 | – |
| tier R | 98 | 1 | 1 | 2 | 8 | 50 | 63 | 316 |  |
| without agridat | 98 | 1 | 1 | 2 | 8 | 50 | 63 | 316 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 1 | 3 | 3 | 12 | 60 | 160 | 351 | – |
| tier R | 98 | 1 | 3 | 3 | 12 | 60 | 160 | 351 |  |
| without agridat | 98 | 1 | 3 | 3 | 12 | 60 | 160 | 351 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 2 | 3 | 4 | 14 | 90 | 316 | 510 | – |
| tier R | 98 | 2 | 3 | 4 | 14 | 90 | 316 | 510 |  |
| without agridat | 98 | 2 | 3 | 4 | 14 | 90 | 316 | 510 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 2 | 3 | 4 | 18 | 198 | 387 | 969 | 300 |
| tier R | 98 | 2 | 3 | 4 | 18 | 198 | 387 | 969 |  |
| without agridat | 98 | 2 | 3 | 4 | 18 | 198 | 387 | 969 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.469). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 0.6747 | 1.2852 | 1.9069 | 91.9082 | inf | inf | inf | – |
| tier R | 98 | 0.6747 | 1.2852 | 1.9069 | 91.9082 | inf | inf | inf |  |
| without agridat | 98 | 0.6747 | 1.2852 | 1.9069 | 91.9082 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 | – |
| tier R | 98 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 |  |
| without agridat | 98 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 98 | 0 | 0 | 0 | 0.1362 | 0.7204 | 0.8761 | 1.2161 | – |
| tier R | 98 | 0 | 0 | 0 | 0.1362 | 0.7204 | 0.8761 | 1.2161 |  |
| without agridat | 98 | 0 | 0 | 0 | 0.1362 | 0.7204 | 0.8761 | 1.2161 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 68 | 44% |
| categorical | 42 | 27% |
| binary | 37 | 24% |
| ordered | 9 | 6% |

| level | n | share |
|---|---|---|
| within | 100 | 64% |
| group | 56 | 36% |

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
| 2 | 2 | 4% |
| 5 | 2 | 4% |
| 14 | 1 | 2% |
| 7 | 1 | 2% |
| 56 | 1 | 2% |

Implied design columns of a model under the observed categorical share
(0.327) and mean columns per categorical (3.941):
9 terms 17.65 columns, 14 terms 27.46 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table (`d_all`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 76 | 0 | 0 | 1 | 3 | 13 | 21 | 55 | 11 |
| tier R | 76 | 0 | 0 | 1 | 3 | 13 | 21 | 55 |  |
| without agridat | 76 | 0 | 0 | 1 | 3 | 13 | 21 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 76 | 0 | 0 | 1 | 3 | 10 | 22 | 55 | – |
| tier R | 76 | 0 | 0 | 1 | 3 | 10 | 22 | 55 |  |
| without agridat | 76 | 0 | 0 | 1 | 3 | 10 | 22 | 55 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 60 | 79% |
| binary | 8 | 11% |
| count | 5 | 7% |
| binomial | 2 | 3% |
| categorical | 1 | 1% |

| reader | n | share |
|---|---|---|
| pyreadr | 76 | 100% |

| published | n | share |
|---|---|---|
| yes | 69 | 91% |
| no | 7 | 9% |
