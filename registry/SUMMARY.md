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

**Corpus.** 714 registry rows over 639 datasets and 939 grouping
factors; per tier R 261, T 229, E 107, D 104, O 13. Excluded: 2120 objects (no grouping structure 983, derived or duplicated table 782, unreadable format 192, simulated data 49, not the paper's data 46, response missing or undocumented 39, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 7 | 30 | 45 | 445 | 8164 | 21805 | 1000209 | 23025 |
| tier R | 261 | 12 | 24 | 30 | 198 | 3236 | 7185 | 73421 |  |
| tier E | 107 | 20 | 32 | 40 | 528 | 16409 | 28534 | 1000209 |  |
| tier T | 229 | 7 | 36 | 67 | 794 | 7584 | 14364 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 683 | 7 | 30 | 45 | 480 | 8604 | 21814 | 1000209 |  |
| flat | 729 | 3 | 9 | 14 | 75 | 1534 | 4842 | 81422 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 261 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 107 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 229 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 683 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 530 | 56% |
| crossed | 189 | 20% |
| nested | 139 | 15% |
| mixed | 81 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 2 | 4 | 5 | 32 | 369 | 1128 | 92017 | 414 |
| tier R | 346 | 2 | 4 | 4 | 21 | 185 | 312 | 10767 |  |
| tier E | 150 | 3 | 4 | 5 | 34 | 595 | 4434 | 19898 |  |
| tier T | 269 | 2 | 4 | 6 | 50 | 568 | 1323 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 16 | 3 | 3 | 3 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 883 | 2 | 4 | 5 | 38 | 392 | 1236 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 1 | 1 | 1 | 5 | 84 | 255 | 18180 | 1 |
| tier R | 346 | 1 | 1 | 1 | 5 | 32 | 71 | 852 |  |
| tier E | 150 | 1 | 1 | 1 | 7 | 216 | 500 | 1872 |  |
| tier T | 269 | 1 | 1 | 1 | 4 | 50 | 91 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 883 | 1 | 1 | 1 | 5 | 92 | 282 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 1 | 1 | 2 | 7 | 108 | 282 | 18180 | – |
| tier R | 346 | 1 | 1 | 2 | 6 | 38 | 79 | 961 |  |
| tier E | 150 | 1 | 1 | 2 | 7 | 282 | 500 | 2442 |  |
| tier T | 269 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 883 | 1 | 1 | 2 | 7 | 113 | 300 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 1 | 2 | 3 | 10 | 152 | 491 | 18180 | – |
| tier R | 346 | 1 | 2 | 3 | 8 | 52 | 135 | 1395 |  |
| tier E | 150 | 1 | 3 | 3 | 11 | 500 | 660 | 4200 |  |
| tier T | 269 | 1 | 2 | 2 | 9 | 84 | 219 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 16 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 883 | 1 | 2 | 3 | 10 | 164 | 500 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 1 | 2 | 3 | 14 | 247 | 730 | 20425 | – |
| tier R | 346 | 1 | 2 | 3 | 9 | 63 | 217 | 1849 |  |
| tier E | 150 | 2 | 3 | 4 | 14 | 762 | 1292 | 4650 |  |
| tier T | 269 | 2 | 2 | 3 | 13 | 154 | 336 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 16 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 883 | 2 | 2 | 3 | 14 | 263 | 762 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 2 | 3 | 4 | 16 | 316 | 927 | 33076 | 300 |
| tier R | 346 | 2 | 2 | 3 | 10 | 116 | 290 | 7500 |  |
| tier E | 150 | 2 | 3 | 4 | 27 | 873 | 2314 | 4860 |  |
| tier T | 269 | 2 | 2 | 3 | 16 | 215 | 549 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 16 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 883 | 2 | 3 | 4 | 17 | 375 | 969 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.395). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 0.0251 | 0.9496 | 1.7108 | 56 | inf | inf | inf | – |
| tier R | 346 | 0.0251 | 1.1846 | 2.2449 | inf | inf | inf | inf |  |
| tier E | 150 | 0.1733 | 0.3236 | 0.9384 | 23.9674 | inf | inf | inf |  |
| tier T | 269 | 0.0438 | 1.0843 | 1.8788 | 12.1176 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 16 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 883 | 0.0296 | 0.9496 | 1.7027 | 40.1807 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 0 | 0 | 0 | 0 | 0.0932 | 0.2519 | 0.9964 | – |
| tier R | 346 | 0 | 0 | 0 | 0 | 0.0473 | 0.2045 | 0.9964 |  |
| tier E | 150 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier T | 269 | 0 | 0 | 0 | 0 | 0.125 | 0.3155 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 16 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 883 | 0 | 0 | 0 | 0 | 0.0909 | 0.2295 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 939 | 0 | 0 | 0 | 0.1265 | 0.7284 | 1.0049 | 5.899 | – |
| tier R | 346 | 0 | 0 | 0 | 0 | 0.6637 | 0.8761 | 5.899 |  |
| tier E | 150 | 0 | 0 | 0 | 0.1924 | 1.0108 | 1.5292 | 1.9835 |  |
| tier T | 269 | 0 | 0 | 0 | 0.2582 | 0.7105 | 0.9348 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 16 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 883 | 0 | 0 | 0 | 0.1489 | 0.7418 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 989 | 49% |
| binary | 657 | 33% |
| categorical | 292 | 15% |
| ordered | 71 | 4% |

