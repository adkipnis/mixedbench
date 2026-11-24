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

**Corpus.** 1253 registry rows over 1088 datasets and 1620 grouping
factors; per tier R 637, T 240, O 138, D 126, E 112. Excluded: 2718 objects (no grouping structure 1299, derived or duplicated table 944, unreadable format 206, simulated data 81, time series without replication 77, response missing or undocumented 57, not the paper's data 48, too large 4, wide without a long form 1, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 8 | 30 | 42 | 600 | 15524 | 47396 | 25000095 | 23025 |
| tier R | 637 | 8 | 20 | 32 | 236 | 3850 | 8804 | 374250 |  |
| tier E | 112 | 16 | 29 | 40 | 528 | 12573 | 32877 | 1000209 |  |
| tier T | 240 | 12 | 47 | 80 | 846 | 14364 | 36997 | 2745952 |  |
| tier D | 126 | 45 | 160 | 208 | 960 | 19200 | 34350 | 210658 |  |
| tier O | 138 | 52 | 382 | 492 | 12996 | 949137 | 1330816 | 25000095 |  |
| without agridat | 1223 | 8 | 29 | 42 | 610 | 16151 | 48058 | 25000095 |  |
| flat | 1111 | 3 | 9 | 13 | 89 | 2700 | 7019 | 1853035 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 1 | 1 | 1 | 1 | 2 | 2 | 6 | 3 |
| tier R | 637 | 1 | 1 | 1 | 1 | 2 | 2 | 6 |  |
| tier E | 112 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 240 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 126 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 138 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 1223 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 959 | 59% |
| crossed | 318 | 20% |
| nested | 207 | 13% |
| mixed | 136 | 8% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 2 | 4 | 6 | 45 | 554 | 2025 | 241600 | 414 |
| tier R | 779 | 2 | 5 | 6 | 36 | 365 | 605 | 20670 |  |
| tier E | 161 | 3 | 4 | 5 | 25 | 386 | 789 | 19898 |  |
| tier T | 288 | 2 | 5 | 8 | 67 | 1000 | 1683 | 108295 |  |
| tier D | 194 | 2 | 3 | 4 | 53 | 275 | 534 | 13319 |  |
| tier O | 198 | 2 | 9 | 12 | 69 | 26074 | 39393 | 241600 |  |
| without agridat | 1566 | 2 | 5 | 6 | 47 | 581 | 2197 | 241600 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 1 | 1 | 1 | 4 | 101 | 370 | 44194 | 1 |
| tier R | 779 | 1 | 1 | 1 | 4 | 27 | 53 | 1536 |  |
| tier E | 161 | 1 | 1 | 1 | 6 | 216 | 411 | 1872 |  |
| tier T | 288 | 1 | 1 | 1 | 3 | 58 | 135 | 44194 |  |
| tier D | 194 | 1 | 1 | 1 | 12 | 326 | 697 | 8162 |  |
| tier O | 198 | 1 | 1 | 1 | 12 | 864 | 1734 | 23814 |  |
| without agridat | 1566 | 1 | 1 | 1 | 4 | 113 | 376 | 44194 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 1 | 1 | 1 | 6 | 135 | 393 | 44194 | - |
| tier R | 779 | 1 | 1 | 1 | 4 | 31 | 70 | 1536 |  |
| tier E | 161 | 1 | 1 | 2 | 7 | 228 | 456 | 2442 |  |
| tier T | 288 | 1 | 1 | 1 | 5 | 93 | 198 | 44194 |  |
| tier D | 194 | 1 | 1 | 2 | 16 | 340 | 840 | 8162 |  |
| tier O | 198 | 1 | 1 | 1 | 24 | 1026 | 5119 | 24620 |  |
| without agridat | 1566 | 1 | 1 | 1 | 5 | 145 | 395 | 44194 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 1 | 2 | 2 | 8 | 200 | 528 | 58594 | - |
| tier R | 779 | 1 | 2 | 2 | 5 | 40 | 100 | 4489 |  |
| tier E | 161 | 1 | 2 | 2 | 12 | 500 | 660 | 4200 |  |
| tier T | 288 | 1 | 2 | 2 | 9 | 139 | 465 | 58594 |  |
| tier D | 194 | 1 | 3 | 3 | 28 | 412 | 1128 | 8511 |  |
| tier O | 198 | 1 | 1 | 2 | 44 | 1523 | 12644 | 26562 |  |
| without agridat | 1566 | 1 | 2 | 2 | 8 | 214 | 539 | 58594 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 1 | 2 | 2 | 12 | 336 | 900 | 71619 | - |
| tier R | 779 | 1 | 2 | 2 | 7 | 61 | 168 | 23509 |  |
| tier E | 161 | 2 | 2 | 2 | 14 | 773 | 1292 | 4650 |  |
| tier T | 288 | 2 | 2 | 3 | 11 | 215 | 528 | 71619 |  |
| tier D | 194 | 2 | 3 | 4 | 40 | 458 | 1662 | 8639 |  |
| tier O | 198 | 1 | 3 | 6 | 64 | 2853 | 18180 | 35361 |  |
| without agridat | 1566 | 1 | 2 | 2 | 12 | 350 | 921 | 71619 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 2 | 2 | 2 | 16 | 535 | 1517 | 618486 | 300 |
| tier R | 779 | 2 | 2 | 2 | 8 | 104 | 226 | 32017 |  |
| tier E | 161 | 2 | 2 | 2 | 25 | 937 | 2168 | 4860 |  |
| tier T | 288 | 2 | 2 | 3 | 16 | 436 | 1095 | 71619 |  |
| tier D | 194 | 3 | 3 | 4 | 40 | 554 | 1797 | 8639 |  |
| tier O | 198 | 2 | 6 | 14 | 192 | 18180 | 28549 | 618486 |  |
| without agridat | 1566 | 2 | 2 | 2 | 16 | 554 | 1536 | 618486 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.405). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 0.0114 | 0.4942 | 1.1846 | 106.0376 | inf | inf | inf | - |
| tier R | 779 | 0.0251 | 0.8344 | 1.5678 | inf | inf | inf | inf |  |
| tier E | 161 | 0.1733 | 0.4936 | 0.9496 | 36.0263 | inf | inf | inf |  |
| tier T | 288 | 0.0438 | 0.6634 | 1.3575 | 18.622 | inf | inf | inf |  |
| tier D | 194 | 0.2722 | 1.2319 | 1.771 | 213.4257 | inf | inf | inf |  |
| tier O | 198 | 0.0114 | 0.0531 | 0.1947 | 11.5864 | inf | inf | inf |  |
| without agridat | 1566 | 0.0114 | 0.4936 | 1.1832 | 72.2517 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 0 | 0 | 0 | 0 | 0.1569 | 0.4171 | 0.9964 | - |
| tier R | 779 | 0 | 0 | 0 | 0 | 0.1848 | 0.4918 | 0.9964 |  |
| tier E | 161 | 0 | 0 | 0 | 0 | 0.0588 | 0.1036 | 0.5329 |  |
| tier T | 288 | 0 | 0 | 0 | 0 | 0.1602 | 0.4082 | 0.8448 |  |
| tier D | 194 | 0 | 0 | 0 | 0 | 0.0769 | 0.1957 | 0.7481 |  |
| tier O | 198 | 0 | 0 | 0 | 0 | 0.3651 | 0.6326 | 0.9263 |  |
| without agridat | 1566 | 0 | 0 | 0 | 0 | 0.1569 | 0.4082 | 0.9263 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1620 | 0 | 0 | 0 | 0.0988 | 0.8933 | 1.2916 | 9.2873 | - |
| tier R | 779 | 0 | 0 | 0 | 0 | 0.7869 | 1.0828 | 5.899 |  |
| tier E | 161 | 0 | 0 | 0 | 0.1658 | 1.0049 | 1.3311 | 1.9835 |  |
| tier T | 288 | 0 | 0 | 0 | 0.2345 | 0.7919 | 1.0762 | 3.5667 |  |
| tier D | 194 | 0 | 0 | 0 | 0.062 | 0.7252 | 0.8954 | 1.7829 |  |
| tier O | 198 | 0 | 0 | 0 | 0.2975 | 2.2431 | 4.2655 | 9.2873 |  |
| without agridat | 1566 | 0 | 0 | 0 | 0.1131 | 0.8939 | 1.3311 | 9.2873 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 2910 | 53% |
| binary | 1801 | 33% |
| categorical | 665 | 12% |
| ordered | 76 | 1% |

