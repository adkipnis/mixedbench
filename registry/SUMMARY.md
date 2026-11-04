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

**Corpus.** 1076 registry rows over 942 datasets and 1407 grouping
factors; per tier R 523, T 219, O 135, D 104, E 95. Excluded: 2865 objects (no grouping structure 1566, derived or duplicated table 864, unreadable format 204, simulated data 76, time series without replication 59, response missing or undocumented 46, not the paper's data 46, too large 3, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1076 | 7 | 32 | 48 | 714 | 19200 | 59929 | 25000095 | 23025 |
| tier R | 523 | 8 | 25 | 36 | 322 | 4152 | 8465 | 374250 |  |
| tier E | 95 | 20 | 30 | 40 | 528 | 16409 | 32877 | 1000209 |  |
| tier T | 219 | 7 | 44 | 72 | 846 | 15362 | 39925 | 2745952 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 135 | 52 | 382 | 492 | 11700 | 844392 | 1330816 | 25000095 |  |
| without agridat | 1047 | 7 | 32 | 48 | 761 | 20796 | 61248 | 25000095 |  |
| flat | 722 | 3 | 9 | 14 | 75 | 1445 | 3888 | 81422 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1076 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 523 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 95 | 1 | 1 | 1 | 1 | 2 | 4 | 5 |  |
| tier T | 219 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 135 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 1047 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 811 | 58% |
| crossed | 273 | 19% |
| nested | 198 | 14% |
| mixed | 125 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 2 | 5 | 6 | 45 | 600 | 2197 | 162541 | 414 |
| tier R | 656 | 2 | 5 | 6 | 36 | 332 | 688 | 20670 |  |
| tier E | 136 | 3 | 4 | 5 | 25 | 500 | 2025 | 19898 |  |
| tier T | 266 | 2 | 5 | 7 | 60 | 953 | 1595 | 108295 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 191 | 2 | 9 | 13 | 69 | 25489 | 38190 | 162541 |  |
| without agridat | 1356 | 2 | 5 | 6 | 47 | 685 | 2410 | 162541 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 1 | 1 | 1 | 5 | 113 | 420 | 44194 | 1 |
| tier R | 656 | 1 | 1 | 1 | 4 | 30 | 56 | 1536 |  |
| tier E | 136 | 1 | 1 | 1 | 8 | 282 | 500 | 1872 |  |
| tier T | 266 | 1 | 1 | 1 | 3 | 64 | 135 | 44194 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 191 | 1 | 1 | 1 | 13 | 864 | 1734 | 23814 |  |
| without agridat | 1356 | 1 | 1 | 1 | 5 | 132 | 458 | 44194 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 1 | 1 | 1 | 7 | 145 | 459 | 44194 | - |
| tier R | 656 | 1 | 1 | 1 | 5 | 33 | 74 | 1536 |  |
| tier E | 136 | 1 | 1 | 2 | 9 | 282 | 500 | 2442 |  |
| tier T | 266 | 1 | 1 | 1 | 6 | 106 | 201 | 44194 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 191 | 1 | 1 | 1 | 25 | 1026 | 5119 | 24620 |  |
| without agridat | 1356 | 1 | 1 | 1 | 7 | 156 | 500 | 44194 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 1 | 2 | 2 | 10 | 270 | 587 | 58594 | - |
| tier R | 656 | 1 | 2 | 2 | 7 | 44 | 104 | 4489 |  |
| tier E | 136 | 1 | 3 | 3 | 15 | 559 | 823 | 4200 |  |
| tier T | 266 | 1 | 2 | 2 | 10 | 176 | 474 | 58594 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 191 | 1 | 1 | 2 | 47 | 1523 | 12644 | 26562 |  |
| without agridat | 1356 | 1 | 2 | 2 | 10 | 285 | 600 | 58594 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 1 | 2 | 3 | 15 | 400 | 1056 | 71619 | - |
| tier R | 656 | 1 | 2 | 3 | 9 | 72 | 172 | 23509 |  |
| tier E | 136 | 2 | 3 | 3 | 30 | 773 | 2168 | 4650 |  |
| tier T | 266 | 2 | 2 | 3 | 15 | 306 | 698 | 71619 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 191 | 1 | 3 | 6 | 68 | 2853 | 18180 | 35361 |  |
| without agridat | 1356 | 1 | 2 | 3 | 16 | 420 | 1200 | 71619 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 2 | 2 | 4 | 21 | 740 | 1844 | 618486 | 300 |
| tier R | 656 | 2 | 2 | 3 | 11 | 128 | 256 | 32017 |  |
| tier E | 136 | 2 | 3 | 3 | 34 | 1280 | 3428 | 4860 |  |
| tier T | 266 | 2 | 2 | 3 | 18 | 528 | 1324 | 71619 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 191 | 2 | 7 | 15 | 200 | 18180 | 28549 | 618486 |  |
| without agridat | 1356 | 2 | 2 | 4 | 22 | 765 | 1988 | 618486 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.355). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 0.0114 | 0.4671 | 1.0043 | 36.0263 | inf | inf | inf | - |
| tier R | 656 | 0.0251 | 0.7655 | 1.2966 | 3531.5072 | inf | inf | inf |  |
| tier E | 136 | 0.1733 | 0.4936 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 266 | 0.0438 | 0.6485 | 1.3394 | 11.7052 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 191 | 0.0114 | 0.0531 | 0.1947 | 11.5864 | inf | inf | inf |  |
| without agridat | 1356 | 0.0114 | 0.4666 | 0.9884 | 30.4798 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 0 | 0 | 0 | 0 | 0.1877 | 0.4255 | 0.9964 | - |
| tier R | 656 | 0 | 0 | 0 | 0 | 0.2045 | 0.4918 | 0.9964 |  |
| tier E | 136 | 0 | 0 | 0 | 0 | 0.0611 | 0.1053 | 0.5329 |  |
| tier T | 266 | 0 | 0 | 0 | 0 | 0.1667 | 0.3607 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 191 | 0 | 0 | 0 | 0 | 0.4632 | 0.6474 | 0.9263 |  |
| without agridat | 1356 | 0 | 0 | 0 | 0 | 0.1877 | 0.4255 | 0.9263 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1407 | 0 | 0 | 0 | 0.1619 | 0.963 | 1.3976 | 9.2873 | - |
| tier R | 656 | 0 | 0 | 0 | 0.0189 | 0.8442 | 1.1151 | 5.899 |  |
| tier E | 136 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.3558 | 1.9835 |  |
| tier T | 266 | 0 | 0 | 0 | 0.2874 | 0.7937 | 1.1784 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 191 | 0 | 0 | 0 | 0.2927 | 2.2431 | 4.2655 | 9.2873 |  |
| without agridat | 1356 | 0 | 0 | 0 | 0.1801 | 0.9679 | 1.4164 | 9.2873 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 2808 | 55% |
| binary | 1592 | 31% |
| categorical | 633 | 12% |
| ordered | 72 | 1% |

