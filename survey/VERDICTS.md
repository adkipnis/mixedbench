# Alex's verdicts

*The registry's build record, kept for provenance.*

Alex's per-row verdicts on the survey's readings, copied unchanged from the survey README of
before the split. The record around them, and what `m3#` means, is in
[`HISTORY.md`](HISTORY.md); the rules they set are in [`prompts/read.md`](prompts/read.md) and
[`README.md`](README.md#reading-rules). Issue numbers are this repository's, except #20 and #24
inside the bullets (m3#20 and m3#24); `#1`–`#3` after an object is its `model_index`.

## Code read (#15, 2026-10-09)

Findings of #10's code read, checked at the source; `shards/registry_code_read.csv`.

- szollosi_2019_osf_2 exp2.csv: corrected; the Rmd's glmer (L313, L332) has no `block:condition`,
  `condition` is categorical, the fit is on trial > 40 and conditions 1 and 3.
- meyel_2026_dryad: II.1, II.2 #2 and III and IV corrected to the code's combined terms
  (`PopulationID:FamilyID:BoxID`, `PopulationID:FamilyID` for II.2, as II.2 #1 since the
  2026-10-08 spot check), the Gamma shift `+ 0.001` (L287; the paper's `+ 0.01` in notes); I.1
  and I.2 stand.
- sequestro_2024_osf_{2,11,12,16}: stands; current brms codes `(0 + Intercept + condition * RTc
  | ppid)` with five sds, but the supplement's tables (brms 2.16.1) report four, the filed
  `(1 + condition * RT | ppid)`; notes carry the caveat and the trial filters.
- kleisner_2026_osf #1–3: corrected; script 05 fits M0, iid correlated effects by
  `Nationality` (one-to-one with POPULATION); the linguistic covariance of M1–M3 left the formula.
- koczynska_2026_osf_{48,49}: corrected; `models1/2` are not deposited, but the deposited fit2
  processing script predicts from lagged controls, so `gdppc_lag1`, `gdpgrowth_lag1`,
  `unemp_lag1`; `medium`, the random slopes resting on the paper's Eq. 3.
- voorspoels_2015_osf_3 d: corrected; the intended model with `subjectID:premset` and
  `item:premset`; as deposited, `whichRandom = c('ITEM','SS')` matches no column and the fit
  has no random effects (notes). The `premset:sampling` interaction stays as the 2026-10-08
  hand draw kept it, though the code's Bayes factor prefers the model without it.
- lagisz_2020_osf_3 #1–2: corrected; the scripts exist (OSF's GitHub add-on lists them at 0
  bytes); crossed `ScalePoint`, `ArticleID`, `ExperimentID`, `EffectID`, row 2 with the
  phylogeny on `Species_Latin`; `high`.
- valdebenito_2020_dryad_2 #1–3: corrected; the deposited code's `random = ~site + j_date`,
  `j_date` the day of year (72 levels), `date` to `ignore`; `high`.
- johannes_2021b_osf_6 #3: corrected in notes; predictors centered, not standardized.
- gumundsdottir_2026_osf*: corrected; `(1 | c | NewID)` in location and scale; _6's slope
  variable `time` built from `wave` (0, 1, 2, 3, 6), `wave=continuous`.
- naranowicz_2024_osf_2 #1–2: stands, the finding was wrong; the deposited script is complete
  (2466 lines, its checksum the deposit's) and L948 and L1353 are the filed formulas.
- hubbard_2023_osf_2 #1–3: stands in its columns; the formula names each row's part of the
  multivariate fits `p1a`, `p1b`, `p1c`, which share no residual correlation or random effect.
- posteriordb radon_all: corrected to `||`. state_wide_presidential_votes: corrected; the state
  scale by region, year GPs by region and state, 17 variances on one gamma × Dirichlet budget.
  fims_Aus_Jpn_irt: corrected to the slope-intercept form `alpha*theta - beta`.
- stan_arm: polls.dta now renders the script's M2 (`age`, `edu`, `age:edu`, `state`; region and
  the previous vote built in the script, formula only) on survey 9158; srrs2.dat's formula is
  the Minnesota fit on county, the grouping `state:county` as #24 decided; allvar.csv is
  `hiv.stan` on `treatmnt == 1` (`visage` alone); sesame.dta and sesame.data.json are the
  structural bivariate fit (`postlet ~ regular`, `regular ~ encour`), sesame.dta #2 added,
  `pretest` dropped (from `sesame_street2`, whose fit is commented out); Ch.21 radon.data.json
  adds `u`; hiv.data.json and earnings.data.json are `||`; pilots.dat's formula names the
  Gaussian on 40 cell proportions, `low`; Ch.19 pilots.data.json stands.
- pymc_examples: item_response_nba.csv keeps `decision` (the code's `foul_called` is no
  column), the recode in the formula; external_pp.csv is the notebook's final m7 with `FEMALE`
  and `||`, `family` empty for the censored Gumbel; rugby.csv is the home part of a joint
  Poisson fit with sum-to-zero team effects, the away part added as #2; cracker_choice_short.csv
  names person effects per alternative at a fixed sd 0.1.
- rethinking: Primates301.csv #1 is the Rd's Poisson social-learning model with a GP over
  species (`published_model` `yes`), #2 the book's m14.11 brain-size model added (both on
  `genus`, `low`); kl_dyads #1–2 are m14.7 without `dlndist`, `dass` or offset; PrussianHorses.csv
  is the Rd's m0, `published_model` `yes`, `high`.

## Hand sample, batch 1 (#11, 2026-10-09)

`shards/registry_hand_sample_1.csv`.

- stand: alda medication_pp; rethinking PrussianHorses (notes: the Rd exists, the fixed scales
  are priors), NWOGrants (`low`); mixedmodels_jl kb07 (the model is the rank-deficiency
  page's); languageR lexdec (RT is already a log); stan_arm allvar (the script's J = 84 and
  indexing slips in notes); pmlb_apnea1 (`low`, target holds cell frequencies); lme4
  grouseticks (INDEX stays out of `grouping_factors` under #20).
- `published_model` `no`, the formula kept as proposed: fitzmaurice melanoma (`low`; the paper's
  model is Europe-wide, three-level), agridat tai.potato, nlme Cefamandole (`low`; the Rd fits
  `nlsList`, no random effects) and Tetracycline2, SASmixed WaferTypes and Animal (`low`; the
  pages only call `str`), hox estrlong (`log(estrmeas)` in the formula; `log_estr` is log10, the
  narrative's natural log left unresolved).
- corrected to a located source: rabe_hesketh antibiotics (GLLAMM article Table 3, nominal logit
  with category-specific intercepts by doctor and hospital, `Wrdiag` added; `high`), aggression
  (MLMUS4 exercise 10.4, `I(y > 0)` on `person` alone; `high`) and epilep (SABRE 13.3, `v4`
  replaces `visit`; `high`); snijders_bosker 17A (ch17.r, Table 17.2; the country-centered and
  country-mean terms are no columns, formula only; `high`); hox MetaResp (chapter 6 Eq. 6.21,
  binomial logit with mode random slopes, `respisrr` and `mode:year` added; `high`) and
  CurranLong (the PanelModeling chapter's reading growth model, `read` the response, `anti` to
  `ignore`); ros incentives_full (Gelman, Stevens & Chan 2003 Model III; `high`); gamlss.data
  rent99 (Fahrmeir et al. Eq. 9.8, `rentsqm` the response, district a kriged spatial effect;
  `high`); brms loss (theta and omega estimated, not fixed); stan_bugs schools (`I(LRT^2)` and
  the residual variance model in the formula).

## Hand sample, batch 2 (#12, 2026-10-09)

`shards/registry_hand_sample_2.csv`.

- stand: agridat gomez.nonnormal2, archbold.apple, yates.oats #2; faraway worldcup; HLMdiag
  wages; gamlss.data respInf; languageR english; nlme Machines; rabe_hesketh bladder, headache;
  zuur_zim Beavers2; mlmRev Mmmec; alda congress_pp, tolerance_pp.
- formula only: glmmTMB Salamanders (zipm3's `spp * mined` in the zero-inflation part too);
  pymc_examples radon (`log(activity + 0.1)`, the notebook's log_radon, and `||`); nlme
  Phenobarb (ApgarInd on volume only, diagonal random effects, ch06.R); zuur_mixed RIKZ
  (Exposure 8 and 10 pooled against 11); faraway choccake (`factor(temp)`).
- corrected to a located source: rabe_hesketh wine (MLMUS3 exercise 10.9, binary `bitter`
  additive in temp and contact, `published_model` `yes`; `bitterness` moved to `ignore`);
  carData KosteckiDillon (Fox's appendix final model, treatment and `sqrt(posttreat)` derived
  from `time`, random in both); MASS OME (grouped by `ID:Age`, the page's UID; OME only in the
  second-stage regression); goldstein_msm playactivity (Table 9.3 analysis A, continuous log
  duration with activity-specific child effects, not multinomial); hox thaieduc (chapter 6
  uses `SEX` alone).
- `published_model` `no`: rabe_hesketh crime (ch5.do fits county fixed effects; the
  random-intercept rendering is inferred, `log(crmrte)` and `factor(year)` in the formula).

## Hand sample, batch 3 (#12, 2026-10-09)

`shards/registry_hand_sample_3.csv`, `dropped_hand_sample_3.csv`, `excluded_hand_sample_3.csv`.

- stand: stata_toenail; medicaldata indometh, opt (the linear rendering is no published survival
  analysis); agridat cox.stripsplit; stan_arm cty.dat, hiv.data.json; stata_pefrate;
  rabe_hesketh schooleffects (a cohort column alone is no grouping factor), bp, homeless
  (`housing` three ordered values, the stored product `s8lint` a covariate); rethinking Trolley;
  faraway eggprod; languageR warlpiri; nlmeU fcat (the chapter 19 script fits the crossed
  intercepts, no native trials column); brms inhaler.
- formula only: zuur_mixed DeerEcervi (`I(Ecervi > 0)`, the Bernoulli presence model, the raw
  column kept); stata_nlswork3 (metobit with `ul(1.9)`); HLMdiag autism (the book's final
  chapter 6 model, no random intercept, no quadratic-by-group term); agridat
  burgueno.unreplicated (m2's AR1(col) × AR1(row) residual).
- corrected to a located source: rabe_hesketh coursework #2 (the review's bivariate model,
  `published_model` `yes`); snijders_bosker sheet 16 #2 (ch16.r, Table 16.2: `iq_verb * ses` and
  the school means `sch_iqv * sch_ses`); mlmRev Chem97 #2 (`score` `ordinal`, ordered A-level
  grades).
- `published_model` `no`: agridat nass.sorghum (the help fits Illinois corn); cmm_ilea567
  (the seven-predictor model is not in the source).
- excluded: hox SocsLong.sav, `simulated data` per the author's data appendix (DataStories.pdf).

## Hand sample, batch 4 (#12, 2026-10-09)

`shards/registry_hand_sample_4.csv`.

- stand: rabe_hesketh coursework #1 (the verdict read the single-response row of before batch
  3's siblings; the aligned `written` row kept); alda wages_pp (Table 5.4 Model C); posteriordb
  radon_all; stata_catheter (Weibull, patient intercept); stata_earthquake (the [ME] menl
  example); SASmixed Cultivation, zuur_zim OrangedCrownedWarblers, datasets OrchardSprays,
  lattice barley (notes only).
- formula: carData Blackmore (chap-7.R's `bcnPower(exercise, 0.25, 0.1)`); nlme Ovary (an
  independent sine slope by Mare, ch05.R); goldstein_msm HUNGARY #2 (stored column names);
  posteriordb timssAusTwn (the person matrix W's taiwan × female + book14, no columns, in the
  formula only), state_wide_presidential_votes (the Stan mean written out); stan_arm radon
  (`y` the response, log(0.1) for three zeros; `radon` to `ignore`).
- corrected to a located source: zuur_mixed RIKZDATAEnv (Chapter18.r M1, `log(DIN)` with
  smooths of Year, day and coordinates, `published_model` `yes`); rabe_hesketh thailand (MLMUS4
  exercise 10.7, `wt1` a frequency weight, `published_model` `yes`).
- `published_model` `no`, the formula kept as proposed: hox Galo; agridat vargas.wheat2.yield
  (PLS); nlme Relaxin; MASS immer (both years or their mean, Loc fixed); rabe_hesketh garrett
  (pooled xtpcse); zuur_zim SpidersHongKongV2 #2 (hurdle models); pingouin cronbach_alpha.
- uci_760 gait: `replication` a grouping factor in `subject:condition:replication`, the
  proposed formula extended by it.

## The O/low re-read (#13, 2026-10-09)

The blind re-read of the O/low stratum; `shards/registry_reread_o_low.csv`.

- openml_43550: `patientid` added, crossed with `Hospital` (75% of patients in more than one
  hospital); `City_Code_Patient` added beside `Hospital_city`.
- openml_46630: `lesion_id` added, nested in `patient_id` (the authors' patient > lesion > image
  hierarchy).
- uci_760: the batch 4 reading stands against the blind reading's recalled `condition:time`.
- openml_4541: covariates and seven interactions of Strack et al. 2014's final model, the recodes
  named in the formula; the eighth, `diag_1_group:HbA1c_group`, in the formula only (`RULE GAP:
  derived interaction`).
- openml_343: `plot` (the cultivars) and the six other cover measures of 1991–94 added, the
  documented objective predicting 1994 white-clover cover from them.
- openml_1100, pmlb_apnea1: stand.

## Slope decisions (#27, 2026-10-09)

The 35 rows the slope parser reported, decided on Claude's proposals revised after a colleague's
review; `shards/registry_slopes_decisions.csv`. Rules:
- R1: an interaction slope is dropped and only the main effects present after R's expansion
  stay.
- R2: `(1|g) + (0 + x|g)` is `x||g`; a lone `(0 + x|g)` is `x|g` for a categorical `x`
  (equivalent) and an approximation for a numeric one.
- R3: a dropped polynomial slope or a global shift keeps the covariate; a non-affine or
  group-dependent recode is not substituted by default.
- R4: nonlinear parameters stay empty and are refused at admission (#32).

Fidelity: `equivalent` is the same random-effect structure in another basis (not the same
prior), `approximate` changes it.

- nlme Cefamandole, IGF, Muscle, Soybean: empty; random effects on nonlinear parameters,
  refused at admission (`nonlinear_parameter_model`, #32).
- nlme Dialyzer: `pressure|Subject`; approximate, the quadratic slope dropped.
- nlme Ovary: empty; the slope is on `sin(2*pi*Time)`, refused at admission
  (`non_affine_feature`, #32).
- nlme Wafer: empty until #45 puts `Wafer:Site` in the row (its `Site` codes repeat across
  wafers); then `voltage|Wafer;voltage|Wafer:Site`, the quadratic slopes dropped.
- HLMdiag autism: `age2|childid`; approximate, an intercept variance the book removed is added
  and the quadratic slope dropped.
- agridat harris.wateruse: `day||tree`; equivalent, `ti = day/100`.
- carData Blackmore: `age|subject`; equivalent, `I(age - 8)` a shift under a correlated
  intercept.
- carData KosteckiDillon: empty, an approved intercept-only approximation; `treatment` and
  `sqrt(posttreat)` are derived columns the row lacks.
- languageR beginningReaders: `LogFrequency||Subject;OrthLength||Subject;PC1||Subject`;
  equivalent.
- stan_arm ARM/Ch.20/allvar.csv: `visage||newpid`; approximate, `time = visage - baseage` a
  shift per child.
- pymc_examples external_pp: `GRADE||ID`; approximate, the polynomial slopes dropped.
- pymc_examples employee: `lmx||team`; equivalent.
- goldstein_msm playactivity.xls: `activity 1|ID;activity 2|ID;activity 4|ID`; approximate, an
  intercept variance added (names with spaces since 3e536ad).
- rabe_hesketh electricity: `price|id;contract|id;local|id;known|id;tod|id;seasonal|id`;
  approximate, an intercept variance and its correlations added.
- rabe_hesketh yogurt: `brand|house`; equivalent, K brand effects with a full covariance.
- goldstein_msm OXBOYS.xls: `Age centered about 13 years|ID`; approximate, the quadratic slope
  dropped.
- koczynska_2026_osf_48, _49: the five lag-1 slopes over `cntry`; approximate,
  `libdem_lag1:trust_lag1` dropped.
- naranowicz_2024_osf_2 #2: `SenType|PrtpCd;Mood|Trg;SenType|Trg`; approximate,
  `Mood:SenType` dropped.
- timmer_2024_osf_16, _15: `Cue`, `Language`, `trial_type` over `subject`, and `Cue` (16 only)
  and `Language` over `picture`, correlated (`|`); equivalent to the deposited script's lmer
  terms, the filed `||` on categorical columns set aside.
- sequestro_2024_osf_2: `condition|ppid;RTc|ppid`; _11, _12, _16: `condition|ppid;RT..s.|ppid`;
  approximate, `condition:RT` dropped.
- gumundsdottir_2026_osf_6: empty; time is a non-linear recode of wave (0, 1, 2, 3, 6 months),
  refused at admission (`non_affine_feature`, #32).
- avetisyan_2020_osf_2 E3, avetisyan_2020_osf E2: `cond|subj;cond|item`; equivalent, the K − 1
  contrasts of `cond` span its full factorial.
- weaving_2023_osf: `group_n|study;SDO_MC|study;GSJ|study`; approximate, `group_n:SDO_MC`
  dropped.
- kleisner_2026_osf #1–3: `SEX|POPULATION`; approximate, the sex-specific intercepts kept and
  the SEX × covariate slopes dropped.

## Hand sample 2, batch 1 (#61, 2026-10-18)

The second hand sample, over suite 1.1's candidates not yet hand-checked; `shards/registry_hand_sample_2_1.csv`,
`registry_hand_sample_2_1_siblings.csv`. Taken on review: every row whose notes open with `NONLINEAR:` is
refused at admission (`nonlinear_model`); a censored time filed as continuous is refused
(`censored_response`: gehan, bladder, blindness, divorce2, infections, mortality, recurrent, SibDiv,
nlswork3, external_pp); Soils #3 and carData Pottery #1 and #3 follow Soils #2 and Pottery #2 as
siblings. The contract cannot drop amenorrhea's `trt` main effect or keep danish's quadratic.

- **1. Soils — `published_model=no`**; the source uses fixed Block in MANOVA, so the random-Block formula is a proposal. [Source](https://www.jstatsoft.org/article/view/v017i06).

- **2. Owls — stands**; Chapter 13’s `O2.lmer` explicitly fits this Poisson model, including the brood-size offset and random nest intercept. [Scripts](https://www.highstat.com/Books/Book2/ZuurMixedModellingAllRCode.zip).

- **3. troutegg — stands**, including `published_model=no`; Faraway fits fixed `location + period`, and the random-location adaptation is correctly labelled unpublished. [Script](https://julianfaraway.github.io/faraway/ELM/scripts/binary.R).

- **4. ISIT — `published_model=no` for the recorded linear formula**; the documented GAMM uses `Sources ~ s(Depth1000) + fMonth`, with a Station random intercept, where `Depth1000=SampleDepth/1000` and Month is categorical. [Chapter 17 scripts](https://www.highstat.com/Books/Book2/ZuurMixedModellingAllRCode.zip).

- **5. Lanza — stands**, including `published_model=no`; the book’s `cmh_test(classification ~ treatment | study, ...)` conditions on study strata rather than fitting random study intercepts. [Source](https://github.com/cran/HSAUR3/blob/1.0-16/vignettes/Ch_conditional_inference.Rnw).

- **6. indo_rct — stands**, including `published_model=no`; the proposed random-site model is not the trial’s published analysis. [Paper](https://doi.org/10.1056/NEJMoa1111103).

- **7. amenorrhea — `interactions=trt:time`; `formula=y ~ time + I(time^2) + trt:time + trt:I(time^2) + (1|id)`**; FLW §14.7 includes both treatment-by-time terms and no treatment main effect; `published_model=yes` remains correct for this corrected formula. [Author’s code](https://content.sph.harvard.edu/fitzmaur/ala2e/prog14_7.html).

- **8. Alfalfa — stands**; Pinheiro–Bates Chapter 1, Exercise 4(b), explicitly states `fixed=Yield ~ Date*Variety`, `random=~1|Block/Variety`. [Book chapter](https://link.springer.com/chapter/10.1007/978-1-4419-0318-1_1).

- **9. HUNGARY, Physics core — `formula=I(``Physics core``/10) ~ ``gender,girl=1`` + (1|School)`**, using backticks around the two column names; the source divides Physics core by its ten items. `published_model=yes` remains appropriate under the multivariate-split rule. [Source, §4.4](https://www.bristol.ac.uk/media-library/sites/cmm/migrated/documents/multbook1995.pdf).

- **10. bacteria — stands**; the help explicitly fits the recorded binomial PQL model with `I(week > 2)` and an ID random intercept. [Source](https://github.com/cran/MASS/blob/7.3-66/man/bacteria.Rd).

- **11. SibDiv — `published_model=no` for the filed `Surv(...)` formula; refuse the raw-duration candidate**; Hox Chapter 8 instead documents person-year logistic `divorce ~ t + I(t^2) + period53 + educlev + gender + (1|famid)`, with standardized duration `t`. This requires person-year expansion; `family=cox` would not describe that source model. [Hox, pp. 167–168](https://elib.vku.udn.vn/bitstream/123456789/4239/1/2010.%20Multilevel%20Analysis-Techniques%20and%20Applications%20%282nd%20Edition%29.pdf).

- **12. ratdrink — stands**; Faraway’s second edition, Chapter 11, Exercise 11.1(b), p. 251 explicitly specifies treatment-specific mean lines and random rat intercepts and slopes, supporting the recorded formula and `published_model=yes`. [Book](https://julianfaraway.github.io/faraway/ELM/).

- **13. Gasoline — stands**; the authors’ MEMSS companion explicitly fits `yield ~ endpoint + (1|Sample)`. [Source](https://cran.r-universe.dev/MEMSS/doc/manual.html#Gasoline).

- **14. unemployment_pp — stands**; UCLA Chapter 5 Model C uses `cesd ~ months*unemp` with correlated intercept and months effects within ID. [Source](https://stats.oarc.ucla.edu/r/examples/alda/r-applied-longitudinal-data-analysis-ch-5/).

- **15. FirstSexPP — `published_model=no` for the recorded proposal**; Hox’s example is single-level logistic survival with six grade indicators and `partrans`, rather than numeric-only period, PAS, and a person random intercept. [Author’s appendix](https://www.joophox.net/mlbook2/DataStories.pdf).

- **16. tvsfpors — stands**; Stata explicitly fits `meologit thk prethk cc##tv || school: || class:`, with ordinal thk and classes nested within schools. [Source](https://www.stata.com/features/overview/multilevel-ordered-logistic-models/).

- **17. employee — stands**; separate Normal priors for team intercept and lmx-slope deviations confirm `lmx||team`. [Pinned notebook](https://github.com/pymc-devs/pymc-examples/blob/17c8f90dc90691b41587dfdf477698d74cf5c18c/examples/howto/Missing_Data_Imputation.myst.md#L703-L746).

- **18. Loblolly — specify `height ~ SSasymp(age, Asym, R0, lrc)`, with `fixed=Asym+R0+lrc~1`, `random=Asym~1|Seed`**; `published_model=yes` applies to this documented nonlinear model, not its linear surrogate. Refuse the linear candidate. [Source](https://stat.ethz.ch/R-manual/R-patched/library/nlme/html/nlme.html).

- **19. schizophrenia2 — `published_model=no`**; the book’s own slides assign this as a GEE exercise and do not state the recorded random-intercept GLMM. [Pinned source](https://github.com/cran/HSAUR3/blob/1.0-16/inst/slides/Ch_analysing_longitudinal_dataII.Rnw#L286-L297).

- **20. Ospreys — stands as an explicitly unpublished proposal**; `published_model=no` is correct, while random COAST remains an unverified assumption—no accessible source model established it. [Official book page](https://www.highstat.com/index.php/books2?catid=18&id=23&view=article).

- **21. Machines — stands**; the book script explicitly fits `lme(score ~ Machine, random=~1|Worker)`. [Pinned script](https://github.com/cran/nlme/blob/3.1-171/inst/scripts/ch01.R#L52-L60).

- **22. danish — add `LogWordFreq:LogAffixFreq:Sex` to `interactions`**; the source’s three-way product includes this term, and its quadratic LogCUP term must also survive materialization. [Pinned source](https://github.com/cran/languageR/blob/1.6/man/danish.Rd).

- **23. Pottery — `published_model=no` for the recorded random-Site model**; the source fits fixed Site, with `Fe ~ Site` as the iron component of its MANOVA. [SAS manual](https://support.sas.com/documentation/cdl/en/statug/68162/HTML/default/statug_glm_examples06.htm).

- **24. rm_corr — `published_model=no` for the recorded mixed model**; the implementation fits fixed-subject ANCOVA, `PacO2 ~ C(Subject) + pH`, rather than random subject intercepts. [Pinned implementation](https://github.com/raphaelvallat/pingouin/blob/bb1cb22a3137f5864341c7a06cd030c072a170d4/src/pingouin/parametric.py#L1702-L1708).

- **25. fims — the nonlinear reading stands**, with literal latent regression `theta ~ normal(W_adj * lambda_adj, 1)`; `published_model=yes` applies to the documented 2PL, not an additive 1PL surrogate. Refuse that linear candidate; every unsupported `NONLINEAR:` row needs the same admission treatment. [Pinned Stan model](https://github.com/stan-dev/posteriordb/blob/91027f9cdd13b7e76283fec3f2898f59d4b83ec4/posterior_database/models/stan/2pl_latent_reg_irt.stan).
