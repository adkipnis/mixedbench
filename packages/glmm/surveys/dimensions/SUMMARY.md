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

**Corpus.** 149 registry rows over 143 datasets and 210 grouping
factors; per tier R 149. Excluded: 201 objects (no grouping structure 182, unreadable format 9, derived or duplicated table 7, simulated data 3).

## Observations

Rows with a measured response; a pharmacokinetic table's dosing rows are not observations.

| n_obs | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 149 | 12 | 30 | 36 | 196 | 3435 | 7185 | 73421 | 23025 |
| tier R | 149 | 12 | 30 | 36 | 196 | 3435 | 7185 | 73421 |  |
| without agridat | 121 | 18 | 30 | 36 | 234 | 4059 | 7230 | 73421 |  |

## Grouping factors

| n_grouping_factors | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 149 | 1 | 1 | 1 | 1 | 2 | 3 | 4 | 3 |
| tier R | 149 | 1 | 1 | 1 | 1 | 2 | 3 | 4 |  |
| without agridat | 121 | 1 | 1 | 1 | 1 | 2 | 2 | 3 |  |

| relation | n | share |
|---|---|---|
| single | 98 | 47% |
| nested | 57 | 27% |
| crossed | 38 | 18% |
| mixed | 17 | 8% |

## Groups per factor

| n_groups | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 2 | 3 | 4 | 19 | 251 | 888 | 10767 | 414 |
| tier R | 210 | 2 | 3 | 4 | 19 | 251 | 888 | 10767 |  |
| without agridat | 157 | 2 | 4 | 5 | 21 | 312 | 1558 | 10767 |  |

## Group size

| group_size_min | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 1 | 1 | 1 | 6 | 29 | 53 | 539 | 1 |
| tier R | 210 | 1 | 1 | 1 | 6 | 29 | 53 | 539 |  |
| without agridat | 157 | 1 | 1 | 1 | 6 | 28 | 54 | 539 |  |

| group_size_p10 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 1 | 1 | 2 | 8 | 36 | 56 | 539 | – |
| tier R | 210 | 1 | 1 | 2 | 8 | 36 | 56 | 539 |  |
| without agridat | 157 | 1 | 1 | 2 | 7 | 36 | 56 | 539 |  |

| group_size_p50 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 1 | 2 | 3 | 8 | 49 | 65 | 539 | – |
| tier R | 210 | 1 | 2 | 3 | 8 | 49 | 65 | 539 |  |
| without agridat | 157 | 1 | 2 | 3 | 8 | 50 | 160 | 539 |  |

| group_size_p90 | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 1 | 3 | 3 | 9 | 59 | 137 | 539 | – |
| tier R | 210 | 1 | 3 | 3 | 9 | 59 | 137 | 539 |  |
| without agridat | 157 | 2 | 3 | 4 | 9 | 61 | 257 | 539 |  |

| group_size_max | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 2 | 3 | 4 | 10 | 92 | 198 | 969 | 300 |
| tier R | 210 | 2 | 3 | 4 | 10 | 92 | 198 | 969 |  |
| without agridat | 157 | 2 | 3 | 4 | 10 | 118 | 351 | 969 |  |

## Imbalance

The concentration of a symmetric Dirichlet fitted by moment matching to the group-size
proportions, the statistic the simulator draws; a balanced allocation has infinite
concentration (share of grouping factors: 0.576). Singleton share and the
coefficient of variation are readable companions.

| alpha | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 0.0251 | 1.5472 | 2.7846 | inf | inf | inf | inf | – |
| tier R | 210 | 0.0251 | 1.5472 | 2.7846 | inf | inf | inf | inf |  |
| without agridat | 157 | 0.3236 | 1.5472 | 2.6431 | inf | inf | inf | inf |  |

| singleton_share | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 0 | 0 | 0 | 0 | 0.0667 | 0.1525 | 0.9964 | – |
| tier R | 210 | 0 | 0 | 0 | 0 | 0.0667 | 0.1525 | 0.9964 |  |
| without agridat | 157 | 0 | 0 | 0 | 0 | 0.0667 | 0.1525 | 0.6665 |  |

| cv | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 210 | 0 | 0 | 0 | 0 | 0.5729 | 0.7935 | 5.899 | – |
| tier R | 210 | 0 | 0 | 0 | 0 | 0.5729 | 0.7935 | 5.899 |  |
| without agridat | 157 | 0 | 0 | 0 | 0 | 0.615 | 0.7935 | 1.7167 |  |

## Covariates of the documented models

| covariate type | n | share |
|---|---|---|
| continuous | 127 | 42% |
| categorical | 93 | 30% |
| binary | 74 | 24% |
| ordered | 12 | 4% |

| level | n | share |
|---|---|---|
| within | 171 | 56% |
| group | 135 | 44% |

Levels of the categorical covariates:

| K | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 105 | 2 | 3 | 3 | 4 | 8 | 14 | 56 | – |
| tier R | 105 | 2 | 3 | 3 | 4 | 8 | 14 | 56 |  |
| without agridat | 77 | 2 | 3 | 3 | 4 | 7 | 10 | 56 |  |

| K | n | share |
|---|---|---|
| 3 | 43 | 41% |
| 4 | 33 | 31% |
| 5 | 6 | 6% |
| 6 | 5 | 5% |
| 7 | 4 | 4% |
| 14 | 2 | 2% |
| 2 | 2 | 2% |
| 10 | 2 | 2% |
| 8 | 2 | 2% |
| 56 | 1 | 1% |
| 9 | 1 | 1% |
| 15 | 1 | 1% |
| 16 | 1 | 1% |
| 20 | 1 | 1% |
| 49 | 1 | 1% |

Implied design columns of a model under the observed categorical share
(0.343) and mean columns per categorical (4.543):
9 terms 19.94 columns, 14 terms 31.02 columns.

## Design columns

The documented model (`d_doc`) and every covariate column of the table plus the documented
interactions (`d_all`, never below `d_doc`): continuous and
binary count one, a categorical its levels less one, an interaction the product.

| d_doc | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 149 | 0 | 0 | 0 | 4 | 15 | 23 | 55 | 11 |
| tier R | 149 | 0 | 0 | 0 | 4 | 15 | 23 | 55 |  |
| without agridat | 121 | 0 | 0 | 1 | 3 | 13 | 15 | 55 |  |

| d_all | n | min | p5 | p10 | p50 | p90 | p95 | max | practice p90 |
|---|---|---|---|---|---|---|---|---|---|
| pooled | 149 | 0 | 0 | 1 | 5 | 20 | 31 | 60 | – |
| tier R | 149 | 0 | 0 | 1 | 5 | 20 | 31 | 60 |  |
| without agridat | 121 | 0 | 1 | 1 | 5 | 17 | 27 | 55 |  |

## Response, reader and published model

| response type | n | share |
|---|---|---|
| continuous | 117 | 79% |
| count | 11 | 7% |
| binary | 11 | 7% |
| ordinal | 6 | 4% |
| binomial | 3 | 2% |
| categorical | 1 | 1% |

| reader | n | share |
|---|---|---|
| pyreadr | 120 | 81% |
| rscript | 29 | 19% |

| published | n | share |
|---|---|---|
| yes | 136 | 91% |
| no | 13 | 9% |
