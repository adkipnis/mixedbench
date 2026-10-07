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

**Corpus.** 364 registry rows over 346 datasets and 486 grouping
factors; per tier R 252, E 99, O 13. Excluded: 940 objects (no grouping structure 826, simulated data 43, derived or duplicated table 25, time series without replication 21, unreadable format 19, response missing or undocumented 5, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 12 | 24 | 32 | 246 | 5875 | 16409 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 336 | 12 | 24 | 32 | 262 | 7000 | 24613 | 1000209 |  |

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
| single | 266 | 55% |
| crossed | 98 | 20% |
| nested | 76 | 16% |
| mixed | 46 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 2 | 4 | 4 | 21 | 251 | 888 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 433 | 2 | 4 | 4 | 23 | 286 | 1374 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 1 | 1 | 1 | 6 | 50 | 156 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 433 | 1 | 1 | 1 | 6 | 51 | 177 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 1 | 1 | 2 | 7 | 51 | 173 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 433 | 1 | 1 | 2 | 7 | 55 | 215 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 1 | 2 | 3 | 9 | 96 | 308 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 433 | 1 | 2 | 3 | 9 | 117 | 351 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 1 | 2 | 3 | 12 | 169 | 510 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 433 | 2 | 2 | 3 | 12 | 218 | 521 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 2 | 3 | 3 | 12 | 268 | 765 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 433 | 2 | 3 | 4 | 12 | 300 | 773 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.502). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 0.0251 | 0.8817 | 1.671 | inf | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 433 | 0.0296 | 0.8817 | 1.601 | 1001.2857 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 0 | 0 | 0 | 0 | 0.0672 | 0.1633 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 433 | 0 | 0 | 0 | 0 | 0.0672 | 0.1525 | 0.7655 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 486 | 0 | 0 | 0 | 0 | 0.7307 | 1.0139 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 433 | 0 | 0 | 0 | 0.03 | 0.7601 | 1.0645 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 365 | 41% |
| binary | 273 | 30% |
| categorical | 214 | 24% |
| ordered | 45 | 5% |

| level | n | share |
|---|---|---|
| within | 609 | 68% |
| group | 288 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 259 | 1 | 2 | 3 | 4 | 9 | 10 | 56 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 231 | 1 | 2 | 2 | 4 | 8 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 91 | 35% |
| 4 | 56 | 22% |
| 5 | 27 | 10% |
| 2 | 23 | 9% |
| 6 | 14 | 5% |
| 7 | 11 | 4% |
| 10 | 11 | 4% |
| 8 | 7 | 3% |
| 9 | 6 | 2% |
| 14 | 3 | 1% |
| 1 | 2 | 1% |
| 56 | 1 | 0% |
| 15 | 1 | 0% |
| 16 | 1 | 0% |
| 20 | 1 | 0% |
| 49 | 1 | 0% |
| 17 | 1 | 0% |
| 13 | 1 | 0% |
| 11 | 1 | 0% |

Implied design columns of a model under the observed categorical share
(0.289) and mean columns per categorical (4.019):
9 terms 16.85 columns, 14 terms 26.21 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 0 | 0 | 0 | 3 | 13 | 17 | 59 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 336 | 0 | 0 | 0 | 3 | 12 | 15 | 59 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 364 | 0 | 0 | 0 | 5 | 20 | 35 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 336 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 254 | 70% |
| binary | 43 | 12% |
| count | 29 | 8% |
| ordinal | 21 | 6% |
| binomial | 9 | 2% |
| categorical | 8 | 2% |

| reader | n | share |
|---|---|---|
| pyreadr | 216 | 59% |
| pandas | 112 | 31% |
| rscript | 36 | 10% |

| published | n | share |
|---|---|---|
| yes | 301 | 83% |
| no | 63 | 17% |
