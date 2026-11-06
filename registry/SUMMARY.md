# Dimension survey - summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); the files in
[`docs/registry.md`](../docs/registry.md), the method in [`README.md`](../survey/README.md). Evidence for the envelope in metabeta's
design docs, not the envelope itself.

How to read the tables:

- Every number is filled from the measured files by `measure.py` or `flat.py measure`; edit
  `SUMMARY.template.md`, never this file.
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
  (the minimum for the smallest group size), read at measurement time; `-` where the practice survey
  has no such axis.

**Corpus.** 1077 registry rows over 941 datasets and 1409 grouping
factors; per tier R 528, T 214, O 135, D 104, E 96. Excluded: 2868 objects (no grouping structure 1498, derived or duplicated table 933, unreadable format 204, simulated data 78, time series without replication 59, response missing or undocumented 46, not the paper's data 46, too large 3, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1077 | 8 | 32 | 48 | 728 | 19609 | 59929 | 25000095 | 23025 |
| tier R | 528 | 8 | 25 | 36 | 324 | 4360 | 9216 | 374250 |  |
| tier E | 96 | 20 | 30 | 40 | 550 | 16409 | 32877 | 1000209 |  |
| tier T | 214 | 12 | 45 | 72 | 853 | 15362 | 39925 | 2745952 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 135 | 52 | 382 | 492 | 11700 | 844392 | 1330816 | 25000095 |  |
| without agridat | 1048 | 8 | 32 | 48 | 771 | 21263 | 61248 | 25000095 |  |
| flat | 1111 | 3 | 9 | 13 | 89 | 2700 | 7019 | 1853035 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1077 | 1 | 1 | 1 | 1 | 2 | 2 | 6 | 3 |
| tier R | 528 | 1 | 1 | 1 | 1 | 2 | 2 | 6 |  |
| tier E | 96 | 1 | 1 | 1 | 1 | 2 | 4 | 5 |  |
| tier T | 214 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 135 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 1048 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 814 | 58% |
| crossed | 273 | 19% |
| nested | 192 | 14% |
| mixed | 130 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 2 | 5 | 6 | 45 | 600 | 2360 | 162541 | 414 |
| tier R | 662 | 2 | 5 | 6 | 39 | 366 | 688 | 20670 |  |
| tier E | 141 | 3 | 4 | 4 | 23 | 468 | 1518 | 19898 |  |
| tier T | 256 | 2 | 5 | 7 | 64 | 1000 | 1683 | 108295 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 192 | 2 | 9 | 12 | 69 | 25489 | 38190 | 162541 |  |
| without agridat | 1356 | 2 | 5 | 6 | 48 | 685 | 2526 | 162541 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 1 | 1 | 1 | 5 | 113 | 411 | 44194 | 1 |
| tier R | 662 | 1 | 1 | 1 | 4 | 29 | 54 | 1536 |  |
| tier E | 141 | 1 | 1 | 1 | 8 | 228 | 500 | 1872 |  |
| tier T | 256 | 1 | 1 | 1 | 3 | 64 | 135 | 44194 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 192 | 1 | 1 | 1 | 13 | 864 | 1734 | 23814 |  |
| without agridat | 1356 | 1 | 1 | 1 | 5 | 132 | 458 | 44194 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 1 | 1 | 1 | 7 | 146 | 458 | 44194 | - |
| tier R | 662 | 1 | 1 | 1 | 5 | 33 | 74 | 1536 |  |
| tier E | 141 | 1 | 1 | 2 | 8 | 282 | 500 | 2442 |  |
| tier T | 256 | 1 | 1 | 1 | 6 | 106 | 201 | 44194 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 192 | 1 | 1 | 1 | 25 | 1026 | 5119 | 24620 |  |
| without agridat | 1356 | 1 | 1 | 1 | 7 | 162 | 492 | 44194 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 1 | 2 | 2 | 10 | 275 | 559 | 58594 | - |
| tier R | 662 | 1 | 1 | 2 | 7 | 42 | 104 | 4489 |  |
| tier E | 141 | 1 | 2 | 3 | 15 | 522 | 660 | 4200 |  |
| tier T | 256 | 1 | 2 | 2 | 10 | 176 | 474 | 58594 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 192 | 1 | 1 | 2 | 47 | 1523 | 12644 | 26562 |  |
| without agridat | 1356 | 1 | 2 | 2 | 10 | 290 | 600 | 58594 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 1 | 2 | 3 | 15 | 400 | 1040 | 71619 | - |
| tier R | 662 | 1 | 2 | 3 | 8 | 72 | 172 | 23509 |  |
| tier E | 141 | 2 | 2 | 3 | 30 | 773 | 1309 | 4650 |  |
| tier T | 256 | 2 | 2 | 3 | 14 | 306 | 698 | 71619 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 192 | 1 | 3 | 6 | 68 | 2853 | 18180 | 35361 |  |
| without agridat | 1356 | 1 | 2 | 3 | 15 | 435 | 1190 | 71619 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 2 | 2 | 4 | 21 | 762 | 1844 | 618486 | 300 |
| tier R | 662 | 2 | 2 | 3 | 11 | 128 | 267 | 32017 |  |
| tier E | 141 | 2 | 2 | 3 | 34 | 1280 | 2314 | 4860 |  |
| tier T | 256 | 2 | 2 | 3 | 18 | 528 | 1324 | 71619 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 192 | 2 | 7 | 15 | 200 | 18180 | 28549 | 618486 |  |
| without agridat | 1356 | 2 | 2 | 4 | 22 | 767 | 1988 | 618486 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.354). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 0.0114 | 0.4666 | 0.9808 | 37.7793 | inf | inf | inf | - |
| tier R | 662 | 0.0251 | 0.7632 | 1.2852 | 995.2547 | inf | inf | inf |  |
| tier E | 141 | 0.1733 | 0.4258 | 0.9384 | 15.3433 | inf | inf | inf |  |
| tier T | 256 | 0.0438 | 0.596 | 1.3064 | 14.939 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 192 | 0.0114 | 0.0531 | 0.1947 | 19.2643 | inf | inf | inf |  |
| without agridat | 1356 | 0.0114 | 0.4422 | 0.9669 | 30.7312 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 0 | 0 | 0 | 0 | 0.1939 | 0.4622 | 0.9964 | - |
| tier R | 662 | 0 | 0 | 0 | 0 | 0.2295 | 0.5143 | 0.9964 |  |
| tier E | 141 | 0 | 0 | 0 | 0 | 0.0862 | 0.1161 | 0.5329 |  |
| tier T | 256 | 0 | 0 | 0 | 0 | 0.1667 | 0.4082 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 192 | 0 | 0 | 0 | 0 | 0.3651 | 0.6326 | 0.9263 |  |
| without agridat | 1356 | 0 | 0 | 0 | 0 | 0.1939 | 0.4622 | 0.9263 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1409 | 0 | 0 | 0 | 0.1556 | 0.9691 | 1.4228 | 9.2873 | - |
| tier R | 662 | 0 | 0 | 0 | 0.0317 | 0.8518 | 1.1151 | 5.899 |  |
| tier E | 141 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.3558 | 1.9835 |  |
| tier T | 256 | 0 | 0 | 0 | 0.2582 | 0.8574 | 1.2125 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 192 | 0 | 0 | 0 | 0.2816 | 2.2431 | 4.2655 | 9.2873 |  |
| without agridat | 1356 | 0 | 0 | 0 | 0.1801 | 0.9833 | 1.4518 | 9.2873 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 2789 | 55% |
| binary | 1571 | 31% |
| categorical | 632 | 12% |
| ordered | 73 | 1% |

