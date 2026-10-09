"""`Problem`: one registry row under the contract (ADR 0001). `Problem.build` takes the typed
row and the loader's typed table (the row's `types` passed to `load`) and returns the coded
design, the response, the family, the prior and the parameter names; a problem is a pure
function of the pins, the row and the contract."""

from __future__ import annotations

from dataclasses import dataclass

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


def withComposites(df: pd.DataFrame, factors: tuple[str, ...]) -> pd.DataFrame:
    """A grouping factor `a:b` names no column (lme4's `(1|a:b)`, the whole plots of a
    split-plot): the combination of its parts is added under that name, one level per pair of
    levels present; a row missing a part has no level (the ARM radon survey's rows without a
    county). Built here once, so the merge's checks and the measures see a plain column."""
    composites = {}
    for factor in factors:
        columns = parts(factor)
        if len(columns) > 1:
            composite = df[columns[0]].astype(str)
            for part in columns[1:]:
                composite = composite + ':' + df[part].astype(str)  # missing stays missing
            composites[factor] = composite
    return df.assign(**composites)


def levels(values: pd.Series) -> tuple:
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


def refusal(row: Row) -> str | None:
    """Why the rule does not cover the row, or None: a categorical response and a censored
    model are outside suite 1.1 (ADR 0001); every other `family` takes the rule."""
    if row.response_type == 'categorical':
        return 'a categorical response is outside suite 1.1 (ADR 0001)'
    if row.family in CENSORED:
        return f'family {row.family} is a censored model, outside suite 1.1 (ADR 0001)'
    return None


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
# the problem
# =====================================================================================
@dataclass(frozen=True)
class Problem:
    id: str  # <source>/<object>/<model_index>
    row: Row
    table: pd.DataFrame  # the coded columns in raw units; one row per kept row
    # column roles in `table`: the design columns in order, `Intercept` first; the response;
    # the grouping factors as 0-based codes
    design: tuple[str, ...]
    response: str
    factors: tuple[str, ...]
    levels: dict[str, tuple]  # per recoded column, the level of each code (binary: 0 then 1)
    dropped_share: float  # of the loaded rows, those missing a model value
    trials: str | None  # the trials column of a binomial response
    family: str  # brms's names, by the family rule of ADR 0001
    link: str
    prior: dict[str, Prior]  # per brms class the problem has
    parameters: tuple[str, ...]  # the global parameters by the naming rule, in order
    correlations: dict[str, tuple[str, ...]]  # per `cor[<factor>]` block, its elements in order

    @classmethod
    def build(cls, row: Row, table: pd.DataFrame) -> Problem:
        refused = refusal(row)
        if refused is not None:
            raise ValueError(f'{row.source}/{row.object}/{row.model_index}: {refused}')
        return Builder(row, table).problem()


