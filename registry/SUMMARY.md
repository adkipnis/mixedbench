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

**Corpus.** 1253 registry rows over 1088 datasets and 1615 grouping
factors; per tier R 639, T 239, O 137, D 126, E 112. Excluded: 2720 objects (no grouping structure 1299, derived or duplicated table 942, unreadable format 211, simulated data 81, time series without replication 77, response missing or undocumented 56, not the paper's data 48, too large 4, wide without a long form 1, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 8 | 30 | 42 | 599 | 15362 | 46861 | 25000095 | 23025 |
| tier R | 639 | 8 | 20 | 32 | 236 | 3850 | 8804 | 374250 |  |
| tier E | 112 | 16 | 29 | 40 | 432 | 12573 | 32877 | 1000209 |  |
| tier T | 239 | 12 | 47 | 80 | 846 | 14364 | 36997 | 2745952 |  |
| tier D | 126 | 45 | 160 | 208 | 960 | 19200 | 34350 | 210658 |  |
| tier O | 137 | 52 | 382 | 492 | 12960 | 949137 | 1330816 | 25000095 |  |
| without agridat | 1224 | 8 | 29 | 42 | 609 | 15834 | 47396 | 25000095 |  |
| flat | 1111 | 3 | 9 | 13 | 89 | 2700 | 7019 | 1853035 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 1 | 1 | 1 | 1 | 2 | 2 | 6 | 3 |
| tier R | 639 | 1 | 1 | 1 | 1 | 2 | 2 | 6 |  |
| tier E | 112 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 239 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 126 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 137 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 1224 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 962 | 60% |
| crossed | 316 | 20% |
| nested | 207 | 13% |
| mixed | 130 | 8% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 2 | 4 | 6 | 45 | 554 | 2024 | 241600 | 414 |
| tier R | 781 | 2 | 5 | 6 | 36 | 365 | 600 | 20670 |  |
| tier E | 157 | 3 | 4 | 5 | 24 | 392 | 1518 | 19898 |  |
| tier T | 287 | 2 | 5 | 8 | 67 | 1000 | 1683 | 108295 |  |
| tier D | 194 | 2 | 3 | 4 | 53 | 275 | 534 | 13319 |  |
| tier O | 196 | 2 | 9 | 12 | 69 | 26074 | 39393 | 241600 |  |
| without agridat | 1562 | 2 | 5 | 6 | 47 | 571 | 2162 | 241600 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 1 | 1 | 1 | 4 | 101 | 370 | 44194 | 1 |
| tier R | 781 | 1 | 1 | 1 | 4 | 27 | 51 | 1536 |  |
| tier E | 157 | 1 | 1 | 1 | 6 | 228 | 500 | 1872 |  |
| tier T | 287 | 1 | 1 | 1 | 3 | 58 | 135 | 44194 |  |
| tier D | 194 | 1 | 1 | 1 | 12 | 326 | 697 | 8162 |  |
| tier O | 196 | 1 | 1 | 1 | 12 | 864 | 1734 | 23814 |  |
| without agridat | 1562 | 1 | 1 | 1 | 4 | 108 | 376 | 44194 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 1 | 1 | 1 | 6 | 135 | 392 | 44194 | - |
| tier R | 781 | 1 | 1 | 1 | 4 | 30 | 64 | 1536 |  |
| tier E | 157 | 1 | 1 | 2 | 7 | 282 | 500 | 2442 |  |
| tier T | 287 | 1 | 1 | 1 | 5 | 93 | 198 | 44194 |  |
| tier D | 194 | 1 | 1 | 2 | 16 | 340 | 840 | 8162 |  |
| tier O | 196 | 1 | 1 | 1 | 24 | 1026 | 5119 | 24620 |  |
| without agridat | 1562 | 1 | 1 | 1 | 5 | 141 | 393 | 44194 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 1 | 2 | 2 | 8 | 200 | 522 | 58594 | - |
| tier R | 781 | 1 | 2 | 2 | 5 | 39 | 100 | 4489 |  |
| tier E | 157 | 1 | 2 | 3 | 12 | 504 | 660 | 4200 |  |
| tier T | 287 | 1 | 2 | 2 | 9 | 139 | 465 | 58594 |  |
| tier D | 194 | 1 | 3 | 3 | 28 | 413 | 1128 | 8511 |  |
| tier O | 196 | 1 | 1 | 2 | 44 | 1523 | 12644 | 26562 |  |
| without agridat | 1562 | 1 | 2 | 2 | 8 | 211 | 528 | 58594 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 1 | 2 | 2 | 12 | 329 | 894 | 71619 | - |
| tier R | 781 | 1 | 2 | 2 | 7 | 61 | 160 | 23509 |  |
| tier E | 157 | 2 | 2 | 3 | 15 | 773 | 1309 | 4650 |  |
| tier T | 287 | 2 | 2 | 3 | 11 | 215 | 528 | 71619 |  |
| tier D | 194 | 2 | 3 | 4 | 40 | 458 | 1662 | 8639 |  |
| tier O | 196 | 1 | 3 | 6 | 64 | 2853 | 18180 | 35361 |  |
| without agridat | 1562 | 1 | 2 | 2 | 12 | 350 | 912 | 71619 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 2 | 2 | 2 | 16 | 528 | 1508 | 618486 | 300 |
| tier R | 781 | 2 | 2 | 2 | 8 | 101 | 217 | 32017 |  |
| tier E | 157 | 2 | 2 | 3 | 27 | 937 | 2314 | 4860 |  |
| tier T | 287 | 2 | 2 | 3 | 16 | 436 | 1095 | 71619 |  |
| tier D | 194 | 3 | 3 | 4 | 40 | 554 | 1797 | 8639 |  |
| tier O | 196 | 2 | 6 | 14 | 192 | 18180 | 28549 | 618486 |  |
| without agridat | 1562 | 2 | 2 | 2 | 16 | 549 | 1517 | 618486 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.407). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 0.0114 | 0.4942 | 1.1821 | 99.2843 | inf | inf | inf | - |
| tier R | 781 | 0.0251 | 0.8344 | 1.5678 | inf | inf | inf | inf |  |
| tier E | 157 | 0.1733 | 0.4258 | 0.9384 | 28.0769 | inf | inf | inf |  |
| tier T | 287 | 0.0438 | 0.6634 | 1.3575 | 18.622 | inf | inf | inf |  |
| tier D | 194 | 0.2722 | 1.2319 | 1.771 | 213.4257 | inf | inf | inf |  |
| tier O | 196 | 0.0114 | 0.0531 | 0.1947 | 12.6059 | inf | inf | inf |  |
| without agridat | 1562 | 0.0114 | 0.4936 | 1.1765 | 72.2517 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 0 | 0 | 0 | 0 | 0.16 | 0.4171 | 0.9964 | - |
| tier R | 781 | 0 | 0 | 0 | 0 | 0.1848 | 0.4891 | 0.9964 |  |
| tier E | 157 | 0 | 0 | 0 | 0 | 0.0611 | 0.1161 | 0.5329 |  |
| tier T | 287 | 0 | 0 | 0 | 0 | 0.1602 | 0.4082 | 0.8448 |  |
| tier D | 194 | 0 | 0 | 0 | 0 | 0.0769 | 0.1957 | 0.7481 |  |
| tier O | 196 | 0 | 0 | 0 | 0 | 0.3651 | 0.6326 | 0.9263 |  |
| without agridat | 1562 | 0 | 0 | 0 | 0 | 0.16 | 0.4082 | 0.9263 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1615 | 0 | 0 | 0 | 0.0988 | 0.8954 | 1.2916 | 9.2873 | - |
| tier R | 781 | 0 | 0 | 0 | 0 | 0.7869 | 1.0828 | 5.899 |  |
| tier E | 157 | 0 | 0 | 0 | 0.1821 | 1.0108 | 1.3558 | 1.9835 |  |
| tier T | 287 | 0 | 0 | 0 | 0.2305 | 0.7919 | 1.0762 | 3.5667 |  |
| tier D | 194 | 0 | 0 | 0 | 0.062 | 0.7252 | 0.8954 | 1.7829 |  |
| tier O | 196 | 0 | 0 | 0 | 0.2927 | 2.2431 | 4.2655 | 9.2873 |  |
| without agridat | 1562 | 0 | 0 | 0 | 0.1131 | 0.9093 | 1.3311 | 9.2873 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 2916 | 53% |
| binary | 1777 | 33% |
| categorical | 690 | 13% |
| ordered | 76 | 1% |

