# Dimension survey - summary

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

**Corpus.** 692 registry rows over 623 datasets and 909 grouping
factors; per tier R 241, T 220, E 115, D 104, O 12. Excluded: 2136 objects (no grouping structure 978, derived or duplicated table 801, unreadable format 192, simulated data 51, not the paper's data 46, response missing or undocumented 39, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 692 | 7 | 32 | 50 | 504 | 8654 | 24611 | 1000209 | 23025 |
| tier R | 241 | 12 | 24 | 35 | 236 | 3326 | 7185 | 73421 |  |
| tier E | 115 | 20 | 32 | 46 | 600 | 19200 | 32877 | 1000209 |  |
| tier T | 220 | 7 | 45 | 80 | 826 | 8164 | 15362 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 12 | 52 | 52 | 120 | 2298 | 181800 | 318438 | 318438 |  |
| without agridat | 663 | 7 | 32 | 50 | 572 | 9558 | 24613 | 1000209 |  |
| flat | 722 | 3 | 9 | 14 | 75 | 1445 | 3888 | 81422 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 692 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 241 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 115 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 220 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 12 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 663 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 514 | 57% |
| crossed | 179 | 20% |
| nested | 141 | 16% |
| mixed | 75 | 8% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 2 | 4 | 6 | 38 | 391 | 1236 | 92017 | 414 |
| tier R | 319 | 2 | 4 | 5 | 24 | 197 | 336 | 10767 |  |
| tier E | 158 | 3 | 4 | 5 | 34 | 595 | 4434 | 19898 |  |
| tier T | 259 | 2 | 5 | 7 | 59 | 569 | 1333 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 15 | 3 | 3 | 9 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 858 | 2 | 4 | 6 | 40 | 411 | 1323 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 1 | 1 | 1 | 5 | 92 | 278 | 18180 | 1 |
| tier R | 319 | 1 | 1 | 1 | 5 | 30 | 72 | 852 |  |
| tier E | 158 | 1 | 1 | 1 | 7 | 228 | 500 | 1872 |  |
| tier T | 259 | 1 | 1 | 1 | 3 | 48 | 95 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 15 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 858 | 1 | 1 | 1 | 5 | 101 | 282 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 1 | 1 | 1 | 7 | 113 | 300 | 18180 | – |
| tier R | 319 | 1 | 1 | 2 | 6 | 37 | 81 | 961 |  |
| tier E | 158 | 1 | 1 | 2 | 7 | 282 | 500 | 2442 |  |
| tier T | 259 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 15 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 858 | 1 | 1 | 1 | 7 | 120 | 326 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 1 | 2 | 3 | 10 | 162 | 500 | 18180 | – |
| tier R | 319 | 1 | 2 | 2 | 8 | 56 | 135 | 1395 |  |
| tier E | 158 | 1 | 3 | 3 | 12 | 504 | 660 | 4200 |  |
| tier T | 259 | 1 | 2 | 2 | 9 | 84 | 228 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 15 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 858 | 1 | 2 | 3 | 10 | 175 | 528 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 1 | 2 | 3 | 14 | 263 | 762 | 20425 | – |
| tier R | 319 | 1 | 2 | 3 | 8 | 64 | 217 | 1849 |  |
| tier E | 158 | 2 | 3 | 4 | 18 | 773 | 1309 | 4650 |  |
| tier T | 259 | 2 | 2 | 3 | 13 | 139 | 336 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 15 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 858 | 2 | 2 | 3 | 14 | 278 | 773 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 2 | 3 | 4 | 17 | 375 | 969 | 33076 | 300 |
| tier R | 319 | 2 | 2 | 3 | 9 | 118 | 290 | 7500 |  |
| tier E | 158 | 2 | 3 | 4 | 28 | 937 | 2314 | 4860 |  |
| tier T | 259 | 2 | 2 | 3 | 16 | 215 | 549 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 15 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 858 | 2 | 3 | 4 | 18 | 415 | 1056 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.381). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 0.0251 | 0.9384 | 1.7108 | 43.5581 | inf | inf | inf | – |
| tier R | 319 | 0.0251 | 1.0905 | 2.2449 | inf | inf | inf | inf |  |
| tier E | 158 | 0.1733 | 0.3236 | 0.9384 | 15.3433 | inf | inf | inf |  |
| tier T | 259 | 0.0438 | 1.0972 | 1.8839 | 12.0721 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 15 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 858 | 0.0296 | 0.9384 | 1.7108 | 33.9197 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 0 | 0 | 0 | 0 | 0.1 | 0.2588 | 0.9964 | – |
| tier R | 319 | 0 | 0 | 0 | 0 | 0.0672 | 0.2519 | 0.9964 |  |
| tier E | 158 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier T | 259 | 0 | 0 | 0 | 0 | 0.1293 | 0.3182 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 15 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 858 | 0 | 0 | 0 | 0 | 0.1 | 0.25 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 909 | 0 | 0 | 0 | 0.1428 | 0.7439 | 1.0049 | 5.899 | – |
| tier R | 319 | 0 | 0 | 0 | 0 | 0.6637 | 0.9104 | 5.899 |  |
| tier E | 158 | 0 | 0 | 0 | 0.2463 | 1.0108 | 1.5292 | 1.9835 |  |
| tier T | 259 | 0 | 0 | 0 | 0.273 | 0.7041 | 0.9348 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 15 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 858 | 0 | 0 | 0 | 0.1658 | 0.746 | 1.0108 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 944 | 49% |
| binary | 639 | 33% |
| categorical | 282 | 15% |
| ordered | 69 | 4% |

