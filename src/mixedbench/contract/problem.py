"""problem.py defines the contract: a registry row and its table go in, a `Problem` comes out.

A problem holds the table a model is fitted to and metadata:
the model formula, model family, prior, train/test splits, scales, and parameter names.
`Problem.build` follows five decisions.
1. Reproducible: a problem depends only on the pins, the row and the contract version.
   The splits are seeded by the problem id.
2. Uniform: the response type fixes the family.
   One prior serves every problem.
   One typing rule decides each column's kind.
3. Complete cases only: a row that misses a model value is dropped.
   A row outside the contract (a categorical response, a censored model) raises `Refused`.
4. Scaled per fold: the table stays in raw units.
   Each fold records the scales of the rows its fit sees.
5. Parameter names are based on brms and are in brms's block order.

pipeline:
---------
a typed registry row and its loaded table
-> refused if outside the contract             _refuseUncovered
-> composites added, incomplete rows dropped   withComposites, _dropIncomplete
-> each covariate's kind and coded columns     _typeCovariates, _codeTerms
-> the design, factors and response            _assembleDesign, _codeFactor, _codeResponse
-> the regimes `rows` and `groups`, in folds   _dealRegimes
-> each fold's scales                          _measureFolds
-> the family, prior and parameter names       _assignPrior, _nameParameters
-> the problem                                 build
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.metadata import version
from itertools import combinations
from typing import Literal

import numpy as np
import pandas as pd
from mixedbench.registry.row import Row, parts

# =====================================================================================
# the problem
# =====================================================================================
# what `build` returns or raises, and the records a problem holds
CONTRACT = int(version('mixedbench').partition('.')[0])  # the package's major version
Regime = Literal['full', 'rows', 'groups']


@dataclass(frozen=True)
class Problem:
    id: str  # <source>/<object>/<model_index>
    table: pd.DataFrame  # the coded columns in raw units, one row per kept row
    # the column roles in `table`; the factors hold 0-based codes, and the columns `rows` and
    # `groups` hold the fold each row is held out in, -1 for none
    design: tuple[str, ...]  # `Intercept` first
    response: str
    factors: tuple[str, ...]
    levels: dict[str, tuple]  # each recoded column's levels, in code order
    # per regime and fold, the mean and SD of each continuous column over the rows its fit
    # sees, with `full` as one fold that holds nothing out
    scales: dict[Regime, tuple[dict[str, Scale], ...]]
    dropped_share: float  # the share of loaded rows dropped for a missing model value
    trials: str | None  # the trials column of a binomial response
    family: str  # brms's name, set by the family rule
    link: str
    prior: dict[str, Prior]  # one prior per brms class the problem has
    parameters: tuple[str, ...]  # the names of the global parameters, in order
    correlations: dict[str, tuple[str, ...]]  # the elements of each `cor[<factor>]`, in order
    contract: int  # the version of the contract the problem was built under

    @classmethod
    def build(cls, row: Row, table: pd.DataFrame) -> Problem:
        """Raises `Refused` if the contract does not cover the row."""
        return _Builder(row, table).build()

    def standardized(self, regime: Regime = 'full', fold: int = 0) -> pd.DataFrame:
        """Returns the standardized model columns of the rows a fit on the regime's `fold` sees.
        Continuous columns are z-scored with the fold's scales.
        An interaction is the product of its standardized parts,
        see Aiken & West (1991) and Gelman (2008)."""
        columns = [*self.design, self.response]
        if self.trials:
            columns.append(self.trials)
        columns += self.factors
        rows = _selectSeenRows(self.table, regime, fold)
        table = rows[columns].copy()
        for column, scale in self.scales[regime][fold].items():
            table[column] = (table[column] - scale.mean) / scale.sd
        for column, operands in self._findInteractions().items():
            table[column] = table[list(operands)].prod(axis=1)
        return table

    def _findInteractions(self) -> dict[str, tuple[str, ...]]:
        """Returns each interaction column with its parts, in order."""
        # a covariate's coded columns: a continuous one has a scale, a binary one has levels,
        # any other is a contrast
        contrasts = []
        for column, levels in self.levels.items():
            contrasts += [f'{column}[{level}]' for level in levels[1:]]
        covariate_columns = [*self.scales['full'][0], *self.levels, *contrasts]
        design = self.design[1:]  # without `Intercept`
        coded = [column for column in design if column in covariate_columns]
        # every other design column is an interaction
        interactions = {}
        for column in design:
            if column not in coded:
                interactions[column] = self._splitInteraction(column, coded)
        return interactions

    @staticmethod
    def _splitInteraction(column: str, coded: list[str]) -> tuple[str, ...]:
        """Returns the coded parts of an interaction column, read left to right."""
        # a level may contain `:`, so each part is the longest coded column that matches
        parts = []
        rest = column
        while rest:
            matches = [c for c in coded if rest == c or rest.startswith(f'{c}:')]
            part = max(matches, key=len)
            parts.append(part)
            rest = rest[len(part) + 1 :]  # past the part and its `:`
        return tuple(parts)

    def globalDraws(self) -> tuple[str, ...]:
        """Returns `parameters` with each `cor[<factor>]` split into its pairs.
        A pair is `cor[<factor>][<a>,<b>]`, in brms's order."""
        blocks = {}
        for factor, elements in self.correlations.items():
            blocks[f'cor[{factor}]'] = elements
        names = []
        for name in self.parameters:
            if name in blocks:
                pairs = combinations(blocks[name], 2)
                names += [f'{name}[{a},{b}]' for a, b in pairs]
            else:
                names.append(name)
        return tuple(names)

    def localDraws(self) -> dict[str, tuple[str, ...]]:
        """Returns the names of each factor's random effects.
        The intercept's are `r[<factor>][<j>]`, a slope's are `r[<x>|<factor>][<j>]`.
        `<j>` is a group's code in the table."""
        local = {}
        for factor in self.factors:
            slopes = [f'{slope}|{factor}' for slope in self.slopes(factor)]
            effects = [factor, *slopes]  # the intercept first
            groups = range(len(self.levels[factor]))
            names = []
            for effect in effects:
                names += [f'r[{effect}][{j}]' for j in groups]
            local[factor] = tuple(names)
        return local

    def slopes(self, factor: str) -> tuple[str, ...]:
        """Returns the coded columns with a random slope on `factor`, in `sd` order."""
        suffix = f'|{factor}]'
        slopes = []
        for name in self.parameters:
            if name.startswith('sd[') and name.endswith(suffix):
                slope = name.removeprefix('sd[').removesuffix(suffix)
                slopes.append(slope)
        return tuple(slopes)


