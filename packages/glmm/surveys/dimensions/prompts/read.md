# Read prompt — dimension survey

You read the documentation of public grouped datasets and decide only what the data cannot
tell. Every number about a table (rows, groups, group sizes, levels, columns) is measured by
the merge script from the loaded table; you never type one.

## Input

For each object of your shard: its `candidates.csv` row (`source`, `object`, `n_rows`,
`n_cols`, per-dtype counts), its documentation under `help/<source>/<object>.txt` (R help
page, README, codebook, or a paper's methods excerpt) and the first rows of the table.
Vocabulary follows `packages/glmm/CONTEXT.md`: a **grouping factor** is a column whose levels
index random effects; the **response** is the column a documented model explains; the
**family** is the likelihood that model names for it.

## Decide per object

1. **Grouped or not.** If the documentation names no grouping factor (no subject, plot, school,
   herd, site, judge or the like that observations repeat within), or the table is one time
   series without replication, or a grouping column has fewer than two groups, the object goes
   to the excluded shard with its reason. Likewise a response that is missing or undocumented,
   a table derived from another object of the same source (a summary, an aggregate, a subset),
   a table the documentation calls simulated (the survey measures real grouped data), a format
   the loader refuses, a licence that forbids redistribution, or a table too large to hold in
   memory.
2. **The documented model.** The model the documentation fits or describes, verbatim in
   `formula` (lme4 syntax where the source gives one). Its response goes in `response`, what
   that column holds in `response_type` (not the family: a Poisson or negative binomial fit
   over counts is `count`; a binomial fit over successes out of trials is `binomial` with the
   `trials` column named; a transformed response such as `log(y)` names the raw column `y`).
   Its grouping factors, covariates and interactions as `;`-lists of column names; nested
   factors as two factors, the merge computes the relation; a random term on the combination
   of two columns (`(1|Block:Variety)`, the whole plots of a split-plot) is the term
   `Block:Variety`, which the merge builds from its parts. An observation-level random effect
   (`(1|obs)` on a row id) is no grouping factor: its column goes in `ignore`, the term stays
   in the formula. A nonlinear mixed model (a pharmacokinetic or growth curve fitted with
   `nlme`) stays in the registry for its grouping: `formula` names the model class and its
   inputs in words (`conc ~ one-compartment IV PK model with first-order elimination (dose,
   time); subject-specific clearance and volume`), `notes` open with `NONLINEAR:`, confidence
   at most `medium`; its inputs (time, dose, concentration) are covariates like any other
   column the model uses. Rows without a measured response (dosing events) are no
   observations; the merge drops them before measuring.
3. **Further documented models.** A second or third documented model is a further row with
   `model_index` 2 or 3; never more than three, the documented model first.
4. **Columns to ignore.** Row ids, weights, offsets, alternate responses and derived columns
   in `ignore`, so that the full-table column count excludes them; an offset stays in the
   formula as `offset(log(area))`.
5. **Types the file cannot carry.** For delimited text, Excel and JSON, declare in `types`
   which columns are `categorical`, `ordered` or `continuous` where the documentation says
   so. For R, Stata and SPSS files declare only `ordered` factors (the help page says
   "ordered factor"; the reader loses the ordering) and `categorical` for a numeric column
   the documented model wraps in `factor()` (agridat's `factor(nitro)`); leave the rest
   blank. Declare
   `ordered` for covariates only: a grouping factor stored as an ordered factor (nlme's
   `groupedData` orders subjects by their mean) is a nominal id, declare nothing for it.
6. **Published model.** `published_model` is `yes` when a published model specification
   exists for the dataset (posteriordb, Stan example models, a textbook's worked example), else
   `no`.
7. **Domain, confidence, notes.** One domain tag for reporting; `high` confidence when the
   documentation states the model, `medium` when it describes the design but not a model or
   when you recall the model from the book the page cites (name book and section in `notes`),
   `low` when you inferred the grouping factor from column names. Name what you read and any
   case these rules do not settle in `notes`, starting `RULE GAP:`.

Allowed values and columns are in `README.md` and `schema.py`; the merge refuses a shard with
a value outside them or a column name the table lacks.

## Output — shards only

Write `shards/registry_<label>.csv` with exactly the agent columns of the registry and
`shards/excluded_<label>.csv` with `source,object,reason,detail`. Only when asked to re-read an
object already filed, write `shards/dropped_<label>.csv` with `source,object,reason` first.
Every field double-quoted, internal `"` doubled, no line breaks inside a field. Never write
`registry.csv`, `excluded.csv`, `duplicates.csv` or `dropped.csv`; never type a measured
number; run nothing. Return
`{shard, n_objects, n_rows, n_excluded, n_high}`.
