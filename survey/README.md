# Dimension survey — public grouped datasets

The pipeline that builds the registry: which public grouped tables exist, their documented
models, and their dimensions (lower edges, imbalance, factor levels, covariate mix) measured
by script.

- **Status:** closed 2026-10-08, corrected since. Counts are in
  [`SUMMARY.md`](../registry/SUMMARY.md), regenerated on every merge.
- **History** per pass: [`HISTORY.md`](HISTORY.md).
- **Issue numbers:** `m3#` and `#` as in [`HISTORY.md`](HISTORY.md).
- **Contract test:** metabeta-v3's `packages/glmm/tests/surveys/test_dimension_quantiles.py`
  asserts the shape of `quantiles.yaml`; an axis or tier name changes only with it.

## Files

| file | written by | content |
|---|---|---|
| `registry/sources.yaml` | hand, `mirror.py` | the frame (below) |
| `registry/registry.csv`, `excluded.csv` | `merge.py` | the census tables (below) |
| `registry/dimensions.csv`, `columns.csv`, `column_factors.csv`, `factor_pairs.csv` | `measure.py`, on every merge too | the measured files (below) |
| `registry/manifest.csv` | `merge.py` | per registry object the file it loads from, with sha256 and size |
| `registry/quantiles.yaml`, `SUMMARY.md` | `merge.py` and `measure.py` via `summarize.py` | every axis pooled, per tier and without agridat; the summary from the digit-free `SUMMARY.template.md` |
| `registry/help/`, `cache/` | `pull.py`, the loader | untracked: one help page per kept object; downloads |
| `candidates.csv`, `duplicates.csv`, `dropped.csv` | `pull.py`, `merge.py` | the survey's bookkeeping (below) |
| `deposits.csv`, `deposit_files.csv` | the archived `deposits.py`, `resolve.py` | Tier D's frame: the drawn papers and every file their deposits list |
| `sample.csv`, `agreement.csv` | `verify.py` | the second hand sample (#61): 100 candidates not yet hand-checked with their readings at draw time, and the share of readings that stood per field |
| `practice_quantiles.yaml` | copied | the practice survey's `quantiles.yaml` (metabeta-v3), the practice column of `SUMMARY.md` |
| `shards/<table>_<label>.csv` | agents, `pull.py` | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped` |
| `prompts/read.md` | | the reading agent's brief |
| `schema.py`, `sources.py`, `help.py`, `measure.py`, `summarize.py` | | file contract, frame, help pages, measures, summary |
| [`archive/`](https://github.com/adkipnis/mixedbench/tree/survey-archive-3/survey/archive) | | finished scripts and their outputs, kept at tag `survey-archive-3` and reproducible at tags `survey-archive` and `survey-archive-2` ([README](https://github.com/adkipnis/mixedbench/blob/survey-archive-3/survey/archive/README.md)) |
| `tests/` | | `uv run pytest survey/tests`, by hand; the root run never recurses here |

```
uv run python survey/pull.py [--tiers E O]
uv run python survey/merge.py survey/shards/<shard>.csv
uv run python survey/measure.py
uv run python survey/mirror.py --tag mirror-<n>
```

`pull.py`, `merge.py` and `measure.py` take `--registry DIR` and `--survey DIR` (default
`registry/`, `survey/`). `pull.py --tiers` pulls only those tiers; the others keep their rows.

## Method

One pass per tier:

1. **Frame.** Sources pinned in `sources.yaml`.
2. **Pull.** `pull.py` fetches every source through the loader, lists its objects in
   `candidates.csv`, pre-screens them and writes a help page per passing object.
3. **Reading.** Agents (`prompts/read.md`, Opus; Sonnet for Tier D) read shards of at most
   about 60 objects and file each in a registry or an excluded shard, deciding only what the
   data cannot tell.
4. **Merge.** `merge.py` loads, validates, upserts, supersedes, reconciles, measures, writes
   the manifest, summarizes and reports.
5. **Duplicates.** Flagged pairs are answered by script where the tables are identical, else by
   one agent.
6. **Blind second reading.** `medium` and `low` rows are re-read by fresh agents and compared
   by script on response, grouping factors, covariates and interactions; open disagreements go
   to Alex.
7. **Spot check.** 20 rows drawn with seed 0, stratified by shard, read by Alex at the source.
8. **Verification** (once after all tiers). A seeded hand sample of Tiers R, E, T and O
   against [ADR 0002](../docs/adr/0002-registry-suite-versioning-licenses.md)'s bar
   ([HISTORY](HISTORY.md#hand-sample-11-12)); a second one over suite 1.1's candidates not yet
   hand-checked (#61).

## Frame: `sources.yaml`

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
  ([HISTORY](HISTORY.md#tier-r-m320-m322-m323-2026-10-07)).
- `mirror` (url only): the package's copy of a CC0 file whose host refuses scripts, asked after
  the host under the same pin (ADR 0003).
- `layout`: the columns of a headerless text file, `name` (whitespace-separated) or
  `name:start-end` (fixed-width, from 1).
- `license`: as the collection states it, or `not stated` once read. An absent key means nobody
  looked, and the merge refuses a git or url source without one; a CRAN entry needs none.
- `dropped`: every candidate left out, with the reason. `nets`: the Tier O keyword net, a
  record the frame reader skips.

The sources of each tier are the entries of `sources.yaml`. Tier D has one `url` entry per
file, labeled `<paper_id>_<repository>` (`_2`, `_3` for further files). Gelman's and West's
sites refuse scripts, so ARM data come through `stan_arm` and `ros`.

## File contracts

`schema.py` holds every column and allowed value; the registry row's column order, its
response types, families and column types, the dialect and the list, term and `types` grammars
are the package's (`src/mixedbench/registry/row.py`), and `schema.py` imports them.
`tests/test_docs.py` asserts that this section names each one. Every CSV field is quoted.

### `candidates.csv` and the pre-screen

- Key `source`, `object`; rewritten whole by every pull, in frame order.
- Columns `tier`, `source`, `pin`, `object`, `file`, `n_rows`, `n_cols` (blank without a
  DataFrame), dtype counts `n_numeric`, `n_categorical`, `n_string`, `n_other`, `reader`
  (`pyreadr` / `rdata` / `pandas` / `deparse`), `screen`, `capped`.
- `screen`: `no frame`, `under 3 rows`, `one column`, `no repeated column` (no column that
  could index groups), else `pass`. Discards go to `shards/excluded_prescreen.csv`, `no frame`
  as `unreadable format`, the rest as `no grouping structure`.
- `capped` is `yes` for passing objects the cap left out. Agents read the `pass`, uncapped rows.

### `registry.csv`

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
| `formula` | the documented model verbatim, lme4 syntax where given; a nonlinear model in words |
| `documented_prior` | the prior as the source states it, one line; only on a `published_model` `yes` row |
| `published_model` | `yes` when a published model specification exists; else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other` |
| `confidence` | `high` / `medium` / `low` |
| `verified` | why the row counts as verified (ADR 0002): `hand` (the hand sample or Tier D) / `high` (confidence `high`) / `second-reading` (a blind second reading) |
| `notes` | what was read; `RULE GAP:` for an unsettled case; `NONLINEAR:` and `RESPONSE INFERRED:` open their rows' notes |

The merge fills `tier`; `sources` (`source:object` of every duplicate folded in, its own
first); `reader`; `license`, the `license:` key or a CRAN DESCRIPTION's `License`, mapped by
`LICENSES` in `schema.py` and rewritten at every merge (ADR 0003).

`random_slopes` and `verified` came in by the header-only `shards/registry_schema_2.csv`;
the archived `verified.py` filled `verified` once through `shards/registry_verified.csv`;
the archived `slopes.py` filled `random_slopes` through `shards/registry_slopes.csv`, Alex's
decisions on the rows it reported through `shards/registry_slopes_decisions.csv`.
A later row fills both in its own shard. The archived `factors.py` regrouped the
rows that named a nested `a:b` by a `b` whose codes repeat across `a` through
`shards/registry_factors.csv`; Wafer's slopes, waiting on that, followed in
`shards/registry_slopes_wafer.csv`.

### `excluded.csv`, `duplicates.csv`, `dropped.csv`

- `excluded.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`,
  `detail`; the merge adds `tier`. `reason` ∈ `no grouping structure`,
  `time series without replication`, `fewer than two groups`,
  `response missing or undocumented`, `derived or duplicated table`, `simulated data`,
  `unreadable format`, `license forbids redistribution`, `too large`, `not the paper's data`
  (Tier D).
- An object is in the registry or the exclusions, never both; to re-file one, drop it first.
- `duplicates.csv`: key `source_a`, `object_a`, `source_b`, `object_b` in frame order, with
  `verdict` and `notes`. The merge flags (`flagged`) two registry objects with equal row counts
  and sorted column cardinalities; a shard answers `same` or `different`. Confirmed groups fold
  into their first object in frame order (nlme before MEMSS), the others leave the registry.
- `dropped.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`, plus
  `tier`. A dropped object leaves `registry.csv` and `excluded.csv` until a later shard re-files
  it. One the loader no longer enumerates is deleted from every file instead (#14).

### `dimensions.csv`, `columns.csv`, `column_factors.csv` and `factor_pairs.csv`

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
  - `condition_doc` and `condition_all`: Belsley, Kuh and Welsch's (1980) condition index of
    the contract's design with the intercept, every column scaled to unit length,
    σ_max / σ_min to four decimals; `inf` when rank-deficient. `condition_doc` over the
    documented model's design from `Problem.standardized`, `condition_all` over the same coding
    of every column of `columns.csv` plus the documented interactions, on the rows complete in
    all of them. Blank for a row the contract refuses; `condition_all` alone blank when no row
    is complete or a column mixes strings and numbers (#105).
- `columns.csv`: key `source`, `object`, `model_index`, `column`, with `tier`; every column
  but the response, trials, grouping factors and ignored ones.
  - `type`, first match: `ordered` if declared; `binary` for two distinct values; `categorical`
    with `K` levels if declared, a string, or an integer column with at most 10 values not
    declared continuous; `continuous`.
  - `level` `group` when constant within every group of some factor (`constant_within` names
    them), else `within`; `missing_share`; `in_model` `yes` for a documented covariate.
  - The quirk statistics of [ADR 0006](../docs/adr/0006-measurement-pass.md), over a column's
    non-missing values, to four decimals with negatives kept, blank where the column's kind or
    its values leave one undefined:
    - `skewness` and `excess_kurtosis`: the sample-adjusted G1 and G2 pandas computes;
      `outlier_share`: the share with |z| > 4 under the mean and sample sd. Continuous columns,
      blank when constant.
    - `zero_share`, `min_share`, `max_share`: the share at zero, at the minimum, at the maximum.
      Continuous and ordered columns, an ordered one by its levels in order, its zero a level
      loaded as the number 0.
    - `unique_share`: distinct values over values. Every column.
    - `rare_level_share`: the smallest present level's share. Binary, categorical and ordered.
    - `max_abs_rho`: the largest |Spearman| with another column of the row, on the rows both
      observe; continuous columns as loaded, binary ones as 0/1, ordered ones as their codes.
      Blank without a partner or when constant on those rows.
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

### `quantiles.yaml`

- Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95`, `max`, pooled, per tier and without
  agridat; observed values, never interpolated.
- Per-factor axes count once per grouping factor; `n_obs`, `n_grouping_factors`, `d_doc` and
  `d_all` once per registry row; `K` once per documented categorical covariate.
- A quirk statistic is an axis named as its column, after `K`, counted once per row of its file
  that defines it; `inf` kept.
- `shares`: `pair_relation` over the rows of `factor_pairs.csv`; `superior` over its nested
  pairs, `factor_a` or `factor_b` for the side that holds the superior, `none` when neither does.
- `implied_columns`: the expected design columns of a 9- and a 14-term model (the practice
  survey's p90 and p95 of terms) under the observed categorical share and mean K − 1.

### What the merge checks

A failing shard is refused, its offending rows printed, nothing written.

- Header, required fields, allowed values, `model_index` 1 to 3.
- The package's row grammar (`Row.refusals`), in its words: the vocabularies, the list, term
  and `types` grammars, a `random_slopes` term `x|g` or `x||g` with `x` a covariate and `g` a
  grouping factor of the row, every part of an interaction a covariate, no column both a
  grouping factor and a covariate. A row it refuses is checked against its table only at the
  next merge.
- Source in the frame, object in the source, every named column (each part of `a:b`) in the
  table.
- Each grouping factor has two levels and a level with two rows.
- The response shows its type: `continuous` numeric, `binary` two values, `count` and
  `binomial` non-negative integers, `ordinal` at most 10 values, `categorical` not float; a
  `binomial` row's integer `trials` never below the response.
- `documented_prior` only when `published_model` is `yes`; every registry source's license in
  the lookup.
- The object not in the rival file; a dropped object in one of the two.

Upsert on the key: a shard merged twice changes nothing, a corrected shard replaces its rows in
place. An older file reads with new columns blank, so a header-only shard migrates a schema
whose new columns the row grammar accepts empty.

## Reading rules

[`prompts/read.md`](prompts/read.md) is the home of the reading rules. Below are the rulings
it does not carry, from the agents' `RULE GAP` notes and Alex's checks, each with an example
object and the deciding issue.

**Grouping factors**

- Counted: a cluster that repeats even when the source treats rows as independent (Tier O's
  hospitals, ROS; m3#24, m3#25); a month or observer with enough levels and rows (Squid,
  Sparrows; m3#25); a repeating dyad the book fits (Crofoot; m3#25); a design level the first
  reading missed (lawn's `machine:speed`; m3#23); a genotype-by-environment term fitted as
  random (salmon.bunt; m3#22).
- Not counted: strata and waves modeled as fixed (CES11; m3#23); field coordinates
  (connolly.potato; m3#22), though a Latin square's rows and columns are blocks (OrchardSprays;
  m3#23); a factor that classifies rather than clusters (singer; m3#23); a dyad with one row
  per pair (Monks; m3#25).
- A term `a:b` has no level where a part is missing (m3#24). Where a column is both a grouping
  factor and a covariate, the grouping stands and the fixed term stays in the formula
  (Cultivation; #12).
- An area factor with many levels groups; one with a handful is a covariate (LGAclaims,
  infmort; m3#23).
- A random intercept on the matched pair (amlxray; m3#23), the GEE cluster (geepack; m3#22), a
  frontier inefficiency term (xtfrontier1; m3#24); a single-level conditional logit is excluded
  (travel2; m3#25).

**Response**

- Totals are `count`, 1–5 ratings `ordinal`, non-integer abundances `continuous`, a bounded
  score without trials `count` (eggprod, InstEval; m3#22–m3#26); a float-coded nominal stays
  `ordinal` (antibiotics; #11).
- A documented normalized score is its own column (jsp_728; m3#25).
- Survival: `continuous`, the event indicator in `ignore` and `Surv(time, event)` in the
  formula (catheter; m3#24). Discrete-time hazard: the indicator is the response, `PERIOD` a
  categorical covariate (cigarette; m3#25).

**Covariates and model rows**

- A baseline is a covariate, not a response (dietox; m3#22). Polynomial and derived terms name
  their column once (muscatine; m3#22).
- An interaction is carried only when fitted (prt; m3#22). The source document beats recall
  (Stata manuals; m3#24). The final model's terms count, not the candidates; subset fits and
  contrasts are named in the formula (m3#26).
- A variant with one row per extra level is the same model (SASmixed, melanoma; m3#22, m3#24).
  posteriordb's ladders render the richest grouping (radon; m3#24).
- `published_model` is `no` for all of Tier O (m3#24).
- Priors in deposit files the page lists are filed (verberk; #10).

**Code against prose** (#15)

- Code not deposited: the paper stands at `medium`.
- An evident bug files the intended model (voorspoels); where a package version changed a fit,
  the published output decides (sequestro).
- A subset fit stays on the whole object, the subset in `notes` (szollosi).
- A fixed scale, sum-to-zero, structured covariance or location-scale correlation keeps the
  grouping and is named in the formula (rugby, gumundsdottir).

**Exclusions**

- `simulated data` only where the source says so (Stata's chicken, hox SocsLong; m3#24, #12);
  a guessed "constructed" stays (SASmixed Animal; m3#22).
- `no grouping structure`: wide repeated-measures tables (nitrofen), replication without a
  replicate column (faraway rats), a uniformity trial without a random term, coordinates as the
  only grouping (besag.checks); m3#22, m3#23. A fixed-effects fit over blocks is rendered with
  random blocks at `low` (mead.germination; m3#22).
- `derived or duplicated table`: a subset with its own model (wages_small_pp), a
  multiple-membership reshape (star_mm), Stan's censored and uncensored halves, read as the
  modal one (BUGS kidney); m3#24, m3#25.
- Stan: pure GP, time-series, CAR and mixture posteriors have no grouping; a GP beside random
  intercepts stays (m3#24).
- Kept: ARM's raw tables of an early chapter, with a later chapter's multilevel fit at `medium`
  when the grouping column is in the table (m3#24).

## Known limits

- One-level categoricals over the measured rows (stata_quinidine's `dose` and `interval`,
  Zuur Seedling's `Year`): the `K` 1 cell.
- Not read: ROS's Congress `.asc` files and `cows.dat`, liu_2022's merged-header workbook,
  walker_2021b's text sentinels.
- Not representable: polynomial and derived terms, multiple membership.
- The re-pulled `candidates.csv` and pre-screen shard of #9 and #14 are not merged: the merge
  would overwrite readers' reasons with `unreadable format`.
