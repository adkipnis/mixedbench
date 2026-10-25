---
status: accepted
date: 2026-10-24
---

# 0007 — The flat sample: the survey's own flat tables, measured like the registry

The registry holds grouped tables alone, so a generator's flat case, a table with no grouping
factor, has no real reference to be matched to, and the question whether grouped tables differ
from flat ones beyond the grouping factor has no data. The survey already read the flat tables
that the registry's sources ship beside their grouped ones and filed them as `no grouping
structure`. This ADR makes them the flat sample: the same frame, the same statistics, beside
the registry. Grilled on 2026-10-24 ([#72](https://github.com/adkipnis/mixedbench/issues/72)).

**Purpose.**

- Decision: the flat sample is the reference a generator's flat case is matched to, the first
  and simplest case of matching a generator to real tables; the differences between flat and
  grouped tables are a finding reported beside it, never the reason for the sample's design.
- Why: a match on flat tables is the proof of concept before the grouped case, and a later
  consumer (a survival generator) matches its flat case the same way.

**The frame.**

- Decision: every object the survey filed `no grouping structure`, in two strata: the tables the
  pre-screen passed and a reading agent filed, and the tables the pre-screen stopped at `no
  repeated column` (no column with a repeated value that could index groups) with at least
  three rows and two columns. Objects stopped at `one column` or `under 3 rows` stay out.
- Why the survey's own frame: the same sources, pins, loader, licence terms and reading brief
  as the registry's rows, so the only difference between a flat table and a registry row is
  that no documented model has a random effect; nothing is gathered.
- Rejected: an outside repository (OpenML, UCI, a curated list such as TabArena's) minus its
  overlap with the registry. Those tables were curated for supervised learning, one target
  column and thousands of rows, so a difference to the registry would mix flat against grouped
  with benchmark against statistics source; and the frame would need its own reading and
  licence pass. Open repositories are in the frame already, as one tier.
- Rejected: the pre-screened stratum alone. Its tables have no categorical column by
  construction (every column is constant or all-unique), so the sample's type mix would be an
  artifact of the pre-screen.

**Comparable.**

- Decision: the whole frame, unmatched; `source` and `tier` are kept per table, so a comparison
  within the sources that also have a registry row, or per tier, is a filter.
- Why: sizes, the type mix and the number of levels are among the dimensions the finding asks
  about, so matching on them would decide the answer before the comparison.
- Rejected: matching on rows and columns; a paired-by-source definition, which is the filter.

**Flat, and the bar.**

- Decision: a table is flat when no documented model fits it with a random effect and no column
  indexes a unit the rows repeat within. Grouped data stored wide, with its repeated measures as
  columns, is not flat but grouped data the registry lacks a long form of.
- Decision: a mechanical screen flags a read table whose filing says wide, repeated, occasion or
  visit, or that holds a column with repeated values and an id-like name or many integer levels.
  The flagged tables get a second reading with one verdict each, `flat`, `wide` or `hidden
  grouping`; the unflagged ones stand on their first reading. A seeded hand sample of 50 tables
  across both strata is checked at the source, and the share that stood is the sample's bar,
  recorded as the registry's hand samples are.
- Why not a second reading of every table: the first reading asked the flatness question, and
  its filing lines carry the evidence; the two oversight cases are the ones the screen flags.
- Decision: a `hidden grouping` verdict re-files the table through the survey's normal path, a
  dropped shard and a registry shard, so the registry gains rows and the fits pass runs on them
  before the release. A `wide` verdict leaves the table out of the sample and on a list that
  opens an issue for a long form, since the manifest names one file per object and the loader
  has no reshape; the reshape is its own decision.

**The statistics.**

- Decision: ADR 0006's per-column statistics unchanged, computed by the same functions over every
  column and every row of a flat table, with the sizes (rows, columns, the type mix, K) and, per
  table, `d_all` and `condition_all` as `dimensions.csv` defines them over every measured
  column. No response, no `in_model`, no fit.
- Why no new statistic: a statistic the registry lacks cannot be compared.
- Decision: a census of the frame, never a draw; the frame's size is the sample's size, and the
  draw is only the hand sample.

**Files, summary and release.**

- Decision: two files beside the registry, written by script from the survey's files (the
  candidates' screen, the exclusions' reason, the verdict shard), never by hand: `flat.csv`, one
  row per flat table with its sizes, `d_all`, `condition_all`, its verdict and evidence; and
  `flat_columns.csv`, the per-column statistics with `columns.csv`'s columns less the ones a
  model binds (`model_index`, `in_model`, `level`, `constant_within`).
- Rejected: a `sample` column in `columns.csv` and `dimensions.csv`, which would make every
  reader of the registry filter on every read, the registry being defined over grouped tables.
- Decision: every statistic both samples share keeps its axis in `quantiles.yaml` under `axes`
  and gains a `flat` split beside `pooled`, the tiers and `without agridat`; `SUMMARY.md`'s
  tables gain a `flat` row. For the size axes, `n_obs` is every row of a flat table and
  `n_design_columns` is `d_all`.
- Why: one home per statistic, and the comparison is visible in the summary without a notebook;
  metabeta's contract test pins the file's top-level keys, which stay as they are.
- Decision: the comparison for the paper is an experiment, `experiments/flat/`, committed with
  its outputs. Its unit is the table, one value per statistic (its median over columns, its type
  shares), with a two-sample test and an effect size per statistic; `SUMMARY.md` keeps the
  registry's per-column pooling.
- Why the table: the question is whether tables differ, and one table of the frame has 26 441
  columns. Rejected: a cap on that table, a rule with no witness.
- Decision: the sample ships as a registry patch release, with the re-filed rows and their fits,
  before a generator's flat case is matched to it.

## Amendment 2026-10-24: the screen's rules ([#72](https://github.com/adkipnis/mixedbench/issues/72))

- Decision: the mechanical screen flags a read table on two rules, a filing line that says wide,
  repeated, occasion or visit, or a column with repeated values and an id-like name; a column of
  many repeated integer levels flags nothing. The tables only that rule would have flagged are a
  stratum of the hand sample of 50, so the sample tests the rule; a share under the bar brings
  the rule back and its tables get the second reading.
- Why: a prototype of the three rules over the 842 read tables flagged 219 by the filing line, 211
  by an id-like name, 362 by either, and 572 by the integer rule alone, which caught field
  coordinates (`row`, `col`) and counts; with it the targeted second reading would be a second
  pass over 677 tables.

## Amendment 2026-10-24: duplicates, and grouped tables the registry leaves out ([#118](https://github.com/adkipnis/mixedbench/issues/118))

- Decision: a frame table that copies another frame table or a registry object leaves the frame
  as `derived or duplicated table`, before the release, and the copy kept is the registry
  object, else the first in frame order. A script settles copies with equal columns and values,
  row order ignored, and a reading agent the rest of the tables that share the merge's
  duplicate signature.
- Why: a census counts each table once, and a copy of a registry object would count a grouped
  table as flat.
- Decision: a table both wide and grouped is `wide`, since its long form is the table the
  registry would hold.
- Decision: a `hidden grouping` whose only repeated unit is a wave that a documented model fits
  as fixed or separately per wave keeps its exclusion, out of the sample and with no registry
  row (GSSvocab).
- Why: its rows repeat within waves, so it is not flat, but the registry's reading rules leave
  such a wave out.

## Amendment 2026-10-25: the response ([#130](https://github.com/adkipnis/mixedbench/issues/130))

- Decision: a reading names each flat table's response, the outcome of its first documented
  model, or `none` when no model is documented, the outcomes are analyzed jointly (e.g. PCA)
  or the outcome is no column of the table. A response is never inferred, and a binomial
  trials column stays a column.
- Decision: the response leaves `flat_columns.csv` and every count and design statistic of
  `flat.csv`, `max_abs_rho` included, as a registry row's response leaves `columns.csv` and
  `dimensions.csv`. This replaces "no response" under the statistics.
- Why: `columns.csv` measures a registry row's covariates alone, so a flat table's response
  would count as a covariate in the comparison. If every flat table's response were
  continuous, the rank-biserial r of the continuous share would move from −0.45 to −0.34.
- Why none is inferred: the registry's reading infers a response because a grouped table
  needs a model to fit, but a flat table without a model has no outcome to leave out.
- Decision: a seeded hand sample of 25 tables (seed 3), stratified by whether the reading
  named a response, checks it at ADR 0002's bar of 0.8 per stratum.
- Rejected: leaving out the trials and `ignore` columns (ids, weights, alternate responses) as
  the registry does, which would turn the response reading into a registry reading.
