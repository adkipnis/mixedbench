# Dimension survey — summary

Public grouped datasets measured by script from [`registry.csv`](registry.csv); frame and
method in [`README.md`](README.md). Every number below is filled by `merge.py` from
`dimensions.csv` and `columns.csv` on each merge; edit `SUMMARY.template.md`, never this file.
Quantiles are observed values, at or below the level in the lower half and at or above it in
the upper half. Per-factor axes count a dataset once per grouping factor, dataset axes once per
registry row. The last column of each axis table is the practice survey's upper quantile, the
maximum over the v1 families' values in [`../practice/quantiles.yaml`](../practice/quantiles.yaml)
(the minimum for the smallest group size), read at merge time; `–` where the practice survey
has no such axis. These are evidence for `docs/design/envelope.md`, not the envelope itself.

**Corpus.** 704 registry rows over 648 datasets and 920 grouping
factors; per tier R 252, T 244, E 99, D 96, O 13. Excluded: 2113 objects (no grouping structure 1174, derived or duplicated table 621, unreadable format 185, not the paper's data 46, simulated data 43, time series without replication 30, response missing or undocumented 13, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 704 | 7 | 29 | 45 | 504 | 8979 | 24611 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 244 | 7 | 36 | 70 | 854 | 7185 | 10036 | 283728 |  |
| tier D | 96 | 45 | 160 | 258 | 1592 | 34350 | 76486 | 333530 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 676 | 7 | 29 | 45 | 577 | 9600 | 24875 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 704 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 244 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 96 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 676 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 521 | 57% |
| crossed | 207 | 22% |
| nested | 127 | 14% |
| mixed | 65 | 7% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 2 | 4 | 5 | 36 | 346 | 1122 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier T | 291 | 2 | 4 | 6 | 59 | 545 | 1323 | 4856 |  |
| tier D | 143 | 2 | 3 | 6 | 63 | 240 | 534 | 13319 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 867 | 2 | 4 | 5 | 40 | 386 | 1151 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 1 | 1 | 1 | 5 | 85 | 240 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier T | 291 | 1 | 1 | 1 | 4 | 50 | 92 | 1353 |  |
| tier D | 143 | 1 | 1 | 1 | 35 | 458 | 1020 | 1948 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 867 | 1 | 1 | 1 | 5 | 92 | 255 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 1 | 1 | 2 | 8 | 113 | 282 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier T | 291 | 1 | 1 | 1 | 6 | 58 | 135 | 1353 |  |
| tier D | 143 | 1 | 1 | 2 | 48 | 458 | 1200 | 4376 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 867 | 1 | 1 | 2 | 7 | 120 | 288 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 1 | 2 | 3 | 11 | 160 | 392 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier T | 291 | 1 | 2 | 3 | 10 | 84 | 207 | 2037 |  |
| tier D | 143 | 1 | 3 | 4 | 73 | 528 | 1393 | 7222 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 867 | 1 | 2 | 3 | 11 | 168 | 458 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 1 | 3 | 3 | 14 | 240 | 539 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier T | 291 | 2 | 2 | 3 | 15 | 139 | 336 | 4014 |  |
| tier D | 143 | 3 | 3 | 5 | 77 | 554 | 1662 | 11430 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 867 | 2 | 3 | 3 | 15 | 257 | 554 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 2 | 3 | 4 | 18 | 290 | 773 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier T | 291 | 2 | 2 | 3 | 17 | 215 | 528 | 7745 |  |
| tier D | 143 | 3 | 4 | 5 | 80 | 894 | 1797 | 15213 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 867 | 2 | 3 | 4 | 20 | 316 | 792 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.398). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 0.0251 | 0.9713 | 1.8788 | 56.7156 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 291 | 0.0438 | 1.0843 | 1.8788 | 11.4003 | inf | inf | inf |  |
| tier D | 143 | 0.2722 | 1.2319 | 2.2081 | 56.3814 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 867 | 0.0296 | 0.9713 | 1.8141 | 40.1807 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 0 | 0 | 0 | 0 | 0.08 | 0.172 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 291 | 0 | 0 | 0 | 0 | 0.1066 | 0.25 | 0.8448 |  |
| tier D | 143 | 0 | 0 | 0 | 0 | 0.0704 | 0.1293 | 0.7204 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 867 | 0 | 0 | 0 | 0 | 0.08 | 0.1633 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 920 | 0 | 0 | 0 | 0.1265 | 0.7204 | 0.9681 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 291 | 0 | 0 | 0 | 0.2827 | 0.7204 | 0.9093 | 3.5667 |  |
| tier D | 143 | 0 | 0 | 0 | 0.124 | 0.6676 | 0.8954 | 1.7829 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 867 | 0 | 0 | 0 | 0.1474 | 0.7204 | 0.9681 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 874 | 44% |
| binary | 638 | 32% |
| categorical | 394 | 20% |
| ordered | 78 | 4% |

