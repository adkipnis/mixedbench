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

**Corpus.** 693 registry rows over 621 datasets and 917 grouping
factors; per tier R 255, T 223, D 104, E 98, O 13. Excluded: 2138 objects (no grouping structure 1164, derived or duplicated table 622, unreadable format 192, simulated data 49, not the paper's data 46, response missing or undocumented 36, time series without replication 28, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 693 | 7 | 29 | 45 | 438 | 7923 | 21729 | 1000209 | 23025 |
| tier R | 255 | 12 | 21 | 30 | 196 | 3236 | 7185 | 73421 |  |
| tier E | 98 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 223 | 7 | 36 | 67 | 794 | 7382 | 13931 | 283728 |  |
| tier D | 104 | 45 | 76 | 219 | 1211 | 21729 | 61248 | 210658 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 665 | 7 | 29 | 45 | 475 | 8582 | 21805 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 693 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 255 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 98 | 1 | 1 | 1 | 1 | 2 | 4 | 5 |  |
| tier T | 223 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 104 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |  |
| without agridat | 665 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 510 | 56% |
| crossed | 187 | 20% |
| nested | 139 | 15% |
| mixed | 81 | 9% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 2 | 4 | 5 | 32 | 376 | 1151 | 92017 | 414 |
| tier R | 340 | 2 | 4 | 4 | 20 | 184 | 316 | 10767 |  |
| tier E | 140 | 3 | 4 | 5 | 37 | 600 | 4711 | 19898 |  |
| tier T | 263 | 2 | 4 | 6 | 55 | 568 | 1323 | 4856 |  |
| tier D | 158 | 2 | 3 | 5 | 54 | 281 | 554 | 13319 |  |
| tier O | 16 | 3 | 3 | 3 | 32 | 71518 | 92017 | 92017 |  |
| without agridat | 864 | 2 | 4 | 5 | 38 | 398 | 1270 | 92017 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 1 | 1 | 1 | 5 | 84 | 245 | 18180 | 1 |
| tier R | 340 | 1 | 1 | 1 | 5 | 32 | 71 | 567 |  |
| tier E | 140 | 1 | 1 | 1 | 6 | 216 | 500 | 1872 |  |
| tier T | 263 | 1 | 1 | 1 | 4 | 50 | 91 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 21 | 376 | 927 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 864 | 1 | 1 | 1 | 5 | 92 | 278 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 1 | 1 | 2 | 7 | 108 | 282 | 18180 | – |
| tier R | 340 | 1 | 1 | 2 | 6 | 38 | 79 | 583 |  |
| tier E | 140 | 1 | 1 | 1 | 7 | 282 | 500 | 2442 |  |
| tier T | 263 | 1 | 1 | 1 | 6 | 58 | 135 | 1098 |  |
| tier D | 158 | 1 | 1 | 1 | 24 | 384 | 1020 | 8162 |  |
| tier O | 16 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 864 | 1 | 1 | 2 | 7 | 113 | 282 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 1 | 2 | 3 | 10 | 151 | 491 | 18180 | – |
| tier R | 340 | 1 | 2 | 3 | 8 | 52 | 135 | 600 |  |
| tier E | 140 | 1 | 2 | 3 | 11 | 522 | 823 | 4200 |  |
| tier T | 263 | 1 | 2 | 2 | 9 | 84 | 207 | 2037 |  |
| tier D | 158 | 1 | 2 | 3 | 30 | 528 | 1393 | 8511 |  |
| tier O | 16 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 864 | 1 | 2 | 3 | 10 | 162 | 493 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 1 | 2 | 3 | 14 | 240 | 606 | 20425 | – |
| tier R | 340 | 1 | 2 | 3 | 10 | 63 | 217 | 1204 |  |
| tier E | 140 | 2 | 3 | 3 | 14 | 773 | 1309 | 4650 |  |
| tier T | 263 | 2 | 2 | 3 | 12 | 139 | 329 | 4014 |  |
| tier D | 158 | 2 | 3 | 4 | 45 | 806 | 1898 | 8639 |  |
| tier O | 16 | 2 | 2 | 2 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 864 | 2 | 2 | 3 | 14 | 259 | 730 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 2 | 3 | 4 | 16 | 306 | 894 | 33076 | 300 |
| tier R | 340 | 2 | 2 | 3 | 10 | 101 | 290 | 7500 |  |
| tier E | 140 | 2 | 3 | 3 | 27 | 937 | 3428 | 4860 |  |
| tier T | 263 | 2 | 2 | 3 | 16 | 209 | 528 | 7745 |  |
| tier D | 158 | 3 | 4 | 5 | 45 | 927 | 1898 | 8639 |  |
| tier O | 16 | 8 | 8 | 10 | 40 | 18180 | 33076 | 33076 |  |
| without agridat | 864 | 2 | 3 | 4 | 17 | 351 | 937 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.397). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 0.0251 | 0.9496 | 1.7252 | 56.3814 | inf | inf | inf | – |
| tier R | 340 | 0.0251 | 1.1846 | 2.2449 | inf | inf | inf | inf |  |
| tier E | 140 | 0.1733 | 0.3236 | 0.9384 | 21.2235 | inf | inf | inf |  |
| tier T | 263 | 0.0438 | 1.0843 | 1.9684 | 12.1176 | inf | inf | inf |  |
| tier D | 158 | 0.2722 | 0.8708 | 1.7108 | 43.4569 | inf | inf | inf |  |
| tier O | 16 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 864 | 0.0296 | 0.9496 | 1.7108 | 42.214 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 0 | 0 | 0 | 0 | 0.0909 | 0.25 | 0.9964 | – |
| tier R | 340 | 0 | 0 | 0 | 0 | 0.0473 | 0.1525 | 0.9964 |  |
| tier E | 140 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 263 | 0 | 0 | 0 | 0 | 0.1157 | 0.2741 | 0.8448 |  |
| tier D | 158 | 0 | 0 | 0 | 0 | 0.1 | 0.2917 | 0.7481 |  |
| tier O | 16 | 0 | 0 | 0 | 0 | 0.688 | 0.7655 | 0.7655 |  |
| without agridat | 864 | 0 | 0 | 0 | 0 | 0.0909 | 0.2211 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 917 | 0 | 0 | 0 | 0.1258 | 0.7252 | 1.0049 | 5.899 | – |
| tier R | 340 | 0 | 0 | 0 | 0 | 0.6637 | 0.8761 | 5.899 |  |
| tier E | 140 | 0 | 0 | 0 | 0.2329 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 263 | 0 | 0 | 0 | 0.2582 | 0.698 | 0.933 | 3.5667 |  |
| tier D | 158 | 0 | 0 | 0 | 0.1428 | 0.7504 | 0.9946 | 1.7829 |  |
| tier O | 16 | 0 | 0 | 0 | 0.1098 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 864 | 0 | 0 | 0 | 0.1474 | 0.7284 | 1.0049 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 870 | 45% |
| binary | 637 | 33% |
| categorical | 362 | 19% |
| ordered | 70 | 4% |