| level | n | share |
|---|---|---|
| within | 3276 | 65% |
| group | 1789 | 35% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 705 | 2 | 3 | 3 | 4 | 28 | 60 | 1134 | - |
| tier R | 247 | 2 | 3 | 3 | 4 | 10 | 15 | 49 |  |
| tier E | 22 | 2 | 2 | 2 | 3 | 7 | 10 | 13 |  |
| tier T | 98 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 287 | 2 | 3 | 3 | 6 | 70 | 152 | 1134 |  |
| without agridat | 675 | 2 | 3 | 3 | 4 | 29 | 68 | 1134 |  |
| flat | 1415 | 0 | 1 | 3 | 10 | 103 | 234 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 241 | 34% |
| 11+ | 141 | 20% |
| 4 | 138 | 20% |
| 5 | 46 | 7% |
| 6 | 34 | 5% |
| 8 | 26 | 4% |
| 2 | 25 | 4% |
| 7 | 22 | 3% |
| 10 | 17 | 2% |
| 9 | 15 | 2% |

Implied design columns of a model under the observed categorical share
(0.139) and mean columns per categorical (15.739):
9 terms 27.46 columns, 14 terms 42.72 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1077 | 0 | 0 | 0 | 3 | 14 | 25 | 22134 | 11 |
| tier R | 528 | 0 | 0 | 0 | 3 | 12 | 17 | 69 |  |
| tier E | 96 | 0 | 0 | 0 | 2 | 7 | 12 | 31 |  |
| tier T | 214 | 0 | 1 | 1 | 4 | 11 | 13 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 135 | 0 | 0 | 1 | 5 | 76 | 169 | 22134 |  |
| without agridat | 1048 | 0 | 0 | 1 | 3 | 14 | 24 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1077 | 0 | 1 | 1 | 6 | 42 | 159 | 382085 | - |
| tier R | 528 | 0 | 1 | 1 | 6 | 31 | 75 | 9422 |  |
| tier E | 96 | 0 | 0 | 0 | 3 | 12 | 20 | 543 |  |
| tier T | 214 | 0 | 1 | 1 | 5 | 20 | 58 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 120 | 163 | 4580 |  |
| tier O | 135 | 0 | 1 | 3 | 10 | 5227 | 23759 | 382085 |  |
| without agridat | 1048 | 0 | 1 | 1 | 6 | 42 | 162 | 382085 |  |
| flat | 1111 | 0 | 1 | 2 | 5 | 29 | 100 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 1009 | 1 | 1 | 1 | 3.1822 | 13.038 | 19.7338 | inf |
| condition_all | 990 | 1 | 1 | 1.0123 | 5.35 | 43.7951 | 320.1274 | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 6068 | -992.7471 | -1.0032 | -0.627 | 0.5073 | 7.589 | 10.2843 | 898.2178 |
| excess_kurtosis | 6068 | -2.0093 | -1.3054 | -1.2012 | 0.5776 | 80.8554 | 153.3511 | 1050361.6397 |
| outlier_share | 6068 | 0 | 0 | 0 | 0 | 0.0138 | 0.02 | 0.0583 |
| zero_share | 6200 | 0 | 0 | 0 | 0 | 0.5972 | 0.9787 | 1 |
| min_share | 6387 | 0 | 0.0002 | 0.0009 | 0.045 | 0.8509 | 0.9858 | 1 |
| max_share | 6387 | 0 | 0 | 0.0001 | 0.0072 | 0.1967 | 0.3698 | 1 |
| unique_share | 11026 | 0 | 0 | 0.0001 | 0.0048 | 0.25 | 0.7467 | 1 |
| rare_level_share | 4829 | 0 | 0.0002 | 0.0011 | 0.1346 | 0.4937 | 0.5 | 1 |
| max_abs_rho | 8798 | 0 | 0.0294 | 0.0716 | 0.5292 | 0.9956 | 1 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 11311 | -3.1327 | -0.0504 | -0.01 | 0.2379 | 1 | 1 | 1 |
| group_level_r2 | 5186 | -56 | -0.8561 | -0.1219 | 0.001 | 0.9975 | 1 | 1 |
| absent_level_share | 6028 | 0 | 0 | 0 | 0.4978 | 0.9306 | 0.9667 | 1 |
| size_rho | 9316 | -1 | -0.4558 | -0.2558 | 0.0332 | 0.4082 | 0.5724 | 1 |
| within_sd_cv | 8281 | 0 | 0 | 0.0056 | 0.3446 | 3.4251 | 5.5689 | 235.3189 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 235 | 0 | 0 | 0 | 0.1667 | 0.9907 | 0.9973 | 0.9999 |

