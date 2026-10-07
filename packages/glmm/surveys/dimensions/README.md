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
| `net_hits.csv` | `net.py` | Tier O: every table of OpenML, UCI and PMLB whose column names hold a `nets` keyword, kept or not, see below |
| `v05_datasets.csv` | hand (#23) | the 36 R datasets of metabeta v0.5 by `source`, `object` and their v0.5 parquet name; the closing contract test (#27) asserts each is in the registry or the exclusions |
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
| `net.py` | | the Tier O keyword net over the three repositories' APIs |
| `tests/` | | pytest, run by hand, not in CI: `uv run pytest packages/glmm/surveys/dimensions` |

Agents read documentation and write shards; `merge.py` is the only writer of the canonical CSVs.

```
uv run python packages/glmm/surveys/dimensions/deposits.py
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
