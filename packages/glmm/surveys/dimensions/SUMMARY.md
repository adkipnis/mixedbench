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

**Corpus.** 616 registry rows over 580 datasets and 785 grouping
factors; per tier R 252, T 252, E 99, O 13. Excluded: 1218 objects (no grouping structure 1057, derived or duplicated table 50, simulated data 43, time series without replication 30, unreadable format 29, response missing or undocumented 8, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 616 | 7 | 26 | 40 | 400 | 7081 | 15524 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 252 | 7 | 36 | 72 | 854 | 7382 | 14364 | 283728 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 588 | 7 | 26 | 40 | 406 | 7185 | 15834 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 616 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 588 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 475 | 61% |
| crossed | 137 | 17% |
| nested | 118 | 15% |
| mixed | 55 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 2 | 4 | 5 | 28 | 386 | 1236 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier T | 299 | 2 | 4 | 6 | 58 | 545 | 1323 | 4856 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 732 | 2 | 4 | 5 | 31 | 410 | 1333 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 1 | 1 | 1 | 5 | 50 | 135 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier T | 299 | 1 | 1 | 1 | 4 | 54 | 135 | 1353 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 732 | 1 | 1 | 1 | 5 | 51 | 156 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 1 | 1 | 2 | 7 | 56 | 173 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier T | 299 | 1 | 1 | 1 | 6 | 69 | 194 | 1353 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 732 | 1 | 1 | 2 | 6 | 58 | 201 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 1 | 2 | 3 | 10 | 96 | 291 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier T | 299 | 1 | 2 | 3 | 10 | 101 | 290 | 2037 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 732 | 1 | 2 | 3 | 10 | 105 | 312 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 1 | 2 | 3 | 12 | 169 | 448 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier T | 299 | 2 | 2 | 3 | 16 | 180 | 415 | 4014 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 732 | 2 | 2 | 3 | 12 | 180 | 510 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 2 | 3 | 3 | 14 | 251 | 765 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier T | 299 | 2 | 2 | 3 | 17 | 251 | 740 | 7745 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 732 | 2 | 3 | 4 | 14 | 286 | 769 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.413). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 0.0251 | 0.9669 | 1.6866 | 56.7156 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 299 | 0.0438 | 1.0843 | 1.8788 | 14.3427 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 732 | 0.0296 | 0.9496 | 1.671 | 36.0263 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 0 | 0 | 0 | 0 | 0.0862 | 0.194 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 299 | 0 | 0 | 0 | 0 | 0.1066 | 0.25 | 0.8448 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 732 | 0 | 0 | 0 | 0 | 0.0862 | 0.194 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 785 | 0 | 0 | 0 | 0.1265 | 0.7204 | 0.9899 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 299 | 0 | 0 | 0 | 0.2582 | 0.7204 | 0.9093 | 3.5667 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 732 | 0 | 0 | 0 | 0.1658 | 0.7262 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 753 | 43% |
| binary | 578 | 33% |
| categorical | 333 | 19% |
| ordered | 85 | 5% |

| level | n | share |
|---|---|---|
| within | 1233 | 70% |
| group | 516 | 30% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 418 | 1 | 2 | 3 | 4 | 9 | 10 | 83 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 159 | 1 | 2 | 3 | 4 | 9 | 11 | 83 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 390 | 1 | 2 | 2 | 4 | 9 | 10 | 83 |  |

| K | n | share |
|---|---|---|
| 3 | 141 | 34% |
| 4 | 89 | 21% |
| 5 | 45 | 11% |
| 2 | 36 | 9% |
| 6 | 26 | 6% |
| 7 | 23 | 6% |
| 10 | 16 | 4% |
| 9 | 11 | 3% |
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
| 83 | 1 | 0% |

Implied design columns of a model under the observed categorical share
(0.239) and mean columns per categorical (4.108):
9 terms 15.68 columns, 14 terms 24.4 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 616 | 0 | 0 | 1 | 4 | 13 | 16 | 101 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 252 | 0 | 1 | 1 | 4 | 11 | 14 | 101 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 588 | 0 | 0 | 1 | 4 | 12 | 15 | 101 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 616 | 0 | 0 | 1 | 5 | 17 | 27 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 252 | 0 | 1 | 1 | 4 | 13 | 18 | 11030 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 588 | 0 | 0 | 1 | 4 | 16 | 27 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 389 | 63% |
| binary | 90 | 15% |
| count | 70 | 11% |
| ordinal | 42 | 7% |
| binomial | 15 | 2% |
| categorical | 10 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 357 | 58% |
| pyreadr | 223 | 36% |
| rscript | 36 | 6% |

| published | n | share |
|---|---|---|
| yes | 437 | 71% |
| no | 179 | 29% |