| level | n | share |
|---|---|---|
| within | 3452 | 63% |
| group | 2000 | 37% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 741 | 2 | 3 | 3 | 4 | 27 | 56 | 1134 | - |
| tier R | 280 | 2 | 3 | 3 | 4 | 10 | 15 | 49 |  |
| tier E | 27 | 2 | 2 | 2 | 3 | 11 | 13 | 15 |  |
| tier T | 107 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 66 | 3 | 3 | 3 | 4 | 39 | 69 | 117 |  |
| tier O | 261 | 2 | 3 | 3 | 6 | 73 | 155 | 1134 |  |
| without agridat | 709 | 2 | 3 | 3 | 4 | 28 | 60 | 1134 |  |
| flat | 1415 | 0 | 1 | 3 | 10 | 103 | 234 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 255 | 34% |
| 11+ | 143 | 19% |
| 4 | 142 | 19% |
| 5 | 55 | 7% |
| 6 | 38 | 5% |
| 8 | 31 | 4% |
| 2 | 26 | 4% |
| 7 | 19 | 3% |
| 9 | 17 | 2% |
| 10 | 15 | 2% |

Implied design columns of a model under the observed categorical share
(0.136) and mean columns per categorical (15.171):
9 terms 26.33 columns, 14 terms 40.97 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 0 | 0 | 1 | 3 | 13 | 23 | 22045 | 11 |
| tier R | 637 | 0 | 0 | 0 | 3 | 11 | 16 | 77 |  |
| tier E | 112 | 0 | 0 | 0 | 2 | 7 | 12 | 31 |  |
| tier T | 240 | 0 | 1 | 1 | 4 | 11 | 14 | 31 |  |
| tier D | 126 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 138 | 0 | 0 | 1 | 5 | 51 | 169 | 22045 |  |
| without agridat | 1223 | 0 | 0 | 1 | 3 | 13 | 21 | 22045 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1253 | 0 | 1 | 1 | 6 | 40 | 196 | 382085 | - |
| tier R | 637 | 0 | 1 | 1 | 5 | 29 | 53 | 9422 |  |
| tier E | 112 | 0 | 0 | 0 | 3 | 12 | 17 | 543 |  |
| tier T | 240 | 0 | 1 | 1 | 5 | 20 | 40 | 11029 |  |
| tier D | 126 | 1 | 1 | 3 | 12 | 260 | 722 | 4580 |  |
| tier O | 138 | 0 | 1 | 3 | 10 | 5227 | 23670 | 382085 |  |
| without agridat | 1223 | 0 | 1 | 1 | 6 | 40 | 210 | 382085 |  |
| flat | 1111 | 0 | 1 | 2 | 5 | 29 | 100 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 1182 | 1 | 1 | 1 | 3.1653 | 12.129 | 18.3378 | inf |
| condition_all | 1149 | 1 | 1 | 1.0123 | 5.1655 | 37.9484 | 215.2496 | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 6754 | -992.7471 | -1.2422 | -0.7385 | 0.4395 | 6.7918 | 9.8881 | 898.2178 |
| excess_kurtosis | 6754 | -2.0093 | -1.3138 | -1.2021 | 0.4954 | 72.1848 | 131.5196 | 1050361.6397 |
| outlier_share | 6754 | 0 | 0 | 0 | 0 | 0.0136 | 0.0197 | 0.058 |
| zero_share | 7122 | 0 | 0 | 0 | 0 | 0.625 | 0.9834 | 1 |
| min_share | 7314 | 0 | 0.0003 | 0.001 | 0.052 | 0.9659 | 1 | 1 |
| max_share | 7314 | 0 | 0 | 0.0002 | 0.0117 | 0.3333 | 1 | 1 |
| unique_share | 12885 | 0 | 0 | 0.0001 | 0.0054 | 0.2451 | 0.6465 | 1 |
| rare_level_share | 5766 | 0 | 0.0004 | 0.002 | 0.1495 | 0.4993 | 0.5 | 1 |
| max_abs_rho | 10012 | 0 | 0.024 | 0.0738 | 0.5455 | 1 | 1 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 13097 | -3.1327 | -0.0909 | -0.0109 | 0.291 | 1 | 1 | 1 |
| group_level_r2 | 5668 | -56 | -0.6692 | -0.117 | 0.0028 | 0.9691 | 1 | 1 |
| absent_level_share | 7518 | 0 | 0 | 0 | 0.4894 | 0.9034 | 0.9667 | 1 |
| size_rho | 9724 | -1 | -0.4733 | -0.2609 | 0.0322 | 0.4176 | 0.5897 | 1 |
| within_sd_cv | 8979 | 0 | 0 | 0 | 0.297 | 3.2239 | 5.2109 | 235.3189 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 261 | 0 | 0 | 0 | 0.15 | 0.988 | 0.9967 | 0.9999 |

