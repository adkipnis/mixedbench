# Dimension survey — public grouped datasets

The pipeline that builds the registry: which public grouped tables exist, their documented
models, and their dimensions (lower edges, imbalance, factor levels, covariate mix) measured
by script.

- **Status:** closed 2026-10-08, corrected since. Counts are in
  [`SUMMARY.md`](../registry/SUMMARY.md), regenerated on every merge.
- **History** per pass: [`HISTORY.md`](HISTORY.md). Alex's per-row verdicts:
  [`VERDICTS.md`](VERDICTS.md).
- **Issue numbers:** `m3#` is metabeta-v3's, where the survey ran until 2026-10-08 (spec
  m3#14); `#` is this repository's.
- **Contract test:** metabeta-v3's `tests/surveys/test_dimension_quantiles.py` asserts the
  shape of `quantiles.yaml`; an axis or tier name changes only with it.
- **Writers:** agents read documentation and write shards; `merge.py` alone writes the
  canonical files.

## Files

| file | written by | content |
|---|---|---|
| `registry/sources.yaml` | hand, `mirror.py` | the frame (below) |
| `registry/registry.csv`, `excluded.csv`, `dimensions.csv`, `columns.csv` | `merge.py` | the census tables (below) |
| `registry/manifest.csv` | `merge.py` | per registry object the file it loads from, with sha256 and size |
| `registry/quantiles.yaml`, `SUMMARY.md` | `merge.py` via `summarise.py` | every axis pooled, per tier and without agridat; the summary from the digit-free `SUMMARY.template.md` |
| `registry/help/`, `cache/` | `pull.py`, the loader | untracked: one help page per kept object; downloads |
| `candidates.csv`, `duplicates.csv`, `dropped.csv` | `pull.py`, `merge.py` | the survey's bookkeeping (below) |
| `deposits.csv`, `deposit_files.csv` | `archive/` | Tier D's frame: the drawn papers and every file their deposits list |
| `practice_quantiles.yaml` | copied | the practice survey's `quantiles.yaml` (metabeta-v3), the practice column of `SUMMARY.md` |
| `shards/<table>_<label>.csv` | agents, `pull.py` | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped` |
| `prompts/read.md` | | the reading agent's brief |
| `schema.py`, `sources.py`, `help.py`, `measure.py`, `summarise.py` | | file contract, frame, help pages, measures, summary |
| `archive/` | | finished scripts and their outputs, reproducible at tag `survey-archive` ([README](archive/README.md)) |
| `tests/` | | `uv run pytest survey/tests`, by hand; the root run never recurses here |

```
uv run python survey/pull.py [--tiers E O]
uv run python survey/merge.py survey/shards/<shard>.csv
uv run python survey/mirror.py --tag mirror-<n>
```

`pull.py` and `merge.py` take `--registry DIR` and `--survey DIR` (default `registry/`,
`survey/`). `pull.py --tiers` pulls only those tiers; the others keep their rows.

## Method

One pass per tier:

1. **Frame.** Sources pinned in `sources.yaml`.
2. **Pull.** `pull.py` fetches every source through the loader, lists its objects in
   `candidates.csv`, pre-screens them and writes a help page per passing object.
3. **Reading.** Agents (`prompts/read.md`, Opus; Sonnet for Tier D) read shards of at most
   about 60 objects and file each in a registry or an excluded shard, deciding only what the
   data cannot tell.
4. **Merge.** `merge.py` loads, validates, upserts, supersedes, reconciles, measures, writes
   the manifest, summarises and reports.
5. **Duplicates.** Flagged pairs are answered by script where the tables are identical, else by
   one agent.
6. **Blind second reading.** `medium` and `low` rows are re-read by fresh agents and compared
   by script on response, grouping factors, covariates and interactions; open disagreements go
   to Alex.
7. **Spot check.** 20 rows drawn with seed 0, stratified by shard, read by Alex at the source.
8. **Verification** (ADR 0002, once after all tiers). A seeded 100-row hand sample by tier ×
   confidence; a stratum under 80% agreement on response or grouping factors is re-read blind
   ([HISTORY](HISTORY.md#hand-sample-11-12)).

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
    pingouin: {kind: git, name: https://github.com/raphaelvallat/pingouin, pin: b1c2d3e, path: src/pingouin/datasets, licence: GPL-3.0}
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
- `cap` (per entry or top-level): the most objects read from one source, a draw with
  `random.Random(seed)` over the sorted names, `seed` set at the top. Only agridat is capped, at 50.
- `mirror` (url only): the package's copy of a CC0 file whose host refuses scripts, asked after
  the host under the same pin (ADR 0003).
- `layout`: the columns of a headerless text file, `name` (whitespace-separated) or
  `name:start-end` (fixed-width, from 1).
- `licence`: as the collection states it, or `not stated` once read. An absent key means nobody
  looked, and the merge refuses a git or url source without one; a CRAN entry needs none.
- `dropped`: every candidate left out, with the reason. `nets`: the Tier O keyword net, a
  record the frame reader skips.

## File contracts

`schema.py` holds every column and allowed value; `tests/test_docs.py` asserts that this
section names each one. Every CSV field is quoted.

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
| `ignore` | `;`-list of columns no model should use: ids, weights, alternate responses, coordinates |
| `types` | `;`-list of `column=categorical` / `ordered` / `continuous` where the file carries no type, and `ordered` for an R ordered factor; covariates only |
| `formula` | the documented model verbatim, lme4 syntax where given; a nonlinear model in words |
| `documented_prior` | the prior as the source states it, one line; only on a `published_model` `yes` row |
| `published_model` | `yes` when a published model specification exists; else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other` |
| `confidence` | `high` / `medium` / `low` |
| `notes` | what was read; `RULE GAP:` for an unsettled case; `NONLINEAR:` and `RESPONSE INFERRED:` open their rows' notes |