| level | n | share |
|---|---|---|
| within | 3294 | 65% |
| group | 1811 | 35% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 705 | 2 | 3 | 3 | 4 | 28 | 60 | 1134 | - |
| tier R | 247 | 2 | 3 | 3 | 4 | 10 | 15 | 56 |  |
| tier E | 22 | 2 | 2 | 2 | 3 | 7 | 10 | 13 |  |
| tier T | 98 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 287 | 2 | 3 | 3 | 6 | 70 | 152 | 1134 |  |
| without agridat | 675 | 2 | 3 | 3 | 4 | 29 | 68 | 1134 |  |
| flat | 1053 | 0 | 1 | 3 | 11 | 98 | 307 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 242 | 34% |
| 11+ | 141 | 20% |
| 4 | 139 | 20% |
| 5 | 46 | 7% |
| 6 | 33 | 5% |
| 2 | 25 | 4% |
| 8 | 25 | 4% |
| 7 | 22 | 3% |
| 10 | 17 | 2% |
| 9 | 15 | 2% |

Implied design columns of a model under the observed categorical share
(0.138) and mean columns per categorical (15.791):
9 terms 27.38 columns, 14 terms 42.6 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1076 | 0 | 0 | 0 | 3 | 14 | 25 | 22134 | 11 |
| tier R | 523 | 0 | 0 | 0 | 3 | 11 | 17 | 69 |  |
| tier E | 95 | 0 | 0 | 0 | 2 | 7 | 11 | 13 |  |
| tier T | 219 | 0 | 0 | 1 | 4 | 11 | 13 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 135 | 0 | 0 | 1 | 5 | 76 | 169 | 22134 |  |
| without agridat | 1047 | 0 | 0 | 1 | 3 | 13 | 24 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1076 | 0 | 1 | 1 | 6 | 41 | 154 | 382085 | - |
| tier R | 523 | 0 | 1 | 1 | 6 | 31 | 55 | 9422 |  |
| tier E | 95 | 0 | 0 | 0 | 3 | 12 | 13 | 543 |  |
| tier T | 219 | 0 | 1 | 1 | 5 | 20 | 58 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 120 | 163 | 4580 |  |
| tier O | 135 | 0 | 2 | 3 | 10 | 5227 | 23759 | 382085 |  |
| without agridat | 1047 | 0 | 1 | 1 | 6 | 41 | 156 | 382085 |  |
| flat | 722 | 0 | 1 | 2 | 5 | 22 | 72 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 1006 | 1 | 1 | 1 | 3.2179 | 13.0316 | 19.1753 | inf |
| condition_all | 987 | 1 | 1 | 1.0028 | 5.2464 | 38.3174 | 201.5357 | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 6038 | -992.7471 | -0.9977 | -0.627 | 0.5066 | 7.6026 | 10.2843 | 898.2178 |
| excess_kurtosis | 6038 | -2.0093 | -1.306 | -1.2021 | 0.5777 | 81.0538 | 153.3511 | 1050361.6397 |
| outlier_share | 6038 | 0 | 0 | 0 | 0 | 0.0138 | 0.02 | 0.0583 |
| zero_share | 6170 | 0 | 0 | 0 | 0 | 0.6 | 0.979 | 1 |
| min_share | 6354 | 0 | 0.0002 | 0.0009 | 0.0455 | 0.854 | 0.9859 | 1 |
| max_share | 6354 | 0 | 0 | 0.0001 | 0.0072 | 0.1968 | 0.371 | 1 |
| unique_share | 10966 | 0 | 0 | 0.0001 | 0.0047 | 0.25 | 0.7431 | 1 |
| rare_level_share | 4799 | 0 | 0.0002 | 0.0012 | 0.135 | 0.4937 | 0.5 | 1 |
| max_abs_rho | 8758 | 0 | 0.0273 | 0.0706 | 0.5292 | 0.9957 | 1 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 11281 | -3.1327 | -0.0473 | -0.01 | 0.2364 | 1 | 1 | 1 |
| group_level_r2 | 5132 | -56 | -0.9583 | -0.1222 | 0.001 | 0.9984 | 1 | 1 |
| absent_level_share | 5999 | 0 | 0 | 0 | 0.4969 | 0.9286 | 0.9657 | 1 |
| size_rho | 9280 | -1 | -0.4617 | -0.2567 | 0.033 | 0.4079 | 0.5681 | 1 |
| within_sd_cv | 8278 | 0 | 0 | 0.0054 | 0.3432 | 3.4407 | 5.579 | 235.3189 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 230 | 0 | 0 | 0 | 0.1667 | 0.9926 | 0.9974 | 0.9999 |

