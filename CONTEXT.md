# mixedbench

Posterior approximation and prediction on real grouped data for generalized linear mixed
models (GLMMs): what a problem is, what a reference is, and what a result is measured against.
Statistical terms (family, link, fixed and random effects, grouping factor, standardised
scale) are those of metabeta's GLMM glossary and are not redefined here.

## Language

### Problems

**Source**:
A pinned, checksummed upstream location of public data: a CRAN package at a version, a git
repository at a revision, or a url with a sha256. A source is fetched, never redistributed.
_Avoid_: dataset (one source holds many), mirror

**Documented model**:
The GLMM a source's own documentation fits to a table: its help page, textbook chapter,
example notebook or paper. A row whose model is the reader's proposal is marked so.
_Avoid_: ground truth, the true model

**Registry**:
Every documented model over every grouped table the survey read, one row per table and
model, with its dimensions measured by script. Grows with every survey pass; never frozen.
_Avoid_: benchmark, corpus, suite (a subset)

**Contract**:
The frozen rules that turn a registry row and its loaded table into a problem: row
dropping, coding, standardisation, the family rule, the prior, the splits. Versioned; a
change is a new suite.
_Avoid_: preprocessing (one part of it), config

**Problem**:
One registry row under the contract: a design, a family, a prior and the splits, identified
as `<source>/<object>/<model_index>`. The unit everything is computed and scored on.
_Avoid_: dataset, task, posterior (posteriordb's word for the same thing)

**Materialised problem**:
A problem written to files: one table of the coded columns in raw units, with the response,
the trials, the grouping factors and the two split regimes, and beside it the record a table
cannot hold (family, prior, column roles, the per-regime scales, the contract hash). The
package's interface to a problem; a cache rebuilt from the pins, never redistributed.
_Avoid_: dataset, export, the parquet

**Regime**:
The rows a fit sees: the full table (posterior track), or the seen rows of a held-out-rows
or a held-out-groups split (predictive track). Standardisation is computed per regime.
_Avoid_: split (the partition), fold

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
A frozen, versioned set of problems with reference posteriors and diagnostics, admitted by
verification, the diagnostics bar and the compute cap. Immutable once released.
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

### References and results

**Reference posterior**:
The draws of the suite's sampler on a problem that passed the diagnostics bar; the target
every approximation is scored against.
_Avoid_: ground truth, gold standard, MCMC posterior unqualified

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