| level | n | share |
|---|---|---|
| within | 1309 | 68% |
| group | 625 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 351 | 2 | 2 | 3 | 4 | 10 | 17 | 717 | – |
| tier R | 144 | 2 | 3 | 3 | 4 | 8 | 10 | 56 |  |
| tier E | 36 | 2 | 2 | 2 | 3 | 4 | 10 | 13 |  |
| tier T | 85 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 35 | 2 | 2 | 3 | 5 | 26 | 73 | 717 |  |
| without agridat | 321 | 2 | 2 | 2 | 4 | 10 | 17 | 717 |  |
| flat | 1056 | 0 | 1 | 3 | 11 | 107 | 307 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 135 | 38% |
| 4 | 76 | 22% |
| 2 | 34 | 10% |
| 11+ | 33 | 9% |
| 5 | 25 | 7% |
| 6 | 16 | 5% |
| 9 | 9 | 3% |
| 8 | 9 | 3% |
| 7 | 7 | 2% |
| 10 | 7 | 2% |

Implied design columns of a model under the observed categorical share
(0.181) and mean columns per categorical (7.595):
9 terms 19.77 columns, 14 terms 30.76 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 692 | 0 | 0 | 1 | 3 | 11 | 16 | 22134 | 11 |
| tier R | 241 | 0 | 0 | 1 | 3 | 11 | 17 | 55 |  |
| tier E | 115 | 0 | 0 | 0 | 2 | 7 | 11 | 16 |  |
| tier T | 220 | 0 | 0 | 1 | 3 | 9 | 12 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 12 | 2 | 2 | 2 | 11 | 79 | 22134 | 22134 |  |
| without agridat | 663 | 0 | 0 | 1 | 3 | 10 | 15 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 692 | 0 | 0 | 1 | 5 | 21 | 53 | 23759 | – |
| tier R | 241 | 0 | 0 | 1 | 5 | 20 | 32 | 440 |  |
| tier E | 115 | 0 | 0 | 0 | 3 | 12 | 20 | 543 |  |
| tier T | 220 | 0 | 1 | 1 | 4 | 12 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 156 | 163 | 4580 |  |
| tier O | 12 | 2 | 2 | 2 | 19 | 79 | 23759 | 23759 |  |
| without agridat | 663 | 0 | 0 | 1 | 5 | 20 | 55 | 23759 |  |
| flat | 722 | 0 | 1 | 2 | 5 | 22 | 78 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 665 | 1 | 1 | 1 | 3.1463 | 11.9758 | 19.8483 | inf |
| condition_all | 661 | 1 | 1 | 1 | 4.0675 | 47.8697 | inf | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 2201 | -4.9042 | -0.7861 | -0.4935 | 0.1583 | 2.1906 | 3.5499 | 22.8556 |
| excess_kurtosis | 2201 | -1.9902 | -1.36 | -1.2173 | -0.3109 | 6.4063 | 18.2569 | 1191.6867 |
| outlier_share | 2201 | 0 | 0 | 0 | 0 | 0.0077 | 0.0135 | 0.0341 |
| zero_share | 2220 | 0 | 0 | 0 | 0 | 0.1249 | 0.4061 | 1 |
| min_share | 2387 | 0 | 0.0004 | 0.0011 | 0.0383 | 0.5159 | 0.6842 | 1 |
| max_share | 2387 | 0 | 0.0002 | 0.0005 | 0.0172 | 0.2249 | 0.3333 | 1 |
| unique_share | 3957 | 0 | 0.0001 | 0.0003 | 0.0117 | 0.2581 | 0.7353 | 1 |
| rare_level_share | 1740 | 0 | 0.0019 | 0.0042 | 0.2358 | 0.4968 | 0.5 | 1 |
| max_abs_rho | 3220 | 0 | 0.007 | 0.036 | 0.4167 | 0.9106 | 0.9857 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 4495 | -1.6916 | -0.1136 | -0.0137 | 0.2871 | 1 | 1 | 1 |
| group_level_r2 | 2501 | -29.5505 | -1.6025 | -0.1471 | 0.0015 | 1 | 1 | 1 |
| absent_level_share | 2490 | 0 | 0 | 0 | 0.3969 | 0.8453 | 0.9586 | 0.9983 |
| size_rho | 3499 | -1 | -0.8208 | -0.4228 | 0.0273 | 0.5 | 0.7826 | 1 |
| within_sd_cv | 3253 | 0 | 0 | 0.0002 | 0.2863 | 1.5582 | 2.8022 | 129.5068 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 149 | 0 | 0 | 0 | 0.0894 | 0.9 | 0.9523 | 0.9992 |

