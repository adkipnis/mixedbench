"""`Problem`: one registry row under the contract (ADR 0001). `Problem.build` takes the typed
row and the loader's typed table (the row's `types` passed to `load`) and returns the coded
design, the response, the family, the prior and the parameter names; a problem is a pure
function of the pins, the row and the contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import pandas as pd
from mixedbench.registry.row import Row, parts

# =====================================================================================
# the typing rule, shared with the survey's measures so that d_doc is the design's width
# =====================================================================================
# A string or integer column with at most this many distinct values is a categorical (spec #14).
MAX_INTEGER_LEVELS = 10


def columnType(values: pd.Series, declared: str) -> tuple[str, int | str]:
    """The one typing rule, in order: ordered categorical; exactly two distinct values is
    binary; a declared or typed categorical, a string, or an integer with few distinct values
    is categorical with K levels; otherwise continuous. K is blank for a continuous column."""
    distinct = values.dropna().nunique()
    dtype = values.dtype
    if isinstance(dtype, pd.CategoricalDtype) and dtype.ordered:
        return 'ordered', distinct
    if distinct == 2:
        return 'binary', 2
    if declared == 'continuous':
        return 'continuous', ''
    if isinstance(dtype, pd.CategoricalDtype) or pd.api.types.is_string_dtype(dtype):
        return 'categorical', distinct
    if pd.api.types.is_integer_dtype(dtype) and distinct <= MAX_INTEGER_LEVELS:
        return 'categorical', distinct
    return 'continuous', ''


def withComposites(table: pd.DataFrame, factors: tuple[str, ...]) -> pd.DataFrame:
    """A grouping factor `a:b` names no column (lme4's `(1|a:b)`, the whole plots of a
    split-plot): the combination of its parts is added under that name, one level per pair of
    levels present; a row missing a part has no level (the ARM radon survey's rows without a
    county). Built here once, so the merge's checks and the measures see a plain column."""
    composites = {}
    for factor in factors:
        columns = parts(factor)
        if len(columns) > 1:
            composite = table[columns[0]].astype(str)
            for part in columns[1:]:
                composite = composite + ':' + table[part].astype(str)  # missing stays missing
            composites[factor] = composite
    return table.assign(**composites)


def levelOrder(values: pd.Series) -> tuple:
    """The loaded level order: a categorical's categories present in the column, else the
    sorted distinct values (what the loader gives a plain column declared categorical)."""
    if isinstance(values.dtype, pd.CategoricalDtype):
        return tuple(values.cat.remove_unused_categories().cat.categories)
    return tuple(sorted(values.dropna().unique()))


# =====================================================================================
# the family rule (ADR 0001): by response type, brms's family and link
# =====================================================================================
FAMILY = {
    'continuous': ('gaussian', 'identity'),
    'binary': ('bernoulli', 'logit'),
    'count': ('poisson', 'log'),
    'binomial': ('binomial', 'logit'),
    'ordinal': ('cumulative', 'logit'),
}
CENSORED = ('cox', 'weibull')


class Refused(Exception):
    """The contract states no problem for the row: the message names the row, `reason` says
    why."""

    def __init__(self, id: str, reason: str) -> None:
        super().__init__(f'{id}: {reason}')
        self.reason = reason


# =====================================================================================
# the prior (ADR 0001): on the standardised scale, per brms class
# =====================================================================================
@dataclass(frozen=True)
class Prior:
    distribution: str  # brms's name: normal, student_t (half on a scale), lkj
    parameters: tuple[float, ...]


PRIOR = {
    'Intercept': Prior('normal', (0, 2.5)),
    'b': Prior('normal', (0, 2.5)),
    'sd': Prior('student_t', (3, 0, 2.5)),
    'cor': Prior('lkj', (1,)),
    'sigma': Prior('student_t', (3, 0, 2.5)),
}


# =====================================================================================
# the splits and scales (ADR 0001): two regimes, each a column of `seen` and `held`
# =====================================================================================
REGIME = pd.CategoricalDtype(['seen', 'held'])


@dataclass(frozen=True)
class Scale:
    mean: float
    sd: float  # the sample standard deviation, as R's `scale`


