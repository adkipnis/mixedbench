# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); the files in
[`docs/registry.md`](../docs/registry.md), the method in [`README.md`](../survey/README.md). Evidence for the envelope in metabeta's
design docs, not the envelope itself.

How to read the tables:

- Every number is filled from the measured files by `merge.py` on each merge, or by
  `measure.py`; edit `SUMMARY.template.md`, never this file.
- Quantiles are observed values, never interpolated: below the median the nearest value at
  or below the level, from the median on the nearest value at or above it.
- Per-factor axes (groups, group sizes, imbalance) count a dataset once per grouping factor;
  dataset axes (observations, grouping factors, design columns) once per registry row; `K`
  once per categorical covariate of a documented model.
- A quirk statistic counts once per row of its file that defines it: a column, a column and
  grouping factor, a crossed pair of factors or a registry row. Its table shows the pooled
  quantiles, `quantiles.yaml` also those per tier and without agridat. Definitions are in the
  [`docs/registry.md`](../docs/registry.md).
- The last column of an axis table, `practice`, is the practice survey's upper decile, the
  maximum over the v1 families in [`practice_quantiles.yaml`](../survey/practice_quantiles.yaml)
  (the minimum for the smallest group size), read at merge time; `–` where the practice survey
  has no such axis.

**Corpus.** 703 registry rows over 632 datasets and 925 grouping
factors; per tier R 248, T 224, E 115, D 104, O 12. Excluded: 2127 objects (no grouping structure 969, derived or duplicated table 801, unreadable format 192, simulated data 51, not the paper's data 46, response missing or undocumented 39, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 703 | 7 | 32 | 49 | 480 | 8604 | 24261 | 1000209 | 23025 |
| tier R | 248 | 12 | 24 | 32 | 236 | 3326 | 7185 | 73421 |  |
| tier E | 115 | 20 | 32 | 46 | 600 | 19200 | 32877 | 1000209 |  |
| tier T | 224 | 7 | 45 | 80 | 822 | 7584 | 14364 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 12 | 52 | 52 | 120 | 2298 | 181800 | 318438 | 318438 |  |
| without agridat | 674 | 7 | 30 | 49 | 550 | 8979 | 24613 | 1000209 |  |
| flat | 696 | 3 | 9 | 14 | 76 | 1501 | 3941 | 81422 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 703 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 248 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 115 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 224 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 12 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 674 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 521 | 56% |
| crossed | 187 | 20% |
| nested | 139 | 15% |
| mixed | 78 | 8% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 2 | 4 | 5 | 36 | 386 | 1151 | 92017 | 414 |
| tier R | 330 | 2 | 4 | 5 | 23 | 195 | 316 | 10767 |  |
| tier E | 158 | 3 | 4 | 5 | 34 | 595 | 4434 | 19898 |  |
| tier T | 264 | 2 | 5 | 7 | 58 | 568 | 1323 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 15 | 3 | 3 | 9 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 872 | 2 | 4 | 5 | 40 | 405 | 1309 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 1 | 1 | 1 | 5 | 91 | 255 | 18180 | 1 |
| tier R | 330 | 1 | 1 | 1 | 5 | 32 | 71 | 852 |  |
| tier E | 158 | 1 | 1 | 1 | 7 | 228 | 500 | 1872 |  |
| tier T | 264 | 1 | 1 | 1 | 4 | 50 | 91 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 15 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 872 | 1 | 1 | 1 | 5 | 96 | 282 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 1 | 1 | 1 | 7 | 113 | 282 | 18180 | – |
| tier R | 330 | 1 | 1 | 2 | 6 | 37 | 79 | 961 |  |
| tier E | 158 | 1 | 1 | 2 | 7 | 282 | 500 | 2442 |  |
| tier T | 264 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 15 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 872 | 1 | 1 | 1 | 7 | 117 | 316 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 1 | 2 | 3 | 10 | 160 | 500 | 18180 | – |
| tier R | 330 | 1 | 2 | 2 | 8 | 47 | 110 | 1395 |  |
| tier E | 158 | 1 | 3 | 3 | 12 | 504 | 660 | 4200 |  |
| tier T | 264 | 1 | 2 | 2 | 9 | 84 | 219 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 15 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 872 | 1 | 2 | 3 | 10 | 175 | 522 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 1 | 2 | 3 | 14 | 259 | 762 | 20425 | – |
| tier R | 330 | 1 | 2 | 3 | 9 | 63 | 174 | 1849 |  |
| tier E | 158 | 2 | 3 | 4 | 18 | 773 | 1309 | 4650 |  |
| tier T | 264 | 2 | 2 | 3 | 14 | 154 | 336 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 15 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 872 | 2 | 2 | 3 | 14 | 271 | 773 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 2 | 3 | 4 | 17 | 351 | 969 | 33076 | 300 |
| tier R | 330 | 2 | 2 | 3 | 10 | 116 | 290 | 7500 |  |
| tier E | 158 | 2 | 3 | 4 | 28 | 937 | 2314 | 4860 |  |
| tier T | 264 | 2 | 2 | 3 | 16 | 215 | 549 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 15 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 872 | 2 | 3 | 4 | 19 | 392 | 1056 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.386). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 0.0251 | 0.9384 | 1.7108 | 45.8372 | inf | inf | inf | – |
| tier R | 330 | 0.0251 | 1.1846 | 2.2917 | inf | inf | inf | inf |  |
| tier E | 158 | 0.1733 | 0.3236 | 0.9384 | 15.3433 | inf | inf | inf |  |
| tier T | 264 | 0.0438 | 1.0843 | 1.8788 | 12.0721 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 15 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 872 | 0.0296 | 0.9384 | 1.7108 | 34.5248 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 0 | 0 | 0 | 0 | 0.1 | 0.2519 | 0.9964 | – |
| tier R | 330 | 0 | 0 | 0 | 0 | 0.0667 | 0.2295 | 0.9964 |  |
| tier E | 158 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier T | 264 | 0 | 0 | 0 | 0 | 0.125 | 0.3155 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 15 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 872 | 0 | 0 | 0 | 0 | 0.1 | 0.25 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 925 | 0 | 0 | 0 | 0.1385 | 0.7439 | 1.0049 | 5.899 | – |
| tier R | 330 | 0 | 0 | 0 | 0 | 0.6503 | 0.8761 | 5.899 |  |
| tier E | 158 | 0 | 0 | 0 | 0.2463 | 1.0108 | 1.5292 | 1.9835 |  |
| tier T | 264 | 0 | 0 | 0 | 0.2827 | 0.7105 | 0.9348 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 15 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 872 | 0 | 0 | 0 | 0.1621 | 0.746 | 1.0108 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 951 | 49% |
| binary | 655 | 34% |
| categorical | 280 | 14% |
| ordered | 69 | 4% |