| pair relation | n | share |
|---|---|---|
| crossed | 235 | 55% |
| nested | 191 | 45% |

| superior | n | share |
|---|---|---|
| factor_a | 163 | 85% |
| factor_b | 28 | 15% |

## Quirk statistics per response

Every registry row's response, by the statistics its type defines: a binomial one as its
successes' share of the trials, an ordinal one by its levels.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 269 | 2 | 2 | 2 | 2 | 7 | 9 | 1495 |
| response_skewness | 808 | -10.4422 | -0.8192 | -0.573 | 0.3498 | 3.0649 | 4.592 | 254.4069 |
| response_excess_kurtosis | 808 | -1.9502 | -1.2141 | -0.9652 | 0.3397 | 15.4203 | 37.6216 | 69205.0886 |
| response_outlier_share | 808 | 0 | 0 | 0 | 0 | 0.0102 | 0.0131 | 0.0312 |
| response_zero_share | 873 | 0 | 0 | 0 | 0 | 0.1111 | 0.35 | 0.8942 |
| response_min_share | 889 | 0 | 0.0001 | 0.0003 | 0.011 | 0.2409 | 0.3929 | 0.8942 |
| response_max_share | 889 | 0 | 0.0001 | 0.0002 | 0.0065 | 0.1445 | 0.2543 | 0.7713 |
| response_unique_share | 1077 | 0 | 0.0002 | 0.0006 | 0.1838 | 0.98 | 1 | 1 |
| response_rare_level_share | 269 | 0.0001 | 0.0024 | 0.0157 | 0.2037 | 0.4465 | 0.4761 | 0.5 |
| response_max_abs_rho | 930 | 0 | 0.0363 | 0.0743 | 0.3263 | 0.8131 | 0.9013 | 1 |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 776 | 0 | 0 | 0.0004 | 0.5923 | 370.8811 | 3208.4952 | 155213768.6032 |
| sigma2_random | 776 | 0 | 0.0001 | 0.0082 | 0.9728 | 400.1959 | 5590.0247 | 1745712221.7761 |
| sigma2_residual | 537 | 0 | 0.0038 | 0.0173 | 2.2937 | 1396.8423 | 23590.2658 | 471364189.2977 |
| sigma2_distribution | 776 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.676 |
| sd_eta | 776 | 0 | 0.107 | 0.206 | 1.3375 | 30.1039 | 97.6661 | 28202.6124 |
| r2_marginal | 776 | 0 | 0 | 0.0008 | 0.1567 | 0.7239 | 0.863 | 0.9946 |
| r2_conditional | 776 | 0 | 0.0853 | 0.1423 | 0.6351 | 0.9675 | 0.9907 | 1 |
| q | 1041 | 1 | 1 | 1 | 1 | 2 | 3 | 12 |
| sigma2 | 1041 | 0 | 0 | 0.0019 | 0.6745 | 247.5284 | 4086.4295 | 1720517318.1414 |
| icc | 1041 | 0 | 0 | 0.0032 | 0.1504 | 0.6387 | 0.7929 | 0.9996 |
| icc_adjusted | 1041 | 0 | 0 | 0.0062 | 0.2554 | 0.8432 | 0.9422 | 1 |

