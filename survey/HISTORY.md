# Survey history

*The registry's build record, kept for provenance.*

What each pass of the dimension survey did and found, as dated bullets. The method is in
[`README.md`](README.md), the files in [`docs/registry.md`](../docs/registry.md), the current counts in [`SUMMARY.md`](../registry/SUMMARY.md). `m3#` is an issue of
metabeta-v3, a private repository where the survey ran until 2026-10-08 (spec m3#14, tickets m3#15–m3#27); `#` is an
issue of this repository. The finished scripts named here (`deposits.py`, `resolve.py`,
`net.py`, `verify.py`) and the files only they wrote were in `archive/`, reproducible at tag
`survey-archive` and kept at tag [`survey-archive-3`](https://github.com/adkipnis/mixedbench/tree/survey-archive-3/survey/archive).

## Record per tier

| tier | sources | objects | read | rows / datasets | exclusions | published | `high` | Alex's check |
|---|---|---|---|---|---|---|---|---|
| R | 22 packages | 1191 | 689 | 252 / 238 | 559 | 207 | 75 | 5 pilot rows; m3#22 20 rows, 14 stood; m3#23 20 rows, 17 stood |
| E | 84 | 543 | 474 | 99 / 96 | 361 | 94 | 57 | 20 rows with O: 11 stood, 9 changed |
| T | 65 | 534 | 480 | 244 / 227 | 285 | 136 | 44 | 20 rows: 9 stood, 11 changed |
| D | 60 papers | 993 | 766 | 104 / 69 | 917 | 104 | 62 | all 104 rows: 55 stood, 43 changed, 6 left |
| O | 34 tables | 34 | 34 | 13 / 12 | 20 | 0 | 0 | with E |

Counts at each tier's close. `read` is the objects passing the pre-screen and the cap (Tier D's
include 320 filed by script as a series). Beside the drawn rows Alex adjudicated the blind
reading's open disagreements, four to eight per tier.

## Discovery (m3#21, 2026-10-07)

- One Opus agent with web search ran the archived `discover.md` over the spec's list and about
  twenty further queries.
- A second pass by hand added the collections the agent had missed or dropped: Zuur, Stata
  [XT], MixedModels.jl, rethinking, Fitzmaurice, ROS, WWGbook, Diggle.
- Kept URLs were fetched with the loader's user agent and pinned by script: the sha256 of the
  file, the HEAD revision of the repository on 2026-10-07. Everything left out is a `dropped`
  row of `sources.yaml`.

## Tier R (m3#20, m3#22, m3#23, 2026-10-07)

- **Cap**: only agridat is capped, at 50: its about 390 field trials would else be 38% of the
  pool, and a cap for all would drop grouped tables of faraway and MASS at random.
- **Pilot** (m3#20): lme4, nlme and mlmRev by four Sonnet agents, five rows read by Alex. The
  first rules came from it: `ordered` on grouping factors, dosing rows counted as
  observations, vague nonlinear formulas.
- **Mixed-model packages** (m3#22): six Opus agents.
  - Every MEMSS object is a re-export of its nlme namesake and SASmixed Semi2 is nlme Oxide, so
    39 rows folded.
  - The spot check changed none of its eight `high` rows and six of twelve `medium` and `low`
    ones (a missed design level, a coordinate taken for a group). That made the blind second
    reading a standard step: 21 of the 31 census rows agreed.
  - Alex adjudicated buntaran.wheat (zones fixed, genotype random beside location, replicate
    and block), jansen.strawberry (ordinal category weighted by count over the plot),
    kirk.potato (genotype only) and senshu.rice (locations in countries).
- **General packages** (m3#23): twelve Opus agents.
  - 160 of 628 objects pre-screened out; 308 of 362 exclusions `no grouping structure`, as
    expected of one-row-per-unit tables; 16 of 17 flagged pairs the same dataset.
  - Blind reading: 65 of 77 rows agree. Spot check: 17 of 20 agreed; lawn gained
    `machine:speed`, jsp became `school;school:class`, pvc, singer and motorins left.
  - All 36 v0.5 datasets are in the registry.
  - A case collision in the loader's Rscript dump (`CO2.rds` overwritten by `co2.rds`) was
    fixed in 439c813 and `datasets` re-pulled.

## Tiers E and O (m3#24, 2026-10-07)

- **Loader first:** Stan data dicts as the table of their observation-length arrays, `.gz` and
  `.zip` wrappers, Arrow through `pyarrow` (added against the spec's "no pyarrow", decided
  2026-10-07), parquet, whitespace-aligned text, documentation lookup for non-CRAN objects.
- **Tier E:** 474 objects read by eight Opus agents.
  - The ARM chapters repeat their data files, so 357 pairs were flagged: 340 byte-identical and
    answered by script, 17 by one agent, all `same`; 21 Tier R rows now list a Tier E member.
- **Tier O:** `net.py` on 2026-10-07 over 5025 OpenML, 689 UCI and 451 PMLB datasets.
  - 76 whole-name hits (a first run matching substrings had 231), 30 drawn; 16 rows fell to 13
    after the fold, 12 datasets with a documented cluster and none with a published model.
- **Blind reading:** 28 of 45 rows agree.
- **Spot check:** 11 stood, 9 changed, mostly from reading the Stata manual entries more
  closely than the agents had.
  - Changed: quinidine's PK regressions, pisa2000's school mean, the survival indicators of
    catheter and time_to_attrition, independent slopes written `||` (pig, radon_mn, employee),
    rm_anova2's error strata, sesame's second margin and `site:setting`, the 17.6
    ordered-categorical model with player-specific cutpoints.
  - long_heating_data and pancreatitis left.
  - srrs2.dat keeps `state:county`: the object is the unsliced national file, where `county`
    alone would merge namesake counties across states.

## Tier T (m3#25, 2026-10-08)

- **Loader first:** SPSS `.sav` through `pyreadstat` and `.xls` through `xlrd` (decided
  2026-10-08), workbooks with several data sheets as `<file>!<sheet>`, `layout` for headerless
  files, `.txt` as data unless named like documentation, `#` banners, SPSS labels on a scale's
  extremes left numeric; `datasets.py` became the `datasets/` package.
- Fitzmaurice's host sends an incomplete certificate chain Python refuses, so its 37 `.dta` and
  their `.txt` descriptions were seeded into the cache by hand with `curl`, sha256 checked by
  the loader as usual. Since #4 the loader carries the missing intermediate
  (`intermediates.pem`) and fetches them itself.
- 480 objects read by nine Opus agents (Rabe-Hesketh's chapter do-files hold the book's
  models).
  - 50 of the 230 `no grouping structure` exclusions are wide tables, which is how Fitzmaurice,
    Singer & Willett and Hox ship half their data; 26 flagged pairs, all `same`.
  - ROS fits no mixed model (every `.Rmd` grepped), so its 16 rows are repeating clusters.
- **Blind reading** of 196 rows: 89 agree on all four fields; star_mm and ROS earnings left on
  both readers' proposal.
- **Spot check:** 9 stood, 11 changed, mostly the formula to the chapter's actual fit
  (electricity's random coefficients, yogurt's brand intercepts, OXBOYS's polynomial, fev1's
  random slope); travel2, both NES objects, the three Storable tables and CTT_V2 left.

## Tier D (m3#26, 2026-10-08)

- **Decided up front:**
  - one `url` entry per fetched file rather than one on-the-fly zip per deposit (a pin on a zip
    would not survive a re-pull);
  - `deposit_files.csv` as the deposit-level record, since a private deposit, a preprint or a
    bot wall yields no object;
  - Sonnet readers at medium effort (cost), the Opus tiers being the calibration.
- **Frame** (`deposits.py`): every paper of the practice survey's `papers.csv` whose text names
  a Dryad, OSF, Zenodo or figshare deposit by DOI or URL, found by one regex.
  - The match is mechanical and also catches preregistrations and deposits a paper merely
    cites; those were excluded with their reason, never replaced, and that loss is a Tier D
    finding.
  - 15 papers per repository stratum, drawn with `random.Random(0).sample` over the sorted
    ids: equal cells rather than proportional ones, so every stratum stays readable.
- **Resolution** (`resolve.py`): OSF projects with their components, Dryad versions, Zenodo
  records and figshare articles, every answer cached, files classified by name (`data`,
  `documentation`, `script`, `other`).
  - Pull rules from the listing: 50 MB per file (every larger file was a fitted model or
    draws) and no hidden folder.
  - Dryad refuses scripts on every route (401 and 403), so its 11 deposits came through Alex's
    browser into `cache/dryad_raw/`, matched file by file against the API's md5. Since #4 a
    user's loader gets them from the release mirror (ADR 0003).
  - One help page per deposit under `help/deposits/`: title, license, the paper's text around
    the link, its models as the practice survey filed them, the listing, README, codebook,
    scripts.
- **Reading:** 226 objects had no frame (fitted brms and lme4 models saved as `.rds`), 320 of
  jing_2020's per-participant series were filed by script, 424 objects read by nine Sonnet
  agents and the 23 Dryad objects by one.
- **Finding** (`SUMMARY.md`, Tier D): 11 of 60 papers reach no object (8 OSF links that are
  preprints, one restricted project, one user page, one deposit too large). Within deposits
  the analysis table is the exception: raw per-participant logs beside merged tables,
  Qualtrics exports one row per participant, aggregates built in scripts, fitted models,
  stimulus lists.
- **Alex's reading:** the spot check (20 rows) and the Dryad check (5) changed 13 rows, so
  Alex read the remaining 89 in three draws (`shards/registry_tier_d_handdraw*.csv`).
  - Of 104 rows 55 stood, 43 changed (the final model's term set rather than the candidate
    set, per-subset fits and factorial contrasts named, the random structure as described)
    and 6 left under the inferred-model rule.
  - Four verdicts were recorded rather than applied: a response type follows the column, and a
    date string, a cue level that is no column and a derived indicator cannot be a covariate,
    a grouping factor or a response; they stay in the formula.

## Closing (m3#27, 2026-10-08)

- Every tier read and hand-checked: 712 registry rows over 642 datasets and 940 grouping
  factors (Tier R 252, T 244, D 104, E 99, O 13); 2142 exclusions; no open duplicate flag.
  Above the closing minimums of 100 Tier R rows and 40 rows from the other tiers.
- `SUMMARY.md` puts the pooled and per-tier quantiles of every axis beside the practice
  survey's p90; the envelope edges were set in the outcome grill, not here.
- metabeta-v3's CI test `packages/glmm/tests/surveys/test_dimension_quantiles.py` loads
  `quantiles.yaml` as data and asserts its axes, quantile keys, tiers, imbalance block, K
  distribution, shares and the tier minimums.
- At the closing it also asserted that every row of `v05_datasets.csv` (archived) is
  a registry key, a member of a registry row's `sources` (MEMSS MathAchieve in nlme's row; base
  R's Theoph, Orange and Indometh in MEMSS's) or an exclusion.

## Registry columns and verification (#6, 2026-10-09)

### Licenses (#7)

- `GPL-3.0-or-later` and `AGPL-3.0` joined `LICENSES` for CRAN DESCRIPTIONs.
- A string that states access or attribution but no license (OpenML's `Public`) is `other` or
  `not stated`, never a license it does not name.
- The schema change was migrated by merging a shard with the new header and no rows
  (`shards/registry_schema.csv`).

### Readers without R (#8)

- The 34 registry objects that loaded through the Rscript dump and have a Python reader now
  load without R (ADR 0003).
  - agridat's 27 `data/*.txt` files (28 rows) through a utils::data() reader: read.table's
    header, whitespace, quote and `NA` rules, strings as factors with sorted levels.
  - base R's 7 `data/*.R` files through the deparse reader (`datasets/deparse.py`, the subset
    of R those seven files use), fetched from R 4.6.1's source tarball with its sha256 instead
    of dumped from R's namespace.
- Each new frame was compared once with the Rscript dump's on columns, dtype kinds, levels,
  values and the ordered flag: 33 identical.
  - lillemo.wheat's `env` holds the same values but sorts its levels in codepoint order (`BT06`
    before `Ba04`), where R's ICU collation puts `Ba04` first; its first level, the reference
    of treatment coding, is `Aa03` either way.
- The re-merge `shards/registry_readers.csv` set their `reader` to `pandas` and `deparse` and
  gave base R's manifest rows a digest and size; no measure changed.
- The merge now replaces a re-merged row where it stands rather than moving it to the end.

### The Rscript route leaves (#9)

- The loader calls no R: an R file librdata rejects goes to the pure-Python `rdata`, reader
  `rdata`, in place of the ticket's `none` (ADR 0003's amendment).
  - muscatine, dd and dd1 came out identical to the Rscript dump's frames; the re-merge
    `shards/registry_rdata.csv` changed only the two rows' `reader`.
- The deparse reader no longer takes data.frame()'s `row.names =` for a column
  (LifeCycleSavings, randu).
- The re-pull without R has 3285 census objects (3295 before):
  - 137 `file` labels that named a dump (`rds/...`) now name the download;
  - about 60 base R objects outside the deparse subset (time series, matrices, iris) are no
    frame and were excluded already;
  - 19 `excluded.csv` keys, two unread pymc_examples objects and stan_arm's `ideo2.dat` waited
    for #14.
- The re-pulled `shards/excluded_prescreen.csv` is not merged, since it would overwrite the
  readers' reasons with `unreadable format`.
- A cache built before #9 holds the dump's `rds/` folders, which enumeration now lists as
  objects; delete them.

### The census and its tables agree (#14)

- The text reader read a whitespace-separated file with pandas' python engine, which ignores
  quotes under a regex separator: R's `write.table` output with a quoted string holding a space
  (stan_arm's `ideo2.dat`: `"NEW HAM"`) did not parse, and quoted names kept their quotes. The
  C engine honors quotes as read.table does.
  - `ideo2.dat` reads again at 10268 × 22 (its exclusion stands); ros's `hibbs.dat` and
    `hdi.dat` read for the first time; quoted column names in 17 ARM, ROS and Diggle files lose
    their quotes; no registry object changed.
  - ARM's `candidate_effects.dat` and `unemployment.dat` changed column counts at #8 and stay
    excluded for their reasons.
- The re-pull of Tiers E and T rewrote `candidates.csv` and the pre-screen shard (still not
  merged).
- `shards/dropped_census_repull.csv` deleted the 19 stale keys (18 base R objects of
  multi-object files, sequestro_2024_osf_5's `gmmMix2`); the merge now does this for any
  dropped object the loader no longer enumerates.
- `shards/excluded_census_repull.csv` filed their replacements (`beavers`, `state`,
  `UKLungDeaths`, `Harman23.cor`, `Harman74.cor`, `ability.cov`, `EXP2_3_LMM`, all no frame),
  the two pymc_examples objects no reader had seen (`Guber1999data.txt`, one row per state;
  `hurdat2-...txt`, HURDAT2's storm blocks, no table) and re-filed `hibbs.dat` and `hdi.dat`.
  Exclusions 2142 → 2132.
- `tests/test_census.py` asserts both directions: every exclusion is a census object, every
  uncapped census object is a registry row, an exclusion or a confirmed duplicate of either.

### Family and prior (#10)

- `verify.py scan` searched every registry row's `notes`, `formula` and help page, and once each
  the 38 deposit pages Tier D help pages point at, for keywords.
  - Family keywords: negative binomial, probit, cloglog, Weibull, gamma, lognormal,
    zero-inflated, hurdle, beta regression. Prior keywords: `prior`, `set_prior`, Stan and BUGS
    sampling statements.
  - 106 row hits over 48 rows and 1106 deposit hits, most of them `prior` in deposit code
    (`scan_hits.csv`).
- Snippets alone could not settle Tier D, whose help pages only point at the deposit, nor the
  Bayesian Tiers E and T, whose code sits in the cached repositories. The hand look read:
  - the 48 hit rows' snippets;
  - every Tier D row's model call in its deposit code;
  - the 74 rows of posteriordb, stan_arm, pymc_examples, bambi, rethinking and ros in their
    cached code.
  That is 214 rows, agents drafting from the code, Alex deciding.
- Outcome (`shards/registry_family_prior.csv`): `family` on 45 rows (12 also with a prior),
  `documented_prior` alone on 61; the other 108 rows stay on the rule with no stated prior.
- Eight values joined the `family` vocabulary: `bernoulli(cloglog)` (Stata `mecloglog`, meyel's
  glmer and brms fits), `Gamma(identity)` (sequestro), `zero_inflated_beta` (liutu), `student`
  (johannes), `gaussian` (hubbard, king, berweger, naranowicz, two stan_arm rows), `acat`
  (posteriordb's rating-scale and partial-credit IRT models), `weibull` and `cox`.
- The three Zuur zero-inflation rows with a published model (SeaGrass, Turcoparasitos,
  Spiders) stay on the rule: the book is not open and no source read states their family.
- Reading errors the code turned up in other columns, and the Windows CI failure, went to
  #15.

### Code read (#15)

- A `.gitattributes` keeps test fixtures' bytes (`-text`): a Windows checkout had rewritten the
  line endings of the ASCII `fits.rda`, whose magic then did not parse; CI is green on all
  three systems.
- The readings #10's code read questioned were checked at the source by four agents, Alex
  deciding; `shards/registry_code_read.csv` replaced 54 rows and added 3 (registry 712 → 715).
- Left open: valdebenito's MCMCglmm `categorical` fits with residual variance fixed at 1 (a
  logit with an observation-level term) keep `family` blank; fims' item parameters have fixed
  priors and no estimated scale, `ii` stays a grouping factor.

### Hand sample (#11, #12)

- `verify.py draw` wrote `sample.csv`: seed 0, 100 rows of Tiers R, E, T and O (Tier D left
  out, Alex read all of it), stratified by tier × confidence with largest-remainder allocation
  and at least one row per stratum, four batches of 25 in draw order. A further run appends
  one batch of 25 with the next seed and no floor.
- `verify.py handoff --batch k` renders a batch with the source's page and download URLs, the
  reading and the help page. Alex checked each batch at the source.
- **Batch 1** (#11): `shards/registry_hand_sample_1.csv` replaced its 25 rows (registry 715).
  - 8 rows stood in the compared fields (5 of them with notes or confidence corrected), 17
    were corrected: `published_model` and `formula` 11 each, `covariates` 7, `interactions` 2,
    `response` 2, `grouping_factors` 1.
  - Decisions: a `published_model` `no` row keeps its proposed formula; a response holding
    proportions stays `continuous`; a float-coded nominal response stays `ordinal`.
  - Left open as `RULE GAP:` in notes: the documented binomial (MetaResp), nominal
    (antibiotics) and Bernoulli-on-a-recode (aggression) fits have no `family` value.
- **Batch 2** (#12): `shards/registry_hand_sample_2.csv` replaced its 25 rows (registry 715).
  - Each reason is appended to notes, notes contradicting a correction are trimmed; wine,
    KosteckiDillon and playactivity rise to `high` (OME stays `medium`, the nonlinear cap).
  - 14 rows stood, 11 were corrected: `formula` 11, `covariates` 4, `published_model` 2,
    `response_type` 2, `response` 1, `grouping_factors` 1, `interactions` 1. Agreement:
    response 24/25, grouping factors 24/25.
- **Batch 3** (#12): `shards/registry_hand_sample_3.csv` replaced 24 rows; hox SocsLong.sav
  was re-filed as `simulated data` (`dropped_hand_sample_3.csv`, then
  `excluded_hand_sample_3.csv`; registry 714).
  - Notes as in batch 2; coursework #2 and autism raised to `high`.
  - 15 rows stood (schooleffects with its notes trimmed), 9 were corrected: `formula` 6,
    `published_model` 3, `covariates` 1, `interactions` 1, `response_type` 1; 1 left the
    registry. Agreement: response 25/25, grouping factors 25/25.
  - Siblings aligned at Alex's request (`shards/registry_hand_sample_3_siblings.csv`):
    rabe_hesketh coursework #1 takes `written`, the bivariate model's first response
    (`published_model` `yes`, `high`); snijders_bosker sheet 16 #1 takes Table 16.2's
    predictors (ch16.r fits them for both responses); mlmRev Chem97 #1 `score` `ordinal`.
  - Both coursework.dta responses code missing as -1 (202 and 180 rows), kept as values and
    noted; whether the contract recodes them is open.
- **Batch 4** (#12): `shards/registry_hand_sample_4.csv` replaced its 25 rows (registry 714),
  notes as in batch 2, rows corrected to a located source raised to `high`.
  - 9 rows stood (4 of them with a note), 16 were corrected: `formula` 9, `published_model` 9,
    `response` 2, `covariates` 1, `interactions` 1, `grouping_factors` 1. Agreement: response
    23/25, grouping factors 24/25.
  - Alex's verdicts first emptied the formula of eleven `no` rows; batch 1's rule holds (a `no`
    row keeps its proposed formula, the merge requires one).
  - A column stays a grouping factor or a covariate, never both: Cultivation keeps
    `Block:Cult`, the help page's `(1|Cult)` next to the two-level fixed `Cult` being aliased;
    state_wide_presidential_votes keeps `year_ind` as a grouping factor, the GP input in the
    formula.
  - Alex leans towards reading coursework.dta's -1 codes as missing, for the contract to
    settle.

### Agreement and the O/low re-read (#13)

- `verify.py agree` compares each sampled row's reading at draw time (`sample.csv`) with the
  merged registry on response, response type, trials, grouping factors, covariates,
  interactions, formula and published_model, and writes `agreement.csv`.
  - `;`-lists compare as sets, `a:b` unordered, formulas without whitespace; this
    normalization changed no count, so every disagreement is a real change.
  - hox SocsLong.sav, taken out of the registry, disagrees on every field (the per-batch
    tallies above left it out of response and grouping).
  - rabe_hesketh coursework #1, aligned to `written` by batch 3's siblings before batch 4
    checked it, counts as a disagreement on its draw-time reading.
- Agreement over the 100 rows (per stratum in `agreement.csv`):

  | pool | rows | response | response_type | trials | grouping_factors | covariates | interactions | formula | published_model |
  |---|---|---|---|---|---|---|---|---|---|
  | R | 42 | 0.976 | 0.976 | 1.0 | 0.976 | 0.929 | 1.0 | 0.738 | 0.786 |
  | E | 16 | 0.938 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.625 | 0.938 |
  | T | 40 | 0.875 | 0.925 | 0.975 | 0.95 | 0.725 | 0.875 | 0.475 | 0.575 |
  | O | 2 | 1.0 | 1.0 | 1.0 | 0.5 | 1.0 | 1.0 | 0.5 | 1.0 |
  | all | 100 | 0.93 | 0.96 | 0.99 | 0.96 | 0.86 | 0.95 | 0.61 | 0.73 |

- One stratum fell under 80% on response or grouping factors: O/low, 0 of 1 on grouping
  (uci_760 gait, `replication` added in batch 4). The closest passing are T/low on response
  (0.812) and R/medium on grouping (0.938).
- The whole O/low stratum, 7 rows, was re-read blind by a fresh Opus agent with
  `prompts/read.md` into a scratch directory: response 7 of 7, grouping factors 4 of 7. Alex
  decided (`shards/registry_reread_o_low.csv`, 4 rows replaced, registry 714).
- No further batch was drawn: after the re-read no stratum is under the bar, and an untargeted
  batch of 25 would give O/low no row.
- The low formula (0.61) and `published_model` (0.73) agreement, worst in Tier T, is the cost
  of rendering undocumented models; the paper reports it.

## Text floats (#57, 2026-10-10)

- pandas' text-to-float conversion is not correctly rounded: an ulp off on some numbers, more on
  x86 where it computes in an 80-bit long double, and it drops digits from small numbers with
  many decimals (`0.000177387096774173` read as `0.0001773870967741`). The loader now converts
  text floats with Python's `float()`.
- The rerun moved 17 contract hashes of `suite/1.1/candidates.csv`, in the hash alone. Alex
  decided it is a patch, 1.0.1: release 1.0 ships a candidate list, and no suite is frozen
  before release 1.1.
- The 17: `alda/aldatxt/{alcohol2,firstsex,medication,opposites,tolerance,unemployment}_pp.txt/1`,
  `stan_arm/ARM/Ch.20/allvar.csv/1`, `pingouin/src/pingouin/datasets/mixed_anova.csv/1`,
  `laing_2024_osf_7/SiblingsData.csv/1`, `sequestro_2024_osf_2/EXP2_3_pooled.csv/1`,
  `uci_760/data.csv/1`, `lagisz_2020_osf_3/MA_dataset_with_ES.csv/1`,
  `sievers_2020_osf_12/convo_df_2022-04-01.csv/1`,
  `sievers_2020_osf_16/summary_pull_c_pairwise_2019-11-29.csv/1`,
  `villemereuil_2018_dryad/data.csv/{2,3}`, `shanahan_2019_dryad_3/TNetAndTSLR.csv/2`.

## Text integers (#54, 2026-10-10)

- A text file in a CRAN package's `data/` folder read its integer columns as `int64`, where R,
  and every other R route of the loader, reads `int32`. All 397 cached `data/` text files hold
  1,181 such columns, none outside the `int32` range; the loader now casts them.
- The rerun moved 5 contract hashes of `suite/1.1/candidates.csv`, in the hash alone, a patch,
  1.0.2, as for #57.
- The 5: `agridat/burgueno.alpha/1`, `agridat/snedecor.asparagus/1`,
  `agridat/turner.herbicide/1`, `agridat/yates.oats/{1,2}`.

## Second hand sample (#61, 2026-10-18)

- `verify.py` came back from tag `survey-archive-3` with its draw, handoff and agreement steps. It
  drew 100 of the 489 candidates of suite 1.1 not yet checked by hand, stratified by tier and
  `verified`, seed 1 (`sample.csv`). Alex checked them in four batches of 25.
- Agreement per field and stratum is in `agreement.csv`. Response and grouping agreed on at
  least 0.83 of the rows in every stratum, so no stratum was re-read; the formula agreed on 0.84,
  `published_model` on 0.70.
- Every checked row became `verified=hand`. At release 1.0.5, 58 rows stood, 39 had a model field
  corrected and 3 had left the registry as copies of another object.
- Copies were folded into the object first in frame order: sesame.dta into sesame.data.json; the
  1,905 pupils of goldstein Gcsemv.xls, cmm_sci SCI.DAT and rabe_hesketh coursework.dta into
  mlmRev Gcsemv, which gained model 2 on `course`.
- `suite/admit.py` gained refusals, each applied to the whole registry, not only to the sample:
  - `nonlinear_model` for every row whose notes open with `NONLINEAR:`;
  - `censored_response` for ten censored times filed as continuous;
  - `frequency_weighted`, `covariance_structured_effect`, `choice_model` and
    `item_response_model`.
- fat was first refused for its hinge term `pmax(time, 0)`. It then became a candidate again with
  fidelity `approximate`, like the polynomial rows the contract fits as linear terms.

## Targeted hand pass (#82, 2026-10-18 to 2026-10-19)

- The second sample changed most rows from textbook sites, rabe_hesketh and zuur. Alex checked by
  hand the 111 rows from there not yet checked (`targeted/sample.csv`), in five batches by source.
- At release 1.0.5, 30 rows stood, 66 had a model field corrected and 15 had left the registry.
  The corrections were mostly to `published_model` (52 rows) and the formula (35).
- Copies were folded into the object first in frame order, their values checked:
  - goldstein Contraceptive use.xls into mlmRev Contraception, SOCATT.xls into Socatt;
  - goldstein primary-secondary.xls, rabe_hesketh fife.dta and stata_fifeschool into mlmRev
    ScotsSec, which gained fifeschool's two models as models 2 and 3;
  - OXBOYS.xls and cmm_oxboys OXBOYS.DAT into nlme Oxboys;
  - rabe_hesketh drvisits.dta, hsb.dta, skincancer.dta and tvsfpors.dta into stata_drvisits,
    mlmRev Hsb82, mlmRev Mmmec and stata_tvsfpors.
- popular2, Nurses, gpa2long, pupcross2 and sheet 03B left as simulated data, like SocsLong.
- New refusal codes: `multivariate_response` (HTBONEBoys), `known_sampling_variance` (AstLrd),
  `categorical_response` (contraceptive) and `joined_covariate` (ecls_child). `choice_model`
  now covers crackers, hybrid, electricity and yogurt.
- Rules the verdicts applied:
  - a subset, offset, transform or derived term lives in the formula only, so a problem pools
    every row (police, star1, videos);
  - an integer covariate with at most ten values that the source fits linearly is declared
    continuous in `types` (antisocial, towerl, wagepan, taxprep, stata_tvsfpors);
  - a count the source fits as Gaussian stays a count, and the family rule makes it Poisson.
- New models: Socatt model 2, the ordinal `numpos` of Rabe-Hesketh and Skrondal's exercise 11.5;
  star1 model 2 refiled on `treads`, so it no longer repeats model 1's response.
- The registry went from 714 rows over 641 datasets at release 1.0.4 to 694 rows over 621.

## Suite 1.1 candidates at release 1.0.5 (#61, #82)

- `suite/admit.py`'s rerun took the candidates from 675 to 608 and the refused rows from 39 to 86.
  - 71 candidates left: 25 with their registry rows (folds and exclusions), 46 refused.
  - 4 joined: `mlmRev/Gcsemv/2`, `mlmRev/ScotsSec/2`, `mlmRev/ScotsSec/3`, `mlmRev/Socatt/2`.
- 50 contract hashes moved, each with its corrected registry row; no contract rule changed. It is
  a patch, 1.0.5, as for #57: no suite is frozen before release 1.1.

## Grouped K-fold (#87, 2026-10-20)

- The predictive track's single seeded 10% split became grouped K-fold in both regimes, after
  the experiment of #47 (ADR 0001, amended 2026-10-20).
- `suite/admit.py`'s rerun moved all 608 contract hashes of `suite/1.1/candidates.csv`, in the
  hash alone; the refused rows are unchanged. It is a patch, 1.0.6, as for #57: no suite is
  frozen before release 1.1.

## Integer covariates (#108, 2026-10-21)

- An integer covariate with at most ten values was categorical by default. It is now
  continuous unless the source stores it as a factor or `types` declares it categorical
  (ADR 0001, amended 2026-10-21).
- The four columns the documented formula wraps in `factor()` were declared categorical
  through `shards/registry_integer_covariates.csv`: gopherdat2 `year`, koch `day`,
  gomez.splitsplit `nitro` and towerl `group`. Their contract hashes stay.
- The merge measured the registry again, and 327 columns of `columns.csv` went from categorical
  to continuous.
- Five rows whose source transforms the column stand on #82's rule, which keeps an offset, a
  transform or a subset in the formula only:
  - Owls `offset(log(BroodSize))`, like gopherdat2's `offset(log(Area))`;
  - bacteria `I(week > 2)`;
  - muscatine `cage` and `cage2`, where `cage = age − 12` is exact after z-scoring;
  - posteriordb radon_all `floor_measure`, which posteriordb's Stan program multiplies as a
    number, its code 9 included;
  - stan_arm srrs2 `floor`, 0/1 in the Minnesota subset that ARM fits.
- The `continuous` declarations that #82 added for integer columns now restate the rule.
- `suite/admit.py`'s rerun moved the contract hashes of 49 candidates, in the hash alone; the
  refused rows are unchanged. It is a patch, 1.0.7, as for #57: no suite is frozen before
  release 1.1.

## Reading rulings (m3#22 to #15)

The rulings [`prompts/read.md`](prompts/read.md) does not carry, from the agents' `RULE GAP` notes and Alex's checks, each with an example
object and the deciding issue.

**Grouping factors**

- Counted: a cluster that repeats even when the source treats rows as independent (Tier O's
  hospitals, ROS; m3#24, m3#25); a month or observer with enough levels and rows (Squid,
  Sparrows; m3#25); a repeating dyad the book fits (Crofoot; m3#25); a design level the first
  reading missed (lawn's `machine:speed`; m3#23); a genotype-by-environment term fitted as
  random (salmon.bunt; m3#22).
- Not counted: strata and waves modeled as fixed (CES11; m3#23); field coordinates
  (connolly.potato; m3#22), though a Latin square's rows and columns are blocks (OrchardSprays;
  m3#23); a factor that classifies rather than clusters (singer; m3#23); a dyad with one row
  per pair (Monks; m3#25).
- A term `a:b` has no level where a part is missing (m3#24). Where a column is both a grouping
  factor and a covariate, the grouping stands and the fixed term stays in the formula
  (Cultivation; #12).
- An area factor with many levels groups; one with a handful is a covariate (LGAclaims,
  infmort; m3#23).
- A random intercept on the matched pair (amlxray; m3#23), the GEE cluster (geepack; m3#22), a
  frontier inefficiency term (xtfrontier1; m3#24); a single-level conditional logit is excluded
  (travel2; m3#25).

**Response**

- Totals are `count`, 1–5 ratings `ordinal`, non-integer abundances `continuous`, a bounded
  score without trials `count` (eggprod, InstEval; m3#22–m3#26); a float-coded nominal stays
  `ordinal` (antibiotics; #11).
- A documented normalized score is its own column (jsp_728; m3#25).
- Survival: `continuous`, the event indicator in `ignore` and `Surv(time, event)` in the
  formula (catheter; m3#24). Discrete-time hazard: the indicator is the response, `PERIOD` a
  categorical covariate (cigarette; m3#25).

**Covariates and model rows**

- A baseline is a covariate, not a response (dietox; m3#22). Polynomial and derived terms name
  their column once (muscatine; m3#22).
- An interaction is carried only when fitted (prt; m3#22). The source document beats recall
  (Stata manuals; m3#24). The final model's terms count, not the candidates; subset fits and
  contrasts are named in the formula (m3#26).
- A variant with one row per extra level is the same model (SASmixed, melanoma; m3#22, m3#24).
  posteriordb's ladders render the richest grouping (radon; m3#24).
- `published_model` is `no` for all of Tier O (m3#24).
- Priors in deposit files the page lists are filed (verberk; #10).

**Code against prose** (#15)

- Code not deposited: the paper stands at `medium`.
- An evident bug files the intended model (voorspoels); where a package version changed a fit,
  the published output decides (sequestro).
- A subset fit stays on the whole object, the subset in `notes` (szollosi).
- A fixed scale, sum-to-zero, structured covariance or location-scale correlation keeps the
  grouping and is named in the formula (rugby, gumundsdottir).

**Exclusions**

- `simulated data` only where the source says so (Stata's chicken, hox SocsLong; m3#24, #12);
  a guessed "constructed" stays (SASmixed Animal; m3#22).
- `no grouping structure`: wide repeated-measures tables (nitrofen), replication without a
  replicate column (faraway rats), a uniformity trial without a random term, coordinates as the
  only grouping (besag.checks); m3#22, m3#23. A fixed-effects fit over blocks is rendered with
  random blocks at `low` (mead.germination; m3#22).
- `derived or duplicated table`: a subset with its own model (wages_small_pp), a
  multiple-membership reshape (star_mm), Stan's censored and uncensored halves, read as the
  modal one (BUGS kidney); m3#24, m3#25.
- Stan: pure GP, time-series, CAR and mixture posteriors have no grouping; a GP beside random
  intercepts stays (m3#24).
- Kept: ARM's raw tables of an early chapter, with a later chapter's multilevel fit at `medium`
  when the grouping column is in the table (m3#24).

## Columns filled by script (#6 to #15)

- `random_slopes` and `verified` came in by the header-only `shards/registry_schema_2.csv`;
  the archived `verified.py` filled `verified` once through `shards/registry_verified.csv`;
  the archived `slopes.py` filled `random_slopes` through `shards/registry_slopes.csv`, Alex's
  decisions on the rows it reported through `shards/registry_slopes_decisions.csv`.
  A later row fills both in its own shard. The archived `factors.py` regrouped the
  rows that named a nested `a:b` by a `b` whose codes repeat across `a` through
  `shards/registry_factors.csv`; Wafer's slopes, waiting on that, followed in
  `shards/registry_slopes_wafer.csv`.
- The re-pulled `candidates.csv` and pre-screen shard of #9 and #14 are not merged: the merge
  would overwrite readers' reasons with `unreadable format`.
