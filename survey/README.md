# The survey

The pipeline that built the registry: which public grouped tables exist, their documented
models, and their sizes and quirks measured by script. The files it writes are documented in
[`docs/registry.md`](../docs/registry.md), their counts in [`SUMMARY.md`](../registry/SUMMARY.md),
and what each pass did and decided in [`HISTORY.md`](HISTORY.md). The survey closed on
2026-10-08 and has been corrected since.

## Method

One pass per tier (`R` CRAN packages, `E` ecosystem examples, `T` textbook companions, `D`
deposits of the practice survey's papers, `O` open tabular repositories):

1. **Frame.** Sources pinned in `registry/sources.yaml`.
2. **Pull.** `pull.py` fetches every source through the loader, lists its objects in
   `candidates.csv`, pre-screens them and writes a help page per passing object.
3. **Reading.** Agents read shards of about 60 help pages by [`prompts/read.md`](prompts/read.md)
   and file each object in a registry or an excluded shard.
4. **Merge.** `merge.py` validates a shard against the row grammar and the table, upserts it,
   folds duplicates, measures, and rewrites the manifest and the summary. A failing shard is
   refused, its rows printed, nothing written.
5. **Fits.** `fits.py` fits each documented model by lme4, a cluster array task per row, and
   collects `fits.csv`; a merge leaves it as it is.
6. **Checks.** A blind second reading of the `medium` and `low` rows, a spot check per tier and
   two hand samples against [ADR 0002](../docs/adr/0002-registry-suite-versioning-licenses.md)'s
   bar; the outcomes are in [`HISTORY.md`](HISTORY.md).
7. **Flat pass.** `flat.py screen` derives the frame of flat tables from the exclusions filed
   `no grouping structure` and flags a read table whose filing line says wide, repeat, occasion
   or visit, or that has a repeated column with an id-like name. Agents give each flagged table
   a verdict by [`prompts/flat.md`](prompts/flat.md). `flat.py measure` measures the flat sample
   into `registry/flat.csv` and `flat_columns.csv`, then rewrites the summary; a merge leaves the
   two files as they are. `draw`, `handoff` and `agree` run the hand sample, and `wide` lists the
   tables judged `wide` for the issue of their long forms
   ([ADR 0007](../docs/adr/0007-flat-sample.md)).

```
uv run python survey/pull.py [--tiers E O]
uv run python survey/merge.py survey/shards/<shard>.csv
uv run python survey/measure.py
uv run python survey/fits.py run <index>
uv run python survey/fits.py collect
uv run python survey/flat.py screen
uv run python survey/flat.py measure
uv run python survey/flat.py wide
uv run python survey/mirror.py --tag mirror-<n>
```

`pull.py`, `merge.py`, `measure.py`, `fits.py` and `flat.py` take `--registry DIR` and `--survey DIR`
(default `registry/`, `survey/`), `fits.py` also `--dir DIR` for its run directories (default
`fits/`). `pull.py --tiers` pulls only those tiers; the others keep their rows.

## Files

| file | content |
|---|---|
| `pull.py`, `merge.py`, `measure.py`, `mirror.py` | the scripts: the pull, the merge, the measurement pass, a mirror tag for the loader's fallback copies |
| `fits.py`, `fits.sbatch` | the fits pass and its cluster array |
| `flat.py`, `prompts/flat.md` | the flat pass and the second reading's brief |
| `fits_preparation.csv` | the rows a source fitted where they are not the whole table: a subset or a frequency weight, read by `fits.py` |
| `schema.py`, `sources.py`, `help.py`, `summarize.py` | the survey's file contract, the frame, the help pages, the summary |
| `dimensions.py`, `columns.py`, `groups.py`, `pairs.py` | one module per measured file |
| `SUMMARY.template.md` | the digit-free template of `registry/SUMMARY.md` |
| `prompts/read.md` | the reading agent's brief |
| `shards/<table>_<label>.csv` | one shard per reading run; `table` ∈ `registry`, `excluded`, `duplicates`, `dropped`, `flat` (the verdicts) |
| `candidates.csv`, `duplicates.csv`, `dropped.csv` | the bookkeeping (below) |
| `flat_screen.csv`, `flat_verdicts.csv`, `flat_sample.csv`, `flat_agreement.csv` | the flat pass's bookkeeping: the screen (below), the verdicts ([`docs/registry.md`](../docs/registry.md)), the hand sample of 50 with what its handoff showed at draw time, and the share that stood per stratum |
| `deposits.csv`, `deposit_files.csv` | Tier D's frame: the drawn papers and every file their deposits list |
| `sample.csv`, `agreement.csv` | the second hand sample (#61): 100 candidates not yet hand-checked with their readings at draw time, and the share of readings that stood per field |
| `practice_quantiles.yaml` | the practice survey's `quantiles.yaml` (metabeta-v3), the practice column of `SUMMARY.md` |
| `registry/help/`, `registry/cache/` | untracked: one help page per kept object; the downloads |
| [`archive/`](https://github.com/adkipnis/mixedbench/tree/survey-archive-3/survey/archive) | finished scripts and their outputs, kept at tag `survey-archive-3` and reproducible at tags `survey-archive` and `survey-archive-2` ([README](https://github.com/adkipnis/mixedbench/blob/survey-archive-3/survey/archive/README.md)) |
| `tests/` | `uv run pytest survey/tests`, by hand; the root run never recurses here |

## Bookkeeping

`candidates.csv` and the pre-screen:

- Key `source`, `object`; rewritten whole by every pull, in frame order.
- Columns `tier`, `source`, `pin`, `object`, `file`, `n_rows`, `n_cols` (blank without a
  DataFrame), dtype counts `n_numeric`, `n_categorical`, `n_string`, `n_other`, `reader`
  (`pyreadr` / `rdata` / `pandas` / `deparse`), `screen`, `capped`.
- `screen`: `no frame`, `under 3 rows`, `one column`, `no repeated column` (no column that
  could index groups), else `pass`. Discards go to `shards/excluded_prescreen.csv`, `no frame`
  as `unreadable format`, the rest as `no grouping structure`.
- `capped` is `yes` for passing objects the cap left out. Agents read the `pass`, uncapped rows.

The merge's files:

- An object is in the registry or the exclusions, never both; to re-file one, drop it first.
- `duplicates.csv`: key `source_a`, `object_a`, `source_b`, `object_b` in frame order, with
  `verdict` and `notes`. The merge flags (`flagged`) two registry objects with equal row counts
  and sorted column cardinalities; a shard answers `same` or `different`. Confirmed groups fold
  into their first object in frame order (nlme before MEMSS), the others leave the registry.
- `dropped.csv`: key `source`, `object`; agent columns `source`, `object`, `reason`, plus
  `tier`. A dropped object leaves `registry.csv` and `excluded.csv` until a later shard re-files
  it. One the loader no longer enumerates is deleted from every file instead (#14).

`flat_screen.csv`, the second reading's worklist, rewritten whole by `flat.py screen`:

- Key `source`, `object`; one row per table of the flat frame in frame order, with `tier` and
  `stratum`: `read` where the pre-screen passed and an agent filed it, `prescreened` where the
  pre-screen stopped at `no repeated column`.
- `words`: the filing line's words that say wide, repeat, occasion or visit. `id_columns`: the
  columns that could index groups and are named like an id. `integer_columns`: those of more
  than ten integer levels, which flag nothing. Lists are `;`-separated; a prescreened table has
  none.
- `flagged`: `yes` where `words` or `id_columns` is not empty.
