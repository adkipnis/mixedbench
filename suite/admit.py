"""Admit the registry's rows to suite 1.1 (ADR 0002): every row the family rule covers is built
into its problem and materialised under the cache, and its contract hash goes into the
candidate list, in registry order; a refused row goes into the refusals with its reason. Run
from the repo root:

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
from mixedbench.contract import Problem, Refused, materialise
from mixedbench.datasets import Loader
from mixedbench.registry.row import Row, writeCsv

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'registry' / 'cache'
SUITE = ROOT / 'suite' / '1.1'

# =====================================================================================
# the hand decisions, by problem id
# =====================================================================================
# Rows the documented model does not survive into the contract, though the family rule covers
# them: an empty `random_slopes` there is no approved intercept-only model (#27, #45).
REFUSED = {
    'nlme/Cefamandole/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    'nlme/IGF/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    'nlme/Muscle/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    'nlme/Soybean/1': 'nonlinear_parameter_model: random effects on nonlinear parameters (#27)',
    # one-compartment pharmacokinetic models, the nlme tables and Stata's fuller copies (notes)
    'nlme/Phenobarb/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
    'nlme/Quinidine/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
    'stata_phenobarb/phenobarb.dta/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
    'stata_quinidine/quinidine.dta/1': 'nonlinear_parameter_model: a pharmacokinetic model (#32)',
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
}

# How far the problem's random effects are from the documented model's (VERDICTS.md, "Slope
# decisions"; #45): the same structure in another basis (not the same prior), or changed.
Fidelity = Literal['structure_equivalent', 'approximate']
FIDELITY: dict[str, Fidelity] = {
    'agridat/harris.wateruse/1': 'structure_equivalent',
    'carData/Blackmore/1': 'structure_equivalent',
    'languageR/beginningReaders/1': 'structure_equivalent',
    'pymc_examples/examples/data/employee.csv/1': 'structure_equivalent',
    'rabe_hesketh/yogurt.dta/1': 'structure_equivalent',
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
    'pymc_examples/examples/data/external_pp.csv/1': 'approximate',
    'goldstein_msm/playactivity.xls/1': 'approximate',
    'rabe_hesketh/electricity.dta/1': 'approximate',
    'goldstein_msm/OXBOYS.xls/1': 'approximate',
    'koczynska_2026_osf_48/data_means_20241030/1': 'approximate',
    'koczynska_2026_osf_49/merge_iter_20241030/1': 'approximate',
    'naranowicz_2024_osf_2/MO--ST_beh.csv/2': 'approximate',
    'sequestro_2024_osf_2/EXP2_3_pooled.csv/1': 'approximate',
    'sequestro_2024_osf_11/EXP2_elevator_main.csv/1': 'approximate',
    'sequestro_2024_osf_12/EXP1_elevator_main.csv/1': 'approximate',
    'sequestro_2024_osf_16/EXP3_elevator_main.csv/1': 'approximate',
    'weaving_2023_osf/df_ALL/1': 'approximate',
    # an observation-level term or a mapping the table lacks, dropped (#45)
    'lme4/grouseticks/1': 'approximate',
    'rethinking/kl_dyads/1': 'approximate',
    'rethinking/kl_dyads/2': 'approximate',
    'stan_arm/ARM/Ch.14/polls.dta/1': 'approximate',
}


# =====================================================================================
# pipeline: row -> problem -> materialised files -> candidate
# =====================================================================================
@dataclass(frozen=True)
class Admitted:
    candidates: pd.DataFrame  # see `Admission.candidate`
    refused: dict[str, str]  # per refused problem id, the reason
    failed: dict[str, str]  # per problem id whose table did not load, the error

    def write(self, dir: Path) -> None:
        """The candidate list and the refusals with their reasons, both in registry order."""
        dir.mkdir(parents=True, exist_ok=True)
        writeCsv(self.candidates, dir / 'candidates.csv')
        refused = pd.DataFrame(self.refused.items(), columns=['id', 'reason'])
        writeCsv(refused, dir / 'refused.csv')

    def report(self, top: int = 10) -> str:
        """The refusals, the failures, and the `top` candidates by dropped share, largest
        first: ADR 0002 caps no share, so a large one is read before a reference is run."""
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
        table: Callable[[Row], pd.DataFrame],
        cache: Path,
        refused: dict[str, str] = REFUSED,
        fidelity: dict[str, Fidelity] = FIDELITY,
    ) -> None:
        """`table` gives a row's loaded table, its `types` declared; `refused` and `fidelity`
        are the hand decisions by problem id."""
        self.rows = rows
        self.table = table
        self.cache = cache
        self.refused = refused
        self.fidelity = fidelity

    def admit(self) -> Admitted:
        candidates = []
        refused = {}
        failed = {}
        for row in self.rows:
            id = f'{row.source}/{row.object}/{row.model_index}'
            if id in self.refused:
                refused[id] = self.refused[id]
                continue
            try:
                table = self.table(row)
            except Exception as error:  # the loader's verdict, as in the weekly fetch
                failed[id] = f'{type(error).__name__}: {error}'
                continue
            try:
                problem = Problem.build(row, table)
            except Refused as refusal:  # the family rule, a table with no complete row (#29)
                refused[id] = refusal.reason
                continue
            candidates.append(self.candidate(row, problem))
        return Admitted(pd.DataFrame(candidates), refused, failed)

    # ---------------------------------------------------------------------------------
    # pipeline
    # ---------------------------------------------------------------------------------
    def candidate(self, row: Row, problem: Problem) -> dict:
        return {
            'id': problem.id,
            'contract_hash': materialise(problem, self.cache),
            'verified': row.verified,
            'dropped_share': problem.dropped_share,
            'fidelity': self.fidelity.get(problem.id, ''),
        }


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    loader = Loader(CACHE, manifest=registry.manifest())
    sources = registry.sources()

    def table(row: Row) -> pd.DataFrame:
        return loader.load(sources[row.source], row.object, row.types)

    admitted = Admission(registry.rows(), table, CACHE).admit()
    print(admitted.report())
    if admitted.failed:
        sys.exit(1)  # a list missing a row would drop it silently
    admitted.write(SUITE)
