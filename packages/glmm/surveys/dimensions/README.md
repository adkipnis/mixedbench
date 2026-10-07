# Dimension survey — public grouped datasets

The lower edges, imbalance, factor-level distribution and covariate mix of real grouped data,
and the pool the v1 real-data test sets draw from. Spec: issue #14; tickets #15–#27. The
package's loader (`metabeta.glmm.datasets`, research extra) reads every source; the survey
scripts here own the file contract. The practice survey (`../practice/`) is the model;
nothing is imported across surveys. Results: [`SUMMARY.md`](SUMMARY.md), regenerated on every merge.

## Files

| file | written by | content |
|---|---|---|
| `sources.yaml` | discovery and hand (#19, #21) | the frame: tiers of pinned sources, see below |
| `candidates.csv` | pull script (#19) | every enumerated data object with its counts |
| `help/`, `cache/` | pull script, loader | untracked: documentation per object for the agents; downloads and extracted trees |
| `shards/<table>_<label>.csv` | agents | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped` |
| `registry.csv` | `merge.py` | one row per dataset and documented model, at most three per object |
| `excluded.csv` | `merge.py` | every screened-out object with a categorical reason |
| `duplicates.csv` | `merge.py` | candidate pairs the merge flagged and the verdicts agents returned |
| `dropped.csv` | `merge.py` | objects taken out of the registry and the exclusions, awaiting a re-filing shard |
| `dimensions.csv` | `merge.py` via `measure.py` | one row per registry row and grouping factor, see below |
| `columns.csv` | `merge.py` via `measure.py` | one row per registry row and covariate column, see below |
| `quantiles.yaml`, `SUMMARY.md` | `merge.py` via `summarise.py` | every axis pooled, per tier and without agridat; the summary from `SUMMARY.template.md`, which holds no digit |
| `prompts/read.md` | | what a reading agent gets and writes |
| `schema.py` | | file contract and allowed values |
| `measure.py`, `summarise.py` | | what the merge measures from a loaded table, and how it reports it |
| `tests/` | | pytest, run by hand, not in CI: `uv run pytest packages/glmm/surveys/dimensions` |

Agents read documentation and write shards; `merge.py` is the only writer of the canonical CSVs.

```
uv run python packages/glmm/surveys/dimensions/merge.py packages/glmm/surveys/dimensions/shards/<shard>.csv [--root DIR]
```

## `sources.yaml`

Tiers in frame order `R` (CRAN package data), `E` (Python and Stan ecosystem examples), `T`
(textbook companions), `D` (data deposits of the practice survey's papers), `O` (open tabular
repositories). Under each tier, one entry per source keyed by its **label**, the `source` every
shard row names:

```yaml
tiers:
  R:
    lme4: {kind: cran, pin: 1.1-37}
  D:
    smith_2019_dryad: {kind: url, name: https://datadryad.org/.../data.zip, pin: <sha256>}
  E:
    stan_examples: {kind: git, name: https://github.com/stan-dev/example-models, pin: a1b2c3d, path: ARM}
```

`kind` ∈ `cran` / `git` / `url` as the loader's `Source`; `name` defaults to the label (a CRAN
package name); `pin` is the CRAN version, git revision or the file's sha256; `checksum`
(optional) pins a CRAN or git archive; `path` (optional) narrows a git or url tree. Caps,
seeds and dropped candidates are added by #19 and #21.

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
| `grouping_factors` | `;`-list of column names whose levels index random effects, as documented |
| `covariates` | `;`-list of the documented model's covariate columns (main effects) |
| `interactions` | `;`-list of `a:b` terms, every part a column name |
| `ignore` | `;`-list of columns no model should use: row ids, weights, alternate responses |
| `types` | `;`-list of `column=categorical`, `column=ordered` or `column=continuous` declarations for formats without column types (delimited text, Excel), and `ordered` for an R ordered factor, which `pyreadr` reads as unordered; blank otherwise |
| `formula` | the documented model verbatim (lme4 syntax where the source gives one) |
| `published_model` | `yes` when a published model specification exists (posteriordb, Stan example, textbook); else `no` |
| `domain` | `ecology_biology` / `psychology_neuroscience` / `biomedicine` / `social_humanities` / `agriculture` / `education` / `economics` / `industry` / `other`; reporting only |
| `confidence` | `high` / `medium` / `low` |
| `notes` | free text: the documentation read, cases the prompt does not settle (`RULE GAP:`) |

Script columns the merge fills: `tier` (from `sources.yaml`), `sources` (`source:object` of
every confirmed duplicate folded into the row, the row's own first), `reader` (the loader's
route: `pyreadr`, `rscript` or `pandas`).

## `excluded.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason`, `detail`; the merge adds
`tier`. `reason` ∈ `no grouping structure` / `time series without replication` /
`fewer than two groups` / `response missing or undocumented` / `derived or duplicated table` /
`unreadable format` / `licence forbids redistribution` / `too large`. An object is in the
registry or in the exclusions, never both: the shard that would put it in the second file is
refused. To re-file a misjudged object, drop it first (below).

## `duplicates.csv`

Key `source_a`, `object_a`, `source_b`, `object_b`, the pair written earliest tier first
whichever way a shard wrote it. Columns `verdict` and `notes`. The merge writes a pair with
`verdict` `flagged` when two registry objects have the same row count and the same sorted
column cardinalities; an agent answers through a `duplicates_<label>.csv` shard with `same`
or `different`. On every merge the confirmed `same` groups collapse into the row(s) of their
earliest-tier object, whose `sources` lists every member; the other members' rows leave the
registry, and re-merging their shard folds them again.

## `dropped.csv`

Key `source`, `object`. Agent columns `source`, `object`, `reason` (free text); the merge adds
`tier`. Merging a `dropped_<label>.csv` shard removes its objects from `registry.csv` and
`excluded.csv`, so that a later registry or excluded shard can re-file them; that later merge
removes them from `dropped.csv` again. A shard naming an object in neither file is refused.

## `dimensions.csv`

Key `source`, `object`, `model_index`, `factor`, with `tier`. Per grouping factor: `n_obs`,
`n_groups`, group sizes `group_size_min`, `group_size_p10`, `group_size_p50`, `group_size_p90`,
`group_size_max` (observed sizes: at or below the level under p50, at or above from p50 on),
`singleton_share`, `cv` (population standard deviation over the mean) and `alpha`, the
concentration of a symmetric Dirichlet fitted by moment matching to the group-size proportions
(`Var(p) = (1 − 1/G) / (G (G α + 1))` solved for α; `inf` for a balanced allocation). Per row,
repeated on each of its factors: `n_factors`, `relation` (`single` / `nested` / `crossed` /
`mixed`; a pair is nested when every level of one factor lies in one level of the other, the
row is nested or crossed when every pair is, mixed otherwise), `d_doc` and `d_all` (continuous
and binary columns count 1, a categorical K − 1, an interaction the product; `d_doc` over the
documented model, `d_all` over every column of `columns.csv`).

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
exists in the loaded table; each grouping factor has at least two levels and a level with two
or more rows; the response shows its declared type (`continuous` numeric, `binary` two
distinct values, `count` and `binomial` non-negative integers, `ordinal` at most 10 distinct
values, `categorical` not a float column); a `binomial` row names integer `trials` the
response never exceeds; the object is not in the rival file. A failing shard is refused with
its offending rows (line, key, column, value, problem) printed and nothing written. Upsert on
the key: merging a shard twice changes nothing, a corrected shard replaces its rows. Every merge
then measures the whole registry again.