| level | n | share |
|---|---|---|
| within | 1331 | 68% |
| group | 624 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 349 | 2 | 2 | 3 | 4 | 10 | 17 | 717 | – |
| tier R | 143 | 2 | 3 | 3 | 4 | 8 | 10 | 56 |  |
| tier E | 36 | 2 | 2 | 2 | 3 | 4 | 10 | 13 |  |
| tier T | 84 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 35 | 2 | 2 | 3 | 5 | 26 | 73 | 717 |  |
| without agridat | 321 | 2 | 2 | 2 | 4 | 10 | 17 | 717 |  |
| flat | 949 | 0 | 1 | 2 | 11 | 81 | 192 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 135 | 39% |
| 4 | 76 | 22% |
| 2 | 34 | 10% |
| 11+ | 33 | 9% |
| 5 | 26 | 7% |
| 6 | 16 | 5% |
| 9 | 8 | 2% |
| 10 | 8 | 2% |
| 8 | 7 | 2% |
| 7 | 6 | 2% |

Implied design columns of a model under the observed categorical share
(0.179) and mean columns per categorical (7.596):
9 terms 19.6 columns, 14 terms 30.48 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 703 | 0 | 0 | 0 | 3 | 11 | 16 | 22134 | 11 |
| tier R | 248 | 0 | 0 | 0 | 3 | 11 | 17 | 55 |  |
| tier E | 115 | 0 | 0 | 0 | 2 | 7 | 11 | 16 |  |
| tier T | 224 | 0 | 0 | 1 | 3 | 9 | 12 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 12 | 2 | 2 | 2 | 11 | 79 | 22134 | 22134 |  |
| without agridat | 674 | 0 | 0 | 1 | 3 | 10 | 15 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 703 | 0 | 0 | 1 | 5 | 21 | 51 | 23759 | – |
| tier R | 248 | 0 | 0 | 1 | 4 | 20 | 32 | 440 |  |
| tier E | 115 | 0 | 0 | 0 | 3 | 12 | 20 | 543 |  |
| tier T | 224 | 0 | 1 | 1 | 4 | 12 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 156 | 163 | 4580 |  |
| tier O | 12 | 2 | 2 | 2 | 19 | 79 | 23759 | 23759 |  |
| without agridat | 674 | 0 | 0 | 1 | 5 | 20 | 55 | 23759 |  |
| flat | 696 | 0 | 1 | 2 | 4 | 21 | 79 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 676 | 1 | 1 | 1 | 3.1003 | 11.9758 | 20.0502 | inf |
| condition_all | 672 | 1 | 1 | 1 | 3.9973 | 47.8697 | inf | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 2227 | -4.9042 | -0.7623 | -0.4935 | 0.1646 | 2.1964 | 3.6141 | 22.8556 |
| excess_kurtosis | 2227 | -1.9902 | -1.36 | -1.2173 | -0.3044 | 6.6656 | 18.7425 | 1191.6867 |
| outlier_share | 2227 | 0 | 0 | 0 | 0 | 0.0077 | 0.0134 | 0.0341 |
| zero_share | 2246 | 0 | 0 | 0 | 0 | 0.1249 | 0.4061 | 1 |
| min_share | 2413 | 0 | 0.0004 | 0.0011 | 0.0377 | 0.5159 | 0.6861 | 1 |
| max_share | 2413 | 0 | 0.0002 | 0.0005 | 0.0172 | 0.2249 | 0.3333 | 1 |
| unique_share | 4013 | 0 | 0.0001 | 0.0003 | 0.0117 | 0.2568 | 0.7341 | 1 |
| rare_level_share | 1770 | 0 | 0.002 | 0.0044 | 0.2385 | 0.4968 | 0.5 | 1 |
| max_abs_rho | 3276 | 0 | 0.007 | 0.0368 | 0.4192 | 0.9155 | 0.99 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 4554 | -1.6916 | -0.1111 | -0.0132 | 0.2823 | 1 | 1 | 1 |
| group_level_r2 | 2549 | -29.5505 | -1.4575 | -0.1834 | 0.0002 | 1 | 1 | 1 |
| absent_level_share | 2521 | 0 | 0 | 0 | 0.3833 | 0.8347 | 0.9583 | 0.9983 |
| size_rho | 3554 | -1 | -0.8208 | -0.4472 | 0.0273 | 0.5004 | 0.7826 | 1 |
| within_sd_cv | 3309 | 0 | 0 | 0.0002 | 0.2817 | 1.5439 | 2.7109 | 129.5068 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 154 | 0 | 0 | 0 | 0.0833 | 0.8964 | 0.9523 | 0.9992 |