# =====================================================================================
# the problem
# =====================================================================================
CONTRACT = int(version('mixedbench').partition('.')[0])  # the contract version (ADR 0001)


@dataclass(frozen=True)
class Problem:
    id: str  # <source>/<object>/<model_index>
    table: pd.DataFrame  # the coded columns in raw units; one row per kept row
    # column roles in `table`: the design columns in order, `Intercept` first; the response;
    # the grouping factors as 0-based codes
    design: tuple[str, ...]
    response: str
    factors: tuple[str, ...]
    levels: dict[str, tuple]  # per recoded column, the level of each code (binary: 0 then 1)
    # per regime (`full`, `rows`, `groups` where the problem has it), the moments of each
    # continuous covariate and a continuous response over the rows a fit sees
    scales: dict[str, dict[str, Scale]]
    dropped_share: float  # of the loaded rows, those missing a model value
    trials: str | None  # the trials column of a binomial response
    family: str  # brms's names, by the family rule of ADR 0001
    link: str
    prior: dict[str, Prior]  # per brms class the problem has
    parameters: tuple[str, ...]  # the global parameters by the naming rule, in order
    correlations: dict[str, tuple[str, ...]]  # per `cor[<factor>]` block, its elements in order
    contract: int  # the version of the contract the problem was built under

    @classmethod
    def build(cls, row: Row, table: pd.DataFrame) -> Problem:
        """Raises `Refused` where the contract does not cover the row."""
        return Builder(row, table).problem()


# -------------------------------------------------------------------------------------
# pipeline: rows -> covariates -> interactions -> response -> factors -> the problem
# -------------------------------------------------------------------------------------
Coded = dict[str, dict[str, pd.Series]]  # per covariate or interaction, its coded columns