| level | n | share |
|---|---|---|
| within | 1325 | 68% |
| group | 614 | 32% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 432 | 1 | 2 | 3 | 4 | 10 | 14 | 717 | – |
| tier R | 166 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 50 | 1 | 2 | 2 | 3 | 9 | 10 | 10 |  |
| tier T | 121 | 2 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier D | 54 | 3 | 3 | 3 | 4 | 47 | 76 | 117 |  |
| tier O | 41 | 2 | 2 | 3 | 5 | 17 | 37 | 717 |  |
| without agridat | 404 | 1 | 2 | 3 | 4 | 10 | 13 | 717 |  |

| K | n | share |
|---|---|---|
| 3 | 155 | 36% |
| 4 | 91 | 21% |
| 5 | 42 | 10% |
| 2 | 33 | 8% |
| 11+ | 32 | 7% |
| 6 | 22 | 5% |
| 7 | 20 | 5% |
| 10 | 14 | 3% |
| 9 | 13 | 3% |
| 8 | 8 | 2% |
| 1 | 2 | 0% |

Implied design columns of a model under the observed categorical share
(0.223) and mean columns per categorical (6.91):
9 terms 20.85 columns, 14 terms 32.43 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and binary count one, a categorical
its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 693 | 0 | 0 | 1 | 4 | 13 | 16 | 22134 | 11 |
| tier R | 255 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 98 | 0 | 0 | 0 | 3 | 11 | 12 | 16 |  |
| tier T | 223 | 0 | 0 | 1 | 4 | 11 | 13 | 25 |  |
| tier D | 104 | 0 | 1 | 1 | 4 | 15 | 36 | 277 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 85 | 22134 | 22134 |  |
| without agridat | 665 | 0 | 0 | 1 | 4 | 12 | 16 | 22134 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 693 | 0 | 0 | 1 | 5 | 22 | 55 | 23770 | – |
| tier R | 255 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 98 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 223 | 0 | 1 | 1 | 5 | 13 | 16 | 11030 |  |
| tier D | 104 | 1 | 2 | 3 | 15 | 156 | 294 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 85 | 23770 | 23770 |  |
| without agridat | 665 | 0 | 0 | 1 | 5 | 22 | 55 | 23770 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 432 | 62% |
| binary | 113 | 16% |
| count | 75 | 11% |
| ordinal | 45 | 6% |
| binomial | 16 | 2% |
| categorical | 12 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 435 | 63% |
| pyreadr | 246 | 35% |
| deparse | 7 | 1% |
| rdata | 5 | 1% |

| published | n | share |
|---|---|---|
| yes | 500 | 72% |
| no | 193 | 28% |

## Tier D

The practice survey's deposits, resolved and pulled by the archived `resolve.py` (tag
`survey-archive`); the loss by cause is the tier's finding.

- Links: 98 over 60 papers; by status ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1.
- Listed files: 1632; by role other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, hidden path 9.
- Objects excluded: 917 (derived or duplicated table 572, unreadable format 158, no grouping structure 113, not the paper's data 46, response missing or undocumented 28).
- Papers with a registry row: 38, over 104 rows.
