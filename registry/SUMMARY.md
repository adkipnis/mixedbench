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

**Corpus.** 716 registry rows over 641 datasets and 941 grouping
factors; per tier R 261, T 230, E 107, D 104, O 14. Excluded: 2118 objects (no grouping structure 981, derived or duplicated table 782, unreadable format 192, simulated data 49, not the paper's data 46, response missing or undocumented 39, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 716 | 7 | 30 | 45 | 445 | 8164 | 21805 | 1000209 | 23025 |
| tier R | 261 | 12 | 24 | 30 | 198 | 3236 | 7185 | 73421 |  |
| tier E | 107 | 20 | 32 | 40 | 528 | 16409 | 28534 | 1000209 |  |
| tier T | 230 | 7 | 36 | 67 | 800 | 7584 | 14364 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 14 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 685 | 7 | 30 | 45 | 480 | 8604 | 21814 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 716 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 261 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 107 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 230 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 14 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 685 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 532 | 57% |
| crossed | 189 | 20% |
| nested | 139 | 15% |
| mixed | 81 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 2 | 4 | 5 | 32 | 369 | 1128 | 92017 | 414 |
| tier R | 346 | 2 | 4 | 4 | 21 | 185 | 312 | 10767 |  |
| tier E | 150 | 3 | 4 | 5 | 34 | 595 | 4434 | 19898 |  |
| tier T | 270 | 2 | 4 | 6 | 51 | 569 | 1333 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 17 | 3 | 3 | 3 | 19 | 71518 | 92017 | 92017 |  |
| without agridat | 885 | 2 | 4 | 5 | 38 | 398 | 1270 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 1 | 1 | 5 | 84 | 245 | 18180 | 1 |
| tier R | 346 | 1 | 1 | 1 | 5 | 32 | 71 | 852 |  |
| tier E | 150 | 1 | 1 | 1 | 7 | 216 | 500 | 1872 |  |
| tier T | 270 | 1 | 1 | 1 | 4 | 50 | 91 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 17 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 885 | 1 | 1 | 1 | 5 | 92 | 282 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 1 | 2 | 7 | 107 | 282 | 18180 | – |
| tier R | 346 | 1 | 1 | 2 | 6 | 38 | 79 | 961 |  |
| tier E | 150 | 1 | 1 | 2 | 7 | 282 | 500 | 2442 |  |
| tier T | 270 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 17 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 885 | 1 | 1 | 2 | 7 | 113 | 300 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 2 | 3 | 10 | 151 | 491 | 18180 | – |
| tier R | 346 | 1 | 2 | 3 | 8 | 52 | 135 | 1395 |  |
| tier E | 150 | 1 | 3 | 3 | 11 | 500 | 660 | 4200 |  |
| tier T | 270 | 1 | 2 | 2 | 9 | 84 | 219 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 17 | 1 | 1 | 1 | 21 | 8150 | 18180 | 18180 |  |
| without agridat | 885 | 1 | 2 | 3 | 10 | 164 | 500 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 2 | 3 | 14 | 240 | 606 | 20425 | – |
| tier R | 346 | 1 | 2 | 3 | 9 | 63 | 217 | 1849 |  |
| tier E | 150 | 2 | 3 | 4 | 14 | 762 | 1292 | 4650 |  |
| tier T | 270 | 2 | 2 | 3 | 13 | 154 | 336 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 17 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 885 | 2 | 2 | 3 | 14 | 263 | 762 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 2 | 3 | 4 | 16 | 308 | 894 | 33076 | 300 |
| tier R | 346 | 2 | 2 | 3 | 10 | 116 | 290 | 7500 |  |
| tier E | 150 | 2 | 3 | 4 | 27 | 873 | 2314 | 4860 |  |
| tier T | 270 | 2 | 2 | 3 | 16 | 215 | 549 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 17 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 885 | 2 | 3 | 4 | 17 | 375 | 969 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.394). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0.0251 | 0.9496 | 1.7108 | 55.7971 | inf | inf | inf | – |
| tier R | 346 | 0.0251 | 1.1846 | 2.2449 | inf | inf | inf | inf |  |
| tier E | 150 | 0.1733 | 0.3236 | 0.9384 | 23.9674 | inf | inf | inf |  |
| tier T | 270 | 0.0438 | 1.0843 | 1.8788 | 12.1176 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 17 | 1.4564 | 1.4564 | 1.6802 | 80.9739 | inf | inf | inf |  |
| without agridat | 885 | 0.0296 | 0.9496 | 1.7027 | 38.0449 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0 | 0 | 0 | 0 | 0.0932 | 0.2519 | 0.9964 | – |
| tier R | 346 | 0 | 0 | 0 | 0 | 0.0473 | 0.2045 | 0.9964 |  |
| tier E | 150 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier T | 270 | 0 | 0 | 0 | 0 | 0.1293 | 0.3182 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 17 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 885 | 0 | 0 | 0 | 0 | 0.0932 | 0.25 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0 | 0 | 0 | 0.1286 | 0.7284 | 0.9946 | 5.899 | – |
| tier R | 346 | 0 | 0 | 0 | 0 | 0.6637 | 0.8761 | 5.899 |  |
| tier E | 150 | 0 | 0 | 0 | 0.1924 | 1.0108 | 1.5292 | 1.9835 |  |
| tier T | 270 | 0 | 0 | 0 | 0.273 | 0.7105 | 0.9348 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 17 | 0 | 0 | 0 | 0.1098 | 0.7604 | 0.7665 | 0.7665 |  |
| without agridat | 885 | 0 | 0 | 0 | 0.149 | 0.7439 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 993 | 49% |
| binary | 659 | 33% |
| categorical | 292 | 14% |
| ordered | 71 | 4% |