| level | n | share |
|---|---|---|
| within | 1387 | 69% |
| group | 622 | 31% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 363 | 2 | 2 | 3 | 4 | 10 | 17 | 717 | – |
| tier R | 153 | 2 | 3 | 3 | 4 | 9 | 14 | 56 |  |
| tier E | 36 | 2 | 2 | 2 | 3 | 4 | 10 | 13 |  |
| tier T | 86 | 2 | 2 | 2 | 3 | 9 | 11 | 24 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 37 | 2 | 2 | 3 | 5 | 26 | 73 | 717 |  |
| without agridat | 335 | 2 | 2 | 2 | 4 | 10 | 17 | 717 |  |
| flat | 969 | 0 | 1 | 2 | 11 | 93 | 204 | 59548 |  |

| K | n | share |
|---|---|---|
| 3 | 140 | 39% |
| 4 | 78 | 21% |
| 11+ | 35 | 10% |
| 2 | 34 | 9% |
| 5 | 30 | 8% |
| 6 | 16 | 4% |
| 9 | 8 | 2% |
| 10 | 8 | 2% |
| 7 | 7 | 2% |
| 8 | 7 | 2% |

Implied design columns of a model under the observed categorical share
(0.181) and mean columns per categorical (7.496):
9 terms 19.56 columns, 14 terms 30.43 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 0 | 0 | 1 | 3 | 11 | 16 | 22134 | 11 |
| tier R | 261 | 0 | 0 | 0 | 3 | 12 | 17 | 55 |  |
| tier E | 107 | 0 | 0 | 0 | 2 | 8 | 11 | 16 |  |
| tier T | 229 | 0 | 0 | 1 | 3 | 9 | 12 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 79 | 22134 | 22134 |  |
| without agridat | 683 | 0 | 0 | 1 | 3 | 11 | 15 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 0 | 0 | 1 | 5 | 21 | 51 | 23759 | – |
| tier R | 261 | 0 | 0 | 1 | 4 | 20 | 35 | 14954 |  |
| tier E | 107 | 0 | 0 | 0 | 3 | 13 | 20 | 543 |  |
| tier T | 229 | 0 | 1 | 1 | 4 | 12 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 156 | 163 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 79 | 23759 | 23759 |  |
| without agridat | 683 | 0 | 0 | 1 | 5 | 21 | 55 | 23759 |  |
| flat | 729 | 0 | 1 | 2 | 4 | 22 | 88 | 29573 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 692 | 1 | 1 | 1 | 3.1463 | 12.4718 | 21.752 | inf |
| condition_all | 687 | 1 | 1 | 1 | 4.0813 | inf | inf | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 2330 | -6.4268 | -0.7922 | -0.4915 | 0.2031 | 2.3399 | 3.8416 | 22.8556 |
| excess_kurtosis | 2330 | -2.0022 | -1.3574 | -1.2144 | -0.2654 | 8.4865 | 20.5597 | 1191.6867 |
| outlier_share | 2330 | 0 | 0 | 0 | 0 | 0.0092 | 0.0143 | 0.04 |
| zero_share | 2351 | 0 | 0 | 0 | 0 | 0.1646 | 0.4444 | 1 |
| min_share | 2520 | 0 | 0.0004 | 0.0012 | 0.0402 | 0.5157 | 0.6841 | 1 |
| max_share | 2520 | 0 | 0.0002 | 0.0005 | 0.0159 | 0.2249 | 0.3333 | 1 |
| unique_share | 4235 | 0 | 0.0001 | 0.0003 | 0.0117 | 0.3929 | 0.8131 | 1 |
| rare_level_share | 1887 | 0 | 0.0015 | 0.0032 | 0.2245 | 0.4957 | 0.5 | 1 |
| max_abs_rho | 3427 | 0 | 0.0082 | 0.0378 | 0.432 | 0.9189 | 0.9867 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 4710 | -1.6916 | -0.1084 | -0.0137 | 0.2632 | 1 | 1 | 1 |
| group_level_r2 | 2520 | -29.5505 | -1.6025 | -0.196 | 0.0001 | 1 | 1 | 1 |
| absent_level_share | 2639 | 0 | 0 | 0 | 0.3487 | 0.8333 | 0.9559 | 0.9983 |
| size_rho | 3675 | -1 | -0.8208 | -0.4508 | 0.0313 | 0.5398 | 0.8 | 1 |
| within_sd_cv | 3473 | 0 | 0 | 0.0003 | 0.2744 | 1.4924 | 2.6362 | 129.5068 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 156 | 0 | 0 | 0 | 0.0741 | 0.8964 | 0.9523 | 0.9992 |

