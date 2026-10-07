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

**Corpus.** 240 registry rows over 234 datasets and 324 grouping
factors; per tier R 240. Excluded: 563 objects (no grouping structure 498, derived or duplicated table 21, time series without replication 14, simulated data 11, response missing or undocumented 10, unreadable format 9).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 240 | 12 | 20 | 30 | 220 | 3078 | 6402 | 73421 | 23025 |
| tier R | 240 | 12 | 20 | 30 | 220 | 3078 | 6402 | 73421 |  |
| without agridat | 212 | 12 | 20 | 30 | 235 | 3236 | 7185 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 240 | 1 | 1 | 1 | 1 | 2 | 3 | 4 | 3 |
| tier R | 240 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 212 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 170 | 52% |
| nested | 67 | 21% |
| crossed | 64 | 20% |
| mixed | 23 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 2 | 4 | 4 | 20 | 190 | 336 | 10767 | 414 |
| tier R | 324 | 2 | 4 | 4 | 20 | 190 | 336 | 10767 |  |
| without agridat | 271 | 2 | 4 | 4 | 21 | 197 | 539 | 10767 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 1 | 1 | 1 | 6 | 35 | 64 | 567 | 1 |
| tier R | 324 | 1 | 1 | 1 | 6 | 35 | 64 | 567 |  |
| without agridat | 271 | 1 | 1 | 1 | 5 | 32 | 79 | 567 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 1 | 1 | 2 | 7 | 38 | 72 | 583 | – |
| tier R | 324 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| without agridat | 271 | 1 | 1 | 2 | 6 | 38 | 81 | 583 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 1 | 2 | 3 | 8 | 50 | 105 | 600 | – |
| tier R | 324 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| without agridat | 271 | 1 | 2 | 3 | 8 | 51 | 152 | 600 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 1 | 2 | 3 | 9 | 61 | 154 | 600 | – |
| tier R | 324 | 1 | 2 | 3 | 9 | 61 | 154 | 600 |  |
| without agridat | 271 | 2 | 2 | 3 | 9 | 63 | 217 | 600 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 2 | 3 | 3 | 10 | 92 | 206 | 1666 | 300 |
| tier R | 324 | 2 | 3 | 3 | 10 | 92 | 206 | 1666 |  |
| without agridat | 271 | 2 | 3 | 3 | 10 | 118 | 290 | 1666 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.586). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 0.0251 | 1.5472 | 3.2 | inf | inf | inf | inf | – |
| tier R | 324 | 0.0251 | 1.5472 | 3.2 | inf | inf | inf | inf |  |
| without agridat | 271 | 0.0363 | 1.5472 | 2.8425 | inf | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 | – |
| tier R | 324 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| without agridat | 271 | 0 | 0 | 0 | 0 | 0.0428 | 0.1369 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 324 | 0 | 0 | 0 | 0 | 0.5559 | 0.7869 | 5.899 | – |
| tier R | 324 | 0 | 0 | 0 | 0 | 0.5559 | 0.7869 | 5.899 |  |
| without agridat | 271 | 0 | 0 | 0 | 0 | 0.5586 | 0.7869 | 4.4575 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 218 | 41% |
| binary | 160 | 30% |
| categorical | 144 | 27% |
| ordered | 14 | 3% |

| level | n | share |
|---|---|---|
| within | 319 | 60% |
| group | 217 | 40% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 158 | 2 | 3 | 3 | 4 | 9 | 14 | 56 | – |
| tier R | 158 | 2 | 3 | 3 | 4 | 9 | 14 | 56 |  |
| without agridat | 130 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 60 | 38% |
| 4 | 44 | 28% |
| 5 | 15 | 9% |
| 6 | 9 | 6% |
| 10 | 6 | 4% |
| 7 | 5 | 3% |
| 8 | 5 | 3% |
| 9 | 4 | 3% |
| 14 | 2 | 1% |
| 2 | 2 | 1% |
| 56 | 1 | 1% |
| 15 | 1 | 1% |
| 16 | 1 | 1% |
| 20 | 1 | 1% |
| 49 | 1 | 1% |
| 17 | 1 | 1% |

Implied design columns of a model under the observed categorical share
(0.295) and mean columns per categorical (4.449):
9 terms 18.15 columns, 14 terms 28.24 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 240 | 0 | 0 | 0 | 4 | 14 | 19 | 55 | 11 |
| tier R | 240 | 0 | 0 | 0 | 4 | 14 | 19 | 55 |  |
| without agridat | 212 | 0 | 0 | 1 | 4 | 13 | 15 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 240 | 0 | 0 | 1 | 5 | 21 | 38 | 14966 | – |
| tier R | 240 | 0 | 0 | 1 | 5 | 21 | 38 | 14966 |  |
| without agridat | 212 | 0 | 0 | 1 | 4 | 19 | 35 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 182 | 76% |
| binary | 23 | 10% |
| count | 19 | 8% |
| ordinal | 8 | 3% |
| binomial | 7 | 3% |
| categorical | 1 | 0% |

| reader | n | share |
|---|---|---|
| pyreadr | 204 | 85% |
| rscript | 36 | 15% |

| published | n | share |
|---|---|---|
| yes | 198 | 82% |
| no | 42 | 18% |
