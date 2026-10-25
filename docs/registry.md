# The registry files

What `registry/` holds, file by file: the frame of pinned sources, the census of their
documented models and the measured files, all written by the [survey](../survey/README.md)'s
scripts and shipped in the wheel. Counts are in [`SUMMARY.md`](../registry/SUMMARY.md). Every CSV
field is quoted. The survey's `schema.py` holds every column and allowed value; the registry
row's column order, its response types, families and column types, the dialect and the list,
term and `types` grammars are the package's (`src/mixedbench/registry/row.py`), and
`survey/tests/test_docs.py` asserts that this file names each one.

## `sources.yaml`

Tiers in frame order: `R` CRAN packages, `E` ecosystem examples (Python, Stan, Julia, Stata),
`T` textbook companions, `D` deposits of the practice survey's papers, `O` open tabular
repositories. Under each tier, one entry per source keyed by the label that shard rows name:

```yaml
seed: 0
tiers:
  R:
    agridat: {kind: cran, pin: '1.26', cap: 50}
  E:
    pingouin: {kind: git, name: https://github.com/raphaelvallat/pingouin, pin: b1c2d3e, path: src/pingouin/datasets, license: GPL-3.0}
  D:
    smith_2019_dryad: {kind: url, name: https://datadryad.org/.../data.zip, pin: <sha256>}
dropped:
  - {tier: E, name: some-collection, reason: registration wall}
```

- `kind` ∈ `cran` / `git` / `url`; `name` defaults to the label.
- `pin`: the CRAN version, git revision or file sha256; base R's `datasets` is pinned to the R
  version of its source tarball. `checksum` (optional) pins a CRAN or git archive.
- `path` narrows a git or url tree; `file` names a suffix-less download (figshare's
  `files/<id>`) so the loader knows the format.
