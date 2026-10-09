# Read prompt — dimension survey

You read the documentation of public grouped datasets and decide only what the data cannot
tell. Every number about a table (rows, groups, group sizes, levels, columns) is measured by
the merge script from the loaded table; you never type one.

## Input

For each object of your shard: its `candidates.csv` row (`source`, `object`, `n_rows`,
`n_cols`, per-dtype counts), its documentation under `registry/help/<source>/<object>.txt` (R help
page, README, codebook, or a paper's methods excerpt) and the first rows of the table.
Vocabulary follows `CONTEXT.md` at the repository root: a **grouping factor** is a column whose levels
index random effects; the **response** is the column a documented model explains; the
**family** is the likelihood that model names for it.

## Decide per object

1. **Grouped or not.** If the documentation names no grouping factor (no subject, plot, school,
   herd, site, judge or the like that observations repeat within), or the table is one time
   series without replication, or a grouping column has fewer than two groups, the object goes
   to the excluded shard with its reason. Likewise a table derived from another object of the
   same source (a summary, an aggregate, a subset),
   a table the documentation calls simulated (the survey measures real grouped data), a format
   the loader refuses, a licence that forbids redistribution, or a table too large to hold in
   memory.
2. **The documented model.** The model the documentation fits or describes, verbatim in
   `formula` (lme4 syntax where the source gives one). Its response goes in `response`, what
   that column holds in `response_type` (not the family: a Poisson or negative binomial fit
   over counts is `count`; a binomial fit over successes out of trials is `binomial` with the
   `trials` column named; a transformed response such as `log(y)` names the raw column `y`).
   `family` stays blank when the family rule of ADR 0001 covers the documented model (Gaussian
   for continuous, Poisson for count, logit for binary and binomial, cumulative logit for
   ordinal); only a departure is filed, as brms names it: `negbinomial`, `bernoulli(probit)`,
   `cumulative(probit)`, `Gamma(log)`, `lognormal`, `zero_inflated_poisson`,
   `zero_inflated_negbinomial`, `hurdle_poisson`, `hurdle_negbinomial`, `Beta`,
   `bernoulli(cloglog)`, `Gamma(identity)`, `zero_inflated_beta`, `student`, `gaussian` (a
   Gaussian fit to a count or ordinal response), `acat`, `weibull`, `cox`. A departure
   outside this list goes in `notes` as `RULE GAP:`.
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
   `model_index` 2 or 3 only when its response or its grouping factors differ from the first;
   a nested simplification of the fixed effects (Littell's fm1 to fm3 ladders) is the same
   model. Never more than three, the documented model first. A multivariate table (several
   response variables over one grouping, a MANOVA example) is one row per response in the
   order the page lists them, the responses beyond the third named in the first row's `notes`
   and every response not filed in that row's `ignore`.
4. **Undocumented response.** A grouped table whose page documents no response and no model
   is filed with the response a reader of the page would model, the outcome the data were
   collected to study, at `low`; `notes` open with `RESPONSE INFERRED:` and say why. Only a
   table with no defensible response is excluded as `response missing or undocumented`.
5. **Columns to ignore.** Row ids, weights, offsets, alternate responses, derived columns and
   the plot coordinates of a field layout (`row`, `col`, latitude) in `ignore`, so that the
   full-table column count excludes them; an offset stays in the formula as
   `offset(log(area))`.
6. **Types the file cannot carry.** For delimited text, Excel and JSON, declare in `types`
   which columns are `categorical`, `ordered` or `continuous` where the documentation says
   so. For R, Stata and SPSS files declare only `ordered` factors (the help page says
   "ordered factor"; the reader loses the ordering) and `categorical` for a numeric column
   the documented model wraps in `factor()` (agridat's `factor(nitro)`); leave the rest
   blank. Declare
   `ordered` for covariates only: a grouping factor stored as an ordered factor (nlme's
   `groupedData` orders subjects by their mean) is a nominal id, declare nothing for it.
7. **Published model.** `published_model` is `yes` when a published model specification
   exists for the dataset: a posteriordb posterior, a Stan example model, a textbook's worked
   example, or a documentation example (a PyMC or bambi notebook, a Stata manual entry, the
   MixedModels.jl docs) that states the model fitted to this table (decided 2026-10-07, #24);
   `no` when the data appear only in tests or a docstring without a model. A `yes` row whose
   source states the priors (a Stan or BUGS model, brms `set_prior`, a textbook's words) gets
   them in `documented_prior`, in the source's notation, on one line; blank when it states
   none, and always blank on a `no` row.
8. **Stan data.** A Stan data dict (posteriordb, the Stan examples) was read as the table of
   its observation-length arrays; the page says which entries are not in the table (scalars,
   group-level arrays) and which matrices became numbered columns (`X_1`, `X_2`). Integer
   index columns (`county`, `subj`) are grouping factors like any other column and need no
   `types` declaration; a group-level covariate that is not in the table cannot be a
   covariate and is named in `notes`. The hierarchical term is read from the Stan code the
   source fits to the data; `formula` renders it in lme4 syntax.
9. **Domain, confidence, notes.** One domain tag for reporting; `high` confidence when the
   documentation states the model, `medium` when it describes the design but not a model or
   when you recall the model from the book the page cites (name book and section in `notes`),
   `low` when you inferred the grouping factor from column names. Name what you read and any
   case these rules do not settle in `notes`, starting `RULE GAP:`.

10. **Tier D deposits.** A Tier D object is one file of a deposit (Dryad, OSF, Zenodo,
   figshare) named by a paper of the practice survey; its page opens with the deposit's
   page: title, licence, description, the paper's text around the link, the paper's models
   as the practice survey filed them (`formula_verbatim`, `family`, `n_obs`,
   `n_groups_per_factor`), the deposit's file listing, then its README, codebook and
   analysis scripts. The documented model is the paper's model as filed, rendered on the
   table's columns, at `high` when the columns match it and the scripts or codebook confirm
   it; `published_model` is `yes` throughout the tier. A table that is not the paper's data
   (a deposit the paper merely cites, a preregistration's pilot, a stimulus list, a fitted
   model's posterior draws, a simulation output) is excluded as `not the paper's data`; a
   summary table derived from the analysis table is `derived or duplicated table`; the
   analysis table without the grouping column (anonymised away) is `no grouping structure`
   with that said in `detail`; a raw table on which the paper fits nothing (its model runs
   on an aggregate built from it, or needs columns it lacks) is `response missing or
   undocumented`, never a `RESPONSE INFERRED` row: in this tier the recorded model is a
   reported or deposited analysis, not a GLMM that could be fitted (decided 2026-10-08). Several files that are one dataset split by study or
   experiment are one row each; a dataset split into one file per coder, session or
   participant whose pooled table is in no file is excluded as `derived or duplicated
   table` (decided 2026-10-08).

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