| level | n | share |
|---|---|---|
| within | 1393 | 69% |
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
(0.18) and mean columns per categorical (7.496):
9 terms 19.53 columns, 14 terms 30.38 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 716 | 0 | 0 | 1 | 3 | 11 | 16 | 22134 | 11 |
| tier R | 261 | 0 | 0 | 0 | 3 | 12 | 17 | 55 |  |
| tier E | 107 | 0 | 0 | 0 | 2 | 8 | 11 | 16 |  |
| tier T | 230 | 0 | 0 | 1 | 3 | 9 | 12 | 31 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 270 |  |
| tier O | 14 | 2 | 2 | 2 | 11 | 79 | 22134 | 22134 |  |
| without agridat | 685 | 0 | 0 | 1 | 3 | 11 | 15 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 716 | 0 | 0 | 1 | 5 | 21 | 51 | 23759 | – |
| tier R | 261 | 0 | 0 | 1 | 4 | 20 | 35 | 14954 |  |
| tier E | 107 | 0 | 0 | 0 | 3 | 13 | 20 | 543 |  |
| tier T | 230 | 0 | 1 | 1 | 4 | 12 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 10 | 156 | 163 | 4580 |  |
| tier O | 14 | 2 | 2 | 2 | 19 | 79 | 23759 | 23759 |  |
| without agridat | 685 | 0 | 0 | 1 | 5 | 21 | 55 | 23759 |  |

The condition index of the documented design and of the design over every column.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| condition_doc | 693 | 1 | 1 | 1 | 3.1463 | 12.4718 | 21.752 | inf |
| condition_all | 688 | 1 | 1 | 1 | 4.0813 | inf | inf | inf |

## Quirk statistics per column

Every column of `columns.csv`, documented or not, by the statistics its type defines.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| skewness | 2335 | -6.4268 | -0.7861 | -0.4915 | 0.2066 | 2.3399 | 3.8416 | 22.8556 |
| excess_kurtosis | 2335 | -2.0022 | -1.3574 | -1.214 | -0.2667 | 8.4238 | 20.5597 | 1191.6867 |
| outlier_share | 2335 | 0 | 0 | 0 | 0 | 0.0092 | 0.0144 | 0.04 |
| zero_share | 2356 | 0 | 0 | 0 | 0 | 0.1646 | 0.4444 | 1 |
| min_share | 2525 | 0 | 0.0004 | 0.0011 | 0.04 | 0.5157 | 0.6841 | 1 |
| max_share | 2525 | 0 | 0.0002 | 0.0005 | 0.0159 | 0.2236 | 0.3333 | 1 |
| unique_share | 4242 | 0 | 0.0001 | 0.0003 | 0.0117 | 0.3929 | 0.8131 | 1 |
| rare_level_share | 1889 | 0 | 0.0015 | 0.0032 | 0.2245 | 0.4957 | 0.5 | 1 |
| max_abs_rho | 3434 | 0 | 0.0082 | 0.038 | 0.432 | 0.9189 | 0.9867 | 1 |

## Quirk statistics per column and grouping factor

Every column against every grouping factor of its registry row.

| statistic | n | min | p5 | p10 | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|---|
| between_group_share | 4717 | -1.6916 | -0.1111 | -0.0138 | 0.264 | 1 | 1 | 1 |
| group_level_r2 | 2520 | -29.5505 | -1.6025 | -0.196 | 0.0001 | 1 | 1 | 1 |
| absent_level_share | 2641 | 0 | 0 | 0 | 0.3487 | 0.8333 | 0.9545 | 0.9983 |
| size_rho | 3682 | -1 | -0.8208 | -0.4588 | 0.0302 | 0.5398 | 0.8 | 1 |
| within_sd_cv | 3480 | 0 | 0 | 0.0003 | 0.2753 | 1.5039 | 2.6522 | 129.5068 |

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
| continuous | 446 | 62% |
| binary | 114 | 16% |
| count | 78 | 11% |
| ordinal | 50 | 7% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 454 | 63% |
| pyreadr | 250 | 35% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 506 | 71% |
| no | 210 | 29% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 573, unreadable format 158, no grouping structure 111, not the paper's data 46, response missing or undocumented 29).
- Papers with a registry row: 38, over 104 rows.
