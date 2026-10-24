# Flat prompt — second reading

## Role

You read again a table the survey filed `no grouping structure` and the flat pass's screen
flagged, and decide whether it is a flat table. Vocabulary follows `CONTEXT.md`. A run holds
about 60 objects, named in order by its worklist.

## Input

Per object of the worklist:

- its `registry/excluded.csv` row, whose `detail` is the first reading's filing line;
- its `survey/candidates.csv` row;
- its `survey/flat_screen.csv` row: the filing line's `words` and the `id_columns` that flagged
  it;
- its help page `registry/help/<source>/<object>.txt`, which ends with the table's dtypes and
  first rows. A Tier D page opens with the path of its deposit page, which runs to hundreds of
  kilobytes: search it for the table's file name and its model, once per deposit.

## Verdict

One per object, with the evidence for it in one line: the columns that decide and the
documentation's words for them.

- `wide`: grouped data stored wide, its repeated measures as columns (`y1` to `y4` for four
  visits, one column per year), whether or not the source also holds its long form, which the
  evidence then names.
- `hidden grouping`: a column indexes a unit the rows repeat within, a subject, plot, school,
  site or wave with two or more rows each, whether or not the documentation fits a model with
  it. It is a grouping factor the first reading missed.
- `flat`: everything else. No documented model fits the table with a random effect and no
  column indexes a unit the rows repeat within. A design factor of fixed levels (treatment,
  dose, sex), a field coordinate, a count and an id with one row per unit are no grouping
  factor.

The screen's flag is a reason to look, never evidence: a flagged column `trials` that counts
trials is no grouping factor.

## Hidden grouping

A `hidden grouping` re-files the object as the read prompt (`prompts/read.md`) describes, in
shards named by the run's label:

- first `shards/dropped_flat_<label>.csv` with `source,object,reason`, the reason `second
  reading of a flat table found a grouping factor the first reading missed`;
- then the object's rows in `shards/registry_flat_<label>.csv`, read by that prompt;
- where that prompt excludes the object for another reason (a `derived or duplicated table`),
  its row in `shards/excluded_flat_<label>.csv` instead, which replaces its filing without a
  dropped row.

They merge after the verdict shard.

## Output — shards only

- `shards/flat_<label>.csv` with `source,object,verdict,evidence`, one row per object in the
  worklist's order; for a hidden grouping also the shards above.
- Every field double-quoted, internal `"` doubled, no line breaks inside a field.
- Never write `flat_verdicts.csv`, `registry.csv`, `excluded.csv` or `dropped.csv`;
  never type a measured number; run nothing.
- Return `{shard, n_objects, n_flat, n_wide, n_hidden_grouping}`.
