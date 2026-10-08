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

**Corpus.** 793 registry rows over 737 datasets and 1009 grouping
factors; per tier R 252, T 244, D 185, E 99, O 13. Excluded: 2024 objects (no grouping structure 1174, derived or duplicated table 532, unreadable format 185, not the paper's data 46, simulated data 43, time series without replication 30, response missing or undocumented 13, fewer than two groups 1).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 793 | 7 | 30 | 48 | 361 | 7584 | 21729 | 1000209 | 23025 |
| tier R | 252 | 12 | 21 | 30 | 196 | 3078 | 7185 | 73421 |  |
| tier E | 99 | 20 | 30 | 40 | 528 | 19200 | 28534 | 1000209 |  |
| tier T | 244 | 7 | 36 | 70 | 854 | 7185 | 10036 | 283728 |  |
| tier D | 185 | 42 | 74 | 104 | 280 | 14400 | 34350 | 333530 |  |
| tier O | 13 | 52 | 52 | 63 | 478 | 181800 | 318438 | 318438 |  |
| without agridat | 765 | 7 | 30 | 48 | 376 | 8113 | 21805 | 1000209 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 793 | 1 | 1 | 1 | 1 | 2 | 2 | 5 | 3 |
| tier R | 252 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier E | 99 | 1 | 1 | 1 | 1 | 2 | 3 | 5 |  |
| tier T | 244 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |
| tier D | 185 | 1 | 1 | 1 | 1 | 2 | 2 | 4 |  |
| tier O | 13 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |  |
| without agridat | 765 | 1 | 1 | 1 | 1 | 2 | 2 | 5 |  |

| relation | n | share |
|---|---|---|
| single | 610 | 60% |
| crossed | 207 | 21% |
| nested | 127 | 13% |
| mixed | 65 | 6% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 2 | 4 | 4 | 26 | 294 | 888 | 71518 | 414 |
| tier R | 335 | 2 | 4 | 4 | 18 | 184 | 316 | 10767 |  |
| tier E | 138 | 3 | 4 | 5 | 38 | 600 | 4711 | 19898 |  |
| tier T | 291 | 2 | 4 | 6 | 59 | 545 | 1323 | 4856 |  |
| tier D | 232 | 2 | 3 | 4 | 12 | 199 | 281 | 13319 |  |
| tier O | 13 | 3 | 3 | 3 | 19 | 1373 | 71518 | 71518 |  |
| without agridat | 956 | 2 | 4 | 4 | 27 | 316 | 1000 | 71518 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 1 | 1 | 1 | 5 | 76 | 199 | 18180 | 1 |
| tier R | 335 | 1 | 1 | 1 | 6 | 32 | 62 | 567 |  |
| tier E | 138 | 1 | 1 | 1 | 6 | 216 | 392 | 1872 |  |
| tier T | 291 | 1 | 1 | 1 | 4 | 50 | 92 | 1353 |  |
| tier D | 232 | 1 | 1 | 1 | 4 | 199 | 554 | 1948 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 1240 | 18180 | 18180 |  |
| without agridat | 956 | 1 | 1 | 1 | 4 | 81 | 216 | 18180 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 1 | 1 | 1 | 6 | 107 | 240 | 18180 | – |
| tier R | 335 | 1 | 1 | 2 | 7 | 38 | 72 | 583 |  |
| tier E | 138 | 1 | 1 | 1 | 7 | 216 | 456 | 2442 |  |
| tier T | 291 | 1 | 1 | 1 | 6 | 58 | 135 | 1353 |  |
| tier D | 232 | 1 | 1 | 1 | 5 | 266 | 554 | 4376 |  |
| tier O | 13 | 1 | 1 | 1 | 21 | 3630 | 18180 | 18180 |  |
| without agridat | 956 | 1 | 1 | 1 | 6 | 108 | 278 | 18180 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 1 | 2 | 3 | 13 | 145 | 340 | 18180 | – |
| tier R | 335 | 1 | 2 | 3 | 8 | 50 | 105 | 600 |  |
| tier E | 138 | 1 | 3 | 3 | 11 | 491 | 600 | 4200 |  |
| tier T | 291 | 1 | 2 | 3 | 10 | 84 | 207 | 2037 |  |
| tier D | 232 | 1 | 3 | 5 | 40 | 266 | 894 | 7222 |  |
| tier O | 13 | 1 | 1 | 1 | 25 | 8150 | 18180 | 18180 |  |
| without agridat | 956 | 1 | 2 | 3 | 13 | 151 | 376 | 18180 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 1 | 3 | 4 | 20 | 206 | 510 | 20425 | – |
| tier R | 335 | 1 | 2 | 3 | 10 | 61 | 171 | 1204 |  |
| tier E | 138 | 2 | 3 | 4 | 14 | 762 | 921 | 4650 |  |
| tier T | 291 | 2 | 2 | 3 | 15 | 139 | 336 | 4014 |  |
| tier D | 232 | 3 | 4 | 7 | 60 | 288 | 927 | 11430 |  |
| tier O | 13 | 2 | 2 | 3 | 25 | 18180 | 20425 | 20425 |  |
| without agridat | 956 | 2 | 3 | 4 | 20 | 220 | 521 | 20425 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 2 | 3 | 4 | 24 | 270 | 765 | 33076 | 300 |
| tier R | 335 | 2 | 2 | 3 | 11 | 92 | 217 | 7500 |  |
| tier E | 138 | 2 | 3 | 4 | 27 | 773 | 1517 | 4860 |  |
| tier T | 291 | 2 | 2 | 3 | 17 | 215 | 528 | 7745 |  |
| tier D | 232 | 3 | 4 | 9 | 61 | 326 | 1276 | 15213 |  |
| tier O | 13 | 10 | 10 | 12 | 25 | 18180 | 33076 | 33076 |  |
| without agridat | 956 | 2 | 3 | 4 | 25 | 288 | 769 | 33076 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.363). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 0.0251 | 0.9669 | 1.4575 | 30.2479 | inf | inf | inf | – |
| tier R | 335 | 0.0251 | 1.1846 | 2.6431 | inf | inf | inf | inf |  |
| tier E | 138 | 0.1733 | 0.3236 | 0.9384 | 18.3212 | inf | inf | inf |  |
| tier T | 291 | 0.0438 | 1.0843 | 1.8788 | 11.4003 | inf | inf | inf |  |
| tier D | 232 | 0.2722 | 1.0519 | 1.2319 | 5.3091 | inf | inf | inf |  |
| tier O | 13 | 1.6802 | 1.6802 | 1.7019 | 80.9739 | inf | inf | inf |  |
| without agridat | 956 | 0.0296 | 0.9496 | 1.4179 | 23.696 | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 0 | 0 | 0 | 0 | 0.1346 | 0.25 | 0.9964 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.0428 | 0.1525 | 0.9964 |  |
| tier E | 138 | 0 | 0 | 0 | 0 | 0.1036 | 0.1633 | 0.5329 |  |
| tier T | 291 | 0 | 0 | 0 | 0 | 0.1066 | 0.25 | 0.8448 |  |
| tier D | 232 | 0 | 0 | 0 | 0 | 0.2 | 0.25 | 0.7204 |  |
| tier O | 13 | 0 | 0 | 0 | 0 | 0.6038 | 0.7655 | 0.7655 |  |
| without agridat | 956 | 0 | 0 | 0 | 0 | 0.1346 | 0.25 | 0.8448 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 1009 | 0 | 0 | 0 | 0.1801 | 0.7461 | 0.942 | 5.899 | – |
| tier R | 335 | 0 | 0 | 0 | 0 | 0.615 | 0.8761 | 5.899 |  |
| tier E | 138 | 0 | 0 | 0 | 0.2438 | 1.0108 | 1.7167 | 1.9835 |  |
| tier T | 291 | 0 | 0 | 0 | 0.2827 | 0.7204 | 0.9093 | 3.5667 |  |
| tier D | 232 | 0 | 0 | 0 | 0.4084 | 0.7936 | 0.8954 | 1.7829 |  |
| tier O | 13 | 0 | 0 | 0 | 0.1088 | 0.7524 | 0.7665 | 0.7665 |  |
| without agridat | 956 | 0 | 0 | 0 | 0.1875 | 0.7488 | 0.9524 | 4.9111 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 874 | 42% |
| binary | 638 | 31% |
| categorical | 483 | 23% |
| ordered | 78 | 4% |

