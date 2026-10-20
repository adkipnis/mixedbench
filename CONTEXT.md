# mixedbench

Posterior approximation and prediction on real grouped data for generalized linear mixed
models (GLMMs): what a problem is, what a reference is, and what a result is measured against.
Statistical terms (family, link, fixed and random effects, grouping factor, standardized
scale) are those of metabeta's GLMM glossary and are not redefined here.

## Language

### Problems

**Source**:
A pinned, checksummed upstream location of public data: a CRAN package at a version, a git
repository at a revision, or a url with a sha256. A source is fetched, never redistributed.
_Avoid_: dataset (one source holds many), mirror

**Table**:
One loaded data object, one DataFrame: the rows of a grouped dataset with its grouping
factors among the columns. A source holds many tables; a table can carry several documented
models.
_Avoid_: dataset, hierarchical dataset (a table with a grouping factor), data frame

**Manifest**:
The list, per source and object, of the one file inside the source that holds the table, with
its checksum: a cargo list naming each item on board. The loader fetches and checks that file
alone.
_Avoid_: index, file list

**Documented model**:
The GLMM a source's own documentation fits to a table: its help page, textbook chapter,
example notebook or paper. A row whose model is the reader's proposal is marked so.
_Avoid_: ground truth, the true model

**Registry**:
The list of every documented model over every grouped table the survey found, one row per
table and model, with its dimensions measured by script. Built as a census, every object of a
stated frame read rather than a sample of it, and never frozen: it grows with every survey
pass.
_Avoid_: benchmark, corpus, suite (a subset)

**Contract**:
The fixed rules that turn a registry row and its table into a problem (rows dropped, coding,
standardization, family, prior, splits), so that two results on one problem compare. It binds
the benchmark, not the user, who may fit any model to a table; a change to a rule is a new
suite.
_Avoid_: preprocessing (one part of it), config

**Problem**:
One registry row under the contract: a design, a family, a prior and the splits, identified
as `<source>/<object>/<model_index>`. The unit everything is computed and scored on.
_Avoid_: dataset, task, posterior (posteriordb's word for the same thing)

**Materialized problem**:
A problem written to files: one table of the coded columns in raw units, with the response,
the trials, the grouping factors and each row's fold in the two split regimes, and beside it
the record a table cannot hold (family, prior, column roles, the per-fold scales, the contract
hash). The package's interface to a problem; a cache rebuilt from the pins, never
redistributed.
_Avoid_: dataset, export, the parquet

**Regime**:
How a track chooses the rows a fit sees: the full table (posterior track), or held-out rows
inside seen groups or held-out groups (predictive track), each dealt into folds.
_Avoid_: split (the partition)

**Fold**:
One part of a regime: the rows it holds out, predicted by a fit on every row outside it. A
row is held out in at most one fold of a regime, and standardization is computed per fold on
the rows its fit sees. The full table is one fold that holds nothing out.
_Avoid_: split, partition

**Verified row**:
A registry row admitted on its reading: `hand` (the hand sample and Tier D), `high` (a high
confidence reading), or `second-reading` (a blind second reading, adjudicated where it
disagreed). Recorded per row in the `verified` column.
_Avoid_: validated, trusted

**Candidate list**:
The verified rows whose response is in the contract's family rule, with their contract
hashes, written by the admission script before any reference exists. A suite is the subset
whose references pass the bar.
_Avoid_: the suite, shortlist

**Suite**:
A frozen, versioned list of problems with reference posteriors, admitted by verification, the
diagnostics bar and the compute cap. The contract is the recipe and the suite the menu: suites
1.1 and 1.2 share contract 1, and a problem keeps its hash across them.
_Avoid_: benchmark, the registry, test set

### The survey

**Tier**:
One class of sources in the frame, read as one pass: `R` CRAN packages, `E` ecosystem
examples, `T` textbook companions, `D` data deposits of published papers, `O` open tabular
repositories. Frame order is tier order; a duplicate keeps its earliest member.
_Avoid_: stratum (the hand sample's tier × confidence cell), category

**Shard**:
One reading run's output, `survey/shards/<table>_<label>.csv`, which `merge.py` validates and
upserts into a registry file. Agents write shards, never the registry.
_Avoid_: batch (a hand sample's 25 rows), patch

**Help page**:
The documentation a reading agent gets for one data object, `registry/help/<source>/<object>.txt`:
the source's own page, README, codebook or a paper's methods, with the table's dtypes and first
rows.
_Avoid_: docs, metadata

**Published model**:
A model specification published for the table (a posterior, a Stan example, a textbook's
worked example, a documentation example); `published_model` `yes`. Without one, the row's
documented model is the reader's proposal.
_Avoid_: true model, reference model

**Hand sample**:
The seeded 100-row sample of Tiers R, E, T and O, stratified by tier × confidence, that Alex
checked at the source; its per-field agreement is the registry's verification bar (ADR 0002).
_Avoid_: spot check (the 20 rows per tier read before it), audit

**Dimension**:
A size of a table or of a grouping factor, measured by script: observations, grouping
factors, groups, group sizes and their imbalance, design columns. Recorded per registry row
or per grouping factor.
_Avoid_: shape, size axis (metabeta's word for the envelope's side), statistic

**Quirk statistic**:
A property of a column or of a grouping factor beyond its size: its marginal shape, ties,
rare levels, dependence on another column, group confounding, absent levels, empty cells, the
design's conditioning. Recorded per column, per column × grouping factor, per factor pair or
per registry row, under the name TabDGP's glossary gives the property.
_Avoid_: feature, descriptor, metric (a score), quirk (the property itself, TabDGP's word)

### References and results

**Reference posterior**:
The draws of the suite's sampler on a problem's full table that passed the diagnostics bar;
the target every approximation is scored against.
_Avoid_: ground truth, gold standard, MCMC posterior unqualified

**Ladder**:
The sampler settings a reference run climbs, level 0 to 2, each longer and more careful than
the last, until the diagnostics bar passes or the compute cap ends the run.
_Avoid_: retry, escalation schedule

**Diagnostics bar**:
The convergence a run must reach to become a reference posterior: rank-normalized R-hat,
bulk and tail effective sample size on every global parameter, and no divergences.
_Avoid_: threshold, convergence check

**Chain-split null**:
The score of half the reference chains against the other half: the floor a metric has on
that problem, below which differences are Monte Carlo noise.

**Track**:
One way of scoring a method on a problem: the posterior track (draws against the reference),
the predictive track (held-out rows and held-out groups), the oracle track (a semi-synthetic
replicate with known parameters).

**Opponent line**:
A method's scores over the suite, published with the suite so a new method is read against
them. Every posterior-track line targets the contract's posterior exactly.
_Avoid_: baseline, competitor, reference (the posterior)
