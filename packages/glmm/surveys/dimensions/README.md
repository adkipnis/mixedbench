# Dimension survey — public grouped datasets

The lower edges, imbalance, factor-level distribution and covariate mix of real grouped data,
and the pool the v1 real-data test sets draw from. Spec: issue #14; tickets #15–#27. The
package's loader (`metabeta.glmm.datasets`, research extra) reads every source; the survey
scripts here own the file contract. The practice survey (`../practice/`) is the model;
nothing is imported across surveys. Results: [`SUMMARY.md`](SUMMARY.md), regenerated on every merge.

## Files

| file | written by | content |
|---|---|---|
| `sources.yaml` | hand (#19) and discovery (#21) | the frame: tiers of pinned sources, cap, seed, dropped candidates, the Tier O keyword net, see below |
| `deposits.csv` | `deposits.py` | Tier D: the 60 seeded, stratified draws of the practice survey's deposit-naming papers, see below |
| `candidates.csv` | `pull.py` | every enumerated data object with its counts, see below |
| `help/`, `cache/` | `pull.py`, loader | untracked: one help page per kept object for the agents, the table's dtypes and first rows appended; downloads and extracted trees |
| `shards/<table>_<label>.csv` | agents; `pull.py` writes `excluded_prescreen.csv` | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped` |
| `registry.csv` | `merge.py` | one row per dataset and documented model, at most three per object |
| `excluded.csv` | `merge.py` | every screened-out object with a categorical reason |
| `duplicates.csv` | `merge.py` | candidate pairs the merge flagged and the verdicts agents returned |
| `dropped.csv` | `merge.py` | objects taken out of the registry and the exclusions, awaiting a re-filing shard |
| `dimensions.csv` | `merge.py` via `measure.py` | one row per registry row and grouping factor, see below |
| `columns.csv` | `merge.py` via `measure.py` | one row per registry row and covariate column, see below |
| `quantiles.yaml`, `SUMMARY.md` | `merge.py` via `summarise.py` | every axis pooled, per tier and without agridat; the summary from `SUMMARY.template.md`, which holds no digit |
| `prompts/discover.md`, `prompts/read.md` | | what the discovery agent and a reading agent get and write |
| `schema.py`, `sources.py` | | file contract and allowed values; the frame read from `sources.yaml` |
| `measure.py`, `summarise.py` | | what the merge measures from a loaded table, and how it reports it |
| `tests/` | | pytest, run by hand, not in CI: `uv run pytest packages/glmm/surveys/dimensions` |

Agents read documentation and write shards; `merge.py` is the only writer of the canonical CSVs.

```
uv run python packages/glmm/surveys/dimensions/deposits.py
uv run python packages/glmm/surveys/dimensions/pull.py
uv run python packages/glmm/surveys/dimensions/merge.py packages/glmm/surveys/dimensions/shards/<shard>.csv [--root DIR]
```

## `sources.yaml`

Tiers in frame order `R` (CRAN package data), `E` (Python and Stan ecosystem examples), `T`
(textbook companions), `D` (data deposits of the practice survey's papers), `O` (open tabular
repositories). Under each tier, one entry per source keyed by its **label**, the `source` every
shard row names:

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

`kind` ∈ `cran` / `git` / `url` as the loader's `Source`; `name` defaults to the label (a CRAN
package name); `pin` is the CRAN version, git revision or the file's sha256 (base R's
`datasets` is pinned to the R version that dumps it); `checksum` (optional) pins a CRAN or
git archive; `path` (optional) narrows a git or url tree. `cap` (optional, per entry or top-level as a
default) is the most objects read from one source, so that no single collection dominates: a
source with more objects passing the pre-screen (below) keeps a draw of `cap` of them made with
`random.Random(seed)`, `seed` top-level, over their sorted names. Only agridat (about 390 field
trials, else 38% of the pool) is capped; ten Tier R packages hold more than 40 objects, so a cap
for all would have discarded grouped tables of faraway and MASS at random (decided 2026-10-07).
`licence` (optional) is the collection's licence as its LICENSE file, readme or DESCRIPTION
states it, or `not stated` once the collection was read and carries none; an absent key means
nobody has looked yet. The survey redistributes no data, so the field records terms of use to
respect and sources to cite, not permission to publish. #21 filled it where GitHub detects a
LICENSE file and for the CRAN package of Tier T; #24 and #25 fill the rest from the fetched
tree (Tier R from DESCRIPTION), #26 the Tier D entries from the repository APIs (Dryad is CC0
throughout), #24 the Tier O hits from OpenML's and UCI's licence fields.
`dropped` lists every candidate source the discovery step (#21) considered and left out, with
the reason. `nets` is the Tier O keyword net (#24): the repositories, the column-name keywords
a table must document as its clustering column, and the cap over the three repositories
together; it is a record of a search, not a source, so `readFrame` leaves it alone and #24
adds the resolved hits as `url` entries under `O`.

Tier R (#19) is a census of two package groups at the CRAN versions of 2026-10-07. Mixed-model
packages: lme4, nlme, mlmRev, MEMSS, glmmTMB, brms, GLMMadaptive, nlmeU, SASmixed, HLMdiag,
ordinal, geepack, agridat. General data packages with grouped tables: MASS, carData, lattice,
HSAUR3, faraway, boot, gamlss.data, medicaldata, languageR, and base R's `datasets`.
GLMMadaptive ships no data objects and so has no row in `candidates.csv`.

Tiers E and T (#21) come from the discovery step: one Opus agent with web search ran
`prompts/discover.md` over the spec's fixed list and about twenty further queries; every
collection it considered is a kept entry or a `dropped` row. Kept URLs were fetched once more
with the loader's user agent and pinned by script (sha256 of the file, HEAD revision of the
repository on 2026-10-07). Tier E: posteriordb, the Stan example models as two entries (`ARM`
and `bugs_examples`; no BDA folder exists), pingouin, the PyMC examples' data, bambi's thirteen
figshare files (bambi downloads them at load time; its own registry holds the checksums, which
the download confirmed), and the forty datasets of Stata's [ME] manual, which the agent added.
Tier T: Hox (git), Snijders & Bosker, Goldstein's third edition and its partnership data, nine
teaching datasets of the Bristol Centre for Multilevel Modelling, Rabe-Hesketh & Skrondal,
Singer & Willett (UCLA mirror), and three Zuur et al. books (the agent had missed Zuur; found
by hand on highstat.com). Gelman's and West's author sites answer 403 to the loader as well as
to the agent, so ARM data come through `stan_arm` and `ros`, West, Welch & Galecki through
their CRAN package `WWGbook`.

A second pass by hand on 2026-10-07 asked which collections a reviewer would miss and added
seven (every URL fetched and pinned the same way). Tier E: the 25 further datasets of Stata's
[XT] panel-data manual, and MixedModels.jl's dataset artifact (one tar.gz of 17 Arrow files on
OSF; the agent had dropped it as an lme4 mirror, but kb07, mrk17_exp1, ml1m, oxide and d3 are
its own). Tier T: McElreath's *Statistical Rethinking* (`rethinking` is GitHub-only, so not
Tier R; 49 semicolon-separated csv), Fitzmaurice, Laird & Ware's *Applied Longitudinal
Analysis* (one `.dta` per dataset, 36 of them, the description beside each as `<name>.txt`),
Gelman, Hill & Vehtari's *Regression and Other Stories* (`ROS-Examples`, 106 data files under
`<example>/data`, a 225 MB repository that overlaps `stan_arm`), `WWGbook`, and the seven
APTS course files of Diggle (three longitudinal). Recorded as dropped in that pass: statsmodels
(only two panel tables), Hedeker & Gibbons (host down), Verbeke & Molenberghs (Springer extras
not locatable), Littell et al. (`SASmixed`, Tier R), Kruschke (scripts). For the pulls of #24
and #25 the loader still lacks readers for SPSS `.sav` (Hox; the spec says ask before adding
`pyreadstat`), old Excel `.xls` (Goldstein, Zuur), fixed-width `.dat` with an `.asc` layout
(Bristol CMM), Stan data json (a dict of arrays, not a table), R dumps outside a CRAN `data/`
folder (Stan examples), gzipped TSV (PMLB), semicolon-separated csv (`rethinking`) and Arrow
inside a tar.gz whose URL carries no suffix (`mixedmodels_jl`, `pyarrow` is a dependency to
ask about); each is that ticket's decision, read or `unreadable format`.

Tier O (#21) starts with v0.5's four PMLB tables (`analcatdata` apnea 1 and 2 by subject,
boxing 1 and 2 by judge; Simonoff, *Analyzing Categorical Data*, 2003), pinned at PMLB's commit of
2026-10-07. PMLB keeps its data in Git LFS: the raw URL at a commit returns an LFS pointer,
the `media.githubusercontent.com` URL the file, whose sha256 is the LFS object id. The files are
gzipped TSV, which the loader's readers do not open yet, and PMLB's `metadata.yaml` for them is
empty; both are #24's to settle before the Tier O pull. Tier D entries are added by #26 from
`deposits.csv`, labelled `<paper_id>_<repository>`.

## `deposits.csv`

Key `paper_id`; written whole by `deposits.py`. The Tier D frame is every paper of the practice
survey's `papers.csv` whose text (`../practice/texts/<paper_id>.txt`) names a Dryad, OSF, Zenodo
or figshare deposit by DOI or URL, found by one regex and normalised to one identifier per
deposit (the OSF five-character id, `zenodo.org/records/<n>`, DOIs in lower case). The match is
mechanical and therefore also catches preregistrations and deposits a paper merely cites; #26
excludes those with their reason and never replaces them, as the spec says, and that loss is
a Tier D finding. Per stratum, 15 papers are drawn with `random.Random(seed).sample` over the
sorted ids (seed 0), so rerunning the script reproduces the file byte for byte. One row per
drawn paper: `stratum`, `repository` and `url` as `;`-lists over the paper's distinct deposits
in text order, `context` (the text window around each match, joined with ` || `, so #26 sees
which link is the data), `seed`, `n_frame` (deposit-naming papers of the stratum). Equal
cells rather than proportional ones, because the tier exists to compare deposited data with
package data and every stratum should stay readable (decided 2026-10-07).

## `candidates.csv`

Key `source`, `object`; written whole by `pull.py` on every run, in frame order. Per
enumerated data object: `tier`, `source`, `pin`, `object`, `file` (the data file inside the
source tree), `n_rows`, `n_cols` (blank where the loader cannot make a DataFrame of the
object, a table of more than two dimensions), the column counts by dtype `n_numeric`,
`n_categorical`, `n_string`, `n_other` (bool, datetime), `reader` (the loader's route,
`pyreadr` / `rscript` / `pandas`), `screen` and `capped`.

`screen` is the verdict of a mechanical pre-screen on what a grouped table needs before an
agent reads its documentation, conservative by design: `no frame` (the loader cannot make a
DataFrame of the object), `under 3 rows` (two groups, one with two observations), `one column`
(a response and a grouping factor), `no repeated column` (no column whose values could index
groups: not fractional, since R stores integer codes as doubles, two or more distinct values,
some value repeated), else `pass`. On Tier R it discards 164 of 1190 objects, time series,
all-continuous tables and one-row-per-study tables among them. The pull writes the discards as
the shard `shards/excluded_prescreen.csv` (`no frame` under `unreadable format`, the rest under
`no grouping structure`, the verdict as `detail`), which the merge takes like any agent shard.
`capped` is `yes` for the passing objects a source's cap left out. Screened-out and capped
objects stay listed as the screening denominator; agents read the `pass`, `no` rows, whose
help pages are at `help/<source>/<object>.txt`, rewritten per source on every run.

## `registry.csv`

Key `source`, `object`, `model_index`. Agent columns, in order:

| column | content |
|---|---|
| `source` | label in `sources.yaml` |
| `object` | the data object as the loader enumerates it: an R object name, or a file path inside a git or url tree |
| `model_index` | 1 for the documented model, 2 and 3 for further documented models; never more |
| `response` | column name of the response |
| `response_type` | `continuous` / `binary` / `count` / `binomial` / `ordinal` / `categorical`; what the response column holds, not the family fitted to it |
| `trials` | column name of the trials for a `binomial` response, blank otherwise |
| `grouping_factors` | `;`-list of the columns whose levels index random effects, as documented; a random term on the combination of two columns (lme4's `(1\|Block:Variety)`, the whole plots of a split-plot) is `Block:Variety`, which the merge builds from its parts |
| `covariates` | `;`-list of the documented model's covariate columns (main effects) |
| `interactions` | `;`-list of `a:b` terms, every part a column name |
| `ignore` | `;`-list of columns no model should use: row ids, weights, alternate responses |
| `types` | `;`-list of `column=categorical`, `column=ordered` or `column=continuous` declarations for formats without column types (delimited text, Excel), and `ordered` for an R ordered factor, which `pyreadr` reads as unordered, covariates only (a grouping factor stored ordered by nlme's `groupedData` is a nominal id); blank otherwise |
| `formula` | the documented model verbatim (lme4 syntax where the source gives one); a nonlinear mixed model in words, naming the model class and its inputs (`conc ~ one-compartment IV PK model with first-order elimination (dose, time); subject-specific clearance and volume`), the row kept for its grouping |
| `published_model` | `yes` when a published model specification exists (posteriordb, Stan example, textbook); else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other`; reporting only |
| `confidence` | `high` / `medium` / `low` |
| `notes` | free text: the documentation read, cases the prompt does not settle (`RULE GAP:`); `NONLINEAR:` opens the note of a nonlinear mixed model, `RESPONSE INFERRED:` the note of a row whose page documents no response |

Script columns the merge fills: `tier` (from `sources.yaml`), `sources` (`source:object` of
every confirmed duplicate folded into the row, the row's own first), `reader` (the loader's
route: `pyreadr`, `rscript` or `pandas`).

## `excluded.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason`, `detail`; the merge adds
`tier`. `reason` ∈ `no grouping structure` / `time series without replication` /
`fewer than two groups` / `response missing or undocumented` / `derived or duplicated table` /
`simulated data` / `unreadable format` / `licence forbids redistribution` / `too large`. An object is in the
registry or in the exclusions, never both: the shard that would put it in the second file is
refused. To re-file a misjudged object, drop it first (below).

## `duplicates.csv`

Key `source_a`, `object_a`, `source_b`, `object_b`, the pair written in frame order (tier,
then the source's place in `sources.yaml`) whichever way a shard wrote it. Columns `verdict`
and `notes`. The merge writes a pair with `verdict` `flagged` when two registry objects have
the same row count and the same sorted column cardinalities; an agent answers through a
`duplicates_<label>.csv` shard with `same` or `different`. On every merge the confirmed `same`
groups collapse into the row(s) of their first object in frame order (nlme before MEMSS and
mlmRev, so a re-export folds into the nlme row), whose `sources` lists every member of the
group; the other members' rows leave the registry, and re-merging their shard folds them again.

## `dropped.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason` (free text); the merge adds
`tier`. Merging a `dropped_<label>.csv` shard removes its objects from `registry.csv` and
`excluded.csv`, so that a later registry or excluded shard can re-file them; that later merge
removes them from `dropped.csv` again. A shard naming an object in neither file is refused.

## `dimensions.csv`

Key `source`, `object`, `model_index`, `factor`, with `tier`. Every measure runs over the rows
with a measured response (a pharmacokinetic table's dosing rows are not observations). Per
grouping factor: `n_obs`, `n_groups`, group sizes `group_size_min`, `group_size_p10`, `group_size_p50`, `group_size_p90`,
`group_size_max` (observed sizes: at or below the level under p50, at or above from p50 on),
`singleton_share`, `cv` (population standard deviation over the mean) and `alpha`, the
concentration of a symmetric Dirichlet fitted by moment matching to the group-size proportions
(`Var(p) = (1 − 1/G) / (G (G α + 1))` solved for α; `inf` for a balanced allocation). Per row,
repeated on each of its factors: `n_factors`, `relation` (`single` / `nested` / `crossed` /
`mixed`; a pair is nested when every level of one factor lies in one level of the other, the
row is nested or crossed when every pair is, mixed otherwise), `d_doc` and `d_all` (continuous
and binary columns count 1, a categorical K − 1, an interaction the product; `d_doc` over the
documented model, `d_all` over every column of `columns.csv` plus the documented interactions,
so never below `d_doc`).

## `columns.csv`

Key `source`, `object`, `model_index`, `column`, with `tier`: every column of the table that is
not the response, the trials, a grouping factor or ignored. `type` by one rule, in order:
`ordered` for an ordered categorical (declared in `types`, see above); `binary` for exactly two distinct values; `categorical`
with `K` levels for a column the file or `types` declares categorical, a string column, or an
integer column with at most 10 distinct values not declared continuous; `continuous` otherwise.
`level` is `group` when the column is constant within every group of some grouping factor
(`constant_within` lists those factors), `within` otherwise; `missing_share`; `in_model` is
`yes` for a covariate of the documented model.

## `quantiles.yaml`

Per axis `n`, `min`, `p5`, `p10`, `p50`, `p90`, `p95`, `max`, pooled, per tier present and
without agridat. Per-factor axes count a dataset once per grouping factor, dataset axes
(`n_obs`, `n_grouping_factors`, `d_doc`, `d_all`) once per registry row, `K` once per
categorical covariate of a documented model. The covariate-type and level shares and the K
distribution run over the documented models' covariates; `implied_columns` is the expected
design-column count of a 9- and a 14-term model (the practice survey's p90 and p95 of terms)
under that categorical share and mean K − 1. `SUMMARY.md` ends each axis table with the
practice survey's p90, the maximum over the v1 families (the minimum for `group_size_min`)
read from `../practice/quantiles.yaml` at merge time.

## What the merge checks

Header equal to the agent columns; required fields; allowed values; `model_index` an integer
from 1 to 3; a dropped object is in `registry.csv` or `excluded.csv`; the source is in `sources.yaml` and the object in the source; every named column
exists in the loaded table (every part of an `a:b` term); each grouping factor, a composite
built from its parts, has at least two levels and a level with two or more rows; the response shows its declared type (`continuous` numeric, `binary` two
distinct values, `count` and `binomial` non-negative integers, `ordinal` at most 10 distinct
values, `categorical` not a float column); a `binomial` row names integer `trials` the
response never exceeds; the object is not in the rival file. A failing shard is refused with
its offending rows (line, key, column, value, problem) printed and nothing written. Upsert on
the key: merging a shard twice changes nothing, a corrected shard replaces its rows. Every merge
then measures the whole registry again.

## Pilot (#20)

lme4, nlme and mlmRev read end to end by four Sonnet 5.5 agents, 77 objects, five registry rows
drawn with seed 0 (`registry.sample(5, random_state=0)`) and read by Alex against the help
pages: nlme Meat, Orthodont, Phenobarb, Remifentanil and mlmRev star. Disagreements and the
rules they produced:

- `ordered` declared on grouping factors (Meat, Orthodont, and 19 further rows): nlme's
  `groupedData` orders subjects by their mean, no order a model uses. Rule: `ordered` for
  covariates only; the declarations were dropped from the shards.
- Dosing rows without a concentration counted as observations (Phenobarb 744 rows, 155
  measured; Remifentanil, Quinidine, star, Gcsemv, Glucose likewise). Rule: the measurer keeps
  the rows with a measured response.
- Nonlinear formulas too vague ("one-compartment first-order PK"). Rule: name the model class
  and its inputs; the two rows were re-filed.
- star: `tch` is a reconstructed teacher-class identifier, noted. The `ignore` list stays at
  the derived and alternate columns (`read`, `yrs`, `birthy`); unused but usable columns such
  as `hdeg` and `birthq` remain in `columns.csv`, which is what `d_all` measures.

Agreed as filed: the three lme4-syntax formulas, the covariate lists, the ignored copies
(`Apgar`, `ID`, `BSA`). Settled from the agents' `RULE GAP` notes in the same pass: composite
grouping factors `a:b`, the `simulated data` exclusion, the `NONLINEAR:` tag, offsets and
observation-level random effects in `ignore`, transformed responses by their raw column,
models recalled from the cited book at `medium`, `d_all` counting the documented interactions.

## Census (#22)

The remaining mixed-model packages, read by six Opus agents: MEMSS in two shards, SASmixed
with nlmeU and HLMdiag, glmmTMB with brms, ordinal and geepack, agridat's 50 capped objects in
two shards; 144 objects, 79 registry rows over 74 objects before the fold, 31 exclusions
(agridat's 24 uniformity trials and fixed-effects-only tables, the wide and subject-level
twins of nlmeU, the wide geepack tables). GLMMadaptive ships no data. One agent read the 40
flagged pairs: every MEMSS object is a re-export of its nlme namesake (eight relabel the factor
levels), SASmixed Semi2 is nlme Oxide, so 39 rows folded into their nlme rows and MEMSS keeps
CO2, Orange and Theoph, whose namesakes are base R's `datasets` (#23). The MEMSS readings,
made without sight of the nlme shards, agree with the pilot on every response and on 35 of 38
grouping-factor lists (Alfalfa's and Pixel's composite whole-plot term, Gun's `Physique`);
the covariate lists differ mostly on whether a nonlinear model's time or dose axis counts.

Rules settled from the agents' `RULE GAP` notes:

- A column is a grouping factor or a covariate, never both; the merge refuses the row. SASmixed
  Cultivation's `(1|Cult)` next to `Inoc * Cult` is Littell's split-plot, so the random term is
  the whole-plot term `Block:Cult`.
- A nonlinear model's inputs (time, dose, concentration) are covariates, as the pilot filed
  them; a shard that leaves them out measures `d_doc` 0.
- A numeric R column the documented model wraps in `factor()` is declared `nitro=categorical`
  in `types`; the loader applies a declaration on any format (yates.oats).
- A uniformity trial (yield on a grid, no treatment) is excluded as `no grouping structure`
  unless its examples block fits a random term on a column of the table (piepho.barley kept).
- A documented fixed-effects fit over a blocked design (`lm` with `rep`) is rendered as the
  random-effects version at `low` with the fixed model named in `notes`; when the page says
  the replicate is no blocking factor (mead.germination) the object is excluded.
- GEE fits (geepack) are filed as the lme4 equivalent with a random intercept on the cluster,
  `notes` saying the source fits GEE. A censored survival response (brms kidney) stays as
  `continuous` with the censoring indicator in `ignore`.
- Help pages calling their data "constructed" or "probably constructed" (SASmixed Animal, BIB,
  IncBlk) stay in the registry: the page itself only guesses, and only data the source states
  to be simulated are excluded (decided 2026-10-07). Aggregate responses on a real grouping
  (nass.sorghum's state-year yields, lillemo.wheat's mean scores) stay at `low`.
- A further `model_index` row only when the response or the grouping factors differ; a nested
  simplification of the fixed effects is the same model (decided 2026-10-07; five SASmixed
  model-2 rows dropped). Dataset axes count once per registry row, so a ladder of fits would
  weight its dataset several times.
- Plot coordinates of a field layout (`row`, `col`) go in `ignore`, as the pilot's
  latitude and longitude did; a table whose only candidate grouping is its coordinates has
  no grouping structure (besag.checks).

Spot check: 20 registry rows drawn with seed 0, stratified by shard in proportion to the rows
surviving the fold (SASmixed group 8, glmmTMB group 4, agridat a 4 and b 3, MEMSS 1), read by
Alex against the help pages. Agreed as filed: radon, Genetics, TeachingI, SIIdata,
gomez.nonnormal2, gomez.splitplot.subsample, snedecor.asparagus, inhaler, muscatine,
respiratory. Changed:

- Theoph: `Dose;Time` are the covariates (the nonlinear-inputs rule).
- Cultivation: the formula is written with the whole-plot term `(1|Block:Cult)`; the model-2
  row left under the new `model_index` rule.
- WaferTypes: the response is `delta`, which the page defines as `delta ~ 1 | uWafer`;
  `Thick` is a covariate.
- fcat: `scorec` is a bounded target score with target-specific maxima, noted; filed as
  `count` for want of a trials column.
- besag.checks: excluded; `row` and `col` are coordinates, not groups.
- connolly.potato, yates.oats and four further agridat rows: coordinates ignored.
- salmon.bunt: the strong genotype-by-race interaction becomes the random term `bunt:gen`,
  the layout repeat `rep` a fixed covariate.
- spruce: the chamber the trees sit in is a second grouping factor (`chamber;id`).
- muscatine: the page's `cage` and `cage2` are an age polynomial; the registry names the
  column `age` once, so `d_doc` counts the linear term only. Polynomial and other derived
  terms on a column are not representable in the registry.

The spot check found no substantive change in its eight `high` rows and six in its twelve
`medium` and `low` rows, mostly a missed design level (chamber, whole plot, interaction random
term) or a coordinate taken for a group, so the 38 `medium` and `low` rows of the census were
read a second time, blind, by two Opus agents into a scratch directory and compared by script
on response, grouping factors, covariates and interactions (`compare.py` in the session's
scratchpad, not kept). Seven of the rows had seen the verdicts above through this section and
do not count; of the 31 blind rows 21 agree. Six disagreements were covariate choices settled
by rule without reading: a nonlinear model's input is a covariate (CO2, Orange), a
pre-treatment baseline is a covariate rather than an alternate response (ahd, dietox), an
interaction the cited book fits is carried (prt), otherwise the simpler reading stands
(nass.sorghum). Four were grouping choices adjudicated by Alex on 2026-10-07:

- buntaran.wheat: the three zones fixed, genotype random beside location, replicate and
  incomplete block; `(1|loc:gen)` noted as the more faithful MET term.
- jansen.strawberry: ordinal `category` weighted by `count` over the plot `block:male:female`,
  with `male*female` fixed; not a count response. The measurer counts contingency cells.
- kirk.potato: genotype only; the page says the replicates are not blocks.
- senshu.rice: locations nested in countries, the page's own quadratic term dropped because
  the page calls it senseless.

The lesson for #23 on: a second blind reading of the rendered rows costs one agent pass and
hands Alex only the grouping disagreements, about one row in eight.