| pair relation | n | share |
|---|---|---|
| crossed | 261 | 56% |
| nested | 204 | 44% |

| superior | n | share |
|---|---|---|
| factor_a | 171 | 84% |
| factor_b | 33 | 16% |

## Quirk statistics per response

Every registry row's response, by the statistics its type defines: a binomial one as its
successes' share of the trials, an ordinal one by its levels.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 307 | 2 | 2 | 2 | 2 | 6 | 8 | 1495 |
| response_skewness | 946 | -10.4422 | -0.8135 | -0.54 | 0.4203 | 3.1186 | 4.592 | 254.4069 |
| response_excess_kurtosis | 946 | -1.9502 | -1.2021 | -0.9652 | 0.3598 | 15.4203 | 37.6216 | 69205.0886 |
| response_outlier_share | 946 | 0 | 0 | 0 | 0 | 0.0102 | 0.0139 | 0.0385 |
| response_zero_share | 1036 | 0 | 0 | 0 | 0 | 0.1271 | 0.3758 | 0.9652 |
| response_min_share | 1052 | 0 | 0.0001 | 0.0004 | 0.013 | 0.2569 | 0.4151 | 0.9652 |
| response_max_share | 1052 | 0 | 0.0001 | 0.0002 | 0.0085 | 0.1456 | 0.2708 | 0.7713 |
| response_unique_share | 1253 | 0 | 0.0002 | 0.0008 | 0.2083 | 0.98 | 1 | 1 |
| response_rare_level_share | 307 | 0.0001 | 0.0041 | 0.0178 | 0.1904 | 0.4465 | 0.4761 | 0.5 |
| response_max_abs_rho | 1091 | 0 | 0.0319 | 0.0744 | 0.3375 | 0.7993 | 0.8861 | 1 |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 879 | 0 | 0 | 0.0002 | 0.5733 | 324.6186 | 3208.4952 | 155213768.6032 |
| sigma2_random | 879 | 0 | 0 | 0.0068 | 1 | 363.3155 | 5590.0247 | 1745712221.7761 |
| sigma2_residual | 606 | 0 | 0.0027 | 0.0125 | 2.316 | 1336.9035 | 18893.6534 | 471364189.2977 |
| sigma2_distribution | 879 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.8369 |
| sd_eta | 879 | 0 | 0.1046 | 0.206 | 1.3565 | 29.8223 | 96.482 | 28202.6124 |
| r2_marginal | 879 | 0 | 0 | 0.0005 | 0.1524 | 0.7233 | 0.8586 | 0.9946 |
| r2_conditional | 879 | 0 | 0.0829 | 0.1425 | 0.6454 | 0.967 | 0.9936 | 1 |
| q | 1163 | 1 | 1 | 1 | 1 | 2 | 3 | 12 |
| sigma2 | 1163 | 0 | 0 | 0.0015 | 0.7018 | 238.9207 | 3741.3752 | 1720517318.1414 |
| icc | 1163 | 0 | 0 | 0.0031 | 0.1636 | 0.6765 | 0.8151 | 0.9998 |
| icc_adjusted | 1163 | 0 | 0 | 0.0061 | 0.2721 | 0.8493 | 0.95 | 1 |

| status | n | share |
|---|---|---|
| ok | 638 | 61% |
| warning | 140 | 13% |
| error | 118 | 11% |
| singular | 101 | 10% |
| no_formula | 40 | 4% |
| timeout | 4 | 0% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 737 | 59% |
| binary | 172 | 14% |
| count | 132 | 11% |
| ordinal | 106 | 8% |
| binomial | 77 | 6% |
| categorical | 29 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 616 | 49% |
| pyreadr | 612 | 49% |
| rdata | 19 | 2% |
| deparse | 6 | 0% |

| published | n | share |
|---|---|---|
| yes | 760 | 61% |
| no | 493 | 39% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 907 (derived or duplicated table 574, unreadable format 158, no grouping structure 89, not the paper's data 48, response missing or undocumented 38).
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
