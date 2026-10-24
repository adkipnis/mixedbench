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