| level | n | share |
|---|---|---|
| within | 1470 | 71% |
| group | 603 | 29% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 561 | 1 | 2 | 3 | 4 | 10 | 11 | 117 | – |
| tier R | 168 | 2 | 3 | 3 | 4 | 9 | 10 | 56 |  |
| tier E | 51 | 1 | 2 | 2 | 3 | 7 | 10 | 10 |  |
| tier T | 149 | 1 | 2 | 3 | 4 | 9 | 10 | 17 |  |
| tier D | 153 | 3 | 3 | 3 | 9 | 11 | 30 | 117 |  |
| tier O | 40 | 2 | 2 | 2 | 4 | 10 | 13 | 14 |  |
| without agridat | 533 | 1 | 2 | 3 | 4 | 10 | 11 | 117 |  |

| K | n | share |
|---|---|---|
| 3 | 163 | 29% |
| 4 | 96 | 17% |
| 10 | 62 | 11% |
| 5 | 51 | 9% |
| 2 | 35 | 6% |
| 9 | 34 | 6% |
| 7 | 29 | 5% |
| 6 | 28 | 5% |
| 8 | 18 | 3% |
| 11 | 17 | 3% |
| 14 | 6 | 1% |
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
(0.271) and mean columns per categorical (5.526):
9 terms 20.02 columns, 14 terms 31.15 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 793 | 0 | 0 | 1 | 4 | 12 | 16 | 277 | 11 |
| tier R | 252 | 0 | 0 | 0 | 3 | 14 | 19 | 55 |  |
| tier E | 99 | 0 | 0 | 0 | 3 | 9 | 12 | 16 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 11 | 13 | 25 |  |
| tier D | 185 | 0 | 1 | 2 | 8 | 10 | 15 | 277 |  |
| tier O | 13 | 2 | 2 | 2 | 11 | 49 | 59 | 59 |  |
| without agridat | 765 | 0 | 0 | 1 | 4 | 11 | 15 | 277 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 793 | 0 | 0 | 1 | 6 | 32 | 51 | 14966 | – |
| tier R | 252 | 0 | 0 | 1 | 5 | 20 | 35 | 14966 |  |
| tier E | 99 | 0 | 0 | 0 | 4 | 16 | 21 | 555 |  |
| tier T | 244 | 0 | 1 | 1 | 4 | 13 | 16 | 11030 |  |
| tier D | 185 | 1 | 2 | 5 | 17 | 77 | 164 | 4580 |  |
| tier O | 13 | 2 | 2 | 2 | 19 | 59 | 2445 | 2445 |  |
| without agridat | 765 | 0 | 0 | 1 | 6 | 33 | 51 | 14966 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 538 | 68% |
| binary | 104 | 13% |
| count | 71 | 9% |
| ordinal | 45 | 6% |
| categorical | 20 | 3% |
| binomial | 15 | 2% |

| reader | n | share |
|---|---|---|
| pandas | 506 | 64% |
| pyreadr | 249 | 31% |
| rscript | 38 | 5% |

| published | n | share |
|---|---|---|
| yes | 614 | 77% |
| no | 179 | 23% |

## Tier D

The practice survey's deposits, resolved and pulled by `resolve.py` (see the README); the loss
by cause is a finding of the tier: 98 links of 60 papers; deposits by status: ok 89, no files 6, unresolved 1, restricted 1, not a deposit 1. Listed files by role: other 622, data 607, script 231, documentation 172; data files not pulled: too large 30, http 401 18, hidden path 9. Objects excluded: 799 (derived or duplicated table 482, unreadable format 156, no grouping structure 110, not the paper's data 46, response missing or undocumented 5); papers with a registry row: 28 over 185 rows.
