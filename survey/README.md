# Dimension survey — public grouped datasets

The lower edges, imbalance, factor-level distribution and covariate mix of real grouped data,
and the pool the v1 real-data test sets draw from. Spec: issue #14; tickets #15–#27 (issue
numbers in this file are metabeta-v3's: the survey moved here from its
`packages/glmm/surveys/dimensions` with history on 2026-10-08). The package's loader
(`mixedbench.datasets`) reads every source; the scripts here own the file contract. The
practice survey (metabeta-v3's `packages/glmm/surveys/practice`) is the model; nothing is
imported across surveys. Results: [`SUMMARY.md`](../registry/SUMMARY.md), regenerated on every
merge.

The census files the package ships live in [`registry/`](../registry/) (`sources.yaml`,
`registry.csv`, `excluded.csv`, `dimensions.csv`, `columns.csv`, `quantiles.yaml`,
`SUMMARY.md`, `manifest.csv`, and the untracked `cache/` and `help/`); everything else in the table below lives
here in `survey/`.

**Status: closed 2026-10-08** at 712 registry rows over 642 datasets (Tier R 252, T 244,
D 104, E 99, O 13) and 2142 exclusions, above the closing minimums of #27 (100 Tier R rows,
40 rows from the other tiers), no duplicate flag open. metabeta-v3's
`tests/surveys/test_dimension_quantiles.py` asserts the contract of `quantiles.yaml` in CI; the envelope edges are set in the outcome
grill, not here.

## Files

