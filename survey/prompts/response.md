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
  name and its model, once per deposit;
- the files its source ships at its pin in the source's tree under `registry/cache/`: example
  and chapter scripts, vignettes, demos, notebooks, Stan programs, do-files, a deposit's code.
  Search them for the table's name or file name;
- the material the source's authors or publisher wrote, wherever it is hosted: the source's
  documentation site, its book's companion page, the published book code, course scripts.
  Cite it by URL in the evidence.

## Response

1. **The first documented model**, the help page's first, else the first in the source's files,
   else the first in its authors' or publisher's material, each in the order the source
   presents them (a book's chapters, a vignette's sections): a model the documentation fits or
   states on this table (an example in the help page, a vignette, a chapter script, the paper's
   analysis, a Stan program's likelihood).
   A regression of any family, an ANOVA, a test of one outcome across groups, a survival or a
   time-series model each have an outcome, and so does a fit of one column's distribution.
   A model fitted on a subset, a renaming or a re-export of this table's rows documents this
   table too; test code does not.
   Without a model, an outcome the documentation names in words counts: a column it calls the
   response or the outcome, or the quantity it says an analysis of this table relates to the
   other columns.
2. **Its outcome** is the response, named exactly as the dtypes at the page's end name the
   column. A transformed outcome (`log(y)`) names the raw column `y`; successes out of trials
   name the successes, and the trials stay a column.
3. **`none`** when:
   - no model is documented and no outcome named: the table is only described, plotted or
     summarized, or the documentation names a topic of interest but no column, or two outcomes
     without an order;
   - the outcomes are analyzed jointly (e.g. a correlation, a principal component, factor or
     cluster analysis, a test of independence);
   - the outcome is no column of the table: computed from several columns, aggregated to other
     units, or found only in a table that does not hold this table's rows.

A response is never inferred: a table whose documentation neither models nor names an outcome
is `none`, even where one column is plainly the outcome. A model recalled from a book that
neither the source's files nor its authors' or publisher's material hold is no documentation,
and nor is an analysis by others (a blog, another author's course).
`RULE GAP:` opens the evidence of any case these rules do not settle.

## Not flat

A table you find grouped or wide, as `prompts/flat.md` defines `hidden grouping` and `wide`,
keeps its response, and its evidence opens with `NOT FLAT:` and names the deciding columns. Write
no other shard for it.

## Evidence

One line per object: the model as the documentation writes it (the call or the formula), or
its words naming the outcome, and where it stands (the help page's examples, a script's path, a
vignette's section, the paper's table); for `none`, which of the three cases holds and why.

## Output — shards only

- `shards/response_<label>.csv` with `source,object,response,evidence`, one row per object in
  the worklist's order.
- Every field double-quoted, internal `"` doubled, no line breaks inside a field.
- Never write `flat_responses.csv`, `flat.csv` or any file but the shard; never type a measured
  number; run nothing.
- Return `{shard, n_objects, n_named, n_none, n_not_flat}`.
