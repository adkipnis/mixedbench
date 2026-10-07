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

**Corpus.** 364 registry rows over 347 datasets and 483 grouping
factors; per tier R 252, E 99, O 13. Excluded: 939 objects (no grouping structure 824, simulated data 44, derived or duplicated table 25, time series without replication 21, unreadable format 19, response missing or undocumented 5, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 12 | 24 | 32 | 246 | 5500 | 16094 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 16409 | 28534 | 1000209 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 336 | 12 | 24 | 32 | 262 | 6402 | 19200 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 336 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 268 | 55% |
| crossed | 98 | 20% |
| nested | 74 | 15% |
| mixed | 43 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 2 | 4 | 4 | 21 | 251 | 888 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 135 | 3 | 4 | 5 | 37 | 600 | 4434 | 19898 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 430 | 2 | 4 | 4 | 22 | 294 | 1373 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 1 | 1 | 1 | 6 | 48 | 145 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 135 | 1 | 1 | 1 | 6 | 186 | 300 | 1791 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 430 | 1 | 1 | 1 | 6 | 50 | 173 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 1 | 1 | 2 | 7 | 50 | 156 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 135 | 1 | 1 | 2 | 6 | 216 | 300 | 1791 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 430 | 1 | 1 | 2 | 7 | 55 | 189 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 1 | 2 | 3 | 9 | 81 | 291 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 135 | 1 | 3 | 3 | 11 | 491 | 559 | 3221 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 430 | 1 | 2 | 3 | 9 | 117 | 316 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 1 | 2 | 3 | 12 | 161 | 500 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 135 | 2 | 3 | 4 | 14 | 600 | 773 | 4183 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 430 | 2 | 2 | 3 | 12 | 217 | 510 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 2 | 3 | 3 | 12 | 247 | 765 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 135 | 2 | 3 | 4 | 22 | 765 | 1309 | 4183 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 430 | 2 | 3 | 3 | 12 | 290 | 769 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.507). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 0.0251 | 0.8817 | 1.671 | inf | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 135 | 0.1733 | 0.3236 | 0.9384 | 15.3433 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 430 | 0.0296 | 0.8817 | 1.579 | 3531.5072 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 0 | 0 | 0 | 0 | 0.0667 | 0.1525 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 135 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 430 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.7655 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 483 | 0 | 0 | 0 | 0 | 0.7307 | 1.0139 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 135 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 430 | 0 | 0 | 0 | 0.0189 | 0.7601 | 1.0645 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 369 | 41% |
| binary | 273 | 30% |
| categorical | 215 | 24% |
| ordered | 49 | 5% |

| level | n | share |
|---|---|---|
| within | 616 | 68% |
| group | 290 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 264 | 1 | 2 | 2 | 4 | 9 | 10 | 56 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 56 | 1 | 1 | 2 | 3 | 7 | 10 | 10 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 236 | 1 | 2 | 2 | 4 | 8 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 94 | 36% |
| 4 | 56 | 21% |
| 5 | 28 | 11% |
| 2 | 24 | 9% |
| 6 | 14 | 5% |
| 10 | 12 | 5% |
| 7 | 10 | 4% |
| 8 | 7 | 3% |
| 9 | 5 | 2% |
| 14 | 3 | 1% |
| 1 | 3 | 1% |
| 56 | 1 | 0% |
| 15 | 1 | 0% |
| 16 | 1 | 0% |
| 20 | 1 | 0% |
| 49 | 1 | 0% |
| 17 | 1 | 0% |
| 13 | 1 | 0% |
| 11 | 1 | 0% |

Implied design columns of a model under the observed categorical share
(0.291) and mean columns per categorical (3.966):
9 terms 16.78 columns, 14 terms 26.1 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 0 | 0 | 0 | 3 | 13 | 19 | 59 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 21 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 336 | 0 | 0 | 0 | 3 | 12 | 15 | 59 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 0 | 0 | 0 | 5 | 21 | 35 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 23 | 555 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 336 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 254 | 70% |
| binary | 44 | 12% |
| count | 29 | 8% |
| ordinal | 20 | 5% |
| binomial | 9 | 2% |
| categorical | 8 | 2% |

| reader | n | share |
|---|---|---|
| pyreadr | 216 | 59% |
| pandas | 112 | 31% |
| rscript | 36 | 10% |

| published | n | share |
|---|---|---|
| yes | 300 | 82% |
| no | 64 | 18% |
