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

**Corpus.** 694 registry rows over 621 datasets and 918 grouping
factors; per tier R 256, T 223, D 104, E 98, O 13. Excluded: 2138 objects (no grouping structure 1164, derived or duplicated table 622, unreadable format 192, simulated data 49, not the paper's data 46, response missing or undocumented 36, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 694 | 7 | 29 | 45 | 444 | 7923 | 21729 | 1000209 | 23025 |
| tier R | 256 | 12 | 21 | 30 | 198 | 3236 | 7185 | 73421 |  |
| tier E | 98 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 223 | 7 | 36 | 67 | 794 | 7382 | 13931 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 666 | 7 | 29 | 45 | 478 | 8582 | 21805 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 694 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 256 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 98 | 1 | 1 | 1 | 1 | 2 | 4 | 5 |  |
| tier T | 223 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 666 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 511 | 56% |
| crossed | 187 | 20% |
| nested | 139 | 15% |
| mixed | 81 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 2 | 4 | 5 | 32 | 376 | 1151 | 92017 | 414 |
| tier R | 341 | 2 | 4 | 4 | 20 | 184 | 312 | 10767 |  |
| tier E | 140 | 3 | 4 | 5 | 37 | 600 | 4711 | 19898 |  |
| tier T | 263 | 2 | 4 | 6 | 55 | 568 | 1323 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 16 | 3 | 3 | 3 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 865 | 2 | 4 | 5 | 38 | 398 | 1270 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 1 | 1 | 1 | 5 | 84 | 245 | 18180 | 1 |
| tier R | 341 | 1 | 1 | 1 | 5 | 32 | 64 | 567 |  |
| tier E | 140 | 1 | 1 | 1 | 6 | 216 | 500 | 1872 |  |
| tier T | 263 | 1 | 1 | 1 | 4 | 50 | 91 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 865 | 1 | 1 | 1 | 5 | 92 | 278 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 1 | 1 | 2 | 7 | 108 | 282 | 18180 | – |
| tier R | 341 | 1 | 1 | 2 | 6 | 37 | 75 | 583 |  |
| tier E | 140 | 1 | 1 | 1 | 7 | 282 | 500 | 2442 |  |
| tier T | 263 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 865 | 1 | 1 | 2 | 7 | 113 | 282 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 1 | 2 | 3 | 10 | 151 | 491 | 18180 | – |
| tier R | 341 | 1 | 2 | 3 | 8 | 49 | 110 | 600 |  |
| tier E | 140 | 1 | 2 | 3 | 11 | 522 | 823 | 4200 |  |
| tier T | 263 | 1 | 2 | 2 | 9 | 84 | 207 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 16 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 865 | 1 | 2 | 3 | 10 | 162 | 493 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 1 | 2 | 3 | 14 | 240 | 606 | 20425 | – |
| tier R | 341 | 1 | 2 | 3 | 9 | 61 | 174 | 1204 |  |
| tier E | 140 | 2 | 3 | 3 | 14 | 773 | 1309 | 4650 |  |
| tier T | 263 | 2 | 2 | 3 | 12 | 139 | 329 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 16 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 865 | 2 | 2 | 3 | 14 | 259 | 730 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 2 | 3 | 4 | 16 | 306 | 894 | 33076 | 300 |
| tier R | 341 | 2 | 2 | 3 | 10 | 94 | 247 | 7500 |  |
| tier E | 140 | 2 | 3 | 3 | 27 | 937 | 3428 | 4860 |  |
| tier T | 263 | 2 | 2 | 3 | 16 | 209 | 528 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 16 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 865 | 2 | 3 | 4 | 17 | 351 | 937 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.398). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 0.0251 | 0.9496 | 1.7252 | 56.7156 | inf | inf | inf | – |
| tier R | 341 | 0.0251 | 1.1846 | 2.3435 | inf | inf | inf | inf |  |
| tier E | 140 | 0.1733 | 0.3236 | 0.9384 | 21.2235 | inf | inf | inf |  |
| tier T | 263 | 0.0438 | 1.0843 | 1.9684 | 12.1176 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 16 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 865 | 0.0296 | 0.9496 | 1.7108 | 42.214 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 0 | 0 | 0 | 0 | 0.0909 | 0.25 | 0.9964 | – |
| tier R | 341 | 0 | 0 | 0 | 0 | 0.0473 | 0.1525 | 0.9964 |  |
| tier E | 140 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 263 | 0 | 0 | 0 | 0 | 0.1157 | 0.2741 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 16 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 865 | 0 | 0 | 0 | 0 | 0.0909 | 0.2211 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 918 | 0 | 0 | 0 | 0.1258 | 0.7252 | 1.0049 | 5.899 | – |
| tier R | 341 | 0 | 0 | 0 | 0 | 0.6503 | 0.7935 | 5.899 |  |
| tier E | 140 | 0 | 0 | 0 | 0.2329 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 263 | 0 | 0 | 0 | 0.2582 | 0.698 | 0.933 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 16 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 865 | 0 | 0 | 0 | 0.1465 | 0.7284 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 949 | 49% |
| binary | 638 | 33% |
| categorical | 286 | 15% |
| ordered | 70 | 4% |

