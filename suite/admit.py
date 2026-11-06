"""admit.py defines the admission of suite 1.1: registry rows in, candidates and refusals out.

Every row the family rule covers is built into its problem and materialized under the cache.
Its contract hash and its dimensions go into the candidate list. Six decisions guide admission:
- hand decisions first: a row whose documented model does not survive into the contract
  is refused by id, or by its notes' marker when the model is nonlinear;
  a row whose random effects were changed carries its fidelity:
  `structure_equivalent` (the same structure in another basis)
  or `approximate` (terms changed or dropped);
- a refusal is kept with its reason beside the candidates;
- a problem with no more rows than design columns is refused,
  since its likelihood alone identifies no fixed effect;
- a table that fails to load is a failure and stops the run before writing,
  so the list never misses a row silently;
- the list and the refusals keep registry order, not sorted by id;
- no problem is refused for the rows it loses to missing values: the list records the dropped share,
  and the report prints the largest, to be read before a reference is run.

pipeline:
---------
the registry's rows
-> refused by hand decision                    REFUSED
-> refused as nonlinear by its notes' marker   NONLINEAR
-> the loaded table, or a failure              loadTable
-> the problem, or refused by the contract     Problem.build
-> refused with no more rows than columns      Problem.measureDimensions
-> materialized, its candidate                 _candidate
-> the candidate list and the refusals         Admitted.write

Run from the repo root:

    uv run python suite/admit.py
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
from mixedbench import registry
from mixedbench.contract import Dimensions, Problem, Refused, materialize
from mixedbench.registry.row import Row, joinList, writeCsv

# =====================================================================================
# the hand decisions
# =====================================================================================
# what the family rule cannot see, read off each row's documented model

HAZARD = 'hazard_model: a discrete-time hazard without a person intercept (#161)'

# rows the documented model does not survive into the contract, though the family rule covers them:
# an empty `random_slopes` there is no approved intercept-only model (#27, #45).
REFUSED = {
    'nlme/Cefamandole/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    'nlme/Muscle/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    'nlme/Soybean/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    # one-compartment pharmacokinetic models (notes)
    'nlme/Phenobarb/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
    'nlme/Quinidine/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
    'nlme/Ovary/1': 'non_affine_feature: the slope is on sin(2*pi*Time) (#27)',
    'gumundsdottir_2026_osf_6/Questionnaire_data_long/1': (
        'non_affine_feature: time is a non-linear recode of wave (#27)'
    ),
    # a random effect correlated across groups by a known matrix, which no iid factor is (#45)
    'marton_2022_figshare/OS_pigmentation_data.csv/1': (
        'covariance_structured_effect: (1 | phylogeny) (#45)'
    ),
    'marton_2022_figshare/OS_pigmentation_data.csv/2': (
        'covariance_structured_effect: (1 | phylogeny) (#45)'
    ),
    'marton_2022_figshare/OS_pigmentation_data.csv/3': (
        'covariance_structured_effect: (1 | phylogeny) (#45)'
    ),
    'kappers_2018_osf_4/phenotypic_data_for_animal_model.xlsx/1': (
        'covariance_structured_effect: (1 | animal), the pedigree effect (#45)'
    ),
    'kappers_2018_osf_4/phenotypic_data_for_animal_model.xlsx/2': (
        'covariance_structured_effect: (1 | animal), the pedigree effect (#45)'
    ),
    'verberk_2022_zenodo/Data/Pcrit data for 195 fish species ( 2022_02_14).csv/1': (
        'covariance_structured_effect: (1 | animal), phylogenetically correlated (#45)'
    ),
    'lagisz_2020_osf_3/MA_dataset_with_ES.csv/2': (
        'covariance_structured_effect: gr(Species_Latin, cov = ...) (#45)'
    ),
    'kleisner_2026_osf/data.csv/1': (
        'covariance_structured_effect: POPULATION correlated by linguistic similarity (#32)'
    ),
    'kleisner_2026_osf/data.csv/2': (
        'covariance_structured_effect: POPULATION correlated by linguistic similarity (#32)'
    ),
    'kleisner_2026_osf/data.csv/3': (
        'covariance_structured_effect: POPULATION correlated by linguistic similarity (#32)'
    ),
    'rethinking/data/Primates301.csv/1': (
        'covariance_structured_effect: species correlated by phylogenetic distance (#61)'
    ),
    'rethinking/data/Primates301.csv/2': (
        'covariance_structured_effect: species correlated by phylogenetic distance (#61)'
    ),
    'spaMM/arabidopsis/1': (
        'covariance_structured_effect: sites correlated by a Matern field over LAT and LONG (#170)'
    ),
    'rabe_hesketh/family.dta/1': (
        'covariance_structured_effect: genetic effects shared by mother, father and child (#82)'
    ),
    # a row that stands for several observations, which the documented fit weights by count (#61)
    'agridat/keen.potatodamage/1': 'frequency_weighted: each cell weighted by count (#61)',
    'agridat/jansen.strawberry/1': 'frequency_weighted: each cell weighted by count (#179)',
    'rabe_hesketh/twin_hay.dta/1': (
        'frequency_weighted: each response pattern weighted by freq (#61)'
    ),
    'mixor/concen/1': 'frequency_weighted: each response pattern weighted by freq (#162)',
    'mixor/norcag/1': 'frequency_weighted: each response pattern weighted by freq (#162)',
    'mixor/irt.data/1': 'frequency_weighted: each response pattern weighted by freq (#162)',
    # a documented model whose likelihood the filed rows do not hold (#61)
    'rabe_hesketh/elections.dta/1': (
        'choice_model: rank == 1 in conditional and mixed logits over choice sets (#61)'
    ),
    'rabe_hesketh/crackers.dta/1': (
        'choice_model: a mixed multinomial logit over four-brand choice sets (#82)'
    ),
    'rabe_hesketh/hybrid.dta/1': (
        'choice_model: a mixed multinomial logit over three-car choice sets (#82)'
    ),
    'rabe_hesketh/electricity.dta/1': (
        'choice_model: a mixed logit over four-supplier choice sets (#82)'
    ),
    'rabe_hesketh/yogurt.dta/1': (
        'choice_model: a mixed multinomial logit over brand choice sets (#82)'
    ),
    'rabe_hesketh/cito.dta/1': (
        'item_response_model: the items y1-y18 reshaped long, cito a school indicator (#61)'
    ),
    'goldstein_msm/HTBONEBoys.xls/1': (
        'multivariate_response: height and bone age stacked, each with its own residual (#82)'
    ),
    'hox/AstLrd.sav/1': (
        'known_sampling_variance: meta-analysis log odds ratios with variances VarLor (#82)'
    ),
    'rabe_hesketh/ecls_child.dta/1': (
        'joined_covariate: nbhoodcl comes from ecls_school.dta, merged by s4_id (#82)'
    ),
    'liutu_2026_zenodo_3/Measurement_plots.xlsx/1': (
        'recoded_covariate: a two-level peat thickness, the table nine measured classes (#151)'
    ),
    # a vector autoregression, whose predictors are the series' lags, no columns of the table (#120)
    'pymc_examples/examples/data/gdp_data_hierarchical_clean.csv/1': (
        'lagged_predictors: a hierarchical VAR(2) of dl_gdp, dl_cons and dl_gfcf (#120)'
    ),
    'pymc_examples/examples/data/gdp_data_hierarchical_clean.csv/2': (
        'lagged_predictors: a hierarchical VAR(2) of dl_gdp, dl_cons and dl_gfcf (#120)'
    ),
    'pymc_examples/examples/data/gdp_data_hierarchical_clean.csv/3': (
        'lagged_predictors: a hierarchical VAR(2) of dl_gdp, dl_cons and dl_gfcf (#120)'
    ),
    # a censored time filed as a continuous response, whose Gaussian fit ignores the censoring (#61)
    'MASS/gehan/1': 'censored_response: a censored time filed as continuous (#61)',
    'rabe_hesketh/bladder.dta/1': 'censored_response: a censored time filed as continuous (#61)',
    'rabe_hesketh/blindness.dta/1': 'censored_response: a censored time filed as continuous (#61)',
    'rabe_hesketh/infections.dta/1': 'censored_response: a censored time filed as continuous (#61)',
    'rabe_hesketh/mortality.dta/1': 'censored_response: a censored time filed as continuous (#61)',
    'hox/SibDiv.sav/1': 'censored_response: a censored time filed as continuous (#61)',
    'pymc_examples/examples/data/external_pp.csv/1': (
        'censored_response: a censored score filed as continuous (#61)'
    ),
    'beyondarena_sat11_hand_algo_runtime/sat11_hand_algo_runtime.pq/1': (
        'censored_response: a log runtime censored at log(5000) filed as continuous (#162)'
    ),
    'openml_41700/dataset_41700.pq/1': (
        'censored_response: a runtime censored at the 3600 s cutoff filed as continuous (#162)'
    ),
    'openml_43071/dataset_43071.pq/1': (
        'censored_response: a PAR10 runtime with a timeout penalty filed as continuous (#162)'
    ),
    'mixor/SmokeOnset/1': 'censored_response: a censored onset interval filed as continuous (#162)',
    'mixor/SmokeOnset/2': 'censored_response: a censored onset interval filed as continuous (#162)',
    # a response computed from several columns, which the contract would model as its first (#162)
    'AER/CASchools/1': 'computed_response: the average of math and read (#162)',
    'Ecdat/Star/1': 'computed_response: the sum of tmathssk and treadssk (#162)',
    'Ecdat/PSID/1': 'computed_response: the log hourly wage from earnings and hours (#162)',
    'AER/Fatalities/1': (
        'computed_response: the deaths per 10,000 residents from fatal and pop (#162)'
    ),
    'osf_confidence_kvam_2016/data_Kvam_2016.csv/1': (
        'computed_response: the log odds of Confidence folded by accuracy (#162)'
    ),
    'metadat/dat.besson2016/1': 'computed_response: a standardized mean difference (#162)',
    'metadat/dat.bornmann2007/1': 'computed_response: a log odds ratio (#162)',
    'metadat/dat.bourassa1996/1': 'computed_response: a log odds ratio (#162)',
    'metadat/dat.curtis1998/1': 'computed_response: a log ratio of means (#162)',
    'metadat/dat.dagostino1998/1': 'computed_response: a standardized mean difference (#162)',
    'DAAG/codling/1': (
        'computed_response: the complementary log-log of the mortality adjusted for cm (#162)'
    ),
    'osf_confidence_siedlecka_2019/data_Siedlecka_2019.csv/1': (
        'computed_response: the accuracy, Response equal to Stimulus (#162)'
    ),
    'osf_confidence_wierzchon_2014/data_Wierzchon_2014.csv/1': (
        'computed_response: the accuracy, Response equal to Stimulus (#162)'
    ),
    'osf_manylabs3/ML3AllSites.csv/1': (
        'computed_response: the prime-consistent answer, SRMeetingResponse by SRCondition (#162)'
    ),
    # a person-period table of a discrete-time hazard, which its source fits without a person
    # intercept, since a person holds at most one event (#161)
    'alda/aldatxt/teachers_pp.txt/1': HAZARD,
    'alda/aldatxt/tenure_pp.txt/1': HAZARD,
    'alda/aldatxt/mathdropout_pp.txt/1': HAZARD,
    'alda/aldatxt/firstarrest_pp.txt/1': HAZARD,
    'alda/aldatxt/suicide_pp.txt/1': HAZARD,
    'alda/aldatxt/congress_pp.txt/1': HAZARD,
    'alda/aldatxt/cocaine_relapse_pp.txt/1': HAZARD,
    'hox/FirstSexPP.sav/1': HAZARD,
    'alda/aldatxt/depression_pp.txt/1': HAZARD,
    # a table whose rows stack posterior draws of the same units (#161)
    'koczynska_2026_osf_49/merge_iter_20241030/1': (
        'stacked_draws: 100 posterior draws of the same country-years stacked as rows (#161)'
    ),
    # a table whose rows repeat its unit, which the contract cannot drop (#170)
    'bayesrules/moma/1': (
        'repeated_units: an artist repeated over the departments of its works (#170)'
    ),
}

# The marker that opens the notes of a row whose documented model is nonlinear in its parameters
# (survey README). No linear problem stands for such a model, so every marked row is refused.
NONLINEAR = 'NONLINEAR:'

# how far the problem's random effects are from the documented model's
# (#45): the same structure in another basis or changed.
Fidelity = Literal['structure_equivalent', 'approximate']
FIDELITY: dict[str, Fidelity] = {
    'agridat/harris.wateruse/1': 'structure_equivalent',
    'carData/Blackmore/1': 'structure_equivalent',
    'languageR/beginningReaders/1': 'structure_equivalent',
    'pymc_examples/examples/data/employee.csv/1': 'structure_equivalent',
    'timmer_2024_osf_16/color_experiments_data_27.05.2024.txt/1': 'structure_equivalent',
    'timmer_2024_osf_15/tone_experiments_data_27.05.2024.txt/1': 'structure_equivalent',
    'avetisyan_2020_osf_2/E3_data.csv/1': 'structure_equivalent',
    'avetisyan_2020_osf/E2_data.csv/1': 'structure_equivalent',
    'lagisz_2020_osf_3/MA_dataset_with_ES.csv/1': 'structure_equivalent',  # sigma absorbs EffectID
    'nlme/Dialyzer/1': 'approximate',
    'nlme/Wafer/1': 'approximate',
    'HLMdiag/autism/1': 'approximate',
    'carData/KosteckiDillon/1': 'approximate',
    'stan_arm/ARM/Ch.20/allvar.csv/1': 'approximate',
    'goldstein_msm/playactivity.xls/1': 'approximate',
    'rabe_hesketh/electricity.dta/1': 'approximate',
    'rabe_hesketh/fat.dta/1': 'approximate',  # the hinge after = pmax(time, 0) dropped (#61)
    'rabe_hesketh/yogurt.dta/1': 'approximate',  # two brand contrasts, no intercept (#61)
    'koczynska_2026_osf_48/data_means_20241030/1': 'approximate',
    'naranowicz_2024_osf_2/MO--ST_beh.csv/2': 'approximate',
    'sequestro_2024_osf_2/EXP2_3_pooled.csv/1': 'approximate',
    'sequestro_2024_osf_11/EXP2_elevator_main.csv/1': 'approximate',
    'sequestro_2024_osf_12/EXP1_elevator_main.csv/1': 'approximate',
    'sequestro_2024_osf_16/EXP3_elevator_main.csv/1': 'approximate',
    'weaving_2023_osf/df_ALL/1': 'approximate',
    # an observation-level term or a mapping the table lacks, dropped (#45)
    'lme4/grouseticks/1': 'approximate',
    'stan_arm/ARM/Ch.14/polls.dta/1': 'approximate',
    # a term the contract cannot write, dropped or simplified (#197)
    'fitzmaurice_progesterone/progesterone.dta/1': 'approximate',  # the hinge and the spline
    'rethinking/data/Achehunting.csv/1': 'approximate',  # one family for the hurdle, linear slopes
    'nlme/Spruce/1': 'approximate',  # the smoothing spline
    'mixedmodels_jl/mrk17_exp1.arrow/1': 'approximate',  # the uncorrelated lT slope correlated
    'nlmeU/prt/1': 'approximate',  # the fiber.f:occ.f slope
    'gamlss.data/Leukemia/1': 'approximate',  # the splines
    'nlmeU/SIIdata/1': 'approximate',  # the cubic in mathkind linear
    'MASS/Sitka/1': 'approximate',  # ordered(Time) as linear
    'faraway/hprice/1': 'approximate',  # the yearly ypc for the first year's income
    'fitzmaurice_cd4/cd4.dta/1': 'approximate',  # the hinge, triple therapy as group by week
    'pmlb_boxing1/analcatdata_boxing1.tsv.gz/1': 'approximate',  # the probit's fixed scales
    'pmlb_boxing2/analcatdata_boxing2.tsv.gz/1': 'approximate',  # the probit's fixed scales
    'fitzmaurice_muscatine/muscatine.dta/1': 'approximate',  # the quadratic in age
    'west_welch_galecki/autism/1': 'approximate',  # the quadratic, a random intercept added
    'diggle_cd4/CD4_data.txt/1': 'approximate',  # the hinge
    'rethinking/data/Wines2012.csv/1': 'approximate',  # the fixed SDs
    'datasets/ChickWeight/1': 'approximate',  # the quadratic and AR(1), a random intercept added
}


# =====================================================================================
# row -> problem -> materialized files -> candidate
# =====================================================================================
# the result first, then the admission that makes it one row at a time
@dataclass(frozen=True)
class Admitted:
    candidates: pd.DataFrame  # see `Admission._candidate`
    refused: dict[str, str]  # per refused problem id, the reason
    failed: dict[str, str]  # per problem id whose table did not load, the error

    def write(self, dir: Path) -> None:
        """The candidate list and the refusals with their reasons, both in registry order."""
        dir.mkdir(parents=True, exist_ok=True)
        writeCsv(self.candidates, dir / 'candidates.csv')
        refused = pd.DataFrame(self.refused.items(), columns=['id', 'reason'])
        writeCsv(refused, dir / 'refused.csv')

    def report(self, top: int = 10) -> str:
        """The refusals, the failures, and the `top` candidates by dropped share, largest first:
        no problem is refused for its dropped share,
        so the largest are read before a reference is run."""
        lines = [f'refused: {len(self.refused)}']
        lines += [f'  {id}\t{reason}' for id, reason in self.refused.items()]
        lines += [f'failed: {len(self.failed)}']
        lines += [f'  {id}\t{error}' for id, error in self.failed.items()]
        lines += [f'dropped share, top {top} of {len(self.candidates)} candidates:']
        largest = self.candidates.nlargest(top, 'dropped_share')
        lines += [
            f'  {share:.3f}\t{id}' for id, share in zip(largest['id'], largest['dropped_share'])
        ]
        return '\n'.join(lines)


class Admission:
    def __init__(
        self,
        rows: list[Row],
        loadTable: Callable[[Row], pd.DataFrame],
        cache: Path,
        refused: dict[str, str] = REFUSED,
        fidelity: dict[str, Fidelity] = FIDELITY,
    ) -> None:
        """`loadTable` gives a row's loaded table, its `types` declared; `refused` and `fidelity`
        are the hand decisions by problem id."""
        self.rows = rows
        self.loadTable = loadTable
        self.cache = cache
        self.refused = refused
        self.fidelity = fidelity

    def admit(self) -> Admitted:
        candidates = []
        refused = {}
        failed = {}
        for row in self.rows:
            id = row.id
            if id in self.refused:
                refused[id] = self.refused[id]
                continue
            if row.notes.startswith(NONLINEAR):
                refused[id] = 'nonlinear_model: the documented model is nonlinear in its parameters'
                continue
            try:
                table = self.loadTable(row)
            except Exception as error:  # the loader's verdict, as in the weekly fetch
                failed[id] = f'{type(error).__name__}: {error}'
                continue
            try:
                problem = Problem.build(row, table)
            except Refused as refusal:  # the family rule, a table with no complete row (#29)
                refused[id] = refusal.reason
                continue
            dimensions = problem.measureDimensions()
            if dimensions.n <= dimensions.d:
                refused[id] = (
                    'saturated_design: no more rows than design columns, '
                    'so the posterior rests on the prior'
                )
                continue
            candidates.append(self._candidate(row, problem, dimensions))
        return Admitted(pd.DataFrame(candidates), refused, failed)

    # ---------------------------------------------------------------------------------
    # problem -> materialized files -> candidate
    # ---------------------------------------------------------------------------------
    # the step that turns a built problem into its row of the list
    def _candidate(self, row: Row, problem: Problem, dimensions: Dimensions) -> dict:
        return {
            'id': problem.id,
            'contract_hash': materialize(problem, self.cache),
            'verified': row.verified,
            'dropped_share': problem.dropped_share,
            'fidelity': self.fidelity.get(problem.id, ''),
            'n': dimensions.n,
            'd': dimensions.d,
            'factors': joinList(problem.factors),
            'grouping': dimensions.grouping,
            'm': joinList(dimensions.m),
            'q': joinList(dimensions.q),
            'n_i_min': joinList(dimensions.n_i_min),
            'n_i_max': joinList(dimensions.n_i_max),
        }


# =====================================================================================
# main
# =====================================================================================
# admits the whole registry and writes suite 1.1 only if every table loaded
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'registry' / 'cache'
SUITE = ROOT / 'suite' / '1.1'

if __name__ == '__main__':
    tables = registry.Tables(CACHE)
    admission = Admission(registry.rows(), tables.load, CACHE)
    admitted = admission.admit()
    print(admitted.report())
    if admitted.failed:
        sys.exit(1)  # a list missing a row would drop it silently
    admitted.write(SUITE)