| level | n | share |
|---|---|---|
| within | 3462 | 63% |
| group | 1997 | 37% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 766 | 2 | 3 | 3 | 4 | 27 | 56 | 1134 | - |
| tier R | 278 | 2 | 3 | 3 | 4 | 9 | 15 | 49 |  |
| tier E | 27 | 2 | 2 | 2 | 3 | 11 | 13 | 15 |  |
| tier T | 107 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 66 | 3 | 3 | 3 | 4 | 39 | 69 | 117 |  |
| tier O | 288 | 2 | 3 | 3 | 6 | 70 | 152 | 1134 |  |
| without agridat | 736 | 2 | 3 | 3 | 4 | 27 | 60 | 1134 |  |
| flat | 1415 | 0 | 1 | 3 | 10 | 103 | 234 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 267 | 35% |
| 4 | 150 | 20% |
| 11+ | 145 | 19% |
| 5 | 55 | 7% |
| 6 | 37 | 5% |
| 8 | 28 | 4% |
| 2 | 26 | 3% |
| 7 | 23 | 3% |
| 10 | 18 | 2% |
| 9 | 17 | 2% |

Implied design columns of a model under the observed categorical share
(0.14) and mean columns per categorical (14.821):
9 terms 26.45 columns, 14 terms 41.15 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 0 | 0 | 1 | 3 | 13 | 23 | 22134 | 11 |
| tier R | 639 | 0 | 0 | 0 | 3 | 11 | 15 | 69 |  |
| tier E | 112 | 0 | 0 | 0 | 2 | 7 | 12 | 31 |  |
| tier T | 239 | 0 | 1 | 1 | 4 | 11 | 14 | 31 |  |
| tier D | 126 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 137 | 0 | 0 | 1 | 6 | 76 | 169 | 22134 |  |
| without agridat | 1224 | 0 | 0 | 1 | 3 | 13 | 22 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 0 | 1 | 1 | 6 | 41 | 196 | 382085 | - |
| tier R | 639 | 0 | 1 | 1 | 5 | 29 | 53 | 9422 |  |
| tier E | 112 | 0 | 0 | 0 | 3 | 12 | 17 | 543 |  |
| tier T | 239 | 0 | 1 | 1 | 5 | 20 | 40 | 11030 |  |
| tier D | 126 | 1 | 1 | 3 | 12 | 260 | 722 | 4580 |  |
| tier O | 137 | 0 | 1 | 3 | 10 | 5227 | 23759 | 382085 |  |
| without agridat | 1224 | 0 | 1 | 1 | 6 | 41 | 210 | 382085 |  |
| flat | 1111 | 0 | 1 | 2 | 5 | 29 | 100 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 1182 | 1 | 1 | 1 | 3.1681 | 12.129 | 18.3554 | inf |
| condition_all | 1149 | 1 | 1 | 1.0123 | 5.1655 | 37.9484 | 252.0727 | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 6765 | -992.7471 | -1.2422 | -0.7362 | 0.4418 | 6.8172 | 9.8881 | 898.2178 |
| excess_kurtosis | 6765 | -2.0093 | -1.314 | -1.2023 | 0.5014 | 72.4138 | 131.528 | 1050361.6397 |
| outlier_share | 6765 | 0 | 0 | 0 | 0 | 0.0136 | 0.0198 | 0.0583 |
| zero_share | 7133 | 0 | 0 | 0 | 0 | 0.6321 | 0.9836 | 1 |
| min_share | 7326 | 0 | 0.0003 | 0.0011 | 0.0523 | 0.9664 | 1 | 1 |
| max_share | 7326 | 0 | 0 | 0.0002 | 0.0117 | 0.3333 | 1 | 1 |
| unique_share | 12893 | 0 | 0 | 0.0001 | 0.0054 | 0.2453 | 0.651 | 1 |
| rare_level_share | 5763 | 0 | 0.0004 | 0.0019 | 0.1472 | 0.4993 | 0.5 | 1 |
| max_abs_rho | 9996 | 0 | 0.0237 | 0.0732 | 0.5445 | 1 | 1 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 13070 | -3.1327 | -0.0909 | -0.011 | 0.2924 | 1 | 1 | 1 |
| group_level_r2 | 5665 | -56 | -0.6692 | -0.1168 | 0.0029 | 0.9691 | 1 | 1 |
| absent_level_share | 7503 | 0 | 0 | 0 | 0.4906 | 0.9053 | 0.9667 | 1 |
| size_rho | 9640 | -1 | -0.4707 | -0.2608 | 0.0324 | 0.4154 | 0.5801 | 1 |
| within_sd_cv | 8954 | 0 | 0 | 0 | 0.3002 | 3.2307 | 5.2645 | 235.3189 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 258 | 0 | 0 | 0 | 0.1441 | 0.988 | 0.9973 | 0.9999 |

