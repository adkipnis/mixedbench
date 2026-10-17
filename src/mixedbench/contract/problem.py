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
4. Scaled per regime: the table stays in raw units.
   Each regime records the scales of the rows its fit sees.
5. Parameter names are based on brms and are in brms's block order.

pipeline:
---------
a typed registry row and its loaded table
-> refused if outside the contract             _refuseUncovered
-> composites added, incomplete rows dropped   withComposites, _keptRows
-> the coded design, response and factors      _kinds, _coded, _design, _codes, _response
-> the regimes `rows` and `groups`             _splits
-> each regime's scales                        _scales
-> the family, prior and parameter names       _prior, _parameters
-> the problem                                 problem
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
    # the column roles in `table`; the factors hold 0-based codes
    design: tuple[str, ...]  # `Intercept` first
    response: str
    factors: tuple[str, ...]
    levels: dict[str, tuple]  # each recoded column's levels, in code order
    # per regime, the mean and SD of each continuous column over the rows its fit sees
    scales: dict[Regime, dict[str, Scale]]
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
        return _Builder(row, table).problem()

    def standardised(self, regime: Regime = 'full') -> pd.DataFrame:
        """Returns the standardised model columns of the rows a fit in `regime` sees.
        Continuous columns are z-scored with the regime's scales.
        An interaction is the product of its standardised parts,
        see Aiken & West (1991) and Gelman (2008)."""
        columns = [*self.design, self.response]
        if self.trials:
            columns.append(self.trials)
        columns += self.factors
        rows = _seenRows(self.table, regime)
        table = rows[columns].copy()
        for column, scale in self.scales[regime].items():
            table[column] = (table[column] - scale.mean) / scale.sd
        for column, operands in self._interactions().items():
            table[column] = table[list(operands)].prod(axis=1)
        return table

    def _interactions(self) -> dict[str, tuple[str, ...]]:
        """Returns each interaction column with its parts, in order."""
        # a covariate's coded columns: a continuous one has a scale, a binary one has levels,
        # any other is a contrast
        contrasts = []
        for column, levels in self.levels.items():
            contrasts += [f'{column}[{level}]' for level in levels[1:]]
        covariate_columns = [*self.scales['full'], *self.levels, *contrasts]
        design = self.design[1:]  # without `Intercept`
        coded = [column for column in design if column in covariate_columns]
        # every other design column is an interaction
        interactions = {}
        for column in design:
            if column not in coded:
                interactions[column] = self._parts(column, coded)
        return interactions

    @staticmethod
    def _parts(column: str, coded: list[str]) -> tuple[str, ...]:
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


