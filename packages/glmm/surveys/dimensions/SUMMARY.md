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

**Corpus.** 154 registry rows over 144 datasets and 214 grouping
factors; per tier R 154. Excluded: 200 objects (no grouping structure 181, unreadable format 9, derived or duplicated table 7, simulated data 3).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 154 | 12 | 24 | 35 | 196 | 2471 | 7185 | 73421 | 23025 |
| tier R | 154 | 12 | 24 | 35 | 196 | 2471 | 7185 | 73421 |  |
| without agridat | 125 | 18 | 24 | 32 | 198 | 4059 | 7230 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 154 | 1 | 1 | 1 | 1 | 2 | 3 | 4 | 3 |
| tier R | 154 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 125 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 104 | 49% |
| nested | 55 | 26% |
| crossed | 42 | 20% |
| mixed | 13 | 6% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 2 | 3 | 4 | 18 | 234 | 888 | 10767 | 414 |
| tier R | 214 | 2 | 3 | 4 | 18 | 234 | 888 | 10767 |  |
| without agridat | 161 | 2 | 4 | 5 | 20 | 294 | 1374 | 10767 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 1 | 1 | 1 | 6 | 28 | 53 | 539 | 1 |
| tier R | 214 | 1 | 1 | 1 | 6 | 28 | 53 | 539 |  |
| without agridat | 161 | 1 | 1 | 1 | 5 | 25 | 50 | 539 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 1 | 1 | 2 | 8 | 36 | 56 | 539 | – |
| tier R | 214 | 1 | 1 | 2 | 8 | 36 | 56 | 539 |  |
| without agridat | 161 | 1 | 1 | 2 | 6 | 30 | 55 | 539 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 1 | 2 | 3 | 8 | 49 | 65 | 539 | – |
| tier R | 214 | 1 | 2 | 3 | 8 | 49 | 65 | 539 |  |
| without agridat | 161 | 1 | 2 | 3 | 8 | 47 | 63 | 539 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 1 | 3 | 3 | 9 | 59 | 137 | 539 | – |
| tier R | 214 | 1 | 3 | 3 | 9 | 59 | 137 | 539 |  |
| without agridat | 161 | 2 | 3 | 4 | 9 | 59 | 174 | 539 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 2 | 3 | 4 | 10 | 83 | 198 | 969 | 300 |
| tier R | 214 | 2 | 3 | 4 | 10 | 83 | 198 | 969 |  |
| without agridat | 161 | 2 | 3 | 4 | 10 | 116 | 290 | 969 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.589). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 0.0251 | 1.579 | 2.9945 | inf | inf | inf | inf | – |
| tier R | 214 | 0.0251 | 1.579 | 2.9945 | inf | inf | inf | inf |  |
| without agridat | 161 | 0.3236 | 1.579 | 2.7846 | inf | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 0 | 0 | 0 | 0 | 0.0476 | 0.1525 | 0.9964 | – |
| tier R | 214 | 0 | 0 | 0 | 0 | 0.0476 | 0.1525 | 0.9964 |  |
| without agridat | 161 | 0 | 0 | 0 | 0 | 0.0667 | 0.1346 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 214 | 0 | 0 | 0 | 0 | 0.5586 | 0.7869 | 5.899 | – |
| tier R | 214 | 0 | 0 | 0 | 0 | 0.5586 | 0.7869 | 5.899 |  |
| without agridat | 161 | 0 | 0 | 0 | 0 | 0.5917 | 0.7869 | 1.7167 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 121 | 40% |
| categorical | 96 | 32% |
| binary | 74 | 24% |
| ordered | 13 | 4% |

| level | n | share |
|---|---|---|
| within | 174 | 57% |
| group | 130 | 43% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 109 | 2 | 3 | 3 | 4 | 9 | 15 | 56 | – |
| tier R | 109 | 2 | 3 | 3 | 4 | 9 | 15 | 56 |  |
| without agridat | 81 | 2 | 3 | 3 | 4 | 7 | 9 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 44 | 40% |
| 4 | 35 | 32% |
| 5 | 6 | 6% |
| 6 | 5 | 5% |
| 7 | 4 | 4% |
| 14 | 2 | 2% |
| 2 | 2 | 2% |
| 10 | 2 | 2% |
| 8 | 2 | 2% |
| 56 | 1 | 1% |
| 9 | 1 | 1% |
| 15 | 1 | 1% |
| 30 | 1 | 1% |
| 16 | 1 | 1% |
| 20 | 1 | 1% |
| 49 | 1 | 1% |

Implied design columns of a model under the observed categorical share
(0.359) and mean columns per categorical (4.716):
9 terms 20.99 columns, 14 terms 32.65 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 154 | 0 | 0 | 0 | 3 | 15 | 27 | 55 | 11 |
| tier R | 154 | 0 | 0 | 0 | 3 | 15 | 27 | 55 |  |
| without agridat | 125 | 0 | 0 | 1 | 3 | 13 | 15 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 154 | 0 | 0 | 1 | 5 | 23 | 32 | 60 | – |
| tier R | 154 | 0 | 0 | 1 | 5 | 23 | 32 | 60 |  |
| without agridat | 125 | 0 | 1 | 1 | 5 | 17 | 27 | 55 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 122 | 79% |
| count | 11 | 7% |
| binary | 11 | 7% |
| ordinal | 6 | 4% |
| binomial | 3 | 2% |
| categorical | 1 | 1% |

| reader | n | share |
|---|---|---|
| pyreadr | 124 | 81% |
| rscript | 30 | 19% |

| published | n | share |
|---|---|---|
| yes | 140 | 91% |
| no | 14 | 9% |