| pair relation | n | share |
|---|---|---|
| crossed | 230 | 55% |
| nested | 187 | 45% |

| superior | n | share |
|---|---|---|
| factor_a | 158 | 84% |
| factor_b | 29 | 16% |

## Quirk statistics per response

Every registry row's response, by the statistics its type defines: a binomial one as its
successes' share of the trials, an ordinal one by its levels.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 267 | 2 | 2 | 2 | 2 | 7 | 9 | 1495 |
| response_skewness | 809 | -10.4422 | -0.8231 | -0.5739 | 0.3503 | 3.1465 | 4.8245 | 254.4069 |
| response_excess_kurtosis | 809 | -1.9502 | -1.2475 | -0.9652 | 0.3544 | 15.6477 | 37.6216 | 69205.0886 |
| response_outlier_share | 809 | 0 | 0 | 0 | 0 | 0.0102 | 0.0131 | 0.0312 |
| response_zero_share | 874 | 0 | 0 | 0 | 0 | 0.1189 | 0.3758 | 0.8942 |
| response_min_share | 890 | 0 | 0.0001 | 0.0003 | 0.0111 | 0.2419 | 0.3963 | 0.8942 |
| response_max_share | 890 | 0 | 0.0001 | 0.0002 | 0.0067 | 0.1445 | 0.2624 | 0.7713 |
| response_unique_share | 1076 | 0 | 0.0002 | 0.0006 | 0.1838 | 0.98 | 1 | 1 |
| response_rare_level_share | 267 | 0.0001 | 0.0024 | 0.0157 | 0.2037 | 0.4465 | 0.4761 | 0.5 |
| response_max_abs_rho | 924 | 0 | 0.0363 | 0.0743 | 0.3301 | 0.8131 | 0.9013 | 1 |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 787 | 0 | 0 | 0.0004 | 0.6006 | 350.7875 | 2356.2815 | 155213768.6032 |
| sigma2_random | 787 | 0 | 0.0001 | 0.0076 | 0.9986 | 380.723 | 5590.0247 | 1745712221.7761 |
| sigma2_residual | 545 | 0 | 0.0052 | 0.0176 | 2.4618 | 2284.1696 | 25239.2766 | 471364189.2977 |
| sigma2_distribution | 787 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.676 |
| sd_eta | 787 | 0 | 0.107 | 0.2105 | 1.3369 | 30.1039 | 97.6661 | 28202.6124 |
| r2_marginal | 787 | 0 | 0 | 0.0008 | 0.1567 | 0.7262 | 0.8632 | 0.9999 |
| r2_conditional | 787 | 0 | 0.0934 | 0.1429 | 0.6359 | 0.9649 | 0.9903 | 1 |
| q | 1057 | 1 | 1 | 1 | 1 | 2 | 3 | 12 |
| sigma2 | 1057 | 0 | 0 | 0.0019 | 0.6694 | 247.5284 | 4210.3458 | 1720517318.1414 |
| icc | 1057 | 0 | 0 | 0.0031 | 0.1454 | 0.6372 | 0.7929 | 0.9996 |
| icc_adjusted | 1057 | 0 | 0 | 0.0062 | 0.2533 | 0.8324 | 0.9383 | 1 |