| status | n | share |
|---|---|---|
| ok | 554 | 59% |
| warning | 134 | 14% |
| error | 114 | 12% |
| singular | 88 | 9% |
| no_formula | 39 | 4% |
| timeout | 4 | 0% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 666 | 62% |
| binary | 160 | 15% |
| count | 107 | 10% |
| ordinal | 81 | 8% |
| binomial | 35 | 3% |
| categorical | 28 | 3% |

| reader | n | share |
|---|---|---|
| pandas | 552 | 51% |
| pyreadr | 499 | 46% |
| rdata | 19 | 2% |
| deparse | 7 | 1% |

| published | n | share |
|---|---|---|
| yes | 708 | 66% |
| no | 369 | 34% |

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

**Corpus.** 1111 flat tables; per stratum read 867, prescreened 244; per tier R 731, T 152, E 140, D 58, O 30.
The screen flagged 464 of the frame's 1053 read tables for a second reading and the response reading found 77 not flat; verdicts flat 335, wide 244, hidden grouping 61.
The hand sample of 50 tables stood at 0.92.
579 of the 1111 tables name a response; the response check of 25 tables stood at 0.84, its recheck of 15 `none` tables at 1.0.

| column type | n | share |
|---|---|---|
| continuous | 39438 | 84% |
| binary | 6373 | 13% |
| categorical | 1277 | 3% |
| ordered | 138 | 0% |

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_all | 1085 | 1 | 1 | 1.1372 | 6.2016 | 1666.5388 | inf | inf |
| skewness | 38595 | -20.7557 | -0.5924 | -0.0822 | 1.3621 | 3.5352 | 4.0096 | 911.9213 |
| excess_kurtosis | 38560 | -5.6896 | -1.8815 | -1.6249 | 1.1639 | 12.3827 | 18.5267 | 908754.4834 |
| outlier_share | 38595 | 0 | 0 | 0 | 0 | 0.0196 | 0.0318 | 0.0565 |
| zero_share | 39376 | 0 | 0 | 0 | 0.6714 | 0.9152 | 0.9364 | 1 |
| min_share | 39514 | 0 | 0.0053 | 0.0134 | 0.7 | 0.9152 | 0.9399 | 1 |
| max_share | 39514 | 0 | 0.0025 | 0.0068 | 0.0476 | 0.364 | 0.4417 | 1 |
| unique_share | 47157 | 0 | 0.0036 | 0.0071 | 0.0106 | 0.7407 | 0.9259 | 1 |
| rare_level_share | 7781 | 0 | 0.0021 | 0.0106 | 0.1343 | 0.4417 | 0.486 | 1 |
| max_abs_rho | 44985 | 0 | 0.2572 | 0.3161 | 0.8961 | 0.9973 | 1 | 1 |