class Builder:
    def __init__(self, row: Row, table: pd.DataFrame) -> None:
        self.row = row
        self.id = row.id
        self.refuseUncovered()
        self.table = self.keptRows(withComposites(table, row.grouping_factors))
        if self.table.empty:  # nlme Phenobarb: doses and responses on different rows
            raise Refused(self.id, 'no row has every model value')
        self.dropped_share = (len(table) - len(self.table)) / len(table)

    def refuseUncovered(self) -> None:
        """A categorical response and a censored model are outside suite 1.1 (ADR 0001); every
        other `family` takes the family rule."""
        if self.row.response_type == 'categorical':
            raise Refused(self.id, 'a categorical response is outside suite 1.1 (ADR 0001)')
        if self.row.family in CENSORED:
            reason = f'family {self.row.family} is a censored model, outside suite 1.1 (ADR 0001)'
            raise Refused(self.id, reason)

    def keptRows(self, table: pd.DataFrame) -> pd.DataFrame:
        """A row with a missing value in any model column is dropped (ADR 0001); a composite
        factor is missing where a part is."""
        model = [self.row.response, *self.row.covariates]
        for factor in self.row.grouping_factors:
            model += parts(factor)
        if self.row.trials:
            model.append(self.row.trials)
        return table.dropna(subset=model)

    def problem(self) -> Problem:
        kinds = self.kinds()
        coded = self.coded(kinds)
        design = self.design(coded)
        factors = {factor: self.codeFactor(factor) for factor in self.row.grouping_factors}
        regimes = self.splits(factors)
        table = pd.DataFrame(design | self.response() | factors | regimes).reset_index(drop=True)
        correlations = self.correlations(coded)
        family, link = FAMILY[self.row.response_type]
        return Problem(
            id=self.id,
            table=table,
            design=tuple(design),
            response=self.row.response,
            factors=self.row.grouping_factors,
            levels=self.levels(kinds),
            scales=self.scales(table, kinds),
            dropped_share=self.dropped_share,
            trials=self.row.trials or None,
            family=family,
            link=link,
            prior=self.prior(design, correlations),
            parameters=self.parameters(design, coded, correlations),
            correlations=correlations,
            contract=CONTRACT,
        )

    def kinds(self) -> dict[str, str]:
        """Per covariate, its kind by the typing rule."""
        kinds = {}
        for column in self.row.covariates:
            kinds[column], _ = columnType(self.table[column], self.row.types.get(column, ''))
        return kinds

    def coded(self, kinds: dict[str, str]) -> Coded:
        """Per covariate, then per interaction, its coded columns."""
        coded = {}
        for covariate, kind in kinds.items():
            coded[covariate] = self.codeCovariate(covariate, kind)
        for term in self.row.interactions:
            coded[term] = self.codeInteraction(term, coded)
        return coded

    def codeCovariate(self, column: str, kind: str) -> dict[str, pd.Series]:
        """Continuous raw; binary 0/1 with the first loaded level 0; a categorical or ordered
        factor as K − 1 treatment contrasts against the first level, `<column>[<level>]`."""
        values = self.table[column]
        if kind == 'continuous':
            return {column: values.astype(float)}
        loaded = levelOrder(values)
        if kind == 'binary':
            return {column: (values != loaded[0]).astype(float)}
        return {f'{column}[{level}]': (values == level).astype(float) for level in loaded[1:]}

    @staticmethod
    def codeInteraction(term: str, coded: Coded) -> dict[str, pd.Series]:
        """The products of the coded columns of its parts, `<a>:<b>` per pair in order."""
        columns = {'': 1.0}
        for part in parts(term):
            products = {}
            for name, column in columns.items():
                for partName, partColumn in coded[part].items():
                    products[f'{name}:{partName}'.removeprefix(':')] = column * partColumn
            columns = products
        return columns

    def design(self, coded: Coded) -> dict[str, pd.Series]:
        """`Intercept` first, then the coded columns in the row's order."""
        design = {'Intercept': pd.Series(1.0, index=self.table.index)}
        for columns in coded.values():
            design.update(columns)
        return design

    def response(self) -> dict[str, pd.Series]:
        """By `response_type`: continuous, count and binomial successes as loaded, binary 0/1
        with the first loaded level 0, ordinal its 1-based index in the loaded level order; a
        binomial's trials beside it."""
        values = self.table[self.row.response]
        if self.row.response_type == 'binary':
            values = (values != levelOrder(values)[0]).astype(int)
        if self.row.response_type == 'ordinal':
            codes = pd.Categorical(values, categories=levelOrder(values)).codes
            values = pd.Series(codes + 1, index=self.table.index)
        response = {self.row.response: values}
        if self.row.trials:
            response[self.row.trials] = self.table[self.row.trials]
        return response

    def codeFactor(self, factor: str) -> pd.Series:
        values = self.table[factor]
        codes = pd.Categorical(values, categories=levelOrder(values)).codes
        return pd.Series(codes, index=self.table.index)

    def correlations(self, coded: Coded) -> dict[str, tuple[str, ...]]:
        """Per factor with a correlated slope, the elements of `cor[<factor>]`: `Intercept`,
        then the coded columns of its correlated slopes in order."""
        correlations = {}
        for term in self.row.random_slopes:
            if term.correlated:
                elements = correlations.get(term.factor, ('Intercept',))
                correlations[term.factor] = elements + tuple(coded[term.covariate])
        return correlations

    def levels(self, kinds: dict[str, str]) -> dict[str, tuple]:
        """The loaded level order of every recoded column: a covariate that is not continuous,
        a binary or ordinal response, a grouping factor."""
        recoded = [column for column, kind in kinds.items() if kind != 'continuous']
        if self.row.response_type in ('binary', 'ordinal'):
            recoded.append(self.row.response)
        recoded += self.row.grouping_factors
        return {column: levelOrder(self.table[column]) for column in recoded}

    def prior(
        self, design: dict[str, pd.Series], correlations: dict[str, tuple[str, ...]]
    ) -> dict[str, Prior]:
        """ADR 0001's prior over the classes the problem has (brms refuses one on an absent
        class): no `Intercept` on an ordinal model, whose thresholds take brms's default."""
        classes = []
        if self.row.response_type != 'ordinal':
            classes.append('Intercept')
        if len(design) > 1:
            classes.append('b')
        classes.append('sd')
        if correlations:
            classes.append('cor')
        if self.row.response_type == 'continuous':
            classes.append('sigma')
        return {name: PRIOR[name] for name in classes}

    def parameters(
        self,
        design: dict[str, pd.Series],
        coded: Coded,
        correlations: dict[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        """brms's block order: the fixed effects (an ordinal model's thresholds `Intercept[k]`
        in place of `Intercept`, brms's name without its `b_`), per factor `sd[<factor>]`, the
        slopes `sd[<x>|<factor>]` and `cor[<factor>]` where a slope is correlated, `sigma`."""
        names = list(design)
        if self.row.response_type == 'ordinal':
            thresholds = len(levelOrder(self.table[self.row.response])) - 1
            names = [f'Intercept[{k}]' for k in range(1, thresholds + 1)] + names[1:]
        for factor in self.row.grouping_factors:
            names += self.randomEffects(factor, coded)
            if factor in correlations:
                names.append(f'cor[{factor}]')
        if self.row.response_type == 'continuous':
            names.append('sigma')
        return tuple(names)

    def randomEffects(self, factor: str, coded: Coded) -> list[str]:
        names = [f'sd[{factor}]']
        for term in self.row.random_slopes:
            if term.factor == factor:
                names += [f'sd[{slope}|{factor}]' for slope in coded[term.covariate]]
        return names

    def splits(self, factors: dict[str, pd.Series]) -> dict[str, pd.Series]:
        """Seeded by the first 8 bytes of sha256 of the id; rows draw before groups. A first
        factor of two groups has no `groups` regime: holding one would leave one."""
        seed = int.from_bytes(hashlib.sha256(self.id.encode()).digest()[:8], 'big')
        rng = np.random.default_rng(seed)
        regimes = {'rows': self.regime(self.heldRows(rng, factors))}
        first = factors[self.row.grouping_factors[0]]
        if first.max() + 1 > 2:
            regimes['groups'] = self.regime(self.heldGroups(rng, first))
        return regimes

    def heldRows(self, rng: np.random.Generator, factors: dict[str, pd.Series]) -> np.ndarray:
        """Every group of every factor keeps seen the row it shows first in the seeded order;
        of the other rows, the first nearest whole number to 10% of all rows are held."""
        n = len(self.table)
        order = self.seededOrder(rng, n)  # (n,) row positions
        spare = np.ones(n, dtype=bool)  # (n,) in seeded order
        for codes in factors.values():
            spare &= pd.Series(codes.to_numpy()[order]).duplicated().to_numpy()
        held = np.zeros(n, dtype=bool)  # (n,)
        held[order[spare][: (n + 5) // 10]] = True
        return held

    def heldGroups(self, rng: np.random.Generator, codes: pd.Series) -> np.ndarray:
        """The nearest whole number to 10% of the groups, at least one, at least two left."""
        groups = codes.max() + 1
        count = min(max(1, (groups + 5) // 10), groups - 2)
        held = self.seededOrder(rng, groups)[:count]
        return np.isin(codes.to_numpy(), held)  # (n,)

    @staticmethod
    def seededOrder(rng: np.random.Generator, n: int) -> np.ndarray:
        """An argsort of uniform draws, whose stream numpy keeps across versions (a shuffle's
        algorithm it does not promise)."""
        return np.argsort(rng.random(n), kind='stable')  # (n,)

    def regime(self, held: np.ndarray) -> pd.Series:
        regime = pd.Categorical.from_codes(held.astype(int), dtype=REGIME)
        return pd.Series(regime, index=self.table.index)

    def scales(self, table: pd.DataFrame, kinds: dict[str, str]) -> dict[str, dict[str, Scale]]:
        """The standardisation per regime on the rows a fit sees (ADR 0001, amended
        2026-10-09); the table stays in raw units."""
        columns = [column for column, kind in kinds.items() if kind == 'continuous']
        if self.row.response_type == 'continuous':
            columns.append(self.row.response)
        seen = {'full': pd.Series(True, index=table.index)}
        for regime in ('rows', 'groups'):
            if regime in table:
                seen[regime] = table[regime] == 'seen'
        scales = {}
        for regime, rows in seen.items():
            values = table.loc[rows, columns]
            scales[regime] = {
                c: Scale(float(values[c].mean()), float(values[c].std())) for c in columns
            }
        return scales