| status | n | share |
|---|---|---|
| ok | 567 | 61% |
| warning | 131 | 14% |
| error | 108 | 12% |
| singular | 89 | 10% |
| no_formula | 32 | 3% |
| timeout | 4 | 0% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 665 | 62% |
| binary | 157 | 15% |
| count | 109 | 10% |
| ordinal | 81 | 8% |
| binomial | 35 | 3% |
| categorical | 29 | 3% |

| reader | n | share |
|---|---|---|
| pandas | 553 | 51% |
| pyreadr | 497 | 46% |
| rdata | 19 | 2% |
| deparse | 7 | 1% |

| published | n | share |
|---|---|---|
| yes | 706 | 66% |
| no | 370 | 34% |

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

**Corpus.** 722 flat tables; per stratum read 569, prescreened 153; per tier R 373, E 142, T 140, D 58, O 9.
The screen flagged 289 of the frame's 674 read tables for a second reading and the response reading found 35 not flat; verdicts flat 218, wide 151, hidden grouping 43.
The hand sample of 50 tables stood at 0.92.
353 of the 722 tables name a response; the response check of 25 tables stood at 0.84, its recheck of 15 `none` tables at 1.0.

| column type | n | share |
|---|---|---|
| continuous | 36812 | 85% |
| binary | 5458 | 13% |
| categorical | 915 | 2% |
| ordered | 138 | 0% |

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_all | 698 | 1 | 1 | 1.1115 | 4.6542 | 93.5414 | inf | inf |
| skewness | 36032 | -11.1669 | -0.5451 | -0.0285 | 1.4166 | 3.5352 | 3.9586 | 244.6948 |
| excess_kurtosis | 35997 | -5.6896 | -1.8923 | -1.6617 | 1.1862 | 12.0888 | 15.7992 | 59915.5349 |
| outlier_share | 36032 | 0 | 0 | 0 | 0 | 0.02 | 0.0318 | 0.0565 |
| zero_share | 36750 | 0 | 0 | 0 | 0.7032 | 0.9152 | 0.9364 | 1 |
| min_share | 36888 | 0 | 0.0098 | 0.0185 | 0.7314 | 0.9187 | 0.9399 | 1 |
| max_share | 36888 | 0 | 0.0035 | 0.0098 | 0.053 | 0.371 | 0.4452 | 1 |
| unique_share | 43255 | 0 | 0.0063 | 0.0071 | 0.0106 | 0.6863 | 0.8585 | 1 |
| rare_level_share | 6505 | 0 | 0.0022 | 0.01 | 0.1343 | 0.435 | 0.4839 | 1 |
| max_abs_rho | 41541 | 0 | 0.2635 | 0.3318 | 0.9059 | 0.9956 | 0.9999 | 1 |

The named responses, by the statistics `responses.csv` defines for their type:

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| response_K | 83 | 2 | 2 | 2 | 2 | 7 | 7 | 10 |
| response_skewness | 270 | -3.6156 | -0.9929 | -0.6077 | 0.4485 | 2.585 | 3.455 | 18.0723 |
| response_excess_kurtosis | 269 | -2.0824 | -1.2961 | -1.1184 | 0.1633 | 10.3938 | 15.314 | 506.2884 |
| response_outlier_share | 270 | 0 | 0 | 0 | 0 | 0.0082 | 0.0144 | 0.0435 |
| response_zero_share | 279 | 0 | 0 | 0 | 0 | 0.0616 | 0.2139 | 0.9418 |
| response_min_share | 287 | 0.0002 | 0.0009 | 0.0025 | 0.0278 | 0.2139 | 0.3333 | 0.9418 |
| response_max_share | 287 | 0 | 0.0008 | 0.0013 | 0.0213 | 0.1308 | 0.1745 | 0.4231 |
| response_unique_share | 353 | 0.0001 | 0.0017 | 0.0033 | 0.5321 | 1 | 1 | 1 |
| response_rare_level_share | 83 | 0.0089 | 0.0368 | 0.0556 | 0.3103 | 0.4857 | 0.4955 | 0.5 |
| response_max_abs_rho | 327 | 0.0092 | 0.1405 | 0.1859 | 0.5979 | 0.9637 | 0.9992 | 1 |