The merge fills `tier`; `sources` (`source:object` of every duplicate folded in, its own
first); `reader`; `licence`, the `licence:` key or a CRAN DESCRIPTION's `License`, mapped by
`LICENCES` in `schema.py` and rewritten at every merge (ADR 0003).

### `excluded.csv`, `duplicates.csv`, `dropped.csv`

- `excluded.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`,
  `detail`; the merge adds `tier`. `reason` ∈ `no grouping structure`,
  `time series without replication`, `fewer than two groups`,
  `response missing or undocumented`, `derived or duplicated table`, `simulated data`,
  `unreadable format`, `licence forbids redistribution`, `too large`, `not the paper's data`
  (Tier D).
- An object is in the registry or the exclusions, never both; to re-file one, drop it first.
- `duplicates.csv`: key `source_a`, `object_a`, `source_b`, `object_b` in frame order, with
  `verdict` and `notes`. The merge flags (`flagged`) two registry objects with equal row counts
  and sorted column cardinalities; a shard answers `same` or `different`. Confirmed groups fold
  into their first object in frame order (nlme before MEMSS), the others leave the registry.
- `dropped.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`, plus
  `tier`. A dropped object leaves `registry.csv` and `excluded.csv` until a later shard re-files
  it. One the loader no longer enumerates is deleted from every file instead (#14).

### `dimensions.csv` and `columns.csv`

- Measures run over the rows with a measured response (dosing rows are no observations).
- `dimensions.csv`: key `source`, `object`, `model_index`, `factor`, with `tier`. Per grouping
  factor `n_obs`, `n_groups`, `group_size_min`, `group_size_p10`, `group_size_p50`,
  `group_size_p90`, `group_size_max`, `singleton_share`, `cv` (population sd over the mean),
  `alpha`; per row `n_factors`, `relation`, `d_doc`, `d_all`.
  - `alpha`: the symmetric Dirichlet concentration matched to the group-size proportions,
    `Var(p) = (1 − 1/G) / (G (G α + 1))`; `inf` when balanced.
  - `relation` ∈ `single` / `nested` / `crossed` / `mixed`: nested or crossed when every pair
    of factors is, mixed otherwise.
  - `d_doc` (documented model) and `d_all` (every column of `columns.csv` plus the documented
    interactions): continuous and binary count 1, a categorical K − 1, an interaction the
    product.
- `columns.csv`: key `source`, `object`, `model_index`, `column`, with `tier`; every column
  but the response, trials, grouping factors and ignored ones.
  - `type`, first match: `ordered` if declared; `binary` for two distinct values; `categorical`
    with `K` levels if declared, a string, or an integer column with at most 10 values;
    `continuous`.
  - `level` `group` when constant within every group of some factor (`constant_within` names
    them), else `within`; `missing_share`; `in_model` `yes` for a documented covariate.

### `quantiles.yaml`

- Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95`, `max`, pooled, per tier and without
  agridat; observed values, never interpolated.
- Per-factor axes count once per grouping factor; `n_obs`, `n_grouping_factors`, `d_doc` and
  `d_all` once per registry row; `K` once per documented categorical covariate.
- `implied_columns`: the expected design columns of a 9- and a 14-term model (the practice
  survey's p90 and p95 of terms) under the observed categorical share and mean K − 1.

### What the merge checks

A failing shard is refused, its offending rows printed, nothing written.

- Header, required fields, allowed values, `model_index` 1 to 3.
- Source in the frame, object in the source, every named column (each part of `a:b`) in the
  table.
- Each grouping factor has two levels and a level with two rows.
- The response shows its type: `continuous` numeric, `binary` two values, `count` and
  `binomial` non-negative integers, `ordinal` at most 10 values, `categorical` not float; a
  `binomial` row's integer `trials` never below the response.
- No column both a grouping factor and a covariate; `documented_prior` only when
  `published_model` is `yes`; every registry source's licence in the lookup.
- The object not in the rival file; a dropped object in one of the two.

Upsert on the key: a shard merged twice changes nothing, a corrected shard replaces its rows in
place. An older file reads with new columns blank, so a header-only shard migrates a schema.

## Reading rules

From the agents' `RULE GAP` notes and Alex's checks; `prompts/read.md` carries those agents
need. An example object and the deciding issue follow each rule.

**Grouping factors**

- The columns whose levels index random effects as documented; a term on two columns is `a:b`
  (Cultivation; m3#20, m3#22), with no level where a part is missing (m3#24).
- Counted: a cluster that repeats even when the source treats rows as independent (Tier O's
  hospitals, ROS; m3#24, m3#25); a month or observer with enough levels and rows (Squid,
  Sparrows; m3#25); a repeating dyad the book fits (Crofoot; m3#25); a design level the first
  reading missed (lawn's `machine:speed`; m3#23).
- Not counted: strata and waves modelled as fixed (CES11; m3#23); field coordinates, which go
  in `ignore` (connolly.potato; m3#22), though a Latin square's rows and columns are blocks
  (OrchardSprays; m3#23); an observation-level effect, its term kept in the formula (m3#20); a
  factor that classifies rather than clusters (singer; m3#23); a dyad with one row per pair
  (Monks; m3#25).
- A column is a grouping factor or a covariate, never both; the grouping stands and the fixed
  term stays in the formula (Cultivation; #12).
- An area factor with many levels groups; one with a handful is a covariate (LGAclaims,
  infmort; m3#23).
- A random intercept on the matched pair (amlxray; m3#23), the GEE cluster (geepack; m3#22), a
  frontier inefficiency term (xtfrontier1; m3#24); a single-level conditional logit is excluded
  (travel2; m3#25).
- The random structure as the paper describes it (goodwin; m3#26) unless deposited code fits
  another (meyel; #15). A genotype-by-environment term fitted as random is the term
  (salmon.bunt; m3#22).
- `ordered` is for covariates only, never for a grouping factor (Orthodont; m3#20).

**Response**

- `response_type` follows the column, not the fit: totals `count`, 1–5 ratings `ordinal`,
  non-integer abundances `continuous`, a bounded score without trials `count` (eggprod,
  InstEval; m3#22–m3#26).
- Proportions stay `continuous`, the denominator named in the formula (MetaResp; #11); a
  float-coded nominal stays `ordinal` (antibiotics; #11).
- A transformed or recoded response names its raw column (schiz; m3#20, m3#25); a documented
  normalised score is its own column (jsp_728; m3#25).
- No documented response: the one a reader would model, `low`, `RESPONSE INFERRED:`
  (worldcup; m3#23). In Tier D such a raw table is `response missing or undocumented`
  (m3#26).
- Survival: `continuous`, the event indicator in `ignore` and `Surv(time, event)` in the
  formula (catheter; m3#24). Discrete-time hazard: the indicator is the response, `PERIOD` a
  categorical covariate (cigarette; m3#25).
- Rows without a measured response are no observations (Phenobarb; m3#20).
- A multivariate table is one row per response up to three, the rest in `notes` and `ignore`
  (Soils; m3#23).

**Covariates and types**

- A nonlinear model's inputs are covariates; `formula` names the model class under
  `NONLINEAR:` (Theoph; m3#20).
- A numeric column wrapped in `factor()` is declared `categorical` (yates.oats; m3#22). A
  baseline is a covariate, not a response (dietox; m3#22).
- What is no column (a model's group mean, a date string, a cue level, a derived indicator)
  stays in the formula only (pisa2000; m3#24, m3#26).
- An interaction is carried only when fitted (prt; m3#22). The source document beats recall
  (Stata manuals; m3#24). The final model's terms count, not the candidates; subset fits and
  contrasts are named in the formula (m3#26).
- Polynomial and derived terms name their column once (muscatine; m3#22).

**Model rows and published models**

- A further `model_index` only when the response or grouping differs; a fixed-effects
  simplification or a variant with one row per extra level is the same model (SASmixed,
  melanoma; m3#22, m3#24). posteriordb's ladders render the richest grouping (radon; m3#24).
- `published_model` `yes`: a posterior, a Stan example, a textbook worked example (m3#25), a
  documentation example stating the model; `no` for test-only data and all of Tier O; `yes`
  throughout Tier D (m3#24, m3#26).
- A `no` row keeps its proposed formula: the merge requires one (#11, #12).

**Family and prior** (#10)

- Both come from the row's model call; a prior is the one passed to it, trimmed to the row's
  response in a multivariate fit.
- Empty: package defaults, priors only in a supplement, priors in words without parameters
  (arriero). Filed: priors in deposit files the page lists (verberk); an unbounded Stan scale
  as such.
- A family missing from the vocabulary leaves `family` blank with a `RULE GAP:` (MetaResp;
  #11).

**Code against prose** (#15)

- Deposited code beats the paper's prose; the prose goes to `notes` (kleisner). Code not
  deposited: the paper stands at `medium`.
- An evident bug files the intended model (voorspoels); where a package version changed a fit,
  the published output decides (sequestro).
- A subset fit stays on the whole object, the subset in `notes` (szollosi).
- Uncorrelated effects are `||` (radon_all); a fixed scale, sum-to-zero, structured covariance
  or location-scale correlation keeps the grouping and is named in the formula (rugby,
  gumundsdottir).
- A multivariate fit is one row per part, the formula naming it (hubbard).

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
- Tier D: a cited deposit or a preregistration is `not the paper's data`; per-coder or
  per-participant files without a pooled table are `derived or duplicated table`; a split by
  study stays one row per file (sievers_2020; m3#26).

## Known limits

- One-level categoricals over the measured rows (stata_quinidine's `dose`, Zuur Seedling's
  `Year`): the `K` 1 cell.
- `-1` codes for missing (Goldstein's Gcsemv.xls, coursework.dta) are kept as values, for the
  contract to settle (#12).
- Not read: ROS's Congress `.asc` files and `cows.dat`, liu_2022's merged-header workbook,
  walker_2021b's text sentinels.
- Not representable: polynomial and derived terms, multiple membership.
- The re-pulled `candidates.csv` and pre-screen shard of #9 and #14 are not merged: the merge
  would overwrite readers' reasons with `unreadable format`.