| level | n | share |
|---|---|---|
| within | 1326 | 68% |
| group | 617 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 356 | 2 | 2 | 3 | 4 | 10 | 17 | 717 | – |
| tier R | 150 | 2 | 3 | 3 | 4 | 9 | 14 | 56 |  |
| tier E | 35 | 2 | 2 | 2 | 3 | 4 | 7 | 10 |  |
| tier T | 83 | 2 | 2 | 2 | 3 | 9 | 11 | 17 |  |
| tier D | 51 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 37 | 2 | 2 | 3 | 5 | 26 | 73 | 717 |  |
| without agridat | 330 | 2 | 2 | 2 | 4 | 10 | 15 | 717 |  |

| K | n | share |
|---|---|---|
| 3 | 140 | 39% |
| 4 | 75 | 21% |
| 2 | 33 | 9% |
| 11+ | 32 | 9% |
| 5 | 30 | 8% |
| 6 | 16 | 4% |
| 9 | 8 | 2% |
| 10 | 8 | 2% |
| 7 | 7 | 2% |
| 8 | 7 | 2% |

Implied design columns of a model under the observed categorical share
(0.183) and mean columns per categorical (7.444):
9 terms 19.63 columns, 14 terms 30.53 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 694 | 0 | 0 | 1 | 3 | 11 | 16 | 22134 | 11 |
| tier R | 256 | 0 | 0 | 0 | 3 | 12 | 17 | 55 |  |
| tier E | 98 | 0 | 0 | 0 | 2 | 7 | 11 | 13 |  |
| tier T | 223 | 0 | 0 | 1 | 3 | 9 | 12 | 25 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 79 | 22134 | 22134 |  |
| without agridat | 666 | 0 | 0 | 1 | 3 | 11 | 15 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 694 | 0 | 0 | 1 | 5 | 21 | 50 | 23759 | – |
| tier R | 256 | 0 | 0 | 1 | 4 | 20 | 35 | 14954 |  |
| tier E | 98 | 0 | 0 | 0 | 3 | 13 | 20 | 543 |  |
| tier T | 223 | 0 | 1 | 1 | 4 | 11 | 14 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 156 | 163 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 79 | 23759 | 23759 |  |
| without agridat | 666 | 0 | 0 | 1 | 5 | 20 | 51 | 23759 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 673 | 1 | 1 | 1 | 3.1463 | 12.4094 | 21.752 | inf |
| condition_all | 668 | 1 | 1 | 1 | 4.0813 | 111097380.4825 | inf | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 2204 | -6.4268 | -0.7521 | -0.4887 | 0.2066 | 2.3649 | 3.8416 | 22.8556 |
| excess_kurtosis | 2204 | -2.0022 | -1.3374 | -1.2042 | -0.2617 | 8.5473 | 20.5597 | 1191.6867 |
| outlier_share | 2204 | 0 | 0 | 0 | 0 | 0.0092 | 0.0143 | 0.04 |
| zero_share | 2219 | 0 | 0 | 0 | 0 | 0.1541 | 0.4361 | 1 |
| min_share | 2386 | 0 | 0.0004 | 0.0012 | 0.0404 | 0.5125 | 0.6661 | 1 |
| max_share | 2386 | 0 | 0.0002 | 0.0005 | 0.0159 | 0.2196 | 0.3315 | 1 |
| unique_share | 4026 | 0 | 0.0001 | 0.0004 | 0.0117 | 0.3625 | 0.8095 | 1 |
| rare_level_share | 1810 | 0 | 0.0014 | 0.0031 | 0.2152 | 0.496 | 0.5 | 1 |
| max_abs_rho | 3232 | 0 | 0.0082 | 0.0372 | 0.4183 | 0.8955 | 0.978 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 4505 | -1.6916 | -0.1111 | -0.0141 | 0.2642 | 1 | 1 | 1 |
| group_level_r2 | 2421 | -29.5505 | -1.9349 | -0.2105 | 0.0024 | 1 | 1 | 1 |
| absent_level_share | 2559 | 0 | 0 | 0 | 0.3436 | 0.8333 | 0.9583 | 0.9983 |
| size_rho | 3485 | -1 | -0.8208 | -0.4617 | 0.0288 | 0.5431 | 0.8 | 1 |
| within_sd_cv | 3288 | 0 | 0 | 0.0001 | 0.2665 | 1.4184 | 2.5194 | 129.5068 |

