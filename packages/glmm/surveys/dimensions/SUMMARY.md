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

**Corpus.** 608 registry rows over 573 datasets and 777 grouping
factors; per tier R 252, T 244, E 99, O 13. Excluded: 1225 objects (no grouping structure 1064, derived or duplicated table 50, simulated data 43, time series without replication 30, unreadable format 29, response missing or undocumented 8, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 608 | 7 | 26 | 40 | 394 | 6539 | 15362 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 244 | 7 | 36 | 70 | 854 | 7185 | 10036 | 283728 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 580 | 7 | 26 | 37 | 400 | 7185 | 15524 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 608 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 244 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 580 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 467 | 60% |
| crossed | 137 | 18% |
| nested | 118 | 15% |
| mixed | 55 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 2 | 4 | 5 | 28 | 386 | 1309 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier T | 291 | 2 | 4 | 6 | 59 | 545 | 1323 | 4856 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 724 | 2 | 4 | 5 | 31 | 411 | 1333 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 1 | 1 | 1 | 5 | 50 | 135 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier T | 291 | 1 | 1 | 1 | 4 | 50 | 92 | 1353 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 724 | 1 | 1 | 1 | 5 | 50 | 135 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 1 | 1 | 2 | 7 | 55 | 156 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier T | 291 | 1 | 1 | 1 | 6 | 58 | 135 | 1353 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 724 | 1 | 1 | 2 | 6 | 56 | 173 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 1 | 2 | 3 | 10 | 85 | 290 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier T | 291 | 1 | 2 | 3 | 10 | 84 | 207 | 2037 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 724 | 1 | 2 | 3 | 10 | 103 | 291 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 1 | 2 | 3 | 12 | 161 | 448 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier T | 291 | 2 | 2 | 3 | 15 | 139 | 336 | 4014 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 724 | 2 | 2 | 3 | 12 | 178 | 448 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 2 | 3 | 3 | 14 | 247 | 762 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier T | 291 | 2 | 2 | 3 | 17 | 215 | 528 | 7745 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 724 | 2 | 3 | 3 | 14 | 268 | 765 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.412). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 0.0251 | 0.9496 | 1.6802 | 56.7156 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 291 | 0.0438 | 1.0843 | 1.8788 | 11.4003 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 724 | 0.0296 | 0.9496 | 1.671 | 34.5248 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 0 | 0 | 0 | 0 | 0.0889 | 0.2045 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 291 | 0 | 0 | 0 | 0 | 0.1066 | 0.25 | 0.8448 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 724 | 0 | 0 | 0 | 0 | 0.0889 | 0.194 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 777 | 0 | 0 | 0 | 0.1265 | 0.7235 | 1.0049 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 291 | 0 | 0 | 0 | 0.2827 | 0.7204 | 0.9093 | 3.5667 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 724 | 0 | 0 | 0 | 0.1699 | 0.7284 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 750 | 43% |
| binary | 574 | 33% |
| categorical | 330 | 19% |
| ordered | 78 | 5% |

| level | n | share |
|---|---|---|
| within | 1215 | 70% |
| group | 517 | 30% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 408 | 1 | 2 | 3 | 4 | 9 | 10 | 56 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 149 | 1 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 380 | 1 | 2 | 2 | 4 | 9 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 141 | 35% |
| 4 | 86 | 21% |
| 5 | 41 | 10% |
| 2 | 35 | 9% |
| 6 | 25 | 6% |
| 7 | 22 | 5% |
| 10 | 16 | 4% |
| 9 | 12 | 3% |
| 8 | 9 | 2% |
| 11 | 4 | 1% |
| 14 | 3 | 1% |
| 1 | 3 | 1% |
| 12 | 3 | 1% |
| 17 | 2 | 0% |
| 56 | 1 | 0% |
| 15 | 1 | 0% |
| 16 | 1 | 0% |
| 20 | 1 | 0% |
| 49 | 1 | 0% |
| 13 | 1 | 0% |

Implied design columns of a model under the observed categorical share
(0.236) and mean columns per categorical (3.936):
9 terms 15.23 columns, 14 terms 23.68 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 608 | 0 | 0 | 1 | 4 | 13 | 16 | 59 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 11 | 13 | 25 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 580 | 0 | 0 | 1 | 4 | 12 | 15 | 59 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 608 | 0 | 0 | 1 | 5 | 16 | 25 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 13 | 16 | 11030 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 580 | 0 | 0 | 1 | 4 | 15 | 24 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 387 | 64% |
| binary | 89 | 15% |
| count | 68 | 11% |
| ordinal | 39 | 6% |
| binomial | 15 | 2% |
| categorical | 10 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 351 | 58% |
| pyreadr | 221 | 36% |
| rscript | 36 | 6% |

| published | n | share |
|---|---|---|
| yes | 437 | 72% |
| no | 171 | 28% |
