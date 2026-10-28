# The registry files

What `registry/` holds, file by file: the frame of pinned sources, the census of their
documented models, the measured files and the flat sample, all written by the
[survey](../survey/README.md)'s scripts and shipped in the wheel.
Counts are in [`SUMMARY.md`](../registry/SUMMARY.md).
The columns and allowed values live in the survey's `schema.py` and the registry row's grammar
in the package's `src/mixedbench/registry/row.py`, and `survey/tests/test_docs.py` checks that
this file names each one.
Every CSV field is quoted.
Measured numbers other than counts have four decimals, negatives and `inf` are kept, and a
blank cell means the statistic is undefined there.

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
- `pin`: the CRAN version, git revision or file sha256. Base R's `datasets` is pinned to the R
  version of its source tarball. `checksum` (optional) pins a CRAN or git archive.
- `path` narrows a git or url tree, and `file` names a suffix-less download (figshare's
  `files/<id>`) so the loader knows the format.
- `cap`: the most objects read from one source, drawn with `random.Random(seed)` over the sorted
  names, `seed` set at the top. Only agridat is capped ([history](../survey/HISTORY.md#tier-r-m320-m322-m323-2026-10-07)).
- `mirror` (url only): the package's copy of a CC0 file whose host refuses scripts, tried after
  the host under the same pin (ADR 0003).
- `layout`: the columns of a headerless text file, `name` (whitespace-separated) or
  `name:start-end` (fixed-width, from 1).
- `license`: as the collection states it, or `not stated` once read, so an absent key means
  nobody looked. The merge refuses a git or url source without one, and a CRAN entry needs none.
- `dropped`: every candidate left out, with the reason. `nets`: the Tier O keyword net, which
  the frame reader skips.

Tier D has one `url` entry per file, labeled `<paper_id>_<repository>` (`_2`, `_3` for further
files).


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

The merge fills `tier`, `sources` (the `source:object` of every duplicate folded in, its own
first), `reader` and `license`. The license is the `license:` key or a CRAN DESCRIPTION's
`License`, mapped by `LICENSES` in `schema.py` at every merge (ADR 0003).


## `excluded.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason` and `detail`, and the merge
adds `tier`. `reason` ∈ `no grouping structure`, `time series without replication`,
`fewer than two groups`, `response missing or undocumented`, `derived or duplicated table`,
`simulated data`, `unreadable format`, `license forbids redistribution`, `too large`,
`not the paper's data` (Tier D).

## `manifest.csv`

Per registry object the file it loads from, with its sha256 and size, written by the merge.

## `dimensions.csv`, `columns.csv`, `column_factors.csv` and `factor_pairs.csv`

Measured over the rows with a measured response, since dosing rows are no observations.

- `dimensions.csv`: key `source`, `object`, `model_index`, `factor`, with `tier`. Per grouping
  factor `n_obs`, `n_groups`, `group_size_min`, `group_size_p10`, `group_size_p50`,
  `group_size_p90`, `group_size_max`, `singleton_share`, `cv` (population sd over the mean) and
  `alpha`. Per row `n_factors`, `relation`, `d_doc`, `d_all`, `condition_doc` and
  `condition_all`.
  - `alpha`: the symmetric Dirichlet concentration matched to the group-size proportions,
    `Var(p) = (1 − 1/G) / (G (G α + 1))`, `inf` when balanced.
  - `relation` ∈ `single` / `nested` / `crossed` / `mixed`: nested or crossed when every pair
    of factors is, mixed otherwise.
  - `d_doc` (the documented model) and `d_all` (every column of `columns.csv` plus the
    documented interactions): a continuous or binary column counts 1, a categorical one K − 1
    and an interaction the product.
  - `condition_doc` and `condition_all`: the condition index σ_max / σ_min of the design of
    `d_doc` or `d_all` with the intercept, coded and centered as the contract codes and centers
    it, each column scaled to unit length (Belsley, Kuh and Welsch 1980), on the rows complete
    in all its columns. Unlike their index, it leaves out the continuous columns' collinearity
    with the intercept. `inf` when rank-deficient, blank for a row the contract refuses, and
    `condition_all` alone blank when no row is complete.
- `columns.csv`: key `source`, `object`, `model_index`, `column`, with `tier`. Every column but
  the response, trials, grouping factors and ignored ones.
  - `type`, the first that matches: `ordered` if declared, `binary` for two distinct values,
    `categorical` with `K` levels if declared, stored as a factor or a string, and `continuous`
    otherwise, an integer column included.
  - `level`: `group` when constant within every group of some factor, which `constant_within`
    names, else `within`. `missing_share` is the share of missing values, and `in_model` is
    `yes` for a documented covariate.
  - The quirk statistics of [ADR 0006](adr/0006-measurement-pass.md), over a column's
    non-missing values:
    - `skewness` and `excess_kurtosis`: the sample-adjusted G1 and G2 pandas computes, and
      `outlier_share`, the share with |z| > 4 under the mean and sample sd. Continuous columns,
      blank when constant, `skewness` also under three values and `excess_kurtosis` under four.
    - `zero_share`, `min_share`, `max_share`: the share at zero, at the minimum and at the
      maximum. Continuous and ordered columns, an ordered one by its levels in order, its zero a
      level loaded as the number 0.
    - `unique_share`: distinct values over values. Every column.
    - `rare_level_share`: the smallest present level's share. Binary, categorical and ordered
      columns.
    - `max_abs_rho`: the largest |Spearman| with another column of the row, on the rows both
      observe. A continuous column as loaded, a binary one as 0/1 and an ordered one by its
      codes, and a categorical one takes no part. Blank without a partner or when constant on
      those rows.
- `column_factors.csv`: key `source`, `object`, `model_index`, `column`, `factor`, with `tier`.
  A row per row of `columns.csv` and grouping factor of its registry row, in that order, over
  the rows that observe both. `absent_level_share` covers the binary, categorical and ordered
  columns, and the others the continuous, binary and ordered ones, coded as for `max_abs_rho`.
  - `between_group_share`: the adjusted ICC(1) of one-way analysis of variance,
    (MSB − MSW) / (MSB + (k₀ − 1) MSW) with k₀ = (n − Σ nⱼ² / n) / (m − 1) (Snijders & Bosker
    2012, section 3.3.1), so 1 for a group-level column. Blank with one group, with singletons
    only or for a constant column.
  - `group_level_r2`: the row-level R² of the column on the factor's other group-level columns,
    coded as the contract codes them, over the rows that observe them all, adjusted by the
    group count, 1 − (1 − R²)(m − 1) / (m − p − 1) with p the design's rank beyond the
    intercept. Blank when p = 0, when m − p − 1 <= 0 or for a constant column.
  - `absent_level_share`: the share of the m × K group × level cells that hold no row.
  - `size_rho`: Spearman's ρ of the groups' sizes with their means, blank when either is
    constant.
  - `within_sd_cv`: the population coefficient of variation of the within-group sample sds over
    the groups of two or more rows, blank with fewer than two such groups or a zero mean.
- `factor_pairs.csv`: key `source`, `object`, `model_index`, `factor_a`, `factor_b`, with
  `tier`. A row per pair of a registry row's grouping factors, in their order, over the rows
  that observe both, and none for a row of one factor.
  - `relation` `nested` or `crossed`, by the test of `dimensions.csv`'s `relation`.
  - `superior`: the factor whose groups each hold whole groups of the other, blank for a crossed
    pair and when each holds the other's.
  - `empty_cell_share`: the share of the m_a × m_b group × group cells that hold no row, blank
    for a nested pair.

## `responses.csv`

- Key `source`, `object`, `model_index`, with `tier`, a row per registry row: its `response`,
  its `response_type` and the response's marginal, written by the measurement pass.
- The response is measured as the column kind its type gives: `continuous` and `count` as
  loaded and `binomial` as its successes' share of the trials, all three as continuous columns,
  `binary` and `categorical` as loaded, and `ordinal` as an ordered column, its levels in the
  order the contract codes them.
- `K`: the present levels of a binary, ordinal or categorical response, blank otherwise.
- `missing_share`: the share of every loaded row without a response, dosing rows included. A
  binomial row of zero trials has no share and counts as missing.
- The quirk statistics as `columns.csv` defines them for that kind, over the response's
  non-missing values. `max_abs_rho` is the largest |Spearman| with a column of `columns.csv` of
  the same registry row.

## `fits.csv`

- The documented model of each registry row with a `continuous`, `binary` or `count` response:
  its `formula` as written, offsets and transforms included, fitted by lme4 on the loaded table
  with the contract's family, `gaussian` by `lmer` (REML), `bernoulli` (logit) and `poisson`
  (log) by `glmer`. `survey/fits.py` runs the pass on a cluster, and a merge leaves the file as
  it is.
- A row whose source fits a subset of the table, or repeats each row by a frequency weight, is
  listed in `survey/fits_preparation.csv` with the subset as a pandas query or the weight's
  column, and the fit and `n_obs` take those rows. A weight that
  counts the groups of a factor (`frequency_factor`, twin_hay's `pair`) makes each copy of a
  group a group of its own.
- Key `source`, `object`, `model_index`, `factor`, with `tier`, a row per grouping factor of the
  fit with the per-row fields repeated. `factor` is the registry's grouping factor that groups
  the rows alike, else lme4's name (`factor(year)`, an observation-level `INDEX`). A fit without
  estimates keeps a row per grouping factor of its registry row.
- Per row:
  - `status`, the worst that applies of `ok`, `singular` (lme4's `isSingular`), `warning`,
    `timeout` (after one hour), `error` and `no_formula` (no `|` term, a model documented in
    words, not fitted). `message` joins every warning and the error by `; ` on one line, a
    `poisson` fit's with those of its null model, which gives `sigma2_distribution`.
  - `seconds`, and `n_obs`, the rows the fit used. `family` is the contract's, and `family_doc`
    the registry's `family`, blank where none.
  - The variance components on the link scale (Nakagawa, Johnson and Schielzeth 2017), blank
    unless `status` is `ok`, `singular` or `warning`:
    - `sigma2_fixed`: the variance over rows of Xβ̂, by n − 1 as performance takes it.
    - `sigma2_random`: the sum of `sigma2` over the fit's factors.
    - `sigma2_residual`: σ̂² of a gaussian fit, blank otherwise.
    - `sigma2_distribution`: 0 for `gaussian`, π²/3 for `bernoulli`, ln(1 + 1/λ) for `poisson`
      with λ = exp(β̂₀ + σ²₀ / 2) of the model with an intercept and the same random effects,
      σ²₀ the sum of its random-intercept variances, as performance computes it.
    - `sd_eta`: the sd over rows of the linear predictor, with the random effects and offsets.
    - `r2_marginal`: `sigma2_fixed` over the total of the four components. `r2_conditional`:
      `sigma2_fixed` and `sigma2_random` over the total.
- Per factor:
  - `q`: the columns of its random terms, over every term of the factor.
  - `sigma2`: the mean over rows of z'Σz over its terms (Johnson 2014).
  - `icc`: `sigma2` over the total. `icc_adjusted`: over the total without `sigma2_fixed`.
- Unlike performance 0.17.1, `sigma2_random` keeps every term of a factor (performance keeps the
  first of an uncorrelated `(1 + x || g)`) and the observation-level ones (it moves them into
  the residual).


## The flat sample

The survey's tables filed `no grouping structure`, screened, read again and measured by
`survey/flat.py` ([ADR 0007](adr/0007-flat-sample.md)).
A frame table is in the sample when it is prescreened, read and unflagged without a verdict, or
judged `flat`.
Neither `flat.csv` nor `flat_columns.csv` measures a table's response, as `columns.csv` and
`dimensions.csv` leave out a registry row's; `flat_response_statistics.csv` measures it as
`responses.csv` does.

- `flat_verdicts.csv`, in `survey/`: key `source`, `object`. Agent columns `source`, `object`,
  `verdict` and `evidence`, and the merge adds `tier`. A verdict of the second reading or of a
  hand check decides its table whatever the screen said:
  - `flat`: no documented model fits the table with a random effect, and no column indexes a
    unit the rows repeat within. The table is in the sample.
  - `wide`: grouped data stored wide, its repeated measures as columns. The table is out of the
    sample and on the [list for a long form](https://github.com/adkipnis/mixedbench/issues/129).
  - `hidden grouping`: a column indexes a unit the rows repeat within. The table is re-filed
    into the registry.
- `flat_responses.csv`, in `survey/`: as `flat_verdicts.csv`, with `response` for `verdict`,
  and `response_type` and `trials`. The response is the outcome of the table's first documented
  model, never inferred, else `none`. A named response carries its `response_type`, and a
  binomial one its `trials`, as a registry row does; both are blank for `none`.
- `flat.csv`: key `source`, `object`, with `tier`, a row per sample table in frame order.
  - `stratum`: `read` (filed by a reading agent) or `prescreened` (stopped by the pre-screen at
    `no repeated column`).
  - `basis` and `evidence`: `prescreen` with the pre-screen's verdict, `first reading` with its
    `detail`, or `second reading` with its line.
  - `response`, from `flat_responses.csv`.
  - `n_obs` and `n_columns`: every row and column. `n_continuous`, `n_binary`, `n_categorical`
    and `n_ordered` count the columns by `type`, and `n_id_columns` the id columns, the
    categoricals whose present values are all distinct.
  - `d_all` and `condition_all` as `dimensions.csv` defines them, over every column but the id
    columns, without interactions and without a coded column of one value.
- `flat_columns.csv`: key `source`, `object`, `column`, with `tier`, a row per column of each
  table of `flat.csv`. `type`, `K`, `missing_share` and the quirk statistics as `columns.csv`
  defines them, over every row of the table. `id_column` is `yes` for an id column, else `no`.
- `flat_response_statistics.csv`: key `source`, `object`, with `tier`, a row per table of
  `flat.csv` that names a response: its `response`, its `response_type` and the response's
  marginal as `responses.csv` defines it, over every row of the table. `max_abs_rho` is the
  largest |Spearman| with another column of the table, the trials included.

## `quantiles.yaml` and `SUMMARY.md`

- Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95` and `max`, pooled, per tier and without
  agridat, all observed values, never interpolated.
- A per-factor axis counts once per grouping factor, `n_obs`, `n_grouping_factors`, `d_doc` and
  `d_all` once per registry row, and `K` once per documented categorical covariate.
- A quirk statistic is an axis named as its column, after `K`, and a fit statistic of
  `fits.csv` one after the quirk statistics. Each counts once per row of its file that defines
  it, a per-row fit statistic once per registry row.
- A statistic of `responses.csv` is an axis named `response_` and its column, after the fit
  statistics, once per registry row that defines it: `response_K` per binary, ordinal or
  categorical response.
- An axis the flat sample shares gains a `flat` block after `without_agridat`: `n_obs`, `d_all`
  and `condition_all` once per table of `flat.csv`, `K` once per categorical or ordered column
  of `flat_columns.csv`, a quirk statistic once per column of it that defines it, and a
  `response_` axis once per row of `flat_response_statistics.csv` that defines it.
- `shares`: `pair_relation` over the rows of `factor_pairs.csv`, `superior` over its nested
  pairs as `factor_a`, `factor_b` or `none`, the side that is superior, `status` over the
  registry rows of `fits.csv`, and `flat_column_type` over the rows of `flat_columns.csv`.
- `implied_columns`: the expected design columns of a 9- and a 14-term model (the practice
  survey's p90 and p95 of terms) under the observed categorical share and mean K − 1.
- `SUMMARY.md` is rendered from the digit-free `survey/SUMMARY.template.md` at every merge and
  measurement, its flat section from the survey's flat files as they stand.
- MetaBeta's `packages/glmm/tests/surveys/test_dimension_quantiles.py` asserts the shape of
  `quantiles.yaml`, so an axis or tier name changes only with it.

## Known limits

- One-level categoricals over the measured rows (stata_quinidine's `dose` and `interval`,
  Zuur Seedling's `Year`): the `K` 1 cell.
- Not read: ROS's Congress `.asc` files and `cows.dat`, liu_2022's merged-header workbook,
  walker_2021b's text sentinels.
- Not representable: polynomial and derived terms, multiple membership.
