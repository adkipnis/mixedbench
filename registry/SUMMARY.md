# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); frame, method
and reading rules in [`README.md`](README.md). Evidence for `docs/design/envelope.md`, not the
envelope itself.

How to read the tables:

- Every number is filled by `merge.py` from `dimensions.csv` and `columns.csv` on each merge;
  edit `SUMMARY.template.md`, never this file.
- Quantiles are observed values: at or below the level in the lower half, at or above it in
  the upper half.
- Per-factor axes (groups, group sizes, imbalance) count a dataset once per grouping factor;
  dataset axes (observations, grouping factors, design columns) once per registry row; `K`
  once per categorical covariate of a documented model.
- The last column of an axis table is the practice survey's upper quantile, the maximum over
  the v1 families in [`practice_quantiles.yaml`](../survey/practice_quantiles.yaml) (the minimum
  for the smallest group size), read at merge time; `–` where the practice survey has no such
  axis.

**Corpus.** 712 registry rows over 642 datasets and 940 grouping
factors; per tier R 252, T 244, D 104, E 99, O 13. Excluded: 2142 objects (no grouping structure 1177, derived or duplicated table 622, unreadable format 187, not the paper's data 46, simulated data 43, response missing or undocumented 36, time series without replication 30, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 712 | 7 | 29 | 45 | 463 | 7584 | 20796 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 244 | 7 | 36 | 70 | 854 | 7185 | 10036 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 684 | 7 | 29 | 45 | 500 | 8113 | 21729 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 712 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 244 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 684 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 523 | 56% |
| crossed | 199 | 21% |
| nested | 149 | 16% |
| mixed | 69 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 2 | 4 | 5 | 32 | 353 | 1122 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier T | 291 | 2 | 4 | 6 | 59 | 545 | 1323 | 4856 |  |
| tier D | 163 | 2 | 3 | 5 | 50 | 275 | 534 | 13319 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 887 | 2 | 4 | 5 | 38 | 386 | 1151 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 1 | 1 | 1 | 5 | 84 | 240 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier T | 291 | 1 | 1 | 1 | 4 | 50 | 92 | 1353 |  |
| tier D | 163 | 1 | 1 | 1 | 17 | 376 | 750 | 8162 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 887 | 1 | 1 | 1 | 5 | 89 | 245 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 1 | 1 | 2 | 7 | 107 | 255 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier T | 291 | 1 | 1 | 1 | 6 | 58 | 135 | 1353 |  |
| tier D | 163 | 1 | 1 | 1 | 24 | 376 | 927 | 8162 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 887 | 1 | 1 | 2 | 7 | 108 | 282 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 1 | 2 | 3 | 11 | 145 | 458 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier T | 291 | 1 | 2 | 3 | 10 | 84 | 207 | 2037 |  |
| tier D | 163 | 1 | 3 | 3 | 33 | 493 | 1276 | 8511 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 887 | 1 | 2 | 3 | 11 | 160 | 465 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 1 | 3 | 3 | 15 | 240 | 554 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier T | 291 | 2 | 2 | 3 | 15 | 139 | 336 | 4014 |  |
| tier D | 163 | 2 | 3 | 4 | 45 | 730 | 1755 | 8639 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 887 | 2 | 3 | 3 | 15 | 257 | 600 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 2 | 3 | 4 | 18 | 290 | 792 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier T | 291 | 2 | 2 | 3 | 17 | 215 | 528 | 7745 |  |
| tier D | 163 | 3 | 4 | 5 | 45 | 894 | 1813 | 8639 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 887 | 2 | 3 | 4 | 20 | 308 | 876 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.386). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 0.0251 | 0.9496 | 1.7027 | 44.8585 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 291 | 0.0438 | 1.0843 | 1.8788 | 11.4003 | inf | inf | inf |  |
| tier D | 163 | 0.2722 | 1.0534 | 1.7612 | 32.002 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 887 | 0.0296 | 0.9496 | 1.7019 | 32.9619 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 0 | 0 | 0 | 0 | 0.0896 | 0.2164 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 291 | 0 | 0 | 0 | 0 | 0.1066 | 0.25 | 0.8448 |  |
| tier D | 163 | 0 | 0 | 0 | 0 | 0.1 | 0.3003 | 0.7481 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 887 | 0 | 0 | 0 | 0 | 0.0896 | 0.1957 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 940 | 0 | 0 | 0 | 0.1402 | 0.7307 | 0.9946 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 291 | 0 | 0 | 0 | 0.2827 | 0.7204 | 0.9093 | 3.5667 |  |
| tier D | 163 | 0 | 0 | 0 | 0.1489 | 0.7455 | 0.9681 | 1.7829 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 887 | 0 | 0 | 0 | 0.1621 | 0.7404 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 900 | 44% |
| binary | 675 | 33% |
| categorical | 385 | 19% |
| ordered | 78 | 4% |

| level | n | share |
|---|---|---|
| within | 1402 | 69% |
| group | 636 | 31% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 463 | 1 | 2 | 3 | 4 | 9 | 11 | 117 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 149 | 1 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier D | 55 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 435 | 1 | 2 | 3 | 4 | 9 | 11 | 117 |  |

| K | n | share |
|---|---|---|
| 3 | 163 | 35% |
| 4 | 100 | 22% |
| 5 | 44 | 10% |
| 2 | 35 | 8% |
| 6 | 27 | 6% |
| 11+ | 27 | 6% |
| 7 | 24 | 5% |
| 10 | 16 | 3% |
| 9 | 14 | 3% |
| 8 | 10 | 2% |
| 1 | 3 | 1% |

Implied design columns of a model under the observed categorical share
(0.227) and mean columns per categorical (4.888):
9 terms 16.95 columns, 14 terms 26.37 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 712 | 0 | 0 | 1 | 4 | 13 | 17 | 277 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 11 | 13 | 25 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 18 | 36 | 277 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 684 | 0 | 0 | 1 | 4 | 12 | 16 | 277 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 712 | 0 | 0 | 1 | 5 | 21 | 48 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 13 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 15 | 156 | 294 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 684 | 0 | 0 | 1 | 5 | 21 | 48 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 451 | 63% |
| binary | 113 | 16% |
| count | 75 | 11% |
| ordinal | 45 | 6% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 429 | 60% |
| pyreadr | 246 | 35% |
| rscript | 37 | 5% |

| published | n | share |
|---|---|---|
| yes | 541 | 76% |
| no | 171 | 24% |

## Tier D

The practice survey's deposits, resolved and pulled by `resolve.py`; the loss by cause is the
tier's finding.

- Links: 98 of 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 572, unreadable format 158, no grouping structure 113, not the paper's data 46, response missing or undocumented 28).
- Papers with a registry row: 38, over 104 rows.
