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

**Suite**:
A frozen, versioned set of problems with reference posteriors and diagnostics, admitted by
verification, the diagnostics bar and the compute cap. Immutable once released.
_Avoid_: benchmark, the registry, test set

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