| file | written by | content |
|---|---|---|
| `sources.yaml` | hand, discovery, `resolve.py`, `mirror.py` (`mirror:`) | the frame: tiers of pinned sources, cap, seed, dropped candidates, the Tier O keyword net |
| `deposits.csv` | `deposits.py` | Tier D frame: 60 seeded, stratified draws of the practice survey's deposit-naming papers |
| `deposit_files.csv` | `resolve.py` | Tier D: every link of `deposits.csv` resolved through its repository's API, one row per listed file with role, checksum, label and pin; one row for a deposit without files |
| `candidates.csv` | `pull.py` | every enumerated data object with its counts and pre-screen verdict |
| `net_hits.csv` | `net.py` | Tier O: every table of OpenML, UCI and PMLB whose column names hold a `nets` keyword, kept or not |
| `v05_datasets.csv` | hand | the 36 R datasets of metabeta v0.5; each is in the registry or the exclusions (asserted at the closing, #27) |
| `help/`, `cache/` | `pull.py`, loader, `resolve.py` | untracked: one help page per kept object (documentation, dtypes, first rows), one per Tier D deposit; downloads, extracted trees, cached API answers |
| `shards/<table>_<label>.csv` | agents; `pull.py` writes `excluded_prescreen.csv` | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped` |
| `registry.csv` | `merge.py` | one row per dataset and documented model, at most three per object |
| `scan_hits.csv` | `verify.py scan` | one row per keyword occurrence: a registry row's `notes`, `formula` or help page, or a Tier D deposit page once per deposit |
| `sample.csv` | `verify.py draw` | the seeded hand sample (ADR 0002): row key, stratum, seed, batch and the compared fields as read at draw time |
| `excluded.csv` | `merge.py` | every screened-out object with a categorical reason |
| `duplicates.csv` | `merge.py` | candidate pairs the merge flagged and the verdicts returned |
| `dropped.csv` | `merge.py` | objects taken out of the registry and the exclusions, awaiting a re-filing shard |
| `dimensions.csv`, `columns.csv` | `merge.py` via `measure.py` | one row per registry row and grouping factor; one per registry row and covariate column |
| `manifest.csv` | `merge.py` | one row per registry object: the file it loads from inside its source, that file's sha256 and size (empty for base R's, which R dumps); a user's loader fetches that file alone |
| `quantiles.yaml`, `SUMMARY.md` | `merge.py` via `summarise.py` | every axis pooled, per tier and without agridat; the summary from `SUMMARY.template.md`, which holds no digit |
| `mirror.py` | | publishes the CC0 files of the registry's Dryad sources as release assets and writes their `mirror:` URLs into `sources.yaml` |
| `practice_quantiles.yaml` | copied | snapshot of the practice survey's `quantiles.yaml` (metabeta-v3), the p90 column of `SUMMARY.md` |
| `prompts/discover.md`, `prompts/read.md` | | what the discovery agent and a reading agent get and write |
| `schema.py`, `sources.py`, `measure.py`, `summarise.py`, `net.py` | | file contract and allowed values; the frame; what the merge measures and how it reports it; the Tier O net |
| `tests/` | | pytest, run by hand, not in CI: `uv run pytest survey/tests` (the root run never recurses into `survey/` or `registry/`, whose cache holds repositories with tests of their own) |

Agents read documentation and write shards; `merge.py` is the only writer of the canonical CSVs.

```
uv run python survey/deposits.py --practice <metabeta-v3>/packages/glmm/surveys/practice
uv run python survey/resolve.py --practice <metabeta-v3>/packages/glmm/surveys/practice [--fetch | --ingest]
uv run python survey/net.py
uv run python survey/pull.py [--tiers E O]
uv run python survey/merge.py survey/shards/<shard>.csv
```

Every script takes `--registry DIR` and `--survey DIR`, defaulting to `registry/` and
`survey/`.

`pull.py --tiers` pulls only those tiers; the others keep their rows in `candidates.csv`, the
pre-screen shard and their help pages.

## Method

One pass per tier, the same steps each time:

1. **Frame.** Sources pinned in `sources.yaml` (below); Tier D's come from `deposits.py` and
   `resolve.py`.
2. **Pull.** `pull.py` fetches every source through the loader, enumerates its data objects
   into `candidates.csv`, applies the mechanical pre-screen and writes one help page per
   passing object under `help/`.
3. **Reading.** Agents (`prompts/read.md`) read the help pages in shards of at most about 60
   objects and file every object in a registry or an excluded shard, deciding only what the
   data cannot tell: the documented model, its response and grouping factors, the types the
   file cannot carry. Opus for Tiers R, E, T and O; Sonnet at medium effort for Tier D
   (cost), the Opus tiers being the calibration.
4. **Merge.** `merge.py` validates the shard against the loaded tables, upserts, flags
   duplicate candidates, measures every registry row into `dimensions.csv` and `columns.csv`,
   names every registry object's file in `manifest.csv` and regenerates `quantiles.yaml` and `SUMMARY.md`.
5. **Duplicates.** Flagged pairs are answered by script where the tables are identical, else
   by one agent; confirmed groups fold into the row of their first object in frame order.
6. **Blind second reading.** The tier's `medium` and `low` rows are re-read by fresh agents
   into a scratch directory and compared by script on response, grouping factors, covariates
   and interactions. Disagreements a rule settles are applied; the rest go to Alex.
7. **Spot check.** 20 rows drawn with seed 0, stratified by shard in proportion to the rows
   surviving the fold, read by Alex against the help pages and the source together with the
   open disagreements. Verdicts become corrected rows and the rules below. In Tier D Alex
   read every row.

## Frame: `sources.yaml`

Tiers in frame order `R` (CRAN package data), `E` (Python, Stan, Julia and Stata ecosystem
examples), `T` (textbook companions), `D` (data deposits of the practice survey's papers),
`O` (open tabular repositories). Under each tier, one entry per source keyed by its label,
the `source` every shard row names:

```yaml
seed: 0
tiers:
  R:
    lme4: {kind: cran, pin: 2.0-6}
    agridat: {kind: cran, pin: '1.26', cap: 50}
  E:
    stan_examples: {kind: git, name: https://github.com/stan-dev/example-models, pin: a1b2c3d, path: ARM}
    pingouin: {kind: git, name: https://github.com/raphaelvallat/pingouin, pin: b1c2d3e, path: src/pingouin/datasets, licence: GPL-3.0}
  D:
    smith_2019_dryad: {kind: url, name: https://datadryad.org/.../data.zip, pin: <sha256>}
dropped:
  - {tier: E, name: some-collection, reason: registration wall}
```

- `kind` ∈ `cran` / `git` / `url` as the loader's `Source`; `name` defaults to the label (a
  CRAN package name); `pin` is the CRAN version, git revision or the file's sha256 (base R's
  `datasets` is pinned to the R version that dumps it); `checksum` (optional) pins a CRAN or
  git archive; `path` narrows a git or url tree; `file` names the download of a url whose
  path has no suffix (figshare's `files/<id>`), so the loader knows the format.
- `cap` (per entry or top-level) is the most objects read from one source: a source with
  more objects passing the pre-screen keeps a draw of `cap` of them made with
  `random.Random(seed)` over their sorted names. Only agridat (about 390 field trials, else
  38% of the pool) is capped, at 50; a cap for all would have discarded grouped tables of
  faraway and MASS at random (decided 2026-10-07).
- `mirror` (url sources only) is the package's copy of a CC0 file whose host refuses a script
  (Dryad's 401), asked after the host under the same pin; written by `mirror.py`, which
  uploads the cached files as assets of a GitHub release (ADR 0003).
- `layout` names the columns of a headerless text file: `name` for a whitespace-separated
  file (Goldstein's partnership data), `name:start-end` for a fixed-width file (the Bristol
  CMM `.DAT` files, positions from 1).
- `licence` is the collection's licence as its LICENSE file, readme, DESCRIPTION or
  repository API states it, or `not stated` once the collection was read and carries none;
  an absent key means nobody has looked, and the merge refuses a registry row of a git or url
  source without one. A CRAN entry needs none: the merge reads its DESCRIPTION; base R's
  `datasets` has none in the loader's tree and carries the installed one's `Part of R 4.6.1`.
  The survey redistributes no data, so the field records terms to respect and sources to
  cite.
- `dropped` lists every candidate the discovery step considered and left out, with the
  reason. `nets` is the Tier O keyword net: the repositories, the column-name keywords a
  table must document as its clustering column, and the cap; a record of a search, which
  `readFrame` leaves alone.

The tiers:

- **R** (#19, #22, #23): a census of two package groups at the CRAN versions of 2026-10-07.
  Mixed-model packages lme4, nlme, mlmRev, MEMSS, glmmTMB, brms, GLMMadaptive (ships no data),
  nlmeU, SASmixed, HLMdiag, ordinal, geepack, agridat; general data packages with grouped
  tables MASS, carData, lattice, HSAUR3, faraway, boot, gamlss.data, medicaldata, languageR
  and base R's `datasets`.
- **E** (#21, #24): posteriordb, the Stan example models (`ARM` and `bugs_examples`),
  pingouin, the PyMC examples' data, bambi's thirteen figshare files, MixedModels.jl's
  dataset artifact (one tar.gz of 17 Arrow files on OSF), the datasets of Stata's [ME] and
  [XT] manuals.
- **T** (#21, #25): Hox, Snijders & Bosker, Goldstein and his partnership data, nine Bristol
  Centre for Multilevel Modelling teaching sets, Rabe-Hesketh & Skrondal, Singer & Willett
  (UCLA mirror), three Zuur et al. books, McElreath's *Statistical Rethinking*, Fitzmaurice,
  Laird & Ware, Gelman, Hill & Vehtari's *Regression and Other Stories* (`ROS-Examples`),
  West, Welch & Galecki (`WWGbook`), Diggle's APTS course files. Gelman's and West's own
  sites answer 403 to scripts, so ARM data come through `stan_arm` and `ros`.
- **D** (#26): 60 papers drawn by `deposits.py`, their Dryad, OSF, Zenodo and figshare
  files resolved by `resolve.py`, one `url` entry per fetched file labelled
  `<paper_id>_<repository>` (`_2`, `_3` for further files), pinned by sha256 and checked on
  download against the digest the repository's API reports.
- **O** (#21, #24): metabeta v0.5's four PMLB tables (`analcatdata` apnea and boxing;
  Simonoff 2003) and the hits of the keyword net over OpenML, UCI and PMLB.

Discovery (#21): one Opus agent with web search ran `prompts/discover.md` over the spec's
list and about twenty further queries; a second pass by hand added seven collections the
agent had missed or dropped (Zuur, Stata [XT], MixedModels.jl, rethinking, Fitzmaurice, ROS,
WWGbook, Diggle). Kept URLs were fetched with the loader's user agent and pinned by script
(sha256 of the file, HEAD revision of the repository on 2026-10-07). Everything considered
and left out is a `dropped` row.

## File contracts

### `deposits.csv`

Key `paper_id`; written whole by `deposits.py`. The Tier D frame is every paper of the
practice survey's `papers.csv` whose text names a Dryad, OSF, Zenodo or figshare deposit by
DOI or URL, found by one regex and normalised to one identifier per deposit. The match is
mechanical and also catches preregistrations and deposits a paper merely cites; #26 excludes
those with their reason and never replaces them, and that loss is a Tier D finding. Per
stratum 15 papers are drawn with `random.Random(seed).sample` over the sorted ids (seed 0):
equal cells rather than proportional ones, because the tier exists to compare deposited data
with package data and every stratum should stay readable. Columns: `stratum`, `repository`
and `url` as `;`-lists over the paper's distinct deposits, `context` (the text around each
match, joined with ` || `), `seed`, `n_frame`.

### `candidates.csv` and the pre-screen

Key `source`, `object`; written whole by `pull.py` on every run, in frame order. Per
enumerated data object: `tier`, `source`, `pin`, `object`, `file`, `n_rows`, `n_cols` (blank
where the loader cannot make a DataFrame), the column counts by dtype `n_numeric`,
`n_categorical`, `n_string`, `n_other`, `reader` (`pyreadr` / `rdata` / `pandas` / `deparse`),
`screen` and `capped`.

`screen` is the verdict of a mechanical pre-screen on what a grouped table needs before an
agent reads it, conservative by design: `no frame`, `under 3 rows`, `one column`,
`no repeated column` (no column whose values could index groups: not fractional, two or more
distinct values, some value repeated), else `pass`. The pull writes the discards as the shard
`shards/excluded_prescreen.csv` (`no frame` under `unreadable format`, the rest under
`no grouping structure`), which the merge takes like any agent shard. `capped` is `yes` for
the passing objects a source's cap left out. Agents read the `pass`, uncapped rows, whose
help pages are at `help/<source>/<object>.txt`.

### `registry.csv`

Key `source`, `object`, `model_index`. Agent columns, in order:

| column | content |
|---|---|
| `source` | label in `sources.yaml` |
| `object` | the data object as the loader enumerates it: an R object name, a file path inside a git or url tree, or `<path>!<sheet>` for a data sheet of a workbook with several |
| `model_index` | 1 for the documented model, 2 and 3 for further documented models; never more |
| `response` | column name of the response |
| `response_type` | `continuous` / `binary` / `count` / `binomial` / `ordinal` / `categorical`; what the column holds, not the family fitted to it |
| `trials` | column name of the trials for a `binomial` response, blank otherwise |
| `family` | blank where the contract's family rule applies (ADR 0001); else the documented model's family and link as brms names it: `negbinomial` / `bernoulli(probit)` / `cumulative(probit)` / `Gamma(log)` / `lognormal` / `zero_inflated_poisson` / `zero_inflated_negbinomial` / `hurdle_poisson` / `hurdle_negbinomial` / `Beta` / `bernoulli(cloglog)` / `Gamma(identity)` / `zero_inflated_beta` / `student` / `gaussian` (a Gaussian fit to a count or ordinal response) / `acat` / `weibull` / `cox` (survival, with censoring in `notes`); a departure from the rule, never a restatement of it (a Poisson count model stays blank) |
| `grouping_factors` | `;`-list of the columns whose levels index random effects, as documented; a random term on the combination of two columns (`(1\|Block:Variety)`) is `Block:Variety`, which the merge builds from its parts |
| `covariates` | `;`-list of the documented model's covariate columns (main effects) |
| `interactions` | `;`-list of `a:b` terms, every part a column name |
| `ignore` | `;`-list of columns no model should use: row ids, weights, alternate responses, coordinates |
| `types` | `;`-list of `column=categorical`, `column=ordered` or `column=continuous` declarations for formats without column types, and `ordered` for an R ordered factor, which `pyreadr` reads as unordered; covariates only |
| `formula` | the documented model verbatim (lme4 syntax where the source gives one); a nonlinear mixed model in words, naming the model class and its inputs |
| `documented_prior` | the prior as the source states it, in its notation (Stan, BUGS, brms or words), one line; blank where it states none; only on a `published_model` `yes` row |
| `published_model` | `yes` when a published model specification exists; else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other`; reporting only |
| `confidence` | `high` / `medium` / `low` |
| `notes` | free text: the documentation read, cases the prompt does not settle (`RULE GAP:`); `NONLINEAR:` opens the note of a nonlinear mixed model, `RESPONSE INFERRED:` the note of a row whose page documents no response |

Script columns the merge fills: `tier`, `sources` (`source:object` of every confirmed
duplicate folded into the row, the row's own first), `reader`, `licence`. `licence` is the
source's `licence:` key in `sources.yaml`, else a CRAN package's DESCRIPTION `License` field,
mapped by the literal lookup `LICENCES` of `schema.py` to `CC0-1.0` / `CC-BY-4.0` /
`CC-BY-NC-4.0` / `CC-BY-NC-SA-4.0` / `ODbL-1.0` / `GPL-2.0-or-later` / `GPL-2.0` /
`GPL-3.0-or-later` / `GPL-3.0` / `AGPL-3.0` / `MIT` / `BSD-3-Clause` / `public-domain` /
`other` / `not stated` (ADR 0003). The merge rewrites it on every row, so a corrected key
reaches the rows merged earlier. `GPL-3.0-or-later` and `AGPL-3.0` were added for CRAN
DESCRIPTIONs (#7); a string that states access or attribution but no licence (OpenML's
`Public`) is `other` or `not stated`, never a licence it does not name.

### `excluded.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason`, `detail`; the merge adds
`tier`. `reason` is one of `no grouping structure`, `time series without replication`,
`fewer than two groups`, `response missing or undocumented`, `derived or duplicated table`,
`simulated data`, `unreadable format`, `licence forbids redistribution`, `too large`,
`not the paper's data` (Tier D only). An object is in the registry or in the exclusions,
never both: the shard that would put it in the second file is refused. To re-file a misjudged
object, drop it first.

### `duplicates.csv`

Key `source_a`, `object_a`, `source_b`, `object_b`, the pair in frame order. The merge
writes a pair with `verdict` `flagged` when two registry objects have the same row count and
the same sorted column cardinalities; a `duplicates_<label>.csv` shard answers `same` or
`different`. On every merge the confirmed `same` groups collapse into the row(s) of their
first object in frame order (nlme before MEMSS and mlmRev, so a re-export folds into the
nlme row), whose `sources` lists every member; the other members' rows leave the registry.

### `dropped.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason`; the merge adds `tier`.
Merging a `dropped_<label>.csv` shard removes its objects from `registry.csv` and
`excluded.csv` so that a later shard can re-file them, which removes them from `dropped.csv`
again. A shard naming an object in neither file is refused. An object the loader no longer
enumerates (a re-pull changed the census) can never be re-filed: dropping it deletes its key
from every file, and the object that replaces it is filed under its own key (#14).

### `dimensions.csv`

Key `source`, `object`, `model_index`, `factor`, with `tier`. Every measure runs over the
rows with a measured response (a pharmacokinetic table's dosing rows are not observations).
Per grouping factor: `n_obs`, `n_groups`, `group_size_min`, `group_size_p10`,
`group_size_p50`, `group_size_p90`, `group_size_max` (observed sizes), `singleton_share`,
`cv` (population standard deviation over the mean) and `alpha`, the concentration of a
symmetric Dirichlet fitted by moment matching to the group-size proportions
(`Var(p) = (1 − 1/G) / (G (G α + 1))` solved for α; `inf` when balanced). Per row, repeated
on each of its factors: `n_factors`, `relation` (`single` / `nested` / `crossed` / `mixed`;
a pair is nested when every level of one factor lies in one level of the other, the row is
nested or crossed when every pair is, mixed otherwise), `d_doc` and `d_all` (continuous and
binary columns count 1, a categorical K − 1, an interaction the product; `d_doc` over the
documented model, `d_all` over every column of `columns.csv` plus the documented
interactions).

### `columns.csv`

Key `source`, `object`, `model_index`, `column`, with `tier`: every column that is not the
response, the trials, a grouping factor or ignored. `type` by one rule, in order: `ordered`
for a declared ordered categorical; `binary` for exactly two distinct values; `categorical`
with `K` levels for a column the file or `types` declares categorical, a string column, or an
integer column with at most 10 distinct values not declared continuous; `continuous`
otherwise. `level` is `group` when the column is constant within every group of some grouping
factor (`constant_within` lists those), `within` otherwise; `missing_share`; `in_model` is
`yes` for a covariate of the documented model.

### `quantiles.yaml`

Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95`, `max`, pooled, per tier and without
agridat. Per-factor axes count a dataset once per grouping factor, dataset axes (`n_obs`,
`n_grouping_factors`, `d_doc`, `d_all`) once per registry row, `K` once per categorical
covariate of a documented model. The covariate-type and level shares and the K distribution
run over the documented models' covariates; `implied_columns` is the expected design-column
count of a 9- and a 14-term model (the practice survey's p90 and p95 of terms) under that
categorical share and mean K − 1. `SUMMARY.md` ends each axis table with the practice
survey's p90 over the v1 families, read from `practice_quantiles.yaml` at merge time.

### What the merge checks

Header equal to the agent columns; required fields; allowed values; `model_index` from 1 to
3; the source in `sources.yaml` and the object in the source; every named column in the
loaded table (every part of an `a:b` term); each grouping factor with at least two levels and
a level with two or more rows; the response shows its declared type (`continuous` numeric,
`binary` two distinct values, `count` and `binomial` non-negative integers, `ordinal` at most
10 distinct values, `categorical` not a float column); a `binomial` row names integer
`trials` the response never exceeds; a column is a grouping factor or a covariate, never
both; `family` in its vocabulary; `documented_prior` only on a `published_model` `yes` row;
the licence of every registry source, the shard's and those merged earlier, in the lookup, and
a git or url source with a `licence:` key; the object is not in the rival file; a dropped
object is in one of the two. A failing
shard is refused with its offending rows printed and nothing written. Upsert on the key:
merging a shard twice changes nothing, a corrected shard replaces its rows. A file of an older
shape is read with the new columns blank, so a schema change is migrated by merging a shard
with the new header and no rows (`shards/registry_schema.csv`, #7). Every merge then
measures the whole registry again.

## Reading rules

Decided from the agents' `RULE GAP` notes and Alex's spot checks in the tickets named;
`prompts/read.md` carries the ones the agents needed. An example object follows each rule.

**Grouping factors**

- A grouping factor is a column whose levels index random effects as the source documents
  them. A random term on two columns is the composite `a:b`, built by the merge (Cultivation's
  split-plot `Block:Cult`; #20, #22); a row missing one part has no level (#24).
- A cluster that repeats within the table counts even when the source's own analysis treats
  the rows as independent (Tier O's patients and hospitals, ROS's rows, headache; #24, #25);
  so does a seasonal month or an observer with enough levels and rows per level (Squid's 12
  months, Sparrows' 10 observers; #25), the dyad where the book fits dyad effects and the
  pairs repeat (Crofoot; #25), a second design level the first reading missed (spruce's
  chamber, lawn's `machine:speed`; #22, #23).
- Not grouping factors: survey strata and waves a source models as fixed (CES11, WVS; #23);
  the coordinates of a field layout, which go in `ignore` (connolly.potato; #22), though the
  rows and columns of a Latin square are crossed blocking factors (OrchardSprays; #23); an
  observation-level random effect, whose column is ignored and whose term stays in the
  formula (#20); a one-way factor that classifies rather than clusters (singer's voice part,
  motorins' tariff factors; #23); a dyad with one row per pair (Monks; #25).
- An area factor is a grouping factor with many levels (LGAclaims' 13 divisions) and a
  covariate with a handful as the predictor of interest (infmort's four regions; #23).
- Matched pairs and other conditional-logistic designs take a random intercept on the pair
  (amlxray; #23), GEE fits one on the cluster (geepack; #22), a stochastic-frontier
  inefficiency term likewise (xtfrontier1; #24). Decided against for one row: travel2's
  single-level conditional logit is excluded (#25).
- The random structure as the paper describes it, not the deepest nesting term (Tier D:
  goodwin's stratum alone; #26), unless the deposited code fits another (meyel's combined
  `PopulationID:FamilyID:BoxID`, not the paper's three factors; #15). A
  genotype-by-environment interaction the page fits as random is the random term (salmon.bunt;
  #22).
- `ordered` declarations are for covariates only: nlme's `groupedData` orders subjects by
  their mean, no order a model uses (Orthodont; #20).

**Response**

- `response_type` is what the column holds, not the family fitted: egg totals `count`, 1–5
  ratings `ordinal` even under a linear fit, non-integer abundances `continuous`, a bounded
  score `count` for want of a trials column (eggprod, InstEval, staton, fcat; #22–#26). A
  transformed response names its raw column (#20); a documented normalised score is its own
  column (jsp_728; #25); an ordinal recoded off the table is its raw column (schiz; #25).
- A grouped table whose page documents no response is filed with the response a reader would
  model, at `low` under `RESPONSE INFERRED:` (MplsStops, worldcup; #23). In Tier D a raw
  table the paper fits nothing on is `response missing or undocumented` instead: the recorded
  model is a reported or deposited analysis (walker's cage tables; #26).
- A survival response stays `continuous`, its event indicator in `ignore` and in the formula
  as `Surv(time, event)` (brms kidney, catheter; #22, #24). A discrete-time hazard model on a
  person-period table has the event indicator as its response, the period among its
  covariates as one categorical `PERIOD` (cigarette, the ALDA rows; #25).
- Rows without a measured response (dosing events) are no observations (Phenobarb; #20).
- A multivariate table is one row per response up to three, the rest named in `notes` and
  listed in `ignore` (Soils, the Hong Kong spider taxa; #23, #25).

**Covariates and types**

- A nonlinear model's inputs (time, dose, concentration) are covariates; `formula` names the
  model class and its inputs in words under `NONLINEAR:` (Theoph, the IRT posteriors; #20,
  #22, #24).
- A numeric column the model wraps in `factor()` is declared `categorical` in `types`
  (yates.oats; #22). A pre-treatment baseline is a covariate, not an alternate response
  (dietox; #22). A column the model needs but the table lacks stays in the formula only
  (pisa2000's school mean; #24).
- An interaction the source fits is carried, otherwise the simpler reading stands (prt,
  mrk17_exp1; #22, #24); a reading from the source document beats a recalled one (the Stata
  manual rows, depression_pp; #24, #25); the final model's term set rather than the candidate
  set, per-subset fits and factorial contrasts named in the formula (Tier D; #26).
- Polynomial and derived terms on a column are not representable; the registry names the
  column once (muscatine's age polynomial; #22).

**Further model rows and published models**

- A further `model_index` row only when the response or the grouping differs; a nested
  simplification of the fixed effects is the same model (SASmixed ladders; #22); a variant
  whose extra level has one row per level, or whose grouping column is also a covariate, is
  not (melanoma, pig; #24). posteriordb's ladders on one dataset render the richest grouping
  (radon; #24).
- `published_model` is `yes` for a posterior, a Stan example, a textbook's worked example (an
  exploratory-only chapter counts; #25) or a documentation example that states the model
  (PyMC, bambi, the Stata manuals, MixedModels.jl docs); `no` for data used only in tests
  and throughout Tier O; `yes` throughout Tier D (#24, #26).

**Code against prose** (#15)

- Deposited code that produced the published results beats the paper's prose for formula,
  grouping and covariates; the prose goes to `notes` (meyel's combined term, kleisner's M0,
  valdebenito's `j_date`). An evident bug files the intended model, the bug in `notes`
  (voorspoels' `whichRandom` case); where a package version changed what a call fits, the
  published output decides (sequestro's four subject sds under brms 2.16.1). Code not
  deposited: the paper stands at `medium`.
- A fit on a subset stays on the whole object, the subset named in `notes` (szollosi's trial >
  40, ARM's survey 9158 and Minnesota).
- Uncorrelated random effects are `||` (posteriordb radon_all, ARM hiv and earnings). A fixed
  scale, a sum-to-zero constraint, a structured covariance or correlated location-scale terms
  keep the grouping factor and are named in the formula (PrussianHorses, rugby, state_wide,
  gumundsdottir's `(1 | c | NewID)`).
- The parts of a multivariate fit are rows per response, the formula naming the part (hubbard,
  rugby, sesame); a model with no brms family leaves `family` empty (external_pp's censored
  Gumbel).

**Exclusions**

- Only data the source states to be simulated, fictional or synthetic are `simulated data`
  (Stata's chicken); a page that only guesses "constructed" stays (SASmixed Animal; #22,
  #24). Aggregate responses on a real grouping stay at `low` (nass.sorghum; #22).
- `no grouping structure`: wide repeated-measures tables, whose unit is no column (nitrofen,
  the nlmeU twins; #22, #23); a designed experiment with replication but no replicate column
  (faraway rats; #23); a uniformity trial without a random term in its examples (#22); a
  table whose only candidate grouping is its coordinates (besag.checks; #22); a fixed-effects
  fit over a blocked design is rendered as the random-effects version at `low` unless the
  page says the replicate is no block (mead.germination; #22).
- `derived or duplicated table`: a subset with its own worked model (wages_small_pp; #25); a
  multiple-membership reshape (star_mm; #25); Stan data split into censored and uncensored
  arrays, read as the modal half (BUGS kidney; #24).
- Stan: pure GP, time-series, CAR and mixture posteriors are `no grouping structure`; a GP
  beside random intercepts stays (#24). ARM raw tables of an early chapter take a later
  chapter's multilevel fit at `medium` when the grouping column is in the table (#24).
- Tier D: a table of a deposit the paper merely cites, or of a preregistration, is `not the
  paper's data`; a dataset split into one file per coder, session or participant whose pooled
  table is in no file is `derived or duplicated table` (sievers_2020's 89 worksheets), while a
  split by study or experiment stays one row per file (#26).

## Record per tier

| tier | sources | objects | read | rows / datasets | exclusions | published | `high` | Alex's check |
|---|---|---|---|---|---|---|---|---|
| R | 22 packages | 1191 | 689 | 252 / 238 | 559 | 207 | 75 | 5 pilot rows; #22 20 rows, 14 stood; #23 20 rows, 17 stood |
| E | 84 | 543 | 474 | 99 / 96 | 361 | 94 | 57 | 20 rows with O: 11 stood, 9 changed |
| T | 65 | 534 | 480 | 244 / 227 | 285 | 136 | 44 | 20 rows: 9 stood, 11 changed |
| D | 60 papers | 993 | 766 | 104 / 69 | 917 | 104 | 62 | all 104 rows: 55 stood, 43 changed, 6 left |
| O | 34 tables | 34 | 34 | 13 / 12 | 20 | 0 | 0 | with E |

`read` is the objects passing the pre-screen and the cap (Tier D's include 320 filed by
script as a series). Beside the drawn rows Alex adjudicated the blind reading's open
disagreements, four to eight per tier.

**Tier R** (#20, #22, #23). Pilot: lme4, nlme and mlmRev by four Sonnet agents, five rows
read by Alex; `ordered` on grouping factors, dosing rows counted as observations and vague
nonlinear formulas became the first rules. Census of the remaining mixed-model packages by
six Opus agents: every MEMSS object is a re-export of its nlme namesake and SASmixed Semi2 is
nlme Oxide, so 39 rows folded. The spot check changed none of its eight `high` rows and six
of twelve `medium` and `low` ones (a missed design level, a coordinate taken for a group),
which made the blind second reading a standard step: 21 of the 31 census rows agreed, and
Alex adjudicated buntaran.wheat (zones fixed, genotype random beside location, replicate and
block), jansen.strawberry (ordinal category weighted by count over the plot), kirk.potato
(genotype only) and senshu.rice (locations in countries). The general packages by twelve
Opus agents: 160 of 628 objects pre-screened out, 308 of 362 exclusions `no grouping
structure`, as expected of one-row-per-unit tables; 16 of 17 flagged pairs the same dataset.
Blind reading: 65 of 77 rows agree. Spot check: 17 of 20 agreed; lawn gained
`machine:speed`, jsp became `school;school:class`, pvc, singer and motorins left. All 36
v0.5 datasets are in the registry. A case collision in the loader's Rscript dump (`CO2.rds`
overwritten by `co2.rds`) was fixed in 439c813 and `datasets` re-pulled.

**Tiers E and O** (#24). Loader first: Stan data dicts as the table of their
observation-length arrays, `.gz` and `.zip` wrappers, Arrow through `pyarrow` (added against
the spec's "no pyarrow", decided 2026-10-07), parquet, whitespace-aligned text, documentation
lookup for non-CRAN objects. Tier E: 474 objects read by eight Opus agents; the ARM chapters
repeat their data files, so 357 pairs were flagged, 340 byte-identical and answered by
script, 17 by one agent, all `same`; 21 Tier R rows now list a Tier E member. Tier O:
`net.py` on 2026-10-07 over 5025 OpenML, 689 UCI and 451 PMLB datasets gave 76 whole-name
hits (a first run matching substrings had 231), 30 drawn; 16 rows fell to 13 after the fold,
12 datasets with a documented cluster and none with a published model. Blind reading: 28 of
45 rows agree. Spot check: 11 stood, 9 changed, mostly from reading the Stata manual entries
more closely than the agents had: quinidine's PK regressions, pisa2000's school mean, the
survival indicators of catheter and time_to_attrition, independent slopes written `||` (pig,
radon_mn, employee), rm_anova2's error strata, sesame's second margin and `site:setting`,
the 17.6 ordered-categorical model with player-specific cutpoints; long_heating_data and
pancreatitis left. srrs2.dat keeps `state:county`: the object is the unsliced national file,
where `county` alone would merge namesake counties across states.

**Tier T** (#25). Loader first: SPSS `.sav` through `pyreadstat` and `.xls` through `xlrd`
(decided 2026-10-08), workbooks with several data sheets as `<file>!<sheet>`, `layout` for
headerless files, `.txt` as data unless named like documentation, `#` banners, SPSS labels on
a scale's extremes left numeric; `datasets.py` became the `datasets/` package. Fitzmaurice's
host sends an incomplete certificate chain Python refuses, so its 37 `.dta` and their `.txt`
descriptions were seeded into the cache by hand (sha256 checked by the loader as usual):

```
grep -oE 'fitzmaurice_[a-z0-9]+: \{kind: url, name: ([^,]+), pin: ([0-9a-f]+)' registry/sources.yaml \
  | sed -E 's/.*name: ([^,]+), pin: ([0-9a-f]+)/\1 \2/' | while read url pin; do
  mkdir -p registry/cache/url/$pin
  curl -sS -o registry/cache/url/$pin/$(basename $url) $url
  curl -sS -o registry/cache/url/$pin/$(basename $url .dta).txt ${url%.dta}.txt
done
```

480 objects read by nine Opus agents (Rabe-Hesketh's chapter do-files hold the book's
models); 50 of the 230 `no grouping structure` exclusions are wide tables, which is how
Fitzmaurice, Singer & Willett and Hox ship half their data; 26 flagged pairs, all `same`.
ROS fits no mixed model (every `.Rmd` grepped), so its 16 rows are repeating clusters. Blind
reading of 196 rows: 89 agree on all four fields; star_mm and ROS earnings left on both
readers' proposal. Spot check: 9 stood, 11 changed, mostly the formula to the chapter's
actual fit (electricity's random coefficients, yogurt's brand intercepts, OXBOYS's
polynomial, fev1's random slope); travel2, both NES objects, the three Storable tables and
CTT_V2 left.

**Tier D** (#26). Decided up front: one `url` entry per fetched file rather than one
on-the-fly zip per deposit (a pin on a zip would not survive a re-pull), `deposit_files.csv`
as the deposit-level record since a private deposit, a preprint or a bot wall yields no
object, Sonnet readers. `resolve.py` walks OSF projects with their components, Dryad
versions, Zenodo records and figshare articles, caches every answer and classifies files by
name (`data`, `documentation`, `script`, `other`); pull rules from the listing: 50 MB per
file (every larger file was a fitted model or draws) and no hidden folder. Dryad refuses
scripts on every route (401 and 403), so its 11 deposits came through Alex's browser into
`cache/dryad_raw/`, which `resolve.py --ingest` matches file by file against the API's md5.
One help page per deposit under `help/deposits/` (title, licence, the paper's text around
the link, its models as the practice survey filed them, the listing, README, codebook,
scripts). 226 objects had no frame (fitted brms and lme4 models saved as `.rds`), 320 of
jing_2020's per-participant series were filed by script, 424 objects read by nine Sonnet
agents and the 23 Dryad objects by one. The tier's finding (`SUMMARY.md`): 11 of 60 papers
reach no object (8 OSF links that are preprints, one restricted project, one user page, one
deposit too large), and within deposits the analysis table is the exception: raw
per-participant logs beside merged tables, Qualtrics exports one row per participant,
aggregates built in scripts, fitted models, stimulus lists. Alex's reading: the spot check
(20 rows) and the Dryad check (5) changed 13 rows, so he read the remaining 89 in three draws
(`shards/registry_tier_d_handdraw*.csv`). Of 104 rows 55 stood, 43 changed (the final
model's term set rather than the candidate set, per-subset fits and factorial contrasts
named, the random structure as described) and 6 left under the inferred-model rule. Four
verdicts were recorded rather than applied: a response type follows the column, and a date
string, a cue level that is no column and a derived indicator cannot be a covariate, a
grouping factor or a response; they stay in the formula.

## Known limits

- Three documented covariates measure as categorical with one level over the measured rows
  (stata_quinidine's `dose` and `interval`, Zuur Seedling's `Year`): the `K` 1 cell.
- Goldstein's Gcsemv.xls codes missing marks as `-1`, which the registry cannot declare;
  mlmRev's `Gcsemv` has proper NAs and a different shape, so the pair did not fold.
- Not read: ROS's 49 Congress `.asc` returns and `cows.dat` (a banner without `#`),
  liu_2022's workbook with a merged group header, walker_2021b's text sentinels among
  counts; a `.txt` data file of the PyMC examples not enumerated under #24's older rule.
- Not representable: polynomial and derived terms on a column, multiple membership.
- Base R's census was taken from R's namespace; the loader now enumerates the files of R's
  source tarball (#8), so 18 base R exclusions name an object no file is named after
  (`beaver1` and `beaver2` live in `beavers.R`, the `state.*` vectors in `state.R`) and 48
  are listed without a table (time series, arrays, `iris`'s `gl(labels =)`). No registry row
  is among them.

## Closing (#27)

Closed on 2026-10-08 with every tier read and hand-checked as recorded above: 712 registry
rows over 642 datasets and 940 grouping factors; 2142 exclusions; `duplicates.csv` holds no
open flag. `SUMMARY.md` puts the pooled and per-tier quantiles of every axis beside the
practice survey's p90; the edges themselves wait for the `/grill-me` outcome session. The CI
test `tests/surveys/test_dimension_quantiles.py` loads `quantiles.yaml` as data and asserts
its axes, quantile keys, tiers, imbalance block, K distribution, shares and the tier
minimums, and that every row of `v05_datasets.csv` is a registry key, a member of a registry
row's `sources` (MEMSS MathAchieve in nlme's row; base R's Theoph, Orange and Indometh in
MEMSS's) or an exclusion.

## Registry columns and verification (#6)

**Readers without R** (#8, 2026-10-09). The 34 registry objects that loaded through the
Rscript dump and have a Python reader now load without R (ADR 0003): agridat's 27
`data/*.txt` files (28 rows) through a utils::data() reader (read.table's header,
whitespace, quote and `NA` rules, strings as factors with sorted levels), base R's 7
`data/*.R` files through the deparse reader (`src/mixedbench/datasets/deparse.py`, the subset
of R those seven files use), fetched from R 4.6.1's source tarball with its sha256 instead of
dumped from R's namespace. Each new frame was compared once with the Rscript dump's on
columns, dtype kinds, levels, values and the ordered flag: 33 identical; lillemo.wheat's
`env` holds the same values but sorts its levels in codepoint order (`BT06` before `Ba04`),
where R's ICU collation puts `Ba04` first; its first level, the reference of treatment
coding, is `Aa03` either way. The re-merge `shards/registry_readers.csv` set their `reader`
to `pandas` and `deparse` and gave base R's manifest rows a digest and size; no measure
changed. The merge now replaces a re-merged row where it stands rather than moving it to the
end. geepack's muscatine and plonsky_2019_osf's dd1, which librdata rejects, still go through
R until #9.

**The Rscript route leaves** (#9, 2026-10-09). The loader calls no R: an R file librdata
rejects goes to the pure-Python `rdata`, reader `rdata`, in place of the ticket's `none`
(ADR 0003's amendment). muscatine, dd and dd1 came out identical to the Rscript dump's
frames; the re-merge `shards/registry_rdata.csv` changed only the two rows' `reader`. The
deparse reader no longer takes data.frame()'s `row.names =` for a column (LifeCycleSavings,
randu). The re-pull without R has 3285 census objects (3295 before): 137 `file` labels that
named a dump (`rds/...`) now name the download, about 60 base R objects outside the deparse
subset (time series, matrices, iris) are no frame and were excluded already, and 19
`excluded.csv` keys, two unread pymc_examples objects and stan_arm's `ideo2.dat` wait for #14.
The re-pulled `shards/excluded_prescreen.csv` is not merged, since it would overwrite the
readers' reasons with `unreadable format`. A cache built before #9 holds the dump's `rds/`
folders, which enumeration now lists as objects; delete them.

**The census and its tables agree** (#14, 2026-10-09). The text reader read a
whitespace-separated file with pandas' python engine, which ignores quotes under a regex
separator, so R's `write.table` output with a quoted string holding a space (stan_arm's
`ideo2.dat`: `"NEW HAM"`) did not parse and quoted names kept their quotes; the C engine
honours quotes as read.table does. `ideo2.dat` reads again at 10268 × 22 (its exclusion stands),
ros's `hibbs.dat` and `hdi.dat` read for the first time, and quoted column names in 17 ARM, ROS
and Diggle files lose their quotes; no registry object changed. ARM's `candidate_effects.dat`
and `unemployment.dat` changed column counts at #8 and stay excluded for their reasons. The
re-pull of Tiers E and T rewrote `candidates.csv` and the pre-screen shard (still not merged).
`shards/dropped_census_repull.csv` deleted the 19 stale keys (18 base R objects of multi-object
files, sequestro_2024_osf_5's `gmmMix2`), which the merge now does for any dropped object
the loader no longer enumerates; `shards/excluded_census_repull.csv` filed their
replacements (`beavers`, `state`, `UKLungDeaths`, `Harman23.cor`, `Harman74.cor`,
`ability.cov`, `EXP2_3_LMM`, all no frame), the two pymc_examples objects no reader had seen
(`Guber1999data.txt`, one row per state; `hurdat2-...txt`, HURDAT2's storm blocks, no table)
and re-filed `hibbs.dat` and `hdi.dat`. Exclusions 2142 → 2132. `tests/test_census.py` asserts
both directions: every exclusion is a census object, every uncapped census object is a registry
row, an exclusion or a confirmed duplicate of either.

**Family and prior** (#10, 2026-10-09). `verify.py scan` searches every registry row's
`notes`, `formula` and help page, and once each the 38 deposit pages Tier D help pages point
at, for family keywords (negative binomial, probit, cloglog, Weibull, gamma, lognormal,
zero-inflated, hurdle, beta regression) and prior keywords (`prior`, `set_prior`, Stan and BUGS
sampling statements): 106 row hits over 48 rows and 1106 deposit hits, most of them `prior` in
deposit code (`scan_hits.csv`). Snippets alone could not settle Tier D, whose help pages only
point at the deposit, nor the Bayesian Tiers E and T, whose Stan files, notebooks and book code
sit in the cached repositories, not the help pages; so the hand look read the 48 hit rows'
snippets, every Tier D row's model call in its deposit code and the 74 rows of posteriordb,
stan_arm, pymc_examples, bambi, rethinking and ros in their cached code: 214 rows, agents
drafting from the code, Alex deciding. Outcome (`shards/registry_family_prior.csv`): `family`
on 45 rows (12 also with a prior), `documented_prior` alone on 61; the other 108 rows stay on
the rule with no stated prior. Rules taken: a prior is the one passed to the row's model call,
trimmed to the row's response in a multivariate fit; package defaults, priors only in a supplement
not on the page and priors stated in words without parameters (arriero, kappers) are empty;
priors in deposit files the page lists but does not show (verberk's GitHub zip, valdebenito's R
file) are filed; an unbounded Stan scale without a sampling statement is written as such. Eight
values joined the vocabulary: `bernoulli(cloglog)` (Stata `mecloglog`, meyel's glmer and brms
fits), `Gamma(identity)` (sequestro), `zero_inflated_beta` (liutu), `student` (johannes),
`gaussian` (Gaussian fits to counts and ordinal ratings: hubbard, king, berweger, naranowicz,
two stan_arm rows), `acat` (posteriordb's rating-scale and partial-credit IRT models), `weibull`
and `cox` (survival rows, censoring in `notes`). The three Zuur zero-inflation rows with a
published model (SeaGrass, Turcoparasitos, Spiders) stay on the rule: the book is not open and
no source read states their family. Reading errors the code turned up in other columns, and the
Windows CI failure, are #15.

**Code read** (#15, 2026-10-09). A `.gitattributes` keeps test fixtures' bytes (`-text`): a
Windows checkout had rewritten the line endings of the ASCII `fits.rda`, whose magic then did
not parse; CI is green on all three systems. The readings #10's code read questioned were
checked at the source by four agents, Alex deciding; `shards/registry_code_read.csv` replaced
54 rows and added 3 (registry 712 → 715), under the rules "Code against prose" above.
Verdicts per finding:

- szollosi_2019_osf_2 exp2.csv: corrected; the Rmd's glmer (L313, L332) has no `block:condition`,
  `condition` is categorical, the fit is on trial > 40 and conditions 1 and 3.
- meyel_2026_dryad: II.1, II.2 #2 and III and IV corrected to the code's combined terms
  (`PopulationID:FamilyID:BoxID`, `PopulationID:FamilyID` for II.2, as II.2 #1 since the
  2026-10-08 spot check), the Gamma shift `+ 0.001` (L287; the paper's `+ 0.01` in notes); I.1
  and I.2 stand.
- sequestro_2024_osf_{2,11,12,16}: stands; current brms codes `(0 + Intercept + condition * RTc
  | ppid)` with five sds, but the supplement's tables (brms 2.16.1) report four, the filed
  `(1 + condition * RT | ppid)`; notes carry the caveat and the trial filters.
- kleisner_2026_osf #1–3: corrected; script 05 fits M0, iid correlated effects by
  `Nationality` (one-to-one with POPULATION); the linguistic covariance of M1–M3 left the formula.
- koczynska_2026_osf_{48,49}: corrected; `models1/2` are not deposited, but the deposited fit2
  processing script predicts from lagged controls, so `gdppc_lag1`, `gdpgrowth_lag1`,
  `unemp_lag1`; `medium`, the random slopes resting on the paper's Eq. 3.
- voorspoels_2015_osf_3 d: corrected; the intended model with `subjectID:premset` and
  `item:premset`; as deposited, `whichRandom = c('ITEM','SS')` matches no column and the fit
  has no random effects (notes). The `premset:sampling` interaction stays as the 2026-10-08
  hand draw kept it, though the code's Bayes factor prefers the model without it.
- lagisz_2020_osf_3 #1–2: corrected; the scripts exist (OSF's GitHub add-on lists them at 0
  bytes); crossed `ScalePoint`, `ArticleID`, `ExperimentID`, `EffectID`, row 2 with the
  phylogeny on `Species_Latin`; `high`.
- valdebenito_2020_dryad_2 #1–3: corrected; the deposited code's `random = ~site + j_date`,
  `j_date` the day of year (72 levels), `date` to `ignore`; `high`.
- johannes_2021b_osf_6 #3: corrected in notes; predictors centred, not standardised.
- gumundsdottir_2026_osf*: corrected; `(1 | c | NewID)` in location and scale; _6's slope
  variable `time` built from `wave` (0, 1, 2, 3, 6), `wave=continuous`.
- naranowicz_2024_osf_2 #1–2: stands, the finding was wrong; the deposited script is complete
  (2466 lines, its checksum the deposit's) and L948 and L1353 are the filed formulas.
- hubbard_2023_osf_2 #1–3: stands in its columns; the formula names each row's part of the
  multivariate fits `p1a`, `p1b`, `p1c`, which share no residual correlation or random effect.
- posteriordb radon_all: corrected to `||`. state_wide_presidential_votes: corrected; the state
  scale by region, year GPs by region and state, 17 variances on one gamma × Dirichlet budget.
  fims_Aus_Jpn_irt: corrected to the slope-intercept form `alpha*theta - beta`.
- stan_arm: polls.dta now renders the script's M2 (`age`, `edu`, `age:edu`, `state`; region and
  the previous vote built in the script, formula only) on survey 9158; srrs2.dat's formula is
  the Minnesota fit on county, the grouping `state:county` as #24 decided; allvar.csv is
  `hiv.stan` on `treatmnt == 1` (`visage` alone); sesame.dta and sesame.data.json are the
  structural bivariate fit (`postlet ~ regular`, `regular ~ encour`), sesame.dta #2 added,
  `pretest` dropped (from `sesame_street2`, whose fit is commented out); Ch.21 radon.data.json
  adds `u`; hiv.data.json and earnings.data.json are `||`; pilots.dat's formula names the
  Gaussian on 40 cell proportions, `low`; Ch.19 pilots.data.json stands.
- pymc_examples: item_response_nba.csv keeps `decision` (the code's `foul_called` is no
  column), the recode in the formula; external_pp.csv is the notebook's final m7 with `FEMALE`
  and `||`, `family` empty for the censored Gumbel; rugby.csv is the home part of a joint
  Poisson fit with sum-to-zero team effects, the away part added as #2; cracker_choice_short.csv
  names person effects per alternative at a fixed sd 0.1.
- rethinking: Primates301.csv #1 is the Rd's Poisson social-learning model with a GP over
  species (`published_model` `yes`), #2 the book's m14.11 brain-size model added (both on
  `genus`, `low`); kl_dyads #1–2 are m14.7 without `dlndist`, `dass` or offset; PrussianHorses.csv
  is the Rd's m0, `published_model` `yes`, `high`.

Left open: valdebenito's MCMCglmm `categorical` fits with residual variance fixed at 1 (a logit
with an observation-level term) keep `family` blank; fims' item parameters have fixed priors
and no estimated scale, `ii` stays a grouping factor.

**Hand sample, batch 1** (#11, 2026-10-09). `verify.py draw` wrote `sample.csv`: seed 0, 100
rows of Tiers R, E, T and O (Tier D left out, Alex read all of it), stratified by tier ×
confidence with largest-remainder allocation and at least one row per stratum, four batches of
25 in draw order; a further run appends one batch of 25 with the next seed and no floor.
`verify.py handoff --batch k` renders a batch with the source's page and download URLs, the
reading and the help page. Alex checked batch 1 at the source; `shards/registry_hand_sample_1.csv`
replaced its 25 rows (registry 715). 8 rows stood in the compared fields (5 of them with notes
or confidence corrected), 17 were corrected: `published_model` and `formula` 11 each,
`covariates` 7, `interactions` 2, `response` 2, `grouping_factors` 1. Verdicts per row:

- stand: alda medication_pp; rethinking PrussianHorses (notes: the Rd exists, the fixed scales
  are priors), NWOGrants (`low`); mixedmodels_jl kb07 (the model is the rank-deficiency
  page's); languageR lexdec (RT is already a log); stan_arm allvar (the script's J = 84 and
  indexing slips in notes); pmlb_apnea1 (`low`, target holds cell frequencies); lme4
  grouseticks (INDEX stays out of `grouping_factors` under #20).
- `published_model` `no`, the formula kept as proposed: fitzmaurice melanoma (`low`; the paper's
  model is Europe-wide, three-level), agridat tai.potato, nlme Cefamandole (`low`; the Rd fits
  `nlsList`, no random effects) and Tetracycline2, SASmixed WaferTypes and Animal (`low`; the
  pages only call `str`), hox estrlong (`log(estrmeas)` in the formula; `log_estr` is log10, the
  narrative's natural log left unresolved).
- corrected to a located source: rabe_hesketh antibiotics (GLLAMM article Table 3, nominal logit
  with category-specific intercepts by doctor and hospital, `Wrdiag` added; `high`), aggression
  (MLMUS4 exercise 10.4, `I(y > 0)` on `person` alone; `high`) and epilep (SABRE 13.3, `v4`
  replaces `visit`; `high`); snijders_bosker 17A (ch17.r, Table 17.2; the country-centred and
  country-mean terms are no columns, formula only; `high`); hox MetaResp (chapter 6 Eq. 6.21,
  binomial logit with mode random slopes, `respisrr` and `mode:year` added; `high`) and
  CurranLong (the PanelModeling chapter's reading growth model, `read` the response, `anti` to
  `ignore`); ros incentives_full (Gelman, Stevens & Chan 2003 Model III; `high`); gamlss.data
  rent99 (Fahrmeir et al. Eq. 9.8, `rentsqm` the response, district a kriged spatial effect;
  `high`); brms loss (theta and omega estimated, not fixed); stan_bugs schools (`I(LRT^2)` and
  the residual variance model in the formula).

Decisions taken: a `published_model` `no` row keeps its proposed formula (the merge requires
one); a response holding proportions stays `continuous`, its binomial denominator named in the
formula (MetaResp); a float-coded nominal response stays `ordinal`, the merge refusing a float
column as `categorical` (antibiotics). Left open as `RULE GAP:` in notes: the documented
binomial (MetaResp), nominal (antibiotics) and Bernoulli-on-a-recode (aggression) fits have no
`family` value.

**Hand sample, batch 2** (#12, 2026-10-09). Alex checked batch 2 at the source;
`shards/registry_hand_sample_2.csv` replaced its 25 rows (registry 715); each reason is appended
to notes, notes contradicting a correction are trimmed, and wine, KosteckiDillon and playactivity
rise to `high` (OME stays `medium`, the nonlinear cap). 14 rows stood, 11 were corrected: `formula` 11,
`covariates` 4, `published_model` 2, `response_type` 2, `response` 1, `grouping_factors` 1,
`interactions` 1. Agreement: response 24/25, grouping factors 24/25. Verdicts per row:

- stand: agridat gomez.nonnormal2, archbold.apple, yates.oats #2; faraway worldcup; HLMdiag
  wages; gamlss.data respInf; languageR english; nlme Machines; rabe_hesketh bladder, headache;
  zuur_zim Beavers2; mlmRev Mmmec; alda congress_pp, tolerance_pp.
- formula only: glmmTMB Salamanders (zipm3's `spp * mined` in the zero-inflation part too);
  pymc_examples radon (`log(activity + 0.1)`, the notebook's log_radon, and `||`); nlme
  Phenobarb (ApgarInd on volume only, diagonal random effects, ch06.R); zuur_mixed RIKZ
  (Exposure 8 and 10 pooled against 11); faraway choccake (`factor(temp)`).
- corrected to a located source: rabe_hesketh wine (MLMUS3 exercise 10.9, binary `bitter`
  additive in temp and contact, `published_model` `yes`; `bitterness` moved to `ignore`);
  carData KosteckiDillon (Fox's appendix final model, treatment and `sqrt(posttreat)` derived
  from `time`, random in both); MASS OME (grouped by `ID:Age`, the page's UID; OME only in the
  second-stage regression); goldstein_msm playactivity (Table 9.3 analysis A, continuous log
  duration with activity-specific child effects, not multinomial); hox thaieduc (chapter 6
  uses `SEX` alone).
- `published_model` `no`: rabe_hesketh crime (ch5.do fits county fixed effects; the
  random-intercept rendering is inferred, `log(crmrte)` and `factor(year)` in the formula).

**Hand sample, batch 3** (#12, 2026-10-09). Alex checked batch 3 at the source;
`shards/registry_hand_sample_3.csv` replaced 24 rows and hox SocsLong.sav was re-filed as
`simulated data` (`dropped_hand_sample_3.csv`, then `excluded_hand_sample_3.csv`; registry 714).
Notes as in batch 2: reasons appended, contradicted passages trimmed, coursework #2 and autism
raised to `high`. 15 rows stood (schooleffects with its notes trimmed), 9 were corrected:
`formula` 6, `published_model` 3, `covariates` 1, `interactions` 1, `response_type` 1; 1 left the
registry. Agreement: response 25/25, grouping factors 25/25. The agreement step (#13) meets a
sampled row no longer in the registry. Verdicts per row:

- stand: stata_toenail; medicaldata indometh, opt (the linear rendering is no published survival
  analysis); agridat cox.stripsplit; stan_arm cty.dat, hiv.data.json; stata_pefrate;
  rabe_hesketh schooleffects (a cohort column alone is no grouping factor), bp, homeless
  (`housing` three ordered values, the stored product `s8lint` a covariate); rethinking Trolley;
  faraway eggprod; languageR warlpiri; nlmeU fcat (the chapter 19 script fits the crossed
  intercepts, no native trials column); brms inhaler.
- formula only: zuur_mixed DeerEcervi (`I(Ecervi > 0)`, the Bernoulli presence model, the raw
  column kept); stata_nlswork3 (metobit with `ul(1.9)`); HLMdiag autism (the book's final
  chapter 6 model, no random intercept, no quadratic-by-group term); agridat
  burgueno.unreplicated (m2's AR1(col) × AR1(row) residual).
- corrected to a located source: rabe_hesketh coursework #2 (the review's bivariate model,
  `published_model` `yes`); snijders_bosker sheet 16 #2 (ch16.r, Table 16.2: `iq_verb * ses` and
  the school means `sch_iqv * sch_ses`); mlmRev Chem97 #2 (`score` `ordinal`, ordered A-level
  grades).
- `published_model` `no`: agridat nass.sorghum (the help fits Illinois corn); cmm_ilea567
  (the seven-predictor model is not in the source).
- excluded: hox SocsLong.sav, `simulated data` per the author's data appendix (DataStories.pdf).