| pair relation | n | share |
|---|---|---|
| crossed | 154 | 56% |
| nested | 121 | 44% |

| superior | n | share |
|---|---|---|
| factor_a | 101 | 83% |
| factor_b | 20 | 17% |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 556 | 0 | 0 | 0.0002 | 0.6156 | 366.1112 | 3357.9388 | 9170746.8354 |
| sigma2_random | 556 | 0 | 0 | 0.0076 | 0.9831 | 356.1538 | 3035.9392 | 18651991.7893 |
| sigma2_residual | 376 | 0 | 0.0057 | 0.0239 | 2.316 | 1229.9175 | 6876.6969 | 1451863.8213 |
| sigma2_distribution | 556 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.676 |
| sd_eta | 556 | 0 | 0.1281 | 0.2202 | 1.3383 | 30.8604 | 86.1292 | 5558.5806 |
| r2_marginal | 556 | 0 | 0 | 0.0003 | 0.1734 | 0.7194 | 0.893 | 0.9999 |
| r2_conditional | 556 | 0 | 0.0815 | 0.1417 | 0.6252 | 0.9647 | 0.9885 | 0.9999 |
| q | 741 | 1 | 1 | 1 | 1 | 2 | 2 | 8 |
| sigma2 | 741 | 0 | 0 | 0.0007 | 0.5736 | 205.3507 | 1965.1447 | 18651991.7893 |
| icc | 741 | 0 | 0 | 0.0018 | 0.1408 | 0.6032 | 0.7669 | 0.9914 |
| icc_adjusted | 741 | 0 | 0 | 0.0032 | 0.2367 | 0.8097 | 0.9368 | 0.9983 |

