# Discover prompt — dimension survey

You search the public web for collections of hierarchical or longitudinal datasets outside
CRAN, so that the non-R part of the frame (`sources.yaml`, Tiers E and T) is as documented as
its CRAN part. Every collection you consider is recorded, kept or dropped, with the reason;
nothing is pulled here. A collection is a place one script can fetch and enumerate: a git
repository, a zip or folder of data files, a package's bundled data.

## What to look for

1. **The fixed list of the spec**, each one located and judged:
   - Tier E, ecosystem examples: posteriordb, the Stan example-models repository (ARM and
     BDA chapters), bambi's bundled data, pingouin's bundled data, the PyMC examples' data.
   - Tier T, textbook companions: Gelman & Hill (ARM), Raudenbush & Bryk (HLM), Snijders &
     Bosker, Hox, Goldstein (MLwiN sample data), Finch, Bolin & Kelley, Faraway's extended GLM
     book, Zuur et al.'s mixed-effects ecology books.
2. **Further collections** of the same kinds: data bundled with other languages' and
   libraries' examples (Stata, SAS, Julia, Python); companion data of other books on
   multilevel, mixed, longitudinal or hierarchical Bayesian modelling; teaching repositories
   and course sites for multilevel modelling; methodological archives (data of reproducible
   methods papers, journal data archives). Search in English; try at least fifteen queries
   with varied wording (multilevel, mixed-effects, hierarchical, longitudinal, repeated
   measures, clustered, panel; "datasets", "companion data", "example data", "course data").

## Judge each candidate

- **kept** when its data are downloadable by a script from public hosting without a login,
  registration form, licence click-through or CAPTCHA, in tabular files (csv, tsv, txt, dta,
  sav, xlsx, json, rda, rds, Stan data json), with documentation of what the columns are.
- **dropped** otherwise, with one of these reasons: `registration wall`, `licence wall`
  (click-through or no-redistribution terms), `not public hosting` (personal drive, email on
  request, software install), `mirror of Tier R` (CRAN package data under another name, such
  as Rdatasets and its ports), `no tabular data` (code only, summaries, simulated data),
  `no documentation`, `not grouped` (no repeated-measures or clustered structure in the
  collection), `unreachable` (dead link after one try). Try each location once; never solve a
  CAPTCHA, never log in.
- A book whose data ship only inside an R package on CRAN is `mirror of Tier R` if the package
  is in Tier R already (lme4, nlme, mlmRev, MEMSS, glmmTMB, brms, GLMMadaptive, nlmeU, SASmixed,
  HLMdiag, ordinal, geepack, agridat, MASS, carData, lattice, HSAUR3, faraway, boot,
  gamlss.data, medicaldata, languageR, datasets); otherwise record the package as the
  collection with `kind: cran` so that the survey can decide to add it.

## Output

Write one YAML file at the path you were given, nothing else:

```yaml
kept:
  - label: stan_examples          # short snake_case, the survey's source label
    tier: E                        # E for software ecosystems, T for books and teaching sites
    name: Stan example models      # what it is, in a few words
    kind: git                      # git, url (one archive or folder) or cran
    url: https://github.com/stan-dev/example-models
    path: ARM                      # for git and url: the folder or file holding the data
    files: csv, R dump, Stan json  # formats seen
    documentation: README per chapter, the book   # where the columns are explained
    licence: BSD-3                 # as stated, or "not stated"
    grouped: radon by county, ...  # two or three examples of grouped datasets seen
    notes: ...                     # anything the pull should know
dropped:
  - label: ...
    tier: ...
    name: ...
    url: ...
    reason: registration wall      # one of the reasons above
    detail: ...                    # one sentence
```

Give the exact download URL (the zip or the folder listing) for `url` kinds and the repository
URL plus the data folder for `git` kinds; do not compute checksums or revisions, the survey
pins them by script. Report every candidate you looked at, including the fixed list, in one of
the two lists. Return a two-line summary: how many kept, how many dropped, and any case these
rules do not settle, starting `RULE GAP:`.
