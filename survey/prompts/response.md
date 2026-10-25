# Response prompt — flat tables

## Role

You read the documentation of tables in the flat sample, tables the survey filed `no grouping
structure`, and name each one's response: the outcome of its first documented model, or `none`.
Vocabulary follows `CONTEXT.md`. A run holds about 60 objects, named in order by its worklist.

## Input

Per object of the worklist:

- its `registry/flat.csv` row: the `stratum`, and the `basis` and `evidence` of the reading that
  put the table in the sample;
- its help page `registry/help/<source>/<object>.txt`, which ends with the table's dtypes and
  first rows. Read a page longer than 20,000 characters in parts. A Tier D page opens with the
  path of its deposit page, which runs to hundreds of kilobytes: search it for the table's file
  name and its model, once per deposit.

## Response

1. **The first documented model** in the page's order: a model the documentation fits or states
   on this table (an example in the help page, a vignette, a textbook's worked example, the
   paper's analysis, a Stan program's likelihood). A regression of any family, an ANOVA, a test
   of one outcome across groups, a survival or a time-series model each have an outcome.
2. **Its outcome** is the response, named exactly as the dtypes at the page's end name the
   column. A transformed outcome (`log(y)`) names the raw column `y`; successes out of trials
   name the successes, and the trials stay a column.
3. **`none`** when:
   - no model is documented: the table is only described, plotted or summarized;
   - the outcomes are analyzed jointly (e.g. a correlation, a principal component, factor or
     cluster analysis, a test of independence);
   - the outcome is no column of the table: computed from several columns, or found only in
     another table.

A response is never inferred: a table without a documented model is `none`, even where one
column is plainly the outcome. `RULE GAP:` opens the evidence of any case these rules do not
settle.

## Not flat

A table you find grouped or wide, as `prompts/flat.md` defines `hidden grouping` and `wide`,
keeps its response, and its evidence opens with `NOT FLAT:` and names the deciding columns. Write
no other shard for it.

## Evidence

One line per object: the model as the documentation writes it (the call or the formula) and
where it stands (the help page's examples, a vignette's section, the paper's table); for `none`,
which of the three cases holds and why.

## Output — shards only

- `shards/response_<label>.csv` with `source,object,response,evidence`, one row per object in
  the worklist's order.
- Every field double-quoted, internal `"` doubled, no line breaks inside a field.
- Never write `flat_responses.csv`, `flat.csv` or any file but the shard; never type a measured
  number; run nothing.
- Return `{shard, n_objects, n_named, n_none, n_not_flat}`.
