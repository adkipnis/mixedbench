# Read prompt — dimension survey

## Role

You read the documentation of public grouped datasets and decide only what the data cannot
tell. Vocabulary follows `CONTEXT.md`.

## Input

Per object: its `candidates.csv` row and its help page `registry/help/<source>/<object>.txt`.
Columns and allowed values are in `README.md` and `schema.py`; the merge refuses a value
outside them or a column the table lacks.

## Exclude when

File the object in the excluded shard with its reason when:

- no grouping factor is documented (no subject, plot, school or site that rows repeat
  within): `no grouping structure`;
- it is one time series without replication (`time series without replication`), or a
  grouping column has `fewer than two groups`;
- it is derived from another object of the source (summary, aggregate table, subset):
  `derived or duplicated table`; an aggregate response on a real grouping stays, at `low`;
- the documentation calls it simulated, fictional or synthetic: `simulated data`;
- the loader refuses its format (`unreadable format`), its license forbids redistribution
  (`license forbids redistribution`), or it is `too large`.

## Record the model

1. **The documented model**, verbatim in `formula` (lme4 syntax where the source gives one).
2. **Response.** The column in `response`; what it holds in `response_type`, not the family: a
   Poisson fit over counts is `count`, successes out of trials `binomial` with `trials` named,
   proportions `continuous` with the denominator in the formula. A transformed response
   (`log(y)`) names the raw column `y`.
3. **Family.** Blank where ADR 0001's rule covers the model (Gaussian for continuous, Poisson
   for count, logit for binary and binomial, cumulative logit for ordinal). A departure takes
   its brms name from `Family` in `mixedbench/registry/row.py`; one outside that list leaves
   `family` blank with `RULE GAP:` in `notes`.
4. **Grouping factors, covariates, interactions** as `;`-lists of column names.
   - Nested factors are two factors; the merge computes the relation.
   - A random term on two columns (`(1|Block:Variety)`) is `Block:Variety`.
   - An observation-level effect (`(1|obs)`) is no grouping factor: its column goes in
     `ignore`, its term stays in the formula.
   - A column is a grouping factor or a covariate, never both.
   - What is no column of the table (a group mean, a recode) stays in the formula only.
5. **Ignore** row ids, weights, offsets, alternate responses, derived columns and field
   coordinates (`row`, `col`, latitude). An offset stays in the formula as `offset(log(area))`.
6. **Types the file cannot carry**, for covariates only. Text, Excel and JSON: `categorical`,
   `ordered` or `continuous` in `types` as documented. R, Stata and SPSS: only `ordered`
   factors, and `categorical` for a numeric column the model wraps in `factor()`.
7. **Published model.** `yes` when a published specification exists for this table: a
   posterior, a Stan example, a textbook's worked example, a documentation example stating the
   model. `no` for data only in tests or a docstring; a `no` row still carries your proposed
   formula.
8. **Documented prior**, only on a `yes` row, in the source's notation on one line:
   - the prior passed to this row's model call, trimmed to this row's response in a
     multivariate fit;
   - blank for package defaults, priors only in a supplement, and priors in words without
     parameters;
   - an unbounded Stan scale without a sampling statement is written as such.
9. **Domain, confidence, notes.** One domain tag. `high` when the documentation states the
   model; `medium` when it describes only the design, or you recall the model from a cited book
   (book and section in `notes`); `low` when you inferred the grouping factor from column
   names. `notes` say what you read; `RULE GAP:` opens any case these rules do not settle.

## Special cases

- **Further models.** A second or third row (`model_index` 2, 3) only when the response or the
  grouping factors differ; a fixed-effects simplification is the same model. Never more than
  three, the documented model first.
- **Multivariate tables.** One row per response in the page's order; responses beyond the third
  named in the first row's `notes`, every response not filed in that row's `ignore`.
- **Undocumented response.** A grouped table with no documented response or model is filed
  with the response a reader would model, at `low`, `notes` opening `RESPONSE INFERRED:`. Only
  a table with no defensible response is `response missing or undocumented`.
- **Nonlinear models** (PK or growth curves in `nlme`) stay for their grouping: `formula` names
  the class and inputs in words (`conc ~ one-compartment IV PK model (dose, time);
  subject-specific clearance and volume`), `notes` open `NONLINEAR:`, confidence at most
  `medium`, the inputs are covariates. Dosing rows without a response are no observations.
- **Stan data.** The table holds a data dict's observation-length arrays (matrices as `X_1`,
  `X_2`). Integer index columns are grouping factors; a group-level covariate not in the table
  goes to `notes`. Render the Stan code's random structure in lme4 syntax.
- **Code against prose.** Deposited code that produced the published results beats the prose;
  the prose goes to `notes`. Uncorrelated effects are `||`.
- **Tier D deposits.**
  - The documented model is the paper's on the table's columns; `high` when scripts or
    codebook confirm it. `published_model` is `yes` throughout.
  - A table that is not the paper's data (a cited deposit, a preregistration's pilot, stimuli,
    posterior draws, simulation output): `not the paper's data`.
  - A summary of the analysis table: `derived or duplicated table`. The analysis table without
    its grouping column: `no grouping structure`, said in `detail`.
  - A raw table the paper fits nothing on: `response missing or undocumented`, never
    `RESPONSE INFERRED`.
  - Files split by study or experiment are one row each; files split by coder, session or
    participant whose pooled table is in no file are `derived or duplicated table`.

## Output — shards only

- `shards/registry_<label>.csv` with exactly the agent columns of the registry;
  `shards/excluded_<label>.csv` with `source,object,reason,detail`.
- Only when asked to re-read a filed object, first `shards/dropped_<label>.csv` with
  `source,object,reason`.
- Every field double-quoted, internal `"` doubled, no line breaks inside a field.
- Never write `registry.csv`, `excluded.csv`, `duplicates.csv` or `dropped.csv`; never type a
  measured number; run nothing.
- Return `{shard, n_objects, n_rows, n_excluded, n_high}`.
