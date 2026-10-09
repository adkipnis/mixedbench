# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); frame, method
and reading rules in [`README.md`](../survey/README.md). Evidence for the envelope in metabeta's
design docs, not the envelope itself.

How to read the tables:

- Every number is filled by `merge.py` from `dimensions.csv` and `columns.csv` on each merge;
  edit `SUMMARY.template.md`, never this file.
- Quantiles are observed values, never interpolated: below the median the nearest value at
  or below the level, from the median on the nearest value at or above it.
- Per-factor axes (groups, group sizes, imbalance) count a dataset once per grouping factor;
  dataset axes (observations, grouping factors, design columns) once per registry row; `K`
  once per categorical covariate of a documented model.
- The last column of an axis table, `practice`, is the practice survey's upper decile, the
  maximum over the v1 families in [`practice_quantiles.yaml`](../survey/practice_quantiles.yaml)
  (the minimum for the smallest group size), read at merge time; `–` where the practice survey
  has no such axis.

**Corpus.** 714 registry rows over 641 datasets and 941 grouping
factors; per tier R 252, T 244, D 104, E 101, O 13. Excluded: 2133 objects (no grouping structure 1164, derived or duplicated table 622, unreadable format 192, not the paper's data 46, simulated data 44, response missing or undocumented 36, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 7 | 29 | 45 | 459 | 7584 | 20796 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 101 | 20 | 32 | 40 | 432 | 16409 | 28534 | 1000209 |  |
| tier T | 244 | 7 | 36 | 70 | 853 | 7185 | 10036 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 686 | 7 | 29 | 45 | 494 | 8164 | 21729 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 101 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 244 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 686 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 527 | 56% |
| crossed | 201 | 21% |
| nested | 132 | 14% |
| mixed | 81 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 2 | 4 | 5 | 32 | 361 | 1128 | 92017 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 144 | 3 | 4 | 5 | 32 | 595 | 4434 | 19898 |  |
| tier T | 288 | 2 | 4 | 6 | 60 | 546 | 1323 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 16 | 3 | 3 | 3 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 888 | 2 | 4 | 5 | 39 | 392 | 1270 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 1 | 1 | 5 | 81 | 240 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 144 | 1 | 1 | 1 | 6 | 216 | 500 | 1872 |  |
| tier T | 288 | 1 | 1 | 1 | 4 | 50 | 92 | 1353 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 888 | 1 | 1 | 1 | 5 | 91 | 278 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 1 | 2 | 7 | 107 | 278 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 144 | 1 | 1 | 2 | 7 | 216 | 500 | 2442 |  |
| tier T | 288 | 1 | 1 | 1 | 6 | 58 | 135 | 1353 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 888 | 1 | 1 | 2 | 7 | 108 | 282 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 2 | 3 | 11 | 145 | 491 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 144 | 1 | 3 | 3 | 12 | 500 | 660 | 4200 |  |
| tier T | 288 | 1 | 2 | 2 | 10 | 84 | 199 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 16 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 888 | 1 | 2 | 3 | 11 | 160 | 493 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 1 | 3 | 3 | 14 | 240 | 600 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 144 | 2 | 3 | 4 | 14 | 762 | 1292 | 4650 |  |
| tier T | 288 | 2 | 2 | 3 | 15 | 139 | 329 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 16 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 888 | 2 | 3 | 3 | 15 | 257 | 730 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 2 | 3 | 4 | 18 | 290 | 876 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 144 | 2 | 3 | 4 | 28 | 873 | 2314 | 4860 |  |
| tier T | 288 | 2 | 2 | 3 | 17 | 215 | 528 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 16 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 888 | 2 | 3 | 4 | 19 | 340 | 937 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.388). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0.0251 | 0.9669 | 1.7027 | 49.9643 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 144 | 0.1733 | 0.3236 | 0.9384 | 15.3433 | inf | inf | inf |  |
| tier T | 288 | 0.0438 | 1.0843 | 1.6398 | 11.3563 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 16 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 888 | 0.0296 | 0.9496 | 1.6866 | 36.0263 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0 | 0 | 0 | 0 | 0.0897 | 0.25 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 144 | 0 | 0 | 0 | 0 | 0.0909 | 0.1525 | 0.5329 |  |
| tier T | 288 | 0 | 0 | 0 | 0 | 0.1154 | 0.2741 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 16 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 888 | 0 | 0 | 0 | 0 | 0.0902 | 0.2211 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 941 | 0 | 0 | 0 | 0.1329 | 0.7307 | 0.9899 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 144 | 0 | 0 | 0 | 0.2474 | 1.0108 | 1.5292 | 1.9835 |  |
| tier T | 288 | 0 | 0 | 0 | 0.2934 | 0.7262 | 0.9096 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 16 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 888 | 0 | 0 | 0 | 0.1572 | 0.7478 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 898 | 44% |
| binary | 666 | 33% |
| categorical | 383 | 19% |
| ordered | 77 | 4% |

| level | n | share |
|---|---|---|
| within | 1395 | 69% |
| group | 629 | 31% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 460 | 1 | 2 | 3 | 4 | 10 | 14 | 717 | – |
| tier R | 166 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 148 | 1 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier D | 54 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 41 | 2 | 2 | 3 | 5 | 17 | 37 | 717 |  |
| without agridat | 432 | 1 | 2 | 3 | 4 | 9 | 12 | 717 |  |

| K | n | share |
|---|---|---|
| 3 | 161 | 35% |
| 4 | 98 | 21% |
| 5 | 43 | 9% |
| 2 | 34 | 7% |
| 11+ | 32 | 7% |
| 6 | 27 | 6% |
| 7 | 23 | 5% |
| 10 | 16 | 3% |
| 9 | 14 | 3% |
| 8 | 9 | 2% |
| 1 | 3 | 1% |

Implied design columns of a model under the observed categorical share
(0.227) and mean columns per categorical (6.737):
9 terms 20.73 columns, 14 terms 32.25 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 0 | 0 | 1 | 4 | 13 | 17 | 22134 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 101 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 11 | 13 | 25 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 277 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 85 | 22134 | 22134 |  |
| without agridat | 686 | 0 | 0 | 1 | 4 | 12 | 16 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 714 | 0 | 0 | 1 | 5 | 21 | 51 | 23770 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 101 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 13 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 15 | 156 | 294 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 85 | 23770 | 23770 |  |
| without agridat | 686 | 0 | 0 | 1 | 5 | 21 | 51 | 23770 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 451 | 63% |
| binary | 115 | 16% |
| count | 75 | 11% |
| ordinal | 45 | 6% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 459 | 64% |
| pyreadr | 243 | 34% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 537 | 75% |
| no | 177 | 25% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 572, unreadable format 158, no grouping structure 113, not the paper's data 46, response missing or undocumented 28).
- Papers with a registry row: 38, over 104 rows.