def _seenRows(table: pd.DataFrame, regime: Regime) -> pd.DataFrame:
    """Returns the rows a fit in `regime` sees: all in `full`, the `seen` ones in a split."""
    if regime == 'full':
        return table
    return table[table[regime] == 'seen']


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
    # the prior on the standardised scale, one per brms class
    PRIOR = {
        'Intercept': Prior('normal', (0, 2.5)),
        'b': Prior('normal', (0, 2.5)),
        'sd': Prior('student_t', (3, 0, 2.5)),
        'cor': Prior('lkj', (1,)),
        'sigma': Prior('student_t', (3, 0, 2.5)),
    }
    # each regime is a column of `seen` and `held`
    REGIME = pd.CategoricalDtype(['seen', 'held'])

    def __init__(self, row: Row, table: pd.DataFrame) -> None:
        self.row = row
        self.id = row.id
        self._refuseUncovered()
        composed = withComposites(table, row.grouping_factors)
        self.table = self._keptRows(composed)
        if self.table.empty:  # nlme Phenobarb: doses and responses on different rows
            raise Refused(self.id, 'no row has every model value')
        self.dropped_share = (len(table) - len(self.table)) / len(table)

    def problem(self) -> Problem:
        kinds = self._kinds()
        coded = self._coded(kinds)
        design = self._design(coded)
        factors = {factor: self._codes(factor) for factor in self.row.grouping_factors}
        regimes = self._splits(factors)
        columns = design | self._response() | factors | regimes
        table = pd.DataFrame(columns).reset_index(drop=True)
        correlations = self._correlations(coded)
        family, link = self.FAMILY[self.row.response_type]
        return Problem(
            id=self.id,
            table=table,
            design=tuple(design),
            response=self.row.response,
            factors=self.row.grouping_factors,
            levels=self._levels(kinds),
            scales=self._scales(table, kinds),
            dropped_share=self.dropped_share,
            trials=self.row.trials or None,
            family=family,
            link=link,
            prior=self._prior(design, correlations),
            parameters=self._parameters(design, coded, correlations),
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

    def _keptRows(self, table: pd.DataFrame) -> pd.DataFrame:
        """Drops the rows that miss a model value."""
        model = [self.row.response, *self.row.covariates]
        for factor in self.row.grouping_factors:
            model += parts(factor)  # a composite is missing where a part is
        if self.row.trials:
            model.append(self.row.trials)
        return table.dropna(subset=model)

    def _kinds(self) -> dict[str, str]:
        """Returns each covariate's kind, by the typing rule."""
        kinds = {}
        for column in self.row.covariates:
            declared = self.row.types.get(column, '')
            kinds[column], _ = columnType(self.table[column], declared)
        return kinds

    def _coded(self, kinds: dict[str, str]) -> Coded:
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
        loaded = self._levelOrder(values)
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

    def _design(self, coded: Coded) -> dict[str, pd.Series]:
        """Returns `Intercept`, then the coded columns in the row's order."""
        design = {'Intercept': pd.Series(1.0, index=self.table.index)}
        for columns in coded.values():
            design.update(columns)
        return design

    def _codes(self, column: str) -> pd.Series:
        """Returns the column's 0-based codes, in the loaded level order."""
        values = self.table[column]
        levels = self._levelOrder(values)
        codes = pd.Categorical(values, categories=levels).codes
        return pd.Series(codes, index=self.table.index)

    def _response(self) -> dict[str, pd.Series]:
        """Codes the response by its type. A binomial response comes with its trials."""
        values = self.table[self.row.response]  # continuous, count and binomial: as loaded
        if self.row.response_type == 'binary':  # 0/1, with the first loaded level as 0
            first = self._levelOrder(values)[0]
            values = (values != first).astype(int)
        if self.row.response_type == 'ordinal':  # 1-based, in the loaded level order
            values = self._codes(self.row.response) + 1
        response = {self.row.response: values}
        if self.row.trials:
            response[self.row.trials] = self.table[self.row.trials]
        return response

    def _levels(self, kinds: dict[str, str]) -> dict[str, tuple]:
        """Returns the loaded level order of each recoded column."""
        recoded = [column for column, kind in kinds.items() if kind != 'continuous']
        if self.row.response_type in ('binary', 'ordinal'):
            recoded.append(self.row.response)
        recoded += self.row.grouping_factors
        return {column: self._levelOrder(self.table[column]) for column in recoded}

    def _splits(self, factors: dict[str, pd.Series]) -> dict[str, pd.Series]:
        """Draws the regimes `rows` and `groups`, seeded by the problem id."""
        digest = hashlib.sha256(self.id.encode()).digest()
        seed = int.from_bytes(digest[:8], 'big')
        rng = np.random.default_rng(seed)
        held = self._heldRows(rng, factors)
        regimes = {'rows': self._regime(held)}
        first = factors[self.row.grouping_factors[0]]
        groups = first.max() + 1
        if groups > 2:  # holding out one of two groups would leave just one
            held = self._heldGroups(rng, first)
            regimes['groups'] = self._regime(held)
        return regimes

    def _heldRows(self, rng: np.random.Generator, factors: dict[str, pd.Series]) -> np.ndarray:
        """Holds out 10% of the rows, rounded.
        Every group of every factor keeps at least one row seen."""
        n = len(self.table)
        order = self._seededOrder(rng, n)  # (n,) row positions
        spare = np.ones(n, dtype=bool)  # (n,) in seeded order
        for codes in factors.values():
            ordered = pd.Series(codes.to_numpy()[order])  # (n,) in seeded order
            spare &= ordered.duplicated().to_numpy()  # not the group's first row
        count = (n + 5) // 10  # the nearest whole number to 10%
        held_rows = order[spare][:count]
        held = np.zeros(n, dtype=bool)  # (n,)
        held[held_rows] = True
        return held

    def _heldGroups(self, rng: np.random.Generator, codes: pd.Series) -> np.ndarray:
        """Holds out 10% of the groups, rounded.
        It holds at least one and leaves at least two."""
        groups = codes.max() + 1
        tenth = (groups + 5) // 10  # the nearest whole number to 10%
        count = min(max(1, tenth), groups - 2)
        held = self._seededOrder(rng, groups)[:count]
        return np.isin(codes.to_numpy(), held)  # (n,)

    @staticmethod
    def _seededOrder(rng: np.random.Generator, n: int) -> np.ndarray:
        """Returns a seeded permutation.
        numpy keeps uniform draws stable across versions, but not shuffles."""
        return np.argsort(rng.random(n), kind='stable')  # (n,)

    def _regime(self, held: np.ndarray) -> pd.Series:
        regime = pd.Categorical.from_codes(held.astype(int), dtype=self.REGIME)
        return pd.Series(regime, index=self.table.index)

    def _scales(
        self,
        table: pd.DataFrame,
        kinds: dict[str, str],
    ) -> dict[Regime, dict[str, Scale]]:
        """Returns each regime's scales over the rows its fit sees."""
        columns = [column for column, kind in kinds.items() if kind == 'continuous']
        if self.row.response_type == 'continuous':
            columns.append(self.row.response)
        splits = [regime for regime in ('rows', 'groups') if regime in table]
        scales = {}
        for regime in ['full', *splits]:
            values = _seenRows(table, regime)[columns]
            scales[regime] = {}
            for column in columns:
                mean = float(values[column].mean())
                sd = float(values[column].std())
                scales[regime][column] = Scale(mean, sd)
        return scales

    def _correlations(self, coded: Coded) -> dict[str, tuple[str, ...]]:
        """Returns the elements of each `cor[<factor>]`.
        They are `Intercept`, then the correlated slopes."""
        correlations = {}
        for term in self.row.random_slopes:
            if term.correlated:
                elements = correlations.get(term.factor, ('Intercept',))
                correlations[term.factor] = elements + tuple(coded[term.covariate])
        return correlations

    def _prior(
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

    def _parameters(
        self,
        design: dict[str, pd.Series],
        coded: Coded,
        correlations: dict[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        """Returns the global parameter names in brms's block order."""
        names = list(design)
        if self.row.response_type == 'ordinal':  # the thresholds replace `Intercept`
            levels = self._levelOrder(self.table[self.row.response])
            thresholds = [f'Intercept[{k}]' for k in range(1, len(levels))]
            names = thresholds + names[1:]
        for factor in self.row.grouping_factors:
            names += self._randomEffects(factor, coded)
            if factor in correlations:
                names.append(f'cor[{factor}]')
        if self.row.response_type == 'continuous':
            names.append('sigma')
        return tuple(names)

    def _randomEffects(self, factor: str, coded: Coded) -> list[str]:
        names = [f'sd[{factor}]']
        for term in self.row.random_slopes:
            if term.factor == factor:
                names += [f'sd[{slope}|{factor}]' for slope in coded[term.covariate]]
        return names

    @staticmethod
    def _levelOrder(values: pd.Series) -> tuple:
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
    """Returns a column's kind and its level count K, blank if continuous.
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