| pair relation | n | share |
|---|---|---|
| crossed | 258 | 56% |
| nested | 200 | 44% |

| superior | n | share |
|---|---|---|
| factor_a | 167 | 84% |
| factor_b | 33 | 16% |

## Quirk statistics per response

Every registry row's response, by the statistics its type defines: a binomial one as its
successes' share of the trials, an ordinal one by its levels.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 307 | 2 | 2 | 2 | 2 | 7 | 8 | 1495 |
| response_skewness | 946 | -10.4422 | -0.8075 | -0.54 | 0.4187 | 3.1186 | 4.592 | 254.4069 |
| response_excess_kurtosis | 946 | -1.9502 | -1.2021 | -0.9652 | 0.3544 | 15.4203 | 37.6216 | 69205.0886 |
| response_outlier_share | 946 | 0 | 0 | 0 | 0 | 0.0102 | 0.0139 | 0.0385 |
| response_zero_share | 1036 | 0 | 0 | 0 | 0 | 0.125 | 0.3758 | 0.9652 |
| response_min_share | 1052 | 0 | 0.0001 | 0.0004 | 0.0129 | 0.25 | 0.4151 | 0.9652 |
| response_max_share | 1052 | 0 | 0.0001 | 0.0002 | 0.0085 | 0.1456 | 0.2708 | 0.7713 |
| response_unique_share | 1253 | 0 | 0.0002 | 0.0008 | 0.2086 | 0.98 | 1 | 1 |
| response_rare_level_share | 307 | 0.0001 | 0.0024 | 0.0157 | 0.189 | 0.4465 | 0.4761 | 0.5 |
| response_max_abs_rho | 1091 | 0 | 0.0319 | 0.0749 | 0.3406 | 0.7993 | 0.8861 | 1 |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 878 | 0 | 0 | 0.0002 | 0.5585 | 324.6186 | 3208.4952 | 155213768.6032 |
| sigma2_random | 878 | 0 | 0 | 0.0068 | 0.9873 | 363.3155 | 5590.0247 | 1745712221.7761 |
| sigma2_residual | 605 | 0 | 0.0027 | 0.0114 | 2.1115 | 1336.9035 | 18893.6534 | 471364189.2977 |
| sigma2_distribution | 878 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.8369 |
| sd_eta | 878 | 0 | 0.1046 | 0.206 | 1.3461 | 29.8223 | 96.482 | 28202.6124 |
| r2_marginal | 878 | 0 | 0 | 0.0005 | 0.1534 | 0.72 | 0.8506 | 0.9946 |
| r2_conditional | 878 | 0 | 0.0829 | 0.1425 | 0.6478 | 0.9675 | 0.9936 | 1 |
| q | 1159 | 1 | 1 | 1 | 1 | 2 | 3 | 12 |
| sigma2 | 1159 | 0 | 0 | 0.0014 | 0.687 | 247.5284 | 4086.4295 | 1720517318.1414 |
| icc | 1159 | 0 | 0 | 0.003 | 0.1641 | 0.6812 | 0.8154 | 0.9998 |
| icc_adjusted | 1159 | 0 | 0 | 0.006 | 0.2736 | 0.8561 | 0.9529 | 1 |

| status | n | share |
|---|---|---|
| ok | 637 | 61% |
| warning | 140 | 13% |
| error | 118 | 11% |
| singular | 101 | 10% |
| no_formula | 41 | 4% |
| timeout | 4 | 0% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 738 | 59% |
| binary | 172 | 14% |
| count | 131 | 10% |
| ordinal | 106 | 8% |
| binomial | 77 | 6% |
| categorical | 29 | 2% |

| reader | n | share |
|---|---|---|
| pyreadr | 614 | 49% |
| pandas | 613 | 49% |
| rdata | 19 | 2% |
| deparse | 7 | 1% |

| published | n | share |
|---|---|---|
| yes | 762 | 61% |
| no | 491 | 39% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 907 (derived or duplicated table 574, unreadable format 159, no grouping structure 89, not the paper's data 48, response missing or undocumented 37).
- Papers with a registry row: 41, over 126 rows.

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