| pair relation | n | share |
|---|---|---|
| crossed | 149 | 55% |
| nested | 120 | 45% |

| superior | n | share |
|---|---|---|
| factor_a | 100 | 83% |
| factor_b | 20 | 17% |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 528 | 0 | 0 | 0.0009 | 0.6216 | 350.7875 | 1987.784 | 9170746.8354 |
| sigma2_random | 528 | 0 | 0 | 0.0082 | 0.9495 | 356.1538 | 3035.9392 | 18651991.7893 |
| sigma2_residual | 350 | 0 | 0.006 | 0.0256 | 2.2937 | 1229.9175 | 6876.6969 | 1451863.8213 |
| sigma2_distribution | 528 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.676 |
| sd_eta | 528 | 0 | 0.1413 | 0.2276 | 1.3221 | 30.1039 | 84.4016 | 5558.5806 |
| r2_marginal | 528 | 0 | 0 | 0.0008 | 0.1734 | 0.7094 | 0.893 | 0.9999 |
| r2_conditional | 528 | 0 | 0.1043 | 0.1425 | 0.6197 | 0.9653 | 0.9885 | 0.9999 |
| q | 706 | 1 | 1 | 1 | 1 | 2 | 2 | 8 |
| sigma2 | 706 | 0 | 0 | 0.001 | 0.5736 | 205.3507 | 2177.5672 | 18651991.7893 |
| icc | 706 | 0 | 0 | 0.0019 | 0.1426 | 0.6026 | 0.7605 | 0.9907 |
| icc_adjusted | 706 | 0 | 0 | 0.0032 | 0.2533 | 0.8077 | 0.9368 | 0.9983 |

| status | n | share |
|---|---|---|
| ok | 386 | 63% |
| warning | 79 | 13% |
| singular | 63 | 10% |
| error | 53 | 9% |
| no_formula | 32 | 5% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 422 | 61% |
| binary | 114 | 16% |
| count | 77 | 11% |
| ordinal | 48 | 7% |
| categorical | 17 | 2% |
| binomial | 14 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 448 | 65% |
| pyreadr | 232 | 34% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 509 | 74% |
| no | 183 | 26% |

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
| continuous | 36809 | 85% |
| binary | 5458 | 13% |
| categorical | 918 | 2% |
| ordered | 138 | 0% |

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_all | 698 | 1 | 1 | 1.1115 | 4.8395 | inf | inf | inf |
| skewness | 36029 | -11.1669 | -0.5451 | -0.0285 | 1.4166 | 3.5352 | 3.9586 | 244.6948 |
| excess_kurtosis | 35994 | -5.6896 | -1.8923 | -1.6617 | 1.1862 | 12.0888 | 15.7992 | 59915.5349 |
| outlier_share | 36029 | 0 | 0 | 0 | 0 | 0.02 | 0.0318 | 0.0565 |
| zero_share | 36747 | 0 | 0 | 0 | 0.7032 | 0.9152 | 0.9364 | 1 |
| min_share | 36885 | 0 | 0.0098 | 0.0185 | 0.7314 | 0.9187 | 0.9399 | 1 |
| max_share | 36885 | 0 | 0.0035 | 0.0098 | 0.053 | 0.371 | 0.4452 | 1 |
| unique_share | 43255 | 0 | 0.0063 | 0.0071 | 0.0106 | 0.6863 | 0.8585 | 1 |
| rare_level_share | 6508 | 0 | 0.0022 | 0.01 | 0.1343 | 0.435 | 0.4839 | 1 |
| max_abs_rho | 41538 | 0 | 0.2635 | 0.3319 | 0.9059 | 0.9956 | 0.9999 | 1 |