- `cap`: the most objects read from one source, a draw with `random.Random(seed)` over the
  sorted names, `seed` set at the top. Only agridat is capped
  ([history](../survey/HISTORY.md#tier-r-m320-m322-m323-2026-10-07)).
- `mirror` (url only): the package's copy of a CC0 file whose host refuses scripts, asked after
  the host under the same pin (ADR 0003).
- `layout`: the columns of a headerless text file, `name` (whitespace-separated) or
  `name:start-end` (fixed-width, from 1).
- `license`: as the collection states it, or `not stated` once read. An absent key means nobody
  looked, and the merge refuses a git or url source without one; a CRAN entry needs none.
- `dropped`: every candidate left out, with the reason. `nets`: the Tier O keyword net, a
  record the frame reader skips.

Tier D has one `url` entry per file, labeled `<paper_id>_<repository>` (`_2`, `_3` for
further files).


## `registry.csv`

Key `source`, `object`, `model_index`. Agent columns, in order:

| column | content |
|---|---|
| `source` | label in `sources.yaml` |
| `object` | as the loader enumerates it: an R object name, a file path, or `<path>!<sheet>` |
| `model_index` | 1 for the documented model, 2 and 3 for further ones |
| `response` | column name of the response |
| `response_type` | `continuous` / `binary` / `count` / `binomial` / `ordinal` / `categorical`: what the column holds, not the family |
| `trials` | the trials column of a `binomial` response |
| `family` | blank on the contract's family rule (ADR 0001); else a departure as brms names it: `negbinomial` / `bernoulli(probit)` / `cumulative(probit)` / `Gamma(log)` / `lognormal` / `zero_inflated_poisson` / `zero_inflated_negbinomial` / `hurdle_poisson` / `hurdle_negbinomial` / `Beta` / `bernoulli(cloglog)` / `Gamma(identity)` / `zero_inflated_beta` / `student` / `gaussian` (on a count or ordinal response) / `acat` / `weibull` / `cox` |
| `grouping_factors` | `;`-list of columns whose levels index random effects; `Block:Variety` for a term on two columns, built by the merge |
| `covariates` | `;`-list of the main-effect columns |
| `interactions` | `;`-list of `a:b` terms |
| `random_slopes` | `;`-list of `x\|g` (correlated with the intercept of `g`) and `x\|\|g` (uncorrelated) terms, `x` a covariate and `g` a grouping factor of the row; blank for an intercept-only model (ADR 0001) |
| `ignore` | `;`-list of columns no model should use: ids, weights, alternate responses, coordinates |
| `types` | `;`-list of `column=categorical` / `ordered` / `continuous` where the file carries no type, and `ordered` for an R ordered factor; covariates only |
| `formula` | the documented model, lme4 syntax where given, its columns named as the table names them and a variable the source derives from columns written as its expression (`I(age - 12)`); a nonlinear model in words; a remark goes to `notes` |
| `documented_prior` | the prior as the source states it, one line; only on a `published_model` `yes` row |
| `published_model` | `yes` when a published model specification exists; else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other` |
| `confidence` | `high` / `medium` / `low` |
| `verified` | why the row counts as verified (ADR 0002): `hand` (the hand sample or Tier D) / `high` (confidence `high`) / `second-reading` (a blind second reading) |
| `notes` | what was read; `RULE GAP:` for an unsettled case; `NONLINEAR:` and `RESPONSE INFERRED:` open their rows' notes |

The merge fills `tier`; `sources` (`source:object` of every duplicate folded in, its own
first); `reader`; `license`, the `license:` key or a CRAN DESCRIPTION's `License`, mapped by
`LICENSES` in `schema.py` and rewritten at every merge (ADR 0003).


## `excluded.csv`

- `excluded.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`,
  `detail`; the merge adds `tier`. `reason` ∈ `no grouping structure`,
  `time series without replication`, `fewer than two groups`,
  `response missing or undocumented`, `derived or duplicated table`, `simulated data`,
  `unreadable format`, `license forbids redistribution`, `too large`, `not the paper's data`
  (Tier D).

## `manifest.csv`

Per registry object the file it loads from, with its sha256 and size; written by the merge.

## `dimensions.csv`, `columns.csv`, `column_factors.csv` and `factor_pairs.csv`

- Measures run over the rows with a measured response (dosing rows are no observations).
- `dimensions.csv`: key `source`, `object`, `model_index`, `factor`, with `tier`. Per grouping
  factor `n_obs`, `n_groups`, `group_size_min`, `group_size_p10`, `group_size_p50`,
  `group_size_p90`, `group_size_max`, `singleton_share`, `cv` (population sd over the mean),
  `alpha`; per row `n_factors`, `relation`, `d_doc`, `d_all`, `condition_doc`, `condition_all`.
  - `alpha`: the symmetric Dirichlet concentration matched to the group-size proportions,
    `Var(p) = (1 − 1/G) / (G (G α + 1))`; `inf` when balanced.
  - `relation` ∈ `single` / `nested` / `crossed` / `mixed`: nested or crossed when every pair
    of factors is, mixed otherwise.
  - `d_doc` (documented model) and `d_all` (every column of `columns.csv` plus the documented
    interactions): continuous and binary count 1, a categorical K − 1, an interaction the
    product.
  - `condition_doc` and `condition_all`: the condition index σ_max / σ_min of the contract's
    design with the intercept, every column scaled to unit length as Belsley, Kuh and Welsch
    (1980) scale it, to four decimals; `inf` when rank-deficient. Unlike their index, it is
    taken after the contract centers the continuous columns, so their collinearity with the
    intercept does not count. `condition_doc` over the documented model's design from
    `Problem.standardized`, `condition_all` over the same coding of every column of
    `columns.csv` plus the documented interactions, on the rows complete in all of them. Blank
    for a row the contract refuses; `condition_all` alone blank when no row is complete.
- `columns.csv`: key `source`, `object`, `model_index`, `column`, with `tier`; every column
  but the response, trials, grouping factors and ignored ones.
  - `type`, first match: `ordered` if declared; `binary` for two distinct values; `categorical`
    with `K` levels if declared, stored as a factor, or a string; `continuous`, an integer
    column included.
  - `level` `group` when constant within every group of some factor (`constant_within` names
    them), else `within`; `missing_share`; `in_model` `yes` for a documented covariate.
  - The quirk statistics of [ADR 0006](adr/0006-measurement-pass.md), over a column's
    non-missing values, to four decimals with negatives kept, blank where the column's kind or
    its values leave one undefined:
    - `skewness` and `excess_kurtosis`: the sample-adjusted G1 and G2 pandas computes;
      `outlier_share`: the share with |z| > 4 under the mean and sample sd. Continuous columns,
      blank when constant, `skewness` also under three values and `excess_kurtosis` under four.
    - `zero_share`, `min_share`, `max_share`: the share at zero, at the minimum, at the maximum.
      Continuous and ordered columns, an ordered one by its levels in order, its zero a level
      loaded as the number 0.
    - `unique_share`: distinct values over values. Every column.
    - `rare_level_share`: the smallest present level's share. Binary, categorical and ordered.
    - `max_abs_rho`: the largest |Spearman| with another column of the row, on the rows both
      observe; continuous columns as loaded, binary ones as 0/1, ordered ones as their codes, a
      categorical one takes no part. Blank without a partner or when constant on those rows.
- `column_factors.csv`: key `source`, `object`, `model_index`, `column`, `factor`, with `tier`;
  a row per row of `columns.csv` and grouping factor of its registry row, in that order. Over
  the rows that observe the column and the factor, to four decimals with negatives kept, blank
  where undefined. `absent_level_share` covers binary, categorical and ordered columns, the
  others continuous columns as loaded, binary ones as 0/1 and ordered ones as their codes:
  - `between_group_share`: the adjusted ICC(1) of one-way analysis of variance,
    (MSB − MSW) / (MSB + (k₀ − 1) MSW) with k₀ = (n − Σ nⱼ² / n) / (m − 1) (Snijders & Bosker
    2012, section 3.3.1), so 1 for a group-level column. Blank with one group, with singletons
    only or for a constant column.
  - `group_level_r2`: the row-level R² of the column on the factor's other group-level columns,
    coded as the contract codes them, over the rows that observe them all, adjusted by the
    group count, 1 − (1 − R²)(m − 1) / (m − p − 1) with p the design's rank beyond the
    intercept. Blank when p = 0, when m − p − 1 ≤ 0 or for a constant column.
  - `absent_level_share`: the share of the m × K group × level cells that hold no row.
  - `size_rho`: Spearman's ρ of the groups' sizes with their means; blank when either is
    constant.
  - `within_sd_cv`: the population coefficient of variation of the within-group sample sds over
    the groups of two or more rows; blank with fewer than two such groups or a zero mean.
- `factor_pairs.csv`: key `source`, `object`, `model_index`, `factor_a`, `factor_b`, with
  `tier`; a row per pair of a registry row's grouping factors, in their order, none for a row of
  one factor. Over the rows that observe both factors:
  - `relation` `nested` or `crossed`, by the test of `dimensions.csv`'s `relation`.
  - `superior`: the factor whose groups each hold whole groups of the other; blank for a
    crossed pair and when each holds the other's.
  - `empty_cell_share`: the share of the m_a × m_b group × group cells that hold no row, to four
    decimals; blank for a nested pair.


## `fits.csv`

- The documented model of each registry row with a `continuous`, `binary` or `count` response:
  its `formula` as written, offsets and transforms included, fitted by lme4 on the loaded table
  with the contract's family, `gaussian` by `lmer` (REML), `bernoulli` (logit) and `poisson`
  (log) by `glmer`. `survey/fits.py` runs the pass on a cluster; a merge leaves the file as it is.
- A row whose source fits a subset of the table, or repeats each row by a frequency weight, is
  listed in `survey/fits_preparation.csv` (the subset as a pandas query, the weight's column,
  the reason); the fit takes those rows, and `n_obs` counts them. A weight that counts the
  groups of a factor (`frequency_factor`, twin_hay's `pair`) makes each copy of a group a group
  of its own.
- Key `source`, `object`, `model_index`, `factor`, with `tier`; a row per grouping factor of the
  fit, the per-row fields repeated. `factor` is the registry's grouping factor that groups the
  rows alike, else lme4's name (`factor(year)`, an observation-level `INDEX`); a fit without
  estimates keeps a row per grouping factor of its registry row.
- Per row:
  - `status`, the worst that applies of `ok`, `singular` (lme4's `isSingular`), `warning`,
    `timeout` (after one hour), `error` and `no_formula` (no `|` term, a model documented in
    words, not fitted); `message`, every warning and the error joined by `; ` on one line.
    A `poisson` fit's warnings and error include those of its null model, which gives
    `sigma2_distribution`.
  - `seconds`; `n_obs`, the rows the fit used; `family`, the contract's; `family_doc`, the
    registry's `family`, blank where none.
  - The variance components on the link scale (Nakagawa, Johnson and Schielzeth 2017), blank
    unless `status` is `ok`, `singular` or `warning`:
    - `sigma2_fixed`: the variance over rows of Xβ̂, by n − 1 as performance takes it.
    - `sigma2_random`: the sum of `sigma2` over the fit's factors.
    - `sigma2_residual`: σ̂² of a gaussian fit, blank otherwise.
    - `sigma2_distribution`: 0 for `gaussian`, π²/3 for `bernoulli`, ln(1 + 1/λ) for `poisson`
      with λ = exp(β̂₀ + σ²₀ / 2) of the model with an intercept and the same random effects,
      σ²₀ the sum of its random-intercept variances, as performance computes it.
    - `sd_eta`: the sd over rows of the linear predictor, with the random effects and offsets.
    - `r2_marginal`, `sigma2_fixed` over the total of the four components; `r2_conditional`,
      `sigma2_fixed` and `sigma2_random` over the total.
- Per factor:
  - `q`: the columns of its random terms, over every term of the factor.
  - `sigma2`: the mean over rows of z'Σz over its terms (Johnson 2014).
  - `icc`: `sigma2` over the total; `icc_adjusted`: over the total without `sigma2_fixed`.
- Four decimals, negatives and `inf` kept, blank where undefined.
- Unlike performance 0.17.1, `sigma2_random` keeps every term of a factor (performance keeps the
  first of an uncorrelated `(1 + x || g)`) and the observation-level ones (it moves them into
  the residual).


## The flat sample

The survey's tables filed `no grouping structure`, screened and read again by `survey/flat.py`
([ADR 0007](adr/0007-flat-sample.md)).

- `flat_verdicts.csv`, in `survey/`: key `source`, `object`; agent columns `source`, `object`,
  `verdict`, `evidence`; the merge adds `tier`. A verdict decides its table whatever the screen
  said, from the second reading or a hand sample's correction:
  - `flat`: no documented model fits the table with a random effect and no column indexes a unit
    the rows repeat within; the table is in the flat sample.
  - `wide`: grouped data stored wide, its repeated measures as columns; the table is out of the
    sample and on the list for a long form.
  - `hidden grouping`: a column indexes a unit the rows repeat within; the table is out of the
    sample and re-filed into the registry by a dropped and a registry shard.
- `flat.csv` and `flat_columns.csv` are written by `survey/flat.py measure`, which refuses while
  a flagged table has no verdict; a merge leaves them as the last pass wrote them. A frame table
  is in the sample when it is prescreened, read and unflagged with no verdict, or judged `flat`.
  Four decimals, negatives and `inf` kept, blank where undefined.
- `flat.csv`: key `source`, `object`, with `tier`; a row per table of the sample, in frame order.
  - `stratum` `read` (filed by a reading agent) or `prescreened` (stopped by the pre-screen at
    `no repeated column`).
  - `basis` `prescreen`, `first reading` or `second reading`, and `evidence` the pre-screen's
    verdict, the first reading's `detail` or the second reading's line.
  - `n_obs` counts every row and `n_columns` every column; `n_continuous`, `n_binary`,
    `n_categorical` and `n_ordered` count the columns by their `type`.
  - `n_id_columns` counts the id columns, the categoricals whose present values are all
    distinct.
  - `d_all` and `condition_all` as `dimensions.csv` defines them, over every column but the id
    columns, with no interaction: the design centered as the contract centers its full regime,
    on the rows complete in all of them. `condition_all` is `inf` when rank-deficient, blank when
    no row is complete.
- `flat_columns.csv`: key `source`, `object`, `column`, with `tier`; a row per column of each
  table of `flat.csv`, the id columns included. `type`, `K`, `missing_share` and the quirk
  statistics as `columns.csv` defines them, over every row; `max_abs_rho` with every other
  column of the table.

## `quantiles.yaml` and `SUMMARY.md`

- Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95`, `max`, pooled, per tier and without
  agridat; observed values, never interpolated.
- Per-factor axes count once per grouping factor; `n_obs`, `n_grouping_factors`, `d_doc` and
  `d_all` once per registry row; `K` once per documented categorical covariate.
- A quirk statistic is an axis named as its column, after `K`, counted once per row of its file
  that defines it; `inf` kept.
- A fit statistic of `fits.csv` is an axis named as its column, after the quirk statistics, a
  per-row one counted once per registry row and a per-factor one once per row of the file.
- An axis the flat sample shares gains a `flat` block after `without_agridat`: `n_obs`, `d_all`
  and `condition_all` once per table of `flat.csv`, `K` once per categorical or ordered column
  of `flat_columns.csv` and a quirk statistic once per column of it that defines it. The other
  axes have none.
- `shares`: `pair_relation` over the rows of `factor_pairs.csv`; `superior` over its nested
  pairs, `factor_a` or `factor_b` for the side that holds the superior, `none` when neither does;
  `status` over the registry rows of `fits.csv`; `flat_column_type` over the rows of
  `flat_columns.csv`.
- `implied_columns`: the expected design columns of a 9- and a 14-term model (the practice
  survey's p90 and p95 of terms) under the observed categorical share and mean K − 1.

- `SUMMARY.md` is rendered from the digit-free `survey/SUMMARY.template.md` on every merge and
  measurement, the flat sample's section from the survey's flat files as they stand.
- metabeta-v3's `packages/glmm/tests/surveys/test_dimension_quantiles.py` asserts the shape of
  `quantiles.yaml`; an axis or tier name changes only with it.

## Known limits

- One-level categoricals over the measured rows (stata_quinidine's `dose` and `interval`,
  Zuur Seedling's `Year`): the `K` 1 cell.
- Not read: ROS's Congress `.asc` files and `cows.dat`, liu_2022's merged-header workbook,
  walker_2021b's text sentinels.
- Not representable: polynomial and derived terms, multiple membership.