# -------------------------------------------------------------------------------------
# pipeline: rows -> covariates -> interactions -> response -> factors -> the problem
# -------------------------------------------------------------------------------------
class Builder:
    def __init__(self, row: Row, table: pd.DataFrame) -> None:
        self.row = row
        self.table = self.keptRows(withComposites(table, row.grouping_factors))
        self.dropped_share = (len(table) - len(self.table)) / len(table)
        self.coded: dict[str, dict[str, pd.Series]] = {}  # covariate -> its coded columns
        self.levels: dict[str, tuple] = {}
        self.correlations: dict[str, tuple[str, ...]] = {}

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
        for covariate in self.row.covariates:
            self.coded[covariate] = self.codeCovariate(covariate)
        for term in self.row.interactions:
            self.coded[term] = self.codeInteraction(term)
        design = {'Intercept': pd.Series(1.0, index=self.table.index)}
        for columns in self.coded.values():
            design.update(columns)
        response = {self.row.response: self.codeResponse()}
        if self.row.trials:
            response[self.row.trials] = self.table[self.row.trials]
        factors = {factor: self.codeFactor(factor) for factor in self.row.grouping_factors}
        family, link = FAMILY[self.row.response_type]
        return Problem(
            id=f'{self.row.source}/{self.row.object}/{self.row.model_index}',
            row=self.row,
            table=pd.DataFrame(design | response | factors).reset_index(drop=True),
            design=tuple(design),
            response=self.row.response,
            factors=self.row.grouping_factors,
            levels=self.levels,
            dropped_share=self.dropped_share,
            trials=self.row.trials or None,
            family=family,
            link=link,
            prior=self.prior(design),
            parameters=self.parameters(design),
            correlations=self.correlations,
        )

    def prior(self, design: dict[str, pd.Series]) -> dict[str, Prior]:
        """ADR 0001's prior over the classes the problem has (brms refuses one on an absent
        class): no `Intercept` on an ordinal model, whose thresholds take brms's default."""
        classes = []
        if self.row.response_type != 'ordinal':
            classes.append('Intercept')
        if len(design) > 1:
            classes.append('b')
        classes.append('sd')
        if any(term.correlated for term in self.row.random_slopes):
            classes.append('cor')
        if self.row.response_type == 'continuous':
            classes.append('sigma')
        return {name: PRIOR[name] for name in classes}

    def parameters(self, design: dict[str, pd.Series]) -> tuple[str, ...]:
        """brms's block order: the fixed effects (an ordinal model's thresholds `Intercept[k]`
        in place of `Intercept`, brms's name without its `b_`), per factor `sd[<factor>]`, the
        slopes `sd[<x>|<factor>]` and `cor[<factor>]` where a slope is correlated, `sigma`."""
        names = list(design)
        if self.row.response_type == 'ordinal':
            thresholds = len(self.levels[self.row.response]) - 1
            names = [f'Intercept[{k}]' for k in range(1, thresholds + 1)] + names[1:]
        for factor in self.row.grouping_factors:
            names += self.randomEffects(factor)
        if self.row.response_type == 'continuous':
            names.append('sigma')
        return tuple(names)

    def randomEffects(self, factor: str) -> list[str]:
        names = [f'sd[{factor}]']
        correlated = ['Intercept']
        for term in self.row.random_slopes:
            if term.factor != factor:
                continue
            slopes = list(self.coded[term.covariate])
            names += [f'sd[{slope}|{factor}]' for slope in slopes]
            if term.correlated:
                correlated += slopes
        if len(correlated) > 1:
            names.append(f'cor[{factor}]')
            self.correlations[factor] = tuple(correlated)
        return names

    def codeCovariate(self, column: str) -> dict[str, pd.Series]:
        """Continuous raw; binary 0/1 with the first loaded level 0; a categorical or ordered
        factor as K − 1 treatment contrasts against the first level, `<column>[<level>]`."""
        values = self.table[column]
        kind, _ = columnType(values, self.row.types.get(column, ''))
        if kind == 'continuous':
            return {column: values.astype(float)}
        loaded = self.levelsOf(column)
        if kind == 'binary':
            return {column: (values != loaded[0]).astype(float)}
        return {f'{column}[{level}]': (values == level).astype(float) for level in loaded[1:]}

    def codeResponse(self) -> pd.Series:
        """By `response_type`: continuous, count and binomial successes as loaded, binary 0/1
        with the first loaded level 0, ordinal its 1-based index in the loaded level order."""
        values = self.table[self.row.response]
        if self.row.response_type == 'binary':
            return (values != self.levelsOf(self.row.response)[0]).astype(int)
        if self.row.response_type == 'ordinal':
            codes = pd.Categorical(values, categories=self.levelsOf(self.row.response)).codes
            return pd.Series(codes + 1, index=self.table.index)
        return values

    def codeFactor(self, factor: str) -> pd.Series:
        codes = pd.Categorical(self.table[factor], categories=self.levelsOf(factor)).codes
        return pd.Series(codes, index=self.table.index)

    def levelsOf(self, column: str) -> tuple:
        self.levels[column] = levels(self.table[column])
        return self.levels[column]

    def codeInteraction(self, term: str) -> dict[str, pd.Series]:
        """The products of the coded columns of its parts, `<a>:<b>` per pair in order."""
        columns = {'': pd.Series(1.0, index=self.table.index)}
        for part in parts(term):
            products = {}
            for name, column in columns.items():
                for partName, partColumn in self.coded[part].items():
                    products[f'{name}:{partName}'.removeprefix(':')] = column * partColumn
            columns = products
        return columns