@dataclass(frozen=True)
class Prior:
    distribution: str  # brms's name: normal, student_t (a half-t on sd and sigma), lkj
    parameters: tuple[float, ...]


@dataclass(frozen=True)
class Scale:
    mean: float
    sd: float  # the sample standard deviation, as R's `scale` computes it


class Refused(Exception):
    """The contract does not cover the row. `reason` says why."""

    def __init__(self, id: str, reason: str) -> None:
        super().__init__(f'{id}: {reason}')
        self.reason = reason


def _selectSeenRows(table: pd.DataFrame, regime: Regime, fold: int) -> pd.DataFrame:
    """Returns the rows a fit on `fold` sees: all in `full`, those outside the fold in a split."""
    if regime == 'full':
        return table
    return table[table[regime] != fold]


# =====================================================================================
# the builder
# =====================================================================================
# the pipeline behind `Problem.build`, one step per rule of the contract
Coded = dict[str, dict[str, pd.Series]]  # the coded columns of each covariate or interaction


class _Builder:
    # the family rule: the response type sets brms's family and link
    FAMILY = {
        'continuous': ('gaussian', 'identity'),
        'binary': ('bernoulli', 'logit'),
        'count': ('poisson', 'log'),
        'binomial': ('binomial', 'logit'),
        'ordinal': ('cumulative', 'logit'),
    }
    CENSORED = ('cox', 'weibull')
    # the prior on the standardized scale, one per brms class
    PRIOR = {
        'Intercept': Prior('normal', (0, 2.5)),
        'b': Prior('normal', (0, 2.5)),
        'sd': Prior('student_t', (3, 0, 2.5)),
        'cor': Prior('lkj', (1,)),
        'sigma': Prior('student_t', (3, 0, 2.5)),
    }
    FOLDS = 5  # per split regime, or G in `groups` if fewer

    def __init__(self, row: Row, table: pd.DataFrame) -> None:
        self.row = row
        self.id = row.id
        self._refuseUncovered()
        composed = withComposites(table, row.grouping_factors)
        self.table = self._dropIncomplete(composed)
        if self.table.empty:  # nlme Phenobarb: doses and responses on different rows
            raise Refused(self.id, 'no row has every model value')
        self.dropped_share = (len(table) - len(self.table)) / len(table)

    def build(self) -> Problem:
        kinds = self._typeCovariates()
        coded = self._codeTerms(kinds)
        design = self._assembleDesign(coded)
        factors = {factor: self._codeFactor(factor) for factor in self.row.grouping_factors}
        regimes = self._dealRegimes(factors)
        columns = design | self._codeResponse() | factors | regimes
        table = pd.DataFrame(columns).reset_index(drop=True)
        correlations = self._listCorrelations(coded)
        family, link = self.FAMILY[self.row.response_type]
        return Problem(
            id=self.id,
            table=table,
            design=tuple(design),
            response=self.row.response,
            factors=self.row.grouping_factors,
            levels=self._listLevels(kinds),
            scales=self._measureFolds(table, kinds),
            dropped_share=self.dropped_share,
            trials=self.row.trials or None,
            family=family,
            link=link,
            prior=self._assignPrior(design, correlations),
            parameters=self._nameParameters(design, coded, correlations),
            correlations=correlations,
            contract=CONTRACT,
        )

    # -------------------------------------------------------------------------------------
    # rows -> coding -> splits -> scales -> model
    # -------------------------------------------------------------------------------------

    def _refuseUncovered(self) -> None:
        """Refuses a categorical response and a censored model."""
        if self.row.response_type == 'categorical':
            raise Refused(self.id, 'a categorical response is outside suite 1.1 (ADR 0001)')
        if self.row.family in self.CENSORED:
            reason = f'family {self.row.family} is a censored model, outside suite 1.1 (ADR 0001)'
            raise Refused(self.id, reason)

    def _dropIncomplete(self, table: pd.DataFrame) -> pd.DataFrame:
        """Drops the rows that miss a model value."""
        model = [self.row.response, *self.row.covariates]
        for factor in self.row.grouping_factors:
            model += parts(factor)  # a composite is missing where a part is
        if self.row.trials:
            model.append(self.row.trials)
        return table.dropna(subset=model)

    def _typeCovariates(self) -> dict[str, str]:
        """Returns each covariate's kind, by the typing rule."""
        kinds = {}
        for column in self.row.covariates:
            declared = self.row.types.get(column, '')
            kinds[column], _ = columnType(self.table[column], declared)
        return kinds

    def _codeTerms(self, kinds: dict[str, str]) -> Coded:
        """Returns the coded columns of each covariate, then of each interaction."""
        coded = {}
        for covariate, kind in kinds.items():
            coded[covariate] = self._codeCovariate(covariate, kind)
        for term in self.row.interactions:
            coded[term] = self._codeInteraction(term, coded)
        return coded

    def _codeCovariate(self, column: str, kind: str) -> dict[str, pd.Series]:
        """A continuous covariate stays raw.
        A binary one becomes 0/1.
        Any other becomes treatment contrasts `<column>[<level>]`.
        The first loaded level is the reference."""
        values = self.table[column]
        if kind == 'continuous':
            return {column: values.astype(float)}
        loaded = self._orderLevels(values)
        if kind == 'binary':
            return {column: (values != loaded[0]).astype(float)}
        contrasts = {}
        for level in loaded[1:]:
            contrasts[f'{column}[{level}]'] = (values == level).astype(float)
        return contrasts

    @staticmethod
    def _codeInteraction(term: str, coded: Coded) -> dict[str, pd.Series]:
        """Returns the products of the parts' coded columns, named `<a>:<b>`."""
        first, *rest = parts(term)
        columns = coded[first]
        for part in rest:
            products = {}
            for name, column in columns.items():
                for part_name, part_column in coded[part].items():
                    products[f'{name}:{part_name}'] = column * part_column
            columns = products
        return columns

    def _assembleDesign(self, coded: Coded) -> dict[str, pd.Series]:
        """Returns `Intercept`, then the coded columns in the row's order."""
        design = {'Intercept': pd.Series(1.0, index=self.table.index)}
        for columns in coded.values():
            design.update(columns)
        return design

    def _codeFactor(self, column: str) -> pd.Series:
        """Returns the column's 0-based codes, in the loaded level order."""
        values = self.table[column]
        levels = self._orderLevels(values)
        codes = pd.Categorical(values, categories=levels).codes
        return pd.Series(codes, index=self.table.index)

    def _codeResponse(self) -> dict[str, pd.Series]:
        """Codes the response by its type. A binomial response comes with its trials."""
        values = self.table[self.row.response]  # continuous, count and binomial: as loaded
        if self.row.response_type == 'binary':  # 0/1, with the first loaded level as 0
            first = self._orderLevels(values)[0]
            values = (values != first).astype(int)
        if self.row.response_type == 'ordinal':  # 1-based, in the loaded level order
            values = self._codeFactor(self.row.response) + 1
        response = {self.row.response: values}
        if self.row.trials:
            response[self.row.trials] = self.table[self.row.trials]
        return response

    def _listLevels(self, kinds: dict[str, str]) -> dict[str, tuple]:
        """Returns the loaded level order of each recoded column."""
        recoded = [column for column, kind in kinds.items() if kind != 'continuous']
        if self.row.response_type in ('binary', 'ordinal'):
            recoded.append(self.row.response)
        recoded += self.row.grouping_factors
        return {column: self._orderLevels(self.table[column]) for column in recoded}

    def _dealRegimes(self, factors: dict[str, pd.Series]) -> dict[str, pd.Series]:
        """Deals the regimes `rows` and `groups` into folds, seeded by the problem id."""
        digest = hashlib.sha256(self.id.encode()).digest()
        seed = int.from_bytes(digest[:8], 'big')
        rng = np.random.default_rng(seed)
        regimes = {'rows': self._dealRows(rng, factors)}
        first = factors[self.row.grouping_factors[0]]
        groups = first.max() + 1
        if groups > 2:  # holding out one of two groups would leave just one
            regimes['groups'] = self._dealGroups(rng, first)
        return regimes

    def _dealRows(self, rng: np.random.Generator, factors: dict[str, pd.Series]) -> pd.Series:
        """Returns each row's fold, the rows dealt into FOLDS folds in seeded order.
        The first row of every group of every factor stays in no fold, as -1."""
        n = len(self.table)
        order = self._drawOrder(rng, n)  # (n,) row positions
        spare = np.ones(n, dtype=bool)  # (n,) in seeded order
        for codes in factors.values():
            ordered = pd.Series(codes.to_numpy()[order])  # (n,) in seeded order
            spare &= ordered.duplicated().to_numpy()  # not the group's first row
        dealt = order[spare]  # the spare rows' positions, in seeded order
        row_folds = np.full(n, -1, dtype=np.int8)  # (n,)
        row_folds[dealt] = np.arange(len(dealt)) % self.FOLDS
        return pd.Series(row_folds, index=self.table.index)

    def _dealGroups(self, rng: np.random.Generator, codes: pd.Series) -> pd.Series:
        """Returns each row's fold.
        Its group is dealt whole into min(FOLDS, G) folds in seeded order."""
        groups = codes.max() + 1
        folds = min(self.FOLDS, groups)
        order = self._drawOrder(rng, groups)  # (m,) group codes
        group_folds = np.empty(groups, dtype=np.int8)  # (m,)
        group_folds[order] = np.arange(groups) % folds
        return pd.Series(group_folds[codes.to_numpy()], index=self.table.index)  # (n,)

    @staticmethod
    def _drawOrder(rng: np.random.Generator, n: int) -> np.ndarray:
        """Returns a seeded permutation.
        numpy keeps uniform draws stable across versions, but not shuffles."""
        return np.argsort(rng.random(n), kind='stable')  # (n,)

    def _measureFolds(
        self,
        table: pd.DataFrame,
        kinds: dict[str, str],
    ) -> dict[Regime, tuple[dict[str, Scale], ...]]:
        """Returns each fold's scales over the rows its fit sees."""
        columns = [column for column, kind in kinds.items() if kind == 'continuous']
        if self.row.response_type == 'continuous':
            columns.append(self.row.response)
        splits = [regime for regime in ('rows', 'groups') if regime in table]
        scales = {'full': (self._measureFold(table[columns]),)}
        for regime in splits:
            folds = table[regime].max() + 1  # dealt from fold 0
            fold_scales = []
            for fold in range(folds):
                seen = _selectSeenRows(table, regime, fold)
                fold_scales.append(self._measureFold(seen[columns]))
            scales[regime] = tuple(fold_scales)
        return scales

    @staticmethod
    def _measureFold(values: pd.DataFrame) -> dict[str, Scale]:
        scales = {}
        for column in values:
            mean = float(values[column].mean())
            sd = float(values[column].std())
            scales[column] = Scale(mean, sd)
        return scales

    def _listCorrelations(self, coded: Coded) -> dict[str, tuple[str, ...]]:
        """Returns the elements of each `cor[<factor>]`.
        They are `Intercept`, then the correlated slopes."""
        correlations = {}
        for term in self.row.random_slopes:
            if term.correlated:
                elements = correlations.get(term.factor, ('Intercept',))
                correlations[term.factor] = elements + tuple(coded[term.covariate])
        return correlations

    def _assignPrior(
        self, design: dict[str, pd.Series], correlations: dict[str, tuple[str, ...]]
    ) -> dict[str, Prior]:
        """Returns the prior of each class the problem has."""
        classes = []  # brms refuses a prior on a class the model lacks
        # an ordinal model has thresholds instead, on brms's default prior
        if self.row.response_type != 'ordinal':
            classes.append('Intercept')
        if len(design) > 1:
            classes.append('b')
        classes.append('sd')
        if correlations:
            classes.append('cor')
        if self.row.response_type == 'continuous':
            classes.append('sigma')
        return {name: self.PRIOR[name] for name in classes}

    def _nameParameters(
        self,
        design: dict[str, pd.Series],
        coded: Coded,
        correlations: dict[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        """Returns the global parameter names in brms's block order."""
        names = list(design)
        if self.row.response_type == 'ordinal':  # the thresholds replace `Intercept`
            levels = self._orderLevels(self.table[self.row.response])
            thresholds = [f'Intercept[{k}]' for k in range(1, len(levels))]
            names = thresholds + names[1:]
        for factor in self.row.grouping_factors:
            names += self._nameRandomEffects(factor, coded)
            if factor in correlations:
                names.append(f'cor[{factor}]')
        if self.row.response_type == 'continuous':
            names.append('sigma')
        return tuple(names)

    def _nameRandomEffects(self, factor: str, coded: Coded) -> list[str]:
        names = [f'sd[{factor}]']
        for term in self.row.random_slopes:
            if term.factor == factor:
                names += [f'sd[{slope}|{factor}]' for slope in coded[term.covariate]]
        return names

    @staticmethod
    def _orderLevels(values: pd.Series) -> tuple:
        """Returns the loaded level order."""
        if isinstance(values.dtype, pd.CategoricalDtype):
            return tuple(values.cat.remove_unused_categories().cat.categories)
        # a plain column declared categorical
        return tuple(sorted(values.dropna().unique()))


# =====================================================================================
# the rules shared with the survey
# =====================================================================================
# the survey uses these rules too, so its design widths match the builds
MAX_INTEGER_LEVELS = 10


def columnType(values: pd.Series, declared: str) -> tuple[str, int | str]:
    """Returns a column's kind and its level count k, blank if continuous.
    The first rule that matches wins."""
    distinct = values.dropna().nunique()
    dtype = values.dtype
    categorical = isinstance(dtype, pd.CategoricalDtype)
    if categorical and dtype.ordered:
        return 'ordered', distinct
    if distinct == 2:
        return 'binary', 2
    if declared == 'continuous':
        return 'continuous', ''
    if categorical or pd.api.types.is_string_dtype(dtype):
        return 'categorical', distinct
    if pd.api.types.is_integer_dtype(dtype) and distinct <= MAX_INTEGER_LEVELS:
        return 'categorical', distinct
    return 'continuous', ''


def withComposites(table: pd.DataFrame, factors: tuple[str, ...]) -> pd.DataFrame:
    """Adds each composite factor `a:b` as a column that joins its parts' levels."""
    composites = {}
    for factor in factors:
        columns = parts(factor)
        if len(columns) > 1:
            composite = table[columns[0]].astype(str)
            for part in columns[1:]:
                composite = composite + ':' + table[part].astype(str)  # missing stays missing
            composites[factor] = composite
    return table.assign(**composites)
