# Dimension survey — public grouped datasets

The lower edges, imbalance, factor-level distribution and covariate mix of real grouped data,
and the pool the v1 real-data test sets draw from. Spec: issue #14; tickets #15–#27. The
package's loader (`metabeta.glmm.datasets`, research extra) reads every source; the survey
scripts here own the file contract. The practice survey (`../practice/`) is the model;
nothing is imported across surveys. Results: `SUMMARY.md` (once #18 lands).

## Files

| file | written by | content |
|---|---|---|
| `sources.yaml` | discovery and hand (#19, #21) | the frame: tiers of pinned sources, see below |
| `candidates.csv` | pull script (#19) | every enumerated data object with its counts |
| `help/`, `cache/` | pull script, loader | untracked: documentation per object for the agents; downloads and extracted trees |
| `shards/<table>_<label>.csv` | agents | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates` |
| `registry.csv` | `merge.py` | one row per dataset and documented model, at most three per object |
| `excluded.csv` | `merge.py` | every screened-out object with a categorical reason |
| `duplicates.csv` | `merge.py` | candidate pairs the merge flagged and the verdicts agents returned |
| `dimensions.csv`, `columns.csv`, `quantiles.yaml`, `SUMMARY.md` | `merge.py` (#18) | measured on every merge, never typed |
| `prompts/read.md` | | what a reading agent gets and writes |
| `schema.py` | | file contract and allowed values |
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
| `types` | `;`-list of `column=categorical` or `column=continuous` declarations for formats without column types (delimited text, Excel); blank where the file carries types |
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
refused.

## `duplicates.csv`

Key `source_a`, `object_a`, `source_b`, `object_b`, the pair written earliest tier first
whichever way a shard wrote it. Columns `verdict` and `notes`. The merge writes a pair with
`verdict` `flagged` when two registry objects have the same row count and the same sorted
column cardinalities; an agent answers through a `duplicates_<label>.csv` shard with `same`
or `different`. On every merge the confirmed `same` groups collapse into the row(s) of their
earliest-tier object, whose `sources` lists every member; the other members' rows leave the
registry, and re-merging their shard folds them again.

## What the merge checks

Header equal to the agent columns; required fields; allowed values; `model_index` an integer
from 1 to 3; the source is in `sources.yaml` and the object in the source; every named column
exists in the loaded table; each grouping factor has at least two levels and a level with two
or more rows; the response shows its declared type (`continuous` numeric, `binary` two
distinct values, `count` and `binomial` non-negative integers, `ordinal` at most 10 distinct
values, `categorical` not a float column); a `binomial` row names integer `trials` the
response never exceeds; the object is not in the rival file. A failing shard is refused with
its offending rows (line, key, column, value, problem) printed and nothing written. Upsert on
the key: merging a shard twice changes nothing, a corrected shard replaces its rows.
