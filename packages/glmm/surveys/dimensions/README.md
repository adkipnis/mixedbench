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
| `deposit_files.csv` | `resolve.py` | Tier D: every link of `deposits.csv` resolved through its repository's API, one row per listed file with its role, checksum, label and pin, one row for a deposit without files, see below |
| `candidates.csv` | `pull.py` | every enumerated data object with its counts, see below |
| `net_hits.csv` | `net.py` | Tier O: every table of OpenML, UCI and PMLB whose column names hold a `nets` keyword, kept or not, see below |
| `v05_datasets.csv` | hand (#23) | the 36 R datasets of metabeta v0.5 by `source`, `object` and their v0.5 parquet name; the closing contract test (#27) asserts each is in the registry or the exclusions |
| `help/`, `cache/` | `pull.py`, loader, `resolve.py` | untracked: one help page per kept object for the agents, the table's dtypes and first rows appended; `help/deposits/` one page per Tier D deposit; downloads, extracted trees and the cached repository API answers |
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
| `net.py` | | the Tier O keyword net over the three repositories' APIs |
| `tests/` | | pytest, run by hand, not in CI: `uv run pytest packages/glmm/surveys/dimensions` |

Agents read documentation and write shards; `merge.py` is the only writer of the canonical CSVs.

```
uv run python packages/glmm/surveys/dimensions/deposits.py
uv run python packages/glmm/surveys/dimensions/resolve.py [--fetch]
uv run python packages/glmm/surveys/dimensions/net.py
uv run python packages/glmm/surveys/dimensions/pull.py [--tiers E O]
uv run python packages/glmm/surveys/dimensions/merge.py packages/glmm/surveys/dimensions/shards/<shard>.csv [--root DIR]
```

`pull.py --tiers` pulls only those tiers (a ticket's pull): the other tiers keep their rows in
`candidates.csv` and the pre-screen shard, and their help pages.

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
git archive; `path` (optional) narrows a git or url tree; `file` (optional) names the download
of a url whose path has no suffix (figshare's `files/<id>`, OSF's `download?version=9`), so the
loader knows the format (`sleepstudy.csv`, `datasets.tar.gz`). `cap` (optional, per entry or top-level as a
default) is the most objects read from one source, so that no single collection dominates: a
source with more objects passing the pre-screen (below) keeps a draw of `cap` of them made with
`random.Random(seed)`, `seed` top-level, over their sorted names. Only agridat (about 390 field
trials, else 38% of the pool) is capped; ten Tier R packages hold more than 40 objects, so a cap
for all would have discarded grouped tables of faraway and MASS at random (decided 2026-10-07).
`layout` (optional) names the columns of a headerless text file, `name` for a
whitespace-separated file with a codes list (Goldstein's partnership data) or `name:start-end`
for a fixed-width file (the Bristol CMM `.DAT` files, transcribed from their `.ASC` sheets;
positions from 1), since nothing in such a file says what its columns are.
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
not locatable), Littell et al. (`SASmixed`, Tier R), Kruschke (scripts). At the time of that pass
the loader still lacked readers for SPSS `.sav` (Hox), old Excel `.xls` (Goldstein, Zuur),
fixed-width `.dat` with an `.asc` layout (Bristol CMM), Stan data json, R dumps outside a CRAN
`data/` folder, gzipped TSV, semicolon-separated csv and Arrow inside a suffix-less tar.gz;
#24 settled the last five, #25 the first three (`pyreadstat`, `xlrd` and the `layout` key
above, decided 2026-10-08).

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
| `object` | the data object as the loader enumerates it: an R object name, a file path inside a git or url tree, or `<path>!<sheet>` for a data sheet of a workbook with several |
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
`simulated data` / `unreadable format` / `licence forbids redistribution` / `too large` /
`not the paper's data` (Tier D only: a table of a deposit the paper merely cites, or of a
preregistration, decided 2026-10-08). An object is in the
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
  `continuous`; the event indicator belongs to the response in `formula` (`Surv(time, cens)`)
  and goes in `ignore`, since the schema has no indicator slot and the indicator is no design
  column (confirmed for all survival rows in #24).
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

## Census of the general packages (#23)

MASS, carData, lattice, HSAUR3, faraway, boot, gamlss.data, medicaldata, languageR and base
R's `datasets`, read by twelve Opus agents (faraway in three shards, MASS and carData in two,
boot with lattice, medicaldata with `datasets`): 628 objects, 160 of them screened out
mechanically, 468 read, 105 registry rows before the fold and 362 exclusions, 308 of them
`no grouping structure`, as expected of packages whose tables are mostly one row per unit. One agent read the 17 flagged pairs: 16 are the same dataset (faraway's
toenail, ohio and semicond beside lme4, geepack and SASmixed; MASS petrol, muscle, oats and
Rabbit beside nlme; MASS michelson and npk, medicaldata indometh and theoph and base R's
Orange, Theoph, npk, morley, Indometh beside their MEMSS or MASS twins; faraway abrasion and
breaking are two Latin squares that share a shape). The fold left 240 rows.

Base R's `CO2` arrived with 468 rows and one column: the loader's Rscript dump had written
`CO2.rds` and then `co2.rds`, the Mauna Loa series, to the same file on this case-insensitive
file system, and `co2` had vanished from the enumeration. Fixed in the loader (the second of
two names differing in case only carries a tilde in the dump, stripped on reading; commit
439c813), `datasets` re-pulled alone through a scratch script, `CO2` dropped and re-filed, where
it folds into the MEMSS row; `co2` is a pre-screen exclusion. The pull of #24 and #25 runs over
the whole frame again.

Second blind reading, now a standard step: the 77 `medium` and `low` rows of these shards
left after the fold were re-read by three Opus agents into a scratch directory and compared
by script on response, grouping factors, covariates and interactions; 65 agree on all four.
Settled by rule: OME gains the covariate `OME`, which the page's `lm(L75 ~ Noise/(Age + OME))`
names; nepali's inferred list falls to `age;sex`, the simpler reading; weightRatings keeps
`Frequency`; the interactions proposed for schizophrenia2, amis and ChickWeight are on no page
and stay out. The response type follows the column, not the Gaussian fit: eggprod's egg totals
are `count`, the seven-point ratings of sizeRatings and weightRatings `ordinal`. Six grouping
disagreements (jsp, lawn, leafblotch, motorins, durationsGe, durationsOnt) went to Alex with
the spot check below.

Rules decided by Alex on 2026-10-07 from the agents' `RULE GAP` notes:

- A multivariate table with a grouping factor and several response variables (carData Soils
  and Pottery, HSAUR3 pottery and skulls, MANOVA examples) is one registry row per response,
  up to the cap of three, the responses left out named in the first row's `notes` and every
  response not filed in `ignore`; the HSAUR3 pair had been excluded and was re-filed.
- A grouped table whose page documents no response and no model is filed with an inferred
  response at `low` under a `RESPONSE INFERRED:` note (carData MplsStops, medicaldata
  covid_testing, faraway worldcup, MASS painters, faraway neighbor, all re-filed); only a table
  with no defensible response stays `response missing or undocumented` (carData LoBD, the
  languageR metadata tables).
- Survey strata and waves a source models as fixed (carData CES11, GSSvocab, HSAUR3 CHFLS,
  WVS) are no grouping factors: the sample design is not a documented random effect.
- Wide repeated-measures tables (boot nitrofen, frets; faraway hemoglobin, potuse; MASS
  anorexia) are excluded as `no grouping structure`, as the nlmeU wide twins were: the
  grouping unit is no column of the loaded table.
- The rows and columns of a Latin square (datasets OrchardSprays, faraway abrasion, alfalfa,
  breaking) are crossed blocking factors, not the ignored coordinates of a field layout.
- Matched case-control pairs and other conditional-logistic designs (faraway amlxray, HSAUR3
  backpain, datasets infert, MASS gehan) are rendered with a random intercept on the pair, as
  GEE fits are rendered with one on the cluster.
- An area factor is a grouping factor when it has many levels (gamlss.data LGAclaims, 13
  statistical divisions) and a covariate when it has a handful and is the predictor of
  interest (faraway infmort's four regions, gamlss.data mviBig).
- A designed experiment with replication but no replicate column (faraway rats, snail, truck,
  turtle, seeds, salmonella) has no grouping structure.

Every one of metabeta v0.5's 36 R datasets is in the registry (28 were after #22, the eight of
MASS, gamlss.data, boot and base R came with this census); `v05_datasets.csv` lists them for
the closing contract test, and no package had to be added to the frame.

Spot check: 20 registry rows drawn with seed 0, stratified by shard in proportion to the rows
surviving the fold (faraway 6, MASS 3, languageR 3, carData 2, boot and lattice 2,
medicaldata and `datasets` 2, HSAUR3 1, gamlss.data 1), handed to Alex as one list with the
six grouping disagreements, each item linking the rdrr.io page. Agreed as filed: 17 of the 20,
among them amlxray's eight exposures and troutegg's `low`. Changed:

- lawn: each machine is tested twice at each speed, so `machine:speed` is a second grouping
  factor, the within-machine stratum (the blind reading had it).
- pvc: excluded; Faraway fits `psize ~ operator * resin` as two fixed factors with replication.
- singer: excluded; one height per singer, `voice.part` classifies singers.
- jsp: `school;school:class`, the blind reading; Faraway's final-year model has no student
  effect, which appears only in the stacked english and math analysis; `id` and `year` ignored.
- leafblotch, durationsGe, durationsOnt: the registry stands (site is the block, variety the
  treatment; one token per word, so Word repeats nothing).
- motorins: excluded; Zone and Make are tariff rating factors, not sampled clustering units.

Of the six grouping disagreements the registry won three, the blind reading two, and one
object left the registry; of the 20 drawn rows two left it, both `medium` rows whose
one-way factor classifies rather than clusters. Tier R closes at 1191 enumerated objects,
689 read, 252 registry rows over 238 datasets and 559 exclusions.


## Tier E census and Tier O net (#24)

Loader work came first, since the Tier E files were unreadable: a Stan data dict (posteriordb's
`.json.zip`, the Stan examples' `.data.json`) is read as the table of its observation-length
arrays, an N-row matrix as numbered columns (`X_1`), scalars, group-level arrays and arrays of
three dimensions left out and named on the help page; `.init.json` files (initial values) are no
data; `.gz` and `.zip` wrappers are opened; Arrow files read through `pyarrow`, added to the
research extra for MixedModels.jl's own datasets (decided 2026-10-07, against the spec's "no
pyarrow"); parquet (OpenML) likewise; a url whose path has no suffix carries `file` in the
frame; delimited text aligned with runs of spaces (the ARM `.dat` files) falls back to
whitespace separation, padded names and fields are stripped, `NA` is missing, a byte-order
mark dropped, and a file no reading parses (the PyMC examples' ice-core csv) is no frame; a
429 is waited out. Documentation for a non-CRAN object is a text file named after its stem in
its folder or a sibling folder (posteriordb's `data/info`), else the README-like files (`.md`,
`.rst`, a `codebook.txt`, a `README` in capitals) in its folder or above it within the pinned
path; a Stata file renders its labels as a codebook; an object with no documentation gets an
empty page and the agent brief names where the source documents it. `pull.py --tiers E O`
pulled the two tiers without touching Tier R. The composite factor builder (`measure.py`)
now leaves a row without one of the parts without a level (the national radon survey's rows
without a county).

Tier E: 543 objects enumerated over 84 sources, 69 screened out mechanically (posteriordb's
one-array time series among them), 474 read by eight Opus agents (posteriordb; the ARM
chapters in three shards; the BUGS volumes; pingouin with the PyMC examples; bambi with
MixedModels.jl; Stata [ME]; Stata [XT]), 189 registry rows before the fold and 360 exclusions
(312 `no grouping structure`: the classical-regression ARM chapters, the BUGS examples' wide
tables and one-row-per-group designs, bambi's regression tables; 25 `simulated data`, Stata's
manual demos among them). The ARM chapters repeat their data files (srrs2.dat in five
chapters, a dozen radon variants per chapter), so the merge flagged 357 pairs: 340 are
byte-identical tables and were answered `same` by script
(`shards/duplicates_tier_e_identical.csv`), the other 17 (MixedModels.jl's, bambi's and
Stata's re-exports of lme4, nlme, MEMSS, mlmRev, brms and MASS tables) by one agent, all
`same`; three MixedModels.jl mirrors that drop a derived column (pastes, grouseticks,
contra) escaped the signature and were folded by hand. After the fold, Tier E holds 99 rows
over 97 datasets (Stata 41, ARM 20, posteriordb 11, pingouin 11, PyMC 10, MixedModels.jl 3,
BUGS 2, bambi 1), 93 of them with a published model, 56 at `high`; 21 Tier R rows now list a
Tier E member in `sources`. After the decisions and the spot check below Tier E closes at
99 rows over 96 datasets (d3 and jobhistory's second model in, long_heating_data and
pancreatitis out), 94 with a published model, 57 at `high`; the registry at 364 rows.

Tier O: `net.py` ran the keyword net on 2026-10-07 (mechanics in `sources.yaml` above the
`nets` block): 5025 OpenML datasets at their lowest version, 689 UCI datasets, 451 PMLB
datasets; 76 hits (65 OpenML, 6 UCI, 5 PMLB; a first run that counted a name merely
containing a keyword had 231, `family_history` and `time_in_hospital` among them, and is the
reason the match is now the whole name), 30 drawn with seed 0, all 34 Tier O objects pass the
pre-screen. One agent read them: 16 registry rows over 14 datasets and 20 exclusions (8
synthetic: OpenML's `hepar2` Bayesian-network samples and a zombie table; 11 `no grouping
structure`: the matched column is an attribute (`family` in anneal, `SUBJECT` as a crop type,
IPUMS `farm` and `school`) or an id with one row per unit; one OpenML parquet holds a single
subject of a 21-subject study). The boxing and Parkinsons twins across repositories folded, so
Tier O closes at 13 rows over 12 datasets, none with a published mixed model, 7 `medium` and 6
`low`: v0.5's four tables, squash and white clover trials, PopularKids, Parkinsons
telemonitoring, gait, and three clinical tables whose cluster (patient, hospital) the source's
own analysis treats as independent (kept at `low`; rule question below). The yield is low as
expected: of 76 keyword hits 12 datasets have a documented clustering unit, and none a
published model.

Blind second reading of the 51 `medium` and `low` Tier E rows by three Opus agents into a
scratch directory, compared by script on response, grouping factors, covariates and
interactions: 45 still in the registry after the fold, 28 agree on all four (two more differ
only in the order of an interaction's parts). Settled by rule without reading: a reading
from the source document beats a recalled one (quinidine, earthquake, nlswork5, psidextract:
the Stata agents read the manual PDFs, the blind readers recalled them), the simpler reading
stands where neither read the source (mrk17_exp1's factorial interactions, radon Ch.12 and
Ch.21's county-level `u`), an interaction the source fits is carried (allvar's
`visage:treatmnt`), the multivariate rule gives the first-listed response (rm_missing) and
the reduced form (sesame.data.json). Re-filed: pymc_examples employee, where the blind reader
found the notebook's hierarchical model (`empower ~ lmx + male + (1 + lmx | team)`) the first
reader had missed (`shards/*_tier_e_refile.csv`). Four grouping disagreements and two
exclusions the blind readers proposed went to Alex with the spot check (below).

Rule-gap decisions of this ticket (from the agents' notes):

- `published_model` is `yes` for a documentation example that states the model (PyMC and
  bambi notebooks, the Stata manual entries, the MixedModels.jl docs), `no` for data used only
  in tests (pingouin pairwise_tests) (decided 2026-10-07).
- posteriordb ships ladders of posteriors on one dataset (radon: 12); the row renders the
  posterior with the richest grouping (varying intercept and slope), its covariates as fitted.
- IRT posteriors (hier_2pl, grsm, gpcm: a discrimination × ability product) are nonlinear
  mixed models over the crossed person × item grouping under the NONLINEAR rule.
- A hierarchical model with Gaussian-process terms beside its random intercepts
  (state_wide_presidential_votes) stays, GP noted; pure GP, time-series, CAR and mixture
  posteriors are `no grouping structure`.
- A Stan data dict that splits observations into censored and uncensored arrays of different
  lengths (BUGS kidney) is read as its modal-length half; excluded as a derived table.
- ARM raw tables of an early chapter whose multilevel fit sits in a later chapter are filed with
  that model at `medium` when the grouping column is in the table; the Ch.4–7 earnings tables
  lack `eth` and `age` and are excluded.
- ml1m's 1–5 ratings are `ordinal` by the #23 rule (set in the shard).

Decided by Alex on 2026-10-07 from the agents' `RULE GAP` notes:

- Data a manual calls "fictional", "fictitious" or "synthetic" are `simulated data` like data
  it calls simulated (Stata's chicken, estatus, wagework, xtcoint).
- MixedModels.jl's d3 stays: no source states its origin or a simulation (the repository,
  docs and Bates's simulation package were searched), and the table reads as anonymised real
  data (coded ids, a composite of two factors, a bounded integer response); filed at `low`
  with the benchmark model, re-filed from the exclusions.
- InstEval's 1–5 ratings are `ordinal` (the pilot row said `continuous`); re-filed.
- A cluster that repeats within the table counts as a grouping factor even when the source's
  own analysis treats the rows as independent (Tier O's patient and hospital clusters).
- A documented variant with a different grouping is a further `model_index` row (jobhistory:
  birthyear crossed with id); a variant whose extra level has one row per level (melanoma's
  county, an observation-level term) or whose grouping column is also a covariate (pig's week)
  is not, and the merge refuses it.
- A stochastic-frontier inefficiency term (xtfrontier1) is rendered as a random intercept.
- Tier O rows carry `published_model` `no`: a documented target and cluster is not a
  published mixed model.

Spot check: 20 Tier E and O rows drawn with seed 0, stratified by shard in proportion to the
rows surviving the fold (Stata 7, pingouin and PyMC 4, ARM 4, Tier O 2, posteriordb 2,
MixedModels.jl 1), read by Alex against the help pages and the sources' online documentation,
together with the four grouping disagreements and two exclusions of the blind reading. Agreed
as filed: tvsfpors, earthquake, productivity, Diabetes130US, boxing2, state-wide votes, kb07,
and the registry's cronbach_alpha (Subj grouping, Items the fixed repeated dimension of alpha)
and the IRT rows (items index their own parameter sets, so `ii` is a grouping factor).
Changed, mostly by reading the Stata manual entries more closely than the agents had:

- quinidine: the PK parameter regressions use glyco, creatinine and weight only, and the
  subject random effect sits on clearance alone; covariates reduced, formula rewritten.
- pisa2000: the school mean `mn_isei` belongs to the model; it is an `egen` column not in
  the table, so it is in the formula only.
- catheter and time_to_attrition: the failure indicator (`infect`, `left`) is written into
  the survival response of the formula; time_to_attrition's covariates are sentiment and
  level, gender stratifies the baseline hazard, intention is not in the model. The indicator
  stays in `ignore` under the #22 kidney convention, which Alex confirmed for all eight
  survival rows after a first version of these two rows had dropped it (and, by mistake,
  catheter's `stset` variables).
- pig and radon_mn: Stata's `|| id: week` and the Stan code fit independent intercept and
  slope deviations, written `(1 + week || id)` and `(1 + floor_measure || county_idx)`;
  employee likewise `(1 | team) + (0 + lmx | team)` (the blind reading's row, re-filed).
- rm_anova2: the two-way repeated-measures ANOVA is written with its error strata,
  `Error(Subject/(Time * Metric))`; `(1|Subject)` alone does not represent them.
- sesame.data.json model 2: `yt_2 ~ z + pretest + (1 | siteset)`, the second margin of a
  bivariate-normal multilevel model (pretest not in the Stan data dict, formula only).
- sesame.dta: grouping `site:setting`, the Ch.23 model's siteset (the blind reading).
- multilevel_ordered_categorical_17.6: a hierarchical ordered-categorical model with
  player-specific cutpoints and scale, not a random intercept.
- long_heating_data and pancreatitis: excluded as `no grouping structure` (the blind
  reading): a fixed softmax choice model on a single choice occasion, and country-specific
  random walks over age.
- srrs2.dat: Alex first picked the blind reading's `county`, since the Ch.12 analysis
  subsets to Minnesota; the object is the unsliced national file (12777 rows, 469 state:county
  pairs, 59 county names in more than one state), so `county` alone would merge namesake
  counties across states. He confirmed `state:county` at medium: the registry classifies the
  unsliced object, and `(1 | state:county)` is a state-disambiguated county grouping, not a
  state-level effect. The Minnesota model itself is in the registry as radon.data.json,
  radon_mn and the PyMC radon.csv.

Of the 20 drawn rows, 11 stood and 9 changed; of the six adjudications the registry won
three, the blind reading three.

## Tier T census (#25)

Loader work came first, since four collections were unreadable or silently absent: SPSS
`.sav` (Hox) through `pyreadstat` and old Excel `.xls` (Goldstein, Zuur) through `xlrd`, both
added to the research extra (decided 2026-10-08); a workbook with several data sheets
(Snijders & Bosker's single companion file) is one object per sheet, `<file>!<sheet>`, its
sheets named like documentation (`Contents`) left out and rendered on the help page, empty
sheets (Excel's `Sheet2`) skipped; headerless files read as the frame's `layout` declares
(the nine Bristol CMM fixed-width `.DAT` files, transcribed from their `.ASC` sheets, and
Goldstein's whitespace-separated partnership file); a `.txt` is a data object unless named
like documentation or after a data file of another format beside it (Fitzmaurice's `lead.txt`
describes `lead.dta`), which no earlier tier had needed; a `#` banner above a table (Diggle's
course files) is skipped and shown on the help page; column names of Excel sheets are
stripped (Goldstein's ` gender,girl=1`); a `.dta` whose value-label section pandas misparses
(mlmus4's scotmap) is read by `pyreadstat`, which also renders the Stata and SPSS codebooks;
SPSS value labels that cover only a scale's extremes (Hox's `lowest`, `highest` on numeric
scores) no longer turn the column categorical; a zip's `__MACOSX` resource forks are no
files; the Rd pages of a repository that is an R package (rethinking, ROS's `rpackage/`)
document the file named after their alias. With two readers landing, `datasets.py` became
the package `datasets/` (`loader.py` pipeline and Rscript route, `readers.py` formats,
`docs.py` help pages), same public names. Fitzmaurice's host sends an incomplete certificate
chain that Python refuses and `curl` accepts, so its 37 `.dta` and the `.txt` descriptions
beside them were seeded into the cache by hand (sha256 checked by the loader as usual):

```
grep -oE 'fitzmaurice_[a-z0-9]+: \{kind: url, name: ([^,]+), pin: ([0-9a-f]+)' packages/glmm/surveys/dimensions/sources.yaml \
  | sed -E 's/.*name: ([^,]+), pin: ([0-9a-f]+)/\1 \2/' | while read url pin; do
  mkdir -p packages/glmm/surveys/dimensions/cache/url/$pin
  curl -sS -o packages/glmm/surveys/dimensions/cache/url/$pin/$(basename $url) $url
  curl -sS -o packages/glmm/surveys/dimensions/cache/url/$pin/$(basename $url .dta).txt ${url%.dta}.txt
done
```

Known limits left as they are: ROS's 49 Congress `.asc` election returns and a two-line
banner without `#` (ROS `cows.dat`) are not read (the first are fixed-effects election
tables, the second one row per cow); Goldstein's Gcsemv.xls codes missing marks as `-1`,
which the registry cannot declare, so its measured rows include them (the dataset is also
mlmRev's `Gcsemv`, with proper NAs, which the fold did not catch since the shapes differ);
a `.txt` data file of Tier E (the PyMC examples) was not enumerated in #24 under the old rule
and would be on a re-pull.

`pull.py --tiers T` enumerated 534 objects over 65 sources, 54 screened out mechanically
(the empty sheets, matrices and model objects of `rethinking`, one-column and wide tables),
480 read by nine Opus agents (Hox, Snijders & Bosker, Goldstein and the CMM sets; Rabe-Hesketh
in two shards, whose chapter do-files hold the book's models; Singer & Willett; the three Zuur
books; McElreath with WWGbook and Diggle; Fitzmaurice; ROS in two shards): 271 registry rows
before the fold and 222 exclusions, 276 with the pre-screen (230 `no grouping structure`, 50
of them wide repeated-measures tables, which is how Fitzmaurice, Singer & Willett and Hox ship
half their data; 24 derived or duplicated; 10 unreadable; 9 time series; 3 without a
response). Eight shard rows were refused by the merge and corrected (a one-level factor, a
phantom row-id name, four responses that were not binary or whose labels were partial, a
padded column name). The merge flagged 26 pairs: 6 identical tables answered `same` by script
(`shards/duplicates_tier_t_identical.csv`), 20 by one agent, all `same` (Rabe-Hesketh's
re-exports of lme4, mlmRev, nlmeU, WWGbook and the Stata manuals; Fitzmaurice's toenail,
birthwt and fat; ALDA's alcohol table in three sources; the CMM and Goldstein twins of faraway
and mlmRev; ROS's `.rda` renderings of its csv files). After the fold Tier T held 248 rows
over 236 datasets (Rabe-Hesketh 80, rethinking 23, Zuur 37 over three books, Hox 20, ALDA
18, ROS 16, Goldstein 15, Snijders & Bosker 13, CMM 7, WWGbook 3, Fitzmaurice 15, Diggle 1),
133 with a published model, 45 at `high`; 12 rows of Tiers R and E now list a Tier T member
in `sources`. ROS contributes no published mixed model: the book fits classical regressions
throughout (every `.Rmd` grepped), so its 16 rows are clusters that repeat under the #24 rule.

Blind second reading of the 196 `medium` and `low` Tier T rows outside the flagged pairs (187
objects) by six Opus agents into a scratch directory, compared by script on response, grouping
factors, covariates and interactions: 89 agree on all four, 3 exclusions proposed, 34 differ
on the response or the grouping. Settled by the data: SocsLong's sender and receiver ids
repeat across groups (the composite stands), skincancer's region codes do not (plain `region`
stands), RiceFieldBirds' SITE has one level, infections' thirteen centres repeat (centre
added, as for Fitzmaurice headache and skin). Settled by rule without reading: a transformed
response names the raw column (Clams AFD, jsp_728 `math yr 3`); several responses over one
grouping are several rows (the three Hong Kong spider taxa, coursework and star1's second
exam, the second direction of the kl_dyads and Monks dyads, whose dyad has one row per pair
and is no grouping factor); a discrete-time hazard model on a person-period table has the
event indicator as its response, the period among its covariates (cigarette, as the ALDA
rows; a continuous-time survival row keeps the time as response and `Surv(time, event)` in
the formula); a block in a variety trial is the random term (wheat's plots, as leafblotch in
#23); the dyad is a grouping factor where the book fits dyad effects and the pairs repeat
(Crofoot); a reading from the source beats a recalled one (depression_pp's cubic age from
the UCLA page); a cluster that repeats stays a grouping factor (headache, skin, aggression's
items, PrussianHorses' years); the simpler or first reading stands where neither reader had
a source (HDI, Pew, Frei et al., Hoogland). Two exclusions both readers supported were
applied (star_mm, a multiple-membership reshape of star1 that the registry cannot represent;
ROS earnings, one row per respondent with a four-level demographic as its only candidate
cluster). Covariate-only differences stay as filed: both readers recalled the same books.
Eight disagreements went to Alex with the spot check (below).

Rules decided by Alex on 2026-10-08 from the agents' `RULE GAP` notes: a discrete-time
hazard model on a person-period table has the event indicator as its response, the period
among its covariates, and `(1 | id)` with the book's fixed-effects fit noted; the period
dummies are one categorical `PERIOD` covariate (as the #22 Bangladesh rule); a subset with
its own worked model (wages_small_pp) is a derived table; a seasonal month or an observer is
a grouping factor when it has enough levels and observations per level (Squid's 12 months,
Clams' 6, Sparrows' 10 observers kept); an exploratory-only chapter counts as the published
worked example (tolerance_pp); an ordinal response recoded off the table (schiz) is filed as
its raw column; Gcsemv's `-1` missing sentinel stays undeclared; reedfrogs (one row per
tank), UCBadmit's long form (derived) and the ROS age-period-cohort aggregates stay excluded.

Spot check: 20 Tier T rows drawn with seed 0, stratified by shard in proportion to the rows
surviving the fold (Rabe-Hesketh 8, the books 4, Zuur 3, rethinking with WWGbook 2, ALDA,
ROS and Fitzmaurice 1), read by Alex against the books' chapter models, together with the
eight disagreements of the blind reading. Agreed as filed: neighborhood, videos, thailand,
height-nonlin, Snijders & Bosker's SOEP sheet, Spiders, BadgersFarmSurveys, RIKZDATAEnv,
rat.brain. Changed, mostly the formula to the chapter's actual fit:

- electricity: a mixed discrete-choice model with respondent-specific random coefficients
  on the six attributes; yogurt: brand-specific random intercepts by household (ch 12);
  ezunem: `log(uclms)` with year effects; infections: the fixed part completed (the survival
  response keeps the #22 kidney convention, the schema having no survival type).
- travel2: excluded; the chapter's conditional logit is single-level and `traveler` the
  choice set, a departure from the #23 rendering of conditional-logistic designs with a
  random intercept on the set, decided for this row.
- jsp_728: Goldstein's normalised score is the documented response, the transform-rule
  reading reverted; OXBOYS: a fourth-degree polynomial in centred age with correlated
  random intercept, age and age-squared effects, season as sinusoidal terms.
- Trolley: main effects only; electric.csv: the book fits `post_test ~ treatment +
  pre_test` separately by grade, the pair kept as grouping under the #24 rule only;
  fev1: log height, log baseline height and a random slope in age; reading_pp: chapter 5,
  formula as filed.
- Of the eight adjudications: NES (both objects) and the three Storable tables excluded,
  the wave and the participant being no random grouping in the documented fits; 17C
  (`married`), Galo (`advice`) and cito (`cito`) take the blind reading's response;
  Cetaceans keeps `Species;DolphinID` with `Sex * Stain * Location` fixed; AstLrd keeps the
  study; CTT_V2 excluded.

Of the 20 drawn rows, 9 stood and 11 changed, one of them leaving the registry; of the
eight adjudications the registry won two, the blind reading four, and four objects left
the registry. Tier T closes at 244 rows over 227 datasets, 136 with a published model, 44
at `high`, and 285 exclusions; the registry at 608 rows.

## Tier D census (#26)

Decided up front on 2026-10-08: one `url` entry per fetched data file rather than one
whole-deposit zip per deposit (the repositories build their zips on the fly, so a pin on one
would not survive a re-pull; Zenodo has none; the per-file route skips images, videos and
genomics), labelled `<paper_id>_<repository>` and `_2`, `_3` for a paper's further files of
that repository, pinned by the file's sha256 and checked on download against the checksum the
repository's API reports (OSF sha256, Dryad, Zenodo and figshare md5); a script-written
`deposit_files.csv` as the deposit-level record, since a private deposit, a preprint or a bot
wall yields no object for `excluded.csv`; the exclusion reason `not the paper's data` for a
table of a deposit the paper merely cites or a preregistration; the registry formula is the
model the practice survey filed for the paper, `published_model` `yes` throughout; the
reading agents on Sonnet at medium effort for this tier (cost), the earlier tiers' Opus
readings being the calibration.

`resolve.py` resolves each link through its repository's API (Dryad datasets and version
files, Zenodo records, figshare articles, OSF guids: a project walked with its storage
providers, folders, wiki and child components, a registration likewise, a file, a preprint's
PDF; a `?view_only=` key printed in the paper travels along), caches every answer under
`cache/deposits/`, and classifies each file by name: a table or archive the loader reads is
`data`, a README, codebook, PDF, docx or knitted html `documentation`, an R, Python, Stata,
SPSS, Julia or Stan file `script`, the rest `other`. The listing of 2026-10-08: 98 links over
the 60 papers (one paper names up to twelve OSF components), 89 resolved, 6 without files
(empty or registration-only OSF nodes), one restricted project, one figshare private link
without its DOI, one OSF user profile cited as a deposit (ip_2020); 1632 files, 607 `data`,
622 `other` (246 MATLAB `.mat`, 227 images), 231 scripts, 172 documentation files. Pull rules
set from the listing: 50 MB per file, since every larger file was a fitted model, posterior
draws or simulation output (30 files, 4.9 GB, the largest a 1.7 GB GitHub snapshot on
Zenodo), and no file under a hidden folder (RStudio's `.Rproj.user` notebook chunks). The
fetch wrote 550 entries under tier `D` of `sources.yaml` (the block is rewritten whole by the
script) and one page per deposit under `help/deposits/`: title, licence, description, the
paper's text around the link, the paper's models as the practice survey filed them, the file
listing, then the README, codebook and scripts (knitted html stripped to text, each file cut
at 40 000 characters, the page at 250 000). The Tier D help page of an object opens with a
pointer to its deposit page rather than the page itself (the first pull had pasted it into
each of a deposit's objects, 250 kB per object). Dryad refuses anonymous downloads on every
route (its file API answers 401 "must have current bearer token", the dataset zip likewise,
the web file stream 403 to the script), so its 11 deposits (25 files, under 60 MB) stayed
unfetched under the no-bot-wall rule; decision pending (below). Two OSF files answered 403.

Loader changes: pyreadr's `IndexError` on a labelled data frame inside an `.RData` (its
value-label handler indexes past the column names) takes the Rscript route like its other
errors; a `continuous` declaration on a string column with decimal commas and no points
(kleisner_2026's BMI, a European csv) reads them as points. The pull renders at most 60
columns of a table's dtypes and first rows (a genotype matrix of thousands of columns had
made a 4 MB page). Known limits left as they are, filed as `unreadable format`: a workbook
with a merged group header above the variable names (liu_2022), a text sentinel
(`destroyed`) among counts and `.` as the missing marker (walker_2021b).

`pull.py --tiers D` enumerated 970 objects over 489 sources (a zip is one source whose files
are its objects: jing_2020's data zip alone 405), 226 screened out mechanically (153 without
a frame: fitted brms and lme4 models saved as `.rds` and `.RData`, Stan json, bookdown
indexes), 744 passing. Of those, 320 were filed by script before the reading
(`shards/excluded_tier_d_series.csv`): jing_2020's one-raw-file-per-participant series
(eight or more same-shaped siblings named `<stem>_<n>`, 48 per experiment), whose merged
tables (`mydata_*` objects) are in the same zip, as `derived or duplicated table`. The
remaining 424 objects were read by nine Sonnet agents (sievers_2020 in three shards,
jing_2020 in two, the other 36 papers in four by stratum order, at most 60 objects each):
185 registry rows over 164 objects and 28 papers, 799 exclusions with the pre-screen and
the series (482 derived or duplicated, 156 unreadable, 110 without grouping structure, 46 not
the paper's data, 5 without a response); 50 rows at `high`, 28 `medium`, 107 `low`. Eleven
rows were refused by the merge and corrected (a key-pressed column and a `y`/`n`/`u` column
filed as binary, two objects named with a suffix the loader strips, one with the file's own
misspelling, a morph score filed as ordinal with more than ten levels, a stem density as
count, and the three unreadable tables above). The merge flagged 11 pairs, all jing_2020's
RData objects present in both of its zips or two experiments of one design, answered by
script from table equality (`shards/duplicates_tier_d_identical.csv`, 7 `same`, 4
`different`).

The loss by cause is the tier's finding (`SUMMARY.md`, Tier D). Of the 60 papers, 22 reach
no object at all: the 11 Dryad deposits, 8 papers whose OSF link is a preprint, one
restricted project, one user page, one deposit too large; of the 38 with objects, 28 have a
registry row. Within the deposits, the paper's analysis table is the exception: deposits
hold raw per-participant logs beside merged tables, Qualtrics exports one row per
participant with the trials as columns, aggregates the model runs on but which were built in
a script from the deposited raw tables (kanber, laing, walker), fitted models and posterior
draws, and stimulus lists. The agents' `RULE GAP` notes (115 rows) name four recurring
cases: a model on an aggregate whose only deposited input is the raw trial table (filed at
`low` with the trial-level response, `RESPONSE INFERRED`); a dataset split into one file per
coder, group or session whose pooled table and response are not in any file (sievers_2020's
82 speech-turn worksheets, filed at `low` with an inferred turn rating); the paper's model
needing a column the table lacks (jing's dot count, slepian's target); and tables of the
paper's own deposit that no model uses, filed as `not the paper's data` for want of a
"not analysed" value.

Decided by Alex on 2026-10-08: sievers_2020's 89 per-coder worksheets leave the registry
(`shards/dropped_tier_d_sievers_worksheets.csv`, re-filed as `derived or duplicated table`)
under the rule that a dataset split into one file per coder, session or participant whose
pooled table is in no file is excluded, while a split by study or experiment stays one row
per file (`prompts/read.md`, rule 10); the Dryad deposits come through Alex's browser at
reading pace into the untracked `cache/dryad_raw/`, which `resolve.py --ingest` matches file
by file against the md5 the Dryad API reported (a dataset zip is opened for its members), so
the pins stay those of verified bytes. Done on 2026-10-08 through Claude in Chrome in Alex's
session: the "Download full dataset" button of each landing page, one deposit at a time with
seconds between; Dryad's BotStopper shows an automatic "Validating..." page before a file
download, which passed by itself (no CAPTCHA was shown or solved). After the drop Tier D stood at 96 rows over 75
objects and 28 papers (50 `high`, 21 `medium`, 25 `low`), the Dryad deposits still to come.

Spot check: 20 rows drawn with seed 0 after the drop, stratified by shard, each with the
paper's DOI, the deposit page and the file URL, read by Alex against the paper's reported
or deposited analysis. Agreed as filed: gumundsdottir's location-scale daily model,
weaving's two punishment studies, sequestro's elevator model, berweger's surprise and
exploration models, timmer's tone experiments, hubbard's diploma model, naranowicz's
behavioural and film-valence models (the latter kept as a deposited-script model), and
sievers' pairwise neural-influence model (ordered ego-alter pairs are distinct pairs).
Changed: liutu's formula names its zero-inflation and dispersion submodels; walker's
feeding assays take the paper's per-site `asin(sqrt(Consumption)) ~ Species + (1 |
Replicate)`; grey's dynamic structural equation model is rendered in words as the
nonlinear rows are. The rule set by the other six verdicts (walker's raw cage tables,
kanber's trial-level Task 2, jing's bootstrap-analysed Experiment 1 tables, slepian's raw
logs without the target column): in Tier D the recorded model is a reported or deposited
analysis, so a raw table on which the paper fits nothing leaves the registry as `response
missing or undocumented` rather than as a `RESPONSE INFERRED` row; applied to the whole
class (`shards/dropped_tier_d_spotcheck.csv`): 16 inferred objects (jing's seven Experiment
1, 4 and 5 tables, kanber's two tasks, laing's utterance table, walker's six raw cage
tables) and slepian's five raw logs. Of the 20 rows, 11 stood, 3 changed their formula
and 6 left the registry.

The 11 Dryad deposits (26 files, all matched by the API's md5 or sha-256 digest) added 23
objects, 22 passing the pre-screen, read by one Sonnet agent: 31 rows over 15 objects and
7 exclusions (shanahan's second-by-second raw dial readings as derived, the paper modelling
its two summary tables; johansson's workbook with its header on row 4 under a banner as
unreadable; goodwin's primer and barcode lists); three count responses that are not
integer-valued corrected to continuous. Tier D closes at 104 rows over 69 objects and 38
papers, every row with a published model, 62 at `high`, 40 `medium`, 2 `low`, and 917
exclusions with the pre-screen (572 derived or duplicated, 158 unreadable, 113 without
grouping structure, 46 not the paper's data, 28 without a response); the registry at 712
rows, no flagged pair open.

Dryad spot check (five rows, seed 0, by Alex on 2026-10-08): shanahan's `T_Net` model
stood; meyel's volume model takes the paper's shifted Gamma-log response and its three
random factors as separate terms, its head-behaviour model the deposited script's single
`(1 | PopulationID:FamilyID)`; barbosa's two reaction-norm rows note that the paper fits
them per population subset (eight models), the whole table kept as the row's grouping, as
walker's per-site feeding assays are. One stood, four changed, none left.