## Quirk statistics per factor pair

Every pair of grouping factors of a registry row: the empty cells over the crossed pairs, and
which factor of a nested pair is the superior, the one listed first, second or neither.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| empty_cell_share | 155 | 0 | 0 | 0 | 0.0727 | 0.8964 | 0.9523 | 0.9992 |

| pair relation | n | share |
|---|---|---|
| crossed | 155 | 56% |
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
| sigma2_fixed | 544 | 0 | 0 | 0.0002 | 0.6046 | 350.7875 | 3234.4203 | 9170746.8354 |
| sigma2_random | 544 | 0 | 0 | 0.0082 | 0.9986 | 356.1538 | 3035.9392 | 18651991.7893 |
| sigma2_residual | 366 | 0.0001 | 0.006 | 0.0251 | 2.316 | 1336.9035 | 6876.6969 | 1451863.8213 |
| sigma2_distribution | 544 | 0 | 0 | 0 | 0 | 3.2899 | 3.2899 | 5.6401 |
| sd_eta | 544 | 0 | 0.132 | 0.2276 | 1.3456 | 30.1039 | 86.1292 | 5558.5806 |
| r2_marginal | 544 | 0 | 0 | 0.0001 | 0.172 | 0.7009 | 0.864 | 0.9999 |
| r2_conditional | 544 | 0 | 0.0815 | 0.1413 | 0.6181 | 0.9647 | 0.9874 | 0.9999 |
| q | 728 | 1 | 1 | 1 | 1 | 2 | 2 | 8 |
| sigma2 | 728 | 0 | 0 | 0.0007 | 0.6064 | 214.4758 | 2177.5672 | 18651991.7893 |
| icc | 728 | 0 | 0 | 0.0018 | 0.1417 | 0.6079 | 0.7707 | 0.9914 |
| icc_adjusted | 728 | 0 | 0 | 0.0032 | 0.2399 | 0.8105 | 0.9383 | 0.9983 |

| status | n | share |
|---|---|---|
| ok | 399 | 64% |
| warning | 79 | 13% |
| singular | 66 | 11% |
| error | 52 | 8% |
| no_formula | 24 | 4% |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 432 | 62% |
| binary | 113 | 16% |
| count | 75 | 11% |
| ordinal | 46 | 7% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 435 | 63% |
| pyreadr | 247 | 36% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 501 | 72% |
| no | 193 | 28% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 572, unreadable format 158, no grouping structure 113, not the paper's data 46, response missing or undocumented 28).
- Papers with a registry row: 38, over 104 rows.