| pair relation | n | share |
|---|---|---|
| crossed | 156 | 56% |
| nested | 123 | 44% |

| superior | n | share |
|---|---|---|
| factor_a | 103 | 84% |
| factor_b | 20 | 16% |

## Fits of the documented models

Every registry row with a continuous, binary or count response, its documented model fitted as
written: the variance components and R² once per row, the ICCs once per grouping factor of the
fit, over the fits that ended with estimates; the status of every row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| sigma2_fixed | 554 | 0 | 0 | 0.0002 | 0.6046 | 350.7875 | 3357.9388 | 9170746.8354 |
| sigma2_random | 554 | 0 | 0 | 0.0076 | 0.9728 | 356.1538 | 3035.9392 | 18651991.7893 |
| sigma2_residual | 374 | 0 | 0.0057 | 0.0239 | 2.2937 | 1229.9175 | 6876.6969 | 1451863.8213 |
| sigma2_distribution | 554 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.676 |
| sd_eta | 554 | 0 | 0.1281 | 0.2202 | 1.3381 | 30.1039 | 86.1292 | 5558.5806 |
| r2_marginal | 554 | 0 | 0 | 0.0003 | 0.1733 | 0.7094 | 0.8863 | 0.9999 |
| r2_conditional | 554 | 0 | 0.0815 | 0.1417 | 0.6232 | 0.9647 | 0.9885 | 0.9999 |
| q | 739 | 1 | 1 | 1 | 1 | 2 | 2 | 8 |
| sigma2 | 739 | 0 | 0 | 0.0006 | 0.5706 | 214.4758 | 2177.5672 | 18651991.7893 |
| icc | 739 | 0 | 0 | 0.0018 | 0.1408 | 0.6036 | 0.7707 | 0.9914 |
| icc_adjusted | 739 | 0 | 0 | 0.0032 | 0.2367 | 0.8101 | 0.9383 | 0.9983 |

| status | n | share |
|---|---|---|
| ok | 407 | 64% |
| warning | 80 | 13% |
| singular | 67 | 11% |
| error | 53 | 8% |
| no_formula | 29 | 5% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 444 | 62% |
| binary | 114 | 16% |
| count | 78 | 11% |
| ordinal | 50 | 7% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 452 | 63% |
| pyreadr | 250 | 35% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 506 | 71% |
| no | 208 | 29% |

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

**Corpus.** 729 flat tables; per stratum read 559, prescreened 170; per tier R 370, E 153, T 136, D 62, O 8.
The screen flagged 294 of the frame's 675 read tables for a second reading; verdicts flat 203, wide 129, hidden grouping 33.
The hand sample of 50 tables stood at 0.92.
346 of the 729 tables name a response; the response check of 25 tables stood at 0.84, its recheck of 15 `none` tables at 1.0.

| column type | n | share |
|---|---|---|
| continuous | 37144 | 85% |
| binary | 5367 | 12% |
| categorical | 835 | 2% |
| ordered | 134 | 0% |

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_all | 705 | 1 | 1 | 1.0747 | 5.4742 | inf | inf | inf |
| skewness | 36365 | -11.1669 | -0.541 | -0.0271 | 1.4008 | 3.5352 | 3.9474 | 244.6948 |
| excess_kurtosis | 36330 | -5.6896 | -1.8923 | -1.6564 | 1.1639 | 12.0767 | 15.574 | 59915.5349 |
| outlier_share | 36365 | 0 | 0 | 0 | 0 | 0.02 | 0.0318 | 0.0565 |
| zero_share | 37082 | 0 | 0 | 0 | 0.6961 | 0.9152 | 0.9364 | 1 |
| min_share | 37216 | 0 | 0.0068 | 0.0185 | 0.7279 | 0.9187 | 0.9399 | 1 |
| max_share | 37216 | 0 | 0.0033 | 0.0098 | 0.053 | 0.3675 | 0.4417 | 1 |
| unique_share | 43412 | 0 | 0.0071 | 0.0071 | 0.0106 | 0.7037 | 0.8824 | 1 |
| rare_level_share | 6330 | 0 | 0.0023 | 0.0108 | 0.1343 | 0.4375 | 0.4841 | 1 |
| max_abs_rho | 41775 | 0 | 0.2637 | 0.3342 | 0.9064 | 0.9951 | 0.9999 | 1 |