| level | n | share |
|---|---|---|
| within | 1381 | 70% |
| group | 603 | 30% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 472 | 1 | 2 | 3 | 4 | 9 | 12 | 117 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 149 | 1 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier D | 64 | 3 | 3 | 3 | 5 | 39 | 69 | 117 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 444 | 1 | 2 | 3 | 4 | 9 | 11 | 117 |  |

| K | n | share |
|---|---|---|
| 3 | 163 | 35% |
| 4 | 96 | 20% |
| 5 | 51 | 11% |
| 2 | 35 | 7% |
| 6 | 28 | 6% |
| 7 | 24 | 5% |
| 10 | 16 | 3% |
| 9 | 14 | 3% |
| 8 | 13 | 3% |
| 14 | 6 | 1% |
| 11 | 4 | 1% |
| 1 | 3 | 1% |
| 12 | 3 | 1% |
| 17 | 2 | 0% |
| 76 | 2 | 0% |
| 56 | 1 | 0% |
| 15 | 1 | 0% |
| 16 | 1 | 0% |
| 20 | 1 | 0% |
| 49 | 1 | 0% |
| 13 | 1 | 0% |
| 39 | 1 | 0% |
| 55 | 1 | 0% |
| 117 | 1 | 0% |
| 69 | 1 | 0% |
| 30 | 1 | 0% |
| 47 | 1 | 0% |

Implied design columns of a model under the observed categorical share
(0.238) and mean columns per categorical (4.939):
9 terms 17.43 columns, 14 terms 27.12 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 704 | 0 | 0 | 1 | 4 | 13 | 16 | 277 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 11 | 13 | 25 |  |
| tier D | 96 | 0 | 1 | 1 | 4 | 15 | 38 | 277 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 676 | 0 | 0 | 1 | 4 | 12 | 16 | 277 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 704 | 0 | 0 | 1 | 5 | 20 | 44 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 13 | 16 | 11030 |  |
| tier D | 96 | 1 | 1 | 2 | 11 | 164 | 294 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 676 | 0 | 0 | 1 | 5 | 20 | 45 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 449 | 64% |
| binary | 104 | 15% |
| count | 71 | 10% |
| ordinal | 45 | 6% |
| categorical | 20 | 3% |
| binomial | 15 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 417 | 59% |
| pyreadr | 249 | 35% |
| rscript | 38 | 5% |

| published | n | share |
|---|---|---|
| yes | 525 | 75% |
| no | 179 | 25% |

## Tier D

The practice survey's deposits, resolved and pulled by `resolve.py` (see the README); the loss
by cause is a finding of the tier: 98 links of 60 papers; deposits by status: ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1. Listed files by role: other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, http 401 18, hidden path 9. Objects excluded: 888 (derived or duplicated table 571, unreadable format 156, no grouping structure 110, not the paper's data 46, response missing or undocumented 5); papers with a registry row: 28 over 96 rows.
