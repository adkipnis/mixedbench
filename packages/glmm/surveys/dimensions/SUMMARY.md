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

**Corpus.** 255 registry rows over 241 datasets and 339 grouping
factors; per tier R 255. Excluded: 556 objects (no grouping structure 498, derived or duplicated table 21, time series without replication 14, simulated data 11, unreadable format 9, response missing or undocumented 3).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 255 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 | 23025 |
| tier R | 255 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| without agridat | 227 | 12 | 21 | 30 | 198 | 3263 | 7185 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 255 | 1 | 1 | 1 | 1 | 2 | 2 | 4 | 3 |
| tier R | 255 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| without agridat | 227 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 185 | 55% |
| nested | 67 | 20% |
| crossed | 64 | 19% |
| mixed | 23 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 2 | 4 | 4 | 18 | 185 | 336 | 10767 | 414 |
| tier R | 339 | 2 | 4 | 4 | 18 | 185 | 336 | 10767 |  |
| without agridat | 286 | 2 | 4 | 4 | 19 | 197 | 537 | 10767 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 1 | 1 | 1 | 6 | 34 | 64 | 567 | 1 |
| tier R | 339 | 1 | 1 | 1 | 6 | 34 | 64 | 567 |  |
| without agridat | 286 | 1 | 1 | 1 | 5 | 32 | 71 | 567 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 1 | 1 | 2 | 7 | 38 | 75 | 583 | – |
| tier R | 339 | 1 | 1 | 2 | 7 | 38 | 75 | 583 |  |
| without agridat | 286 | 1 | 1 | 2 | 6 | 38 | 81 | 583 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 1 | 2 | 3 | 8 | 51 | 110 | 600 | – |
| tier R | 339 | 1 | 2 | 3 | 8 | 51 | 110 | 600 |  |
| without agridat | 286 | 1 | 2 | 3 | 8 | 52 | 152 | 600 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 1 | 2 | 3 | 10 | 61 | 174 | 1204 | – |
| tier R | 339 | 1 | 2 | 3 | 10 | 61 | 174 | 1204 |  |
| without agridat | 286 | 2 | 2 | 3 | 10 | 64 | 218 | 1204 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 2 | 3 | 3 | 11 | 93 | 247 | 7500 | 300 |
| tier R | 339 | 2 | 3 | 3 | 11 | 93 | 247 | 7500 |  |
| without agridat | 286 | 2 | 3 | 3 | 11 | 118 | 306 | 7500 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.575). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf | – |
| tier R | 339 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| without agridat | 286 | 0.0296 | 1.1846 | 2.3435 | inf | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 | – |
| tier R | 339 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| without agridat | 286 | 0 | 0 | 0 | 0 | 0.0428 | 0.1369 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 339 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 | – |
| tier R | 339 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| without agridat | 286 | 0 | 0 | 0 | 0 | 0.6503 | 0.7935 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 220 | 40% |
| binary | 162 | 29% |
| categorical | 157 | 28% |
| ordered | 14 | 3% |

| level | n | share |
|---|---|---|
| within | 338 | 61% |
| group | 215 | 39% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 171 | 2 | 3 | 3 | 4 | 9 | 10 | 56 | – |
| tier R | 171 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| without agridat | 143 | 2 | 3 | 3 | 4 | 8 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 64 | 37% |
| 4 | 47 | 27% |
| 5 | 19 | 11% |
| 6 | 9 | 5% |
| 10 | 6 | 4% |
| 8 | 6 | 4% |
| 7 | 5 | 3% |
| 9 | 5 | 3% |
| 14 | 2 | 1% |
| 2 | 2 | 1% |
| 56 | 1 | 1% |
| 15 | 1 | 1% |
| 16 | 1 | 1% |
| 20 | 1 | 1% |
| 49 | 1 | 1% |
| 17 | 1 | 1% |

Implied design columns of a model under the observed categorical share
(0.309) and mean columns per categorical (4.392):
9 terms 18.44 columns, 14 terms 28.68 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 255 | 0 | 0 | 0 | 3 | 14 | 19 | 55 | 11 |
| tier R | 255 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| without agridat | 227 | 0 | 0 | 0 | 3 | 13 | 15 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 255 | 0 | 0 | 0 | 5 | 20 | 35 | 14966 | – |
| tier R | 255 | 0 | 0 | 0 | 5 | 20 | 35 | 14966 |  |
| without agridat | 227 | 0 | 0 | 1 | 4 | 18 | 35 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 190 | 75% |
| binary | 24 | 9% |
| count | 21 | 8% |
| ordinal | 11 | 4% |
| binomial | 7 | 3% |
| categorical | 2 | 1% |

| reader | n | share |
|---|---|---|
| pyreadr | 219 | 86% |
| rscript | 36 | 14% |

| published | n | share |
|---|---|---|
| yes | 208 | 82% |
| no | 47 | 18% |
