# MixedBench

The language of MixedBench, a benchmark of posterior approximation and prediction for
generalized linear mixed models (GLMMs) on real grouped data.
Statistical terms (family, link, fixed and random effects, grouping factor, standardized
scale) are those of MetaBeta's glossary and are not redefined here.

## Language

### Problems

**Source**:
A pinned and checksummed upstream location of public data, a CRAN package at a version, a git
repository at a revision or a url with a sha256. A source is fetched, never redistributed.
_Avoid_: dataset (one source holds many), mirror

**Table**:
One loaded data object, the rows of a grouped dataset with its grouping factors among the
columns. A source holds many tables, and a table can carry several documented models.
_Avoid_: dataset, hierarchical dataset (a table with a grouping factor), data frame

**Manifest**:
The list of the file that holds each table inside its source, with the file's checksum. The
loader fetches and checks that file alone.
_Avoid_: index, file list

**Documented model**:
The GLMM a source's own documentation fits to a table, in its help page, a textbook chapter,
an example notebook or a paper. A row whose model a reader proposed is marked so.
_Avoid_: ground truth, the true model

**Registry**:
The list of every documented model over every grouped table the survey found, one row per
table and model, with its dimensions measured by script. It is a census of a stated frame,
never a sample, and it grows with every survey pass.
_Avoid_: benchmark, corpus, suite (a subset)

**Contract**:
The fixed rules that turn a registry row and its table into a problem (rows dropped, coding,
standardization, family, prior, splits), so that two results on one problem compare. It binds
the benchmark but not the user, who may fit any model to a table, and a change to a rule makes
a new suite.
_Avoid_: preprocessing (one part of it), config

**Problem**:
One registry row under the contract, with its design, family, prior and splits, identified as
`<source>/<object>/<model_index>`. It is the unit everything is computed and scored on.
_Avoid_: dataset, task, posterior (posteriordb's word for the same thing)

**Materialized problem**:
A problem written to files, a table of its coded columns in raw units with the response,
trials, grouping factors and each row's folds, and a record of what the table cannot hold
(family, prior, column roles, per-fold scales, contract hash). It is the package's interface to
a problem, a cache rebuilt from the pins and never redistributed.
_Avoid_: dataset, export, the parquet

**Regime**:
How a track chooses the rows a fit sees, the full table for the posterior track, or held-out
rows inside seen groups or held-out groups for the predictive track, each dealt into folds.
_Avoid_: split (the partition)

**Fold**:
One part of a regime, the rows it holds out for a fit on every other row to predict. A row is
held out in at most one fold of a regime, and the full table is one fold that holds nothing
out. Standardization is computed per fold on the rows its fit sees.
_Avoid_: split, partition

**Verified row**:
A registry row admitted on its reading, checked by hand, read with high confidence or read
again blind and adjudicated where the two readings disagreed. The `verified` column records
which, as `hand`, `high` or `second-reading`.
_Avoid_: validated, trusted

**Candidate list**:
The verified rows whose response the contract's family rule covers, with their contract
hashes, admitted before any reference exists. A suite is the subset whose references pass the
bar.
_Avoid_: the suite, shortlist

**Suite**:
A frozen, versioned list of problems with reference posteriors, admitted by verification, the
diagnostics bar and the compute cap. The contract is the recipe and the suite the menu, so
suites 1.1 and 1.2 share contract 1 and a problem keeps its hash across them.
_Avoid_: benchmark, the registry, test set

### The survey

**Tier**:
One class of sources in the frame, read as one pass. The tiers are `R` CRAN packages, `E`
ecosystem examples, `T` textbook companions, `D` data deposits of published papers and `O`
open tabular repositories, in frame order, and a duplicate keeps its earliest member.
_Avoid_: stratum (a hand sample's cell), category

**Shard**:
The output of one reading run, which the merge validates and writes into the survey's files.
Agents write shards, never those files.
_Avoid_: batch (a hand sample's 25 rows), patch

**Help page**:
The documentation a reading agent gets for one data object, the source's own page, README,
codebook or a paper's methods, ending with the table's column types and first rows.
_Avoid_: docs, metadata

**Published model**:
A model specification published for the table (a posterior, a Stan example, a textbook's
worked example, a documentation example). Without one, the row's documented model is the
reader's proposal.
_Avoid_: true model, reference model

**Hand sample**:
The seeded sample of 100 rows of Tiers R, E, T and O, stratified by tier and confidence and
checked by hand at the source. Its share of fields that stood is the registry's verification
bar (ADR 0002).
_Avoid_: spot check (the 20 rows per tier read before it), audit

**Dimension**:
A size of a table or of a grouping factor, measured by script per registry row or per grouping
factor (observations, grouping factors, groups, group sizes and their imbalance, design
columns).
_Avoid_: shape, size axis (MetaBeta's word for the envelope's side), statistic

**Quirk statistic**:
A property of a column or a grouping factor beyond its size (its marginal shape, ties, rare
levels, dependence on another column, group confounding, absent levels, empty cells, the
design's conditioning). It is measured per column, per column and grouping factor, per factor
pair or per registry row, under the name TabDGP's glossary gives the property.
_Avoid_: feature, descriptor, metric (a score), quirk (the property itself, TabDGP's word)

**Superior**:
Of a nested pair of grouping factors, the one whose groups each hold whole groups of the other.
Neither is superior when each holds the other's groups, since the two then partition the rows
alike.
_Avoid_: outer factor, parent, higher level

**Flat table**:
A table of the survey's frame that no documented model fits with a random effect and in which
no column indexes a unit the rows repeat within. A wide table is not flat.
_Avoid_: i.i.d. table, unclustered, exclusion (the bookkeeping entry)

**Wide table**:
Grouped data stored with one row per unit and its repeated measures as columns. Its long form
stacks them, one row per unit and occasion, and is the table the registry would hold.
_Avoid_: unstacked table, pivoted table

**Flat sample**:
Every flat table of the survey's frame, measured by script with the registry's per-column
statistics and kept beside the registry, never in it. It is the reference for a generator's
flat case and shows where grouped tables differ beyond the grouping factor.
_Avoid_: control group, negative sample, flat registry

### References and results

**Reference posterior**:
The draws of the suite's sampler on a problem's full table that passed the diagnostics bar,
which every approximation is scored against.
_Avoid_: ground truth, gold standard, MCMC posterior unqualified

**Ladder**:
The sampler settings a reference run climbs, level 0 to 2, each longer and more careful than
the last, until the diagnostics bar passes or the compute cap ends the run.
_Avoid_: retry, escalation schedule

**Diagnostics bar**:
The convergence a run must reach to become a reference posterior, judged by rank-normalized
R-hat and the bulk and tail effective sample size of every global parameter, with no
divergences.
_Avoid_: threshold, convergence check

**Chain-split null**:
The score of half the reference chains against the other half. It is the floor a metric has on
that problem, below which differences are Monte Carlo noise.

**Track**:
One way of scoring a method on a problem. The posterior track scores draws against the
reference, the predictive track held-out rows and held-out groups, and the oracle track a
semi-synthetic replicate with known parameters.

**Opponent line**:
A method's scores over the suite, published with the suite so that a new method is read
against them. Every posterior-track line targets the contract's posterior exactly.
_Avoid_: baseline, competitor, reference (the posterior)