The named responses, by the statistics `responses.csv` defines for their type:

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 110 | 2 | 2 | 2 | 2 | 7 | 7 | 10 |
| response_skewness | 469 | -3.6156 | -0.9777 | -0.5256 | 0.4164 | 2.8839 | 3.8503 | 18.0723 |
| response_excess_kurtosis | 468 | -2.1308 | -1.3957 | -1.1981 | 0.2154 | 11.8515 | 22.2819 | 506.2884 |
| response_outlier_share | 469 | 0 | 0 | 0 | 0 | 0.0083 | 0.0135 | 0.0435 |
| response_zero_share | 479 | 0 | 0 | 0 | 0 | 0.125 | 0.3194 | 0.9418 |
| response_min_share | 488 | 0 | 0.0009 | 0.002 | 0.0351 | 0.2334 | 0.3588 | 0.9418 |
| response_max_share | 488 | 0 | 0.0005 | 0.0011 | 0.0213 | 0.125 | 0.1667 | 0.4446 |
| response_unique_share | 579 | 0 | 0.0015 | 0.0036 | 0.5962 | 1 | 1 | 1 |
| response_rare_level_share | 110 | 0.004 | 0.0368 | 0.0556 | 0.3103 | 0.4667 | 0.4902 | 0.5 |
| response_max_abs_rho | 543 | 0.0021 | 0.1411 | 0.2044 | 0.6224 | 0.9882 | 1 | 1 |