| status | n | share |
|---|---|---|
| ok | 409 | 64% |
| warning | 80 | 12% |
| singular | 67 | 10% |
| error | 53 | 8% |
| no_formula | 32 | 5% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 432 | 61% |
| binary | 114 | 16% |
| count | 77 | 11% |
| ordinal | 48 | 7% |
| categorical | 17 | 2% |
| binomial | 15 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 452 | 64% |
| pyreadr | 239 | 34% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 512 | 73% |
| no | 191 | 27% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 573, unreadable format 158, no grouping structure 111, not the paper's data 46, response missing or undocumented 29).
- Papers with a registry row: 38, over 104 rows.

## Flat sample

The survey's tables filed `no grouping structure`, screened, read again and measured beside the
registry by `flat.py`, every column by the statistics `columns.csv` defines; the files and the
sample's rule are in [`docs/registry.md`](../docs/registry.md). An axis both samples share ends
its table above with the flat sample's row.

**Corpus.** 696 flat tables; per stratum read 543, prescreened 153; per tier R 357, E 142, T 131, D 58, O 8.
The screen flagged 276 of the frame's 648 read tables for a second reading and the response reading found 35 not flat; verdicts flat 205, wide 151, hidden grouping 43.
The hand sample of 50 tables stood at 0.92.
336 of the 696 tables name a response; the response check of 25 tables stood at 0.84, its recheck of 15 `none` tables at 1.0.

| column type | n | share |
|---|---|---|
| continuous | 36594 | 85% |
| binary | 5350 | 12% |
| categorical | 815 | 2% |
| ordered | 134 | 0% |

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_all | 673 | 1 | 1 | 1.0843 | 4.7482 | inf | inf | inf |
| skewness | 35816 | -11.1669 | -0.5434 | -0.0263 | 1.4233 | 3.5352 | 3.9478 | 244.6948 |
| excess_kurtosis | 35781 | -5.6896 | -1.8933 | -1.6631 | 1.1953 | 12.0788 | 15.612 | 59915.5349 |
| outlier_share | 35816 | 0 | 0 | 0 | 0 | 0.0211 | 0.0318 | 0.0565 |
| zero_share | 36532 | 0 | 0 | 0 | 0.7067 | 0.9152 | 0.9364 | 1 |
| min_share | 36666 | 0 | 0.0098 | 0.0185 | 0.7314 | 0.9187 | 0.9399 | 1 |
| max_share | 36666 | 0 | 0.0035 | 0.0098 | 0.053 | 0.371 | 0.4452 | 1 |
| unique_share | 42825 | 0 | 0.0071 | 0.0071 | 0.0106 | 0.6852 | 0.8529 | 1 |
| rare_level_share | 6293 | 0 | 0.0023 | 0.0127 | 0.1343 | 0.4375 | 0.4841 | 1 |
| max_abs_rho | 41215 | 0 | 0.2637 | 0.3333 | 0.9072 | 0.9956 | 0.9999 | 1 |
