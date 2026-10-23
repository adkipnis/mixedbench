"""fits.csv: a registry row's fit read as its variance components, R² and ICC per factor."""

import math
import subprocess

import numpy as np
import pandas as pd
import pytest
from conftest import FIXTURES, mergeShard, parsed, readRows
from fits import FACTOR_STATISTICS, FIT_COLUMNS, ROW_STATISTICS, Fitter, measure
from mixedbench.frequentist import Fit, Term, fit
from mixedbench.registry.row import readCsv, writeCsv


def intercepts(variances: dict[str, float]) -> tuple[Term, ...]:
    """A random intercept per factor, as lme4 reads them back."""
    return tuple(Term(f, ('(Intercept)',), (v,), ((1.0,),)) for f, v in variances.items())


def nested(**components) -> Fit:
    """A fit of the herds row's `(1 | region/herd)`: lme4 names the inner factor `herd:region`.
    The fixed part carries a variance of 1, region 1 and herd 0.5."""
    variances = {'herd:region': 0.5, 'region': 1.0}
    fitted = {
        'status': 'ok', 'seconds': 0.51234, 'n_obs': 14, 'fixed': {'(Intercept)': (500.0, 10.0)},
        'terms': intercepts(variances), 'variances': variances, 'sigma2_fixed': 1.0,
        'sd_eta': 1.5, 'sigma': 1.0, 'sigma2_distribution': 0.0,
    }  # fmt: skip
    return Fit(**(fitted | components))


@pytest.mark.parametrize(
    ('response', 'fit', 'shared', 'region', 'herd'),
    [
        pytest.param(
            {'response_type': 'continuous'}, nested(),
            {'family': 'gaussian', 'family_doc': '', 'sigma2_residual': 1.0, 'sigma2_distribution': 0.0, 'r2_marginal': 0.2857, 'r2_conditional': 0.7143},
            {'icc': 0.2857, 'icc_adjusted': 0.4}, {'icc': 0.1429, 'icc_adjusted': 0.2},
            id='gaussian: a residual of 1, a total of 3.5',
        ),
        pytest.param(
            {'response': 'sick', 'response_type': 'binary', 'family': 'bernoulli(probit)'},
            nested(sigma=None, sigma2_distribution=math.pi**2 / 3),
            {'family': 'bernoulli', 'family_doc': 'bernoulli(probit)', 'sigma2_residual': None, 'sigma2_distribution': 3.2899, 'r2_marginal': 0.1727, 'r2_conditional': 0.4318},
            {'icc': 0.1727, 'icc_adjusted': 0.2088}, {'icc': 0.0864, 'icc_adjusted': 0.1044},
            id='bernoulli: no residual, the logistic pi^2/3, a total of 5.79',
        ),
    ],
)  # fmt: skip
def test_a_fit_shares_its_variance_between_fixed_part_factors_and_residual(
    herds, rows, response, fit, shared, region, herd
):
    """Nakagawa, Johnson and Schielzeth (2017): R² over σ²_f + Σ σ²_g + σ²_ε + σ²_d, a factor's
    ICC its σ²_g over the same total, its adjusted ICC over the total without σ²_f.
    The contract's family rule names the family, the registry's departure rides beside it."""
    row = parsed(rows[0] | response)

    first, second = measure(row, fit, herds)

    every = {
        'source': 'herds', 'object': 'herds.csv', 'model_index': 1, 'tier': 'D', 'status': 'ok',
        'message': '', 'seconds': 0.5123, 'n_obs': 14, 'sigma2_fixed': 1.0, 'sigma2_random': 1.5,
        'sd_eta': 1.5,
    } | shared  # fmt: skip
    assert first == every | {'factor': 'herd', 'q': 1, 'sigma2': 0.5} | herd
    assert second == every | {'factor': 'region', 'q': 1, 'sigma2': 1.0} | region


@pytest.mark.parametrize(
    'fit',
    [
        pytest.param(Fit('error', 0.2, 'could not find function "s"'), id='an error keeps its message'),
        pytest.param(Fit('timeout', 3600.0213, 'reached elapsed time limit'), id='a timeout its seconds'),
        pytest.param(Fit('no_formula'), id='a model documented in words runs no fit'),
    ],
)  # fmt: skip
def test_a_fit_without_estimates_keeps_a_blank_row_per_registry_factor(herds, rows, fit):
    """Nothing is skipped: the consumer filters on `status`."""
    region, herd = measure(parsed(rows[0]), fit, herds)

    assert (region['factor'], herd['factor']) == ('region', 'herd')
    assert (herd['status'], herd['message'], herd['seconds']) == (
        fit.status,
        fit.message,
        fit.seconds,
    )
    assert herd['family'] == 'gaussian'
    assert [herd.get(c) for c in ('n_obs', *ROW_STATISTICS, *FACTOR_STATISTICS)] == [None] * 12


def single(factor: str, terms: tuple[Term, ...] = ()) -> Fit:
    """A fit of one factor, its variance 1 over one intercept unless `terms` say otherwise."""
    return nested(variances={factor: 1.0}, terms=terms or intercepts({factor: 1.0}))


@pytest.mark.parametrize(
    ('relabeled', 'fitted', 'named'),
    [
        pytest.param({}, 'region', 'region', id='a registry factor keeps its name'),
        pytest.param({5: 'h1'}, 'herd:region', 'herd:region', id='h1 in two regions: herd groups otherwise, lme4 names it'),
        pytest.param({}, 'breed', 'breed', id='a factor the registry does not list keeps lme4 name'),
        pytest.param({}, 'factor(region)', 'factor(region)', id='an expression keeps lme4 name'),
    ],
)  # fmt: skip
def test_a_fitted_factor_takes_the_name_of_the_registry_factor_that_groups_alike(
    herds, rows, relabeled, fitted, named
):
    """lme4 names a factor by the formula's columns; the registry lists the factor that groups the
    rows alike, so that fits.csv joins dimensions.csv where the two agree."""
    table = herds.assign(herd=herds['herd'].astype(str))
    for index, label in relabeled.items():
        table.loc[index, 'herd'] = label

    [record] = measure(parsed(rows[0]), single(fitted), table)

    assert record['factor'] == named


def test_a_factor_counts_the_columns_of_every_term_it_has(herds, rows):
    """`(1 + feed || herd)` is two terms of one factor, an intercept and a slope: q is 2."""
    terms = (
        Term('herd', ('(Intercept)',), (0.6,), ((1.0,),)),
        Term('herd', ('feedgrass',), (0.4,), ((1.0,),)),
    )

    [record] = measure(parsed(rows[0]), single('herd', terms), herds)

    assert (record['factor'], record['q'], record['sigma2']) == ('herd', 2, 1.0)


def simulated(response_type: str) -> pd.DataFrame:
    """600 rows over two crossed factors of 20 and 10 groups, an intercept and a slope of `x` per
    `g` drawn apart, so that no variance or correlation lies at its bound."""
    rng = np.random.default_rng(5)
    n = 600
    g = rng.integers(0, 20, n)
    h = rng.integers(0, 10, n)
    x = rng.normal(0, 1, n)
    u = rng.normal(0, 0.7, (20, 2))[g]  # (n, 2)
    eta = 0.2 + 0.6 * x + u[:, 0] + u[:, 1] * x + rng.normal(0, 0.6, 10)[h]
    if response_type == 'continuous':
        y = eta + rng.normal(0, 1, n)
    elif response_type == 'binary':
        y = rng.binomial(1, 1 / (1 + np.exp(-eta)))
    else:
        y = rng.poisson(np.exp(eta))
    return pd.DataFrame({'g': [f'g{j}' for j in g], 'h': [f'h{j}' for j in h], 'x': x, 'y': y})


def nakagawa(dir, formula: str, response_type: str) -> tuple[float, float]:
    """performance's marginal and conditional R² of the same model, fitted to the table `fit` wrote."""
    fitter = {
        'continuous': 'lme4::lmer({})',
        'binary': 'lme4::glmer({}, family = binomial)',
        'count': 'lme4::glmer({}, family = poisson)',
    }[response_type].format(f'{formula}, data = table')
    script = (
        'args <- commandArgs(trailingOnly = TRUE); '
        'table <- read.csv(file.path(args[[1]], "table.csv")); '
        f'r2 <- performance::r2_nakagawa({fitter}); '
        'cat(r2$R2_marginal, r2$R2_conditional)'
    )
    process = subprocess.run(
        ['Rscript', '-e', script, dir], capture_output=True, text=True, check=True
    )
    marginal, conditional = process.stdout.split()
    return float(marginal), float(conditional)


@pytest.mark.lme4
@pytest.mark.parametrize(
    ('response_type', 'formula'),
    [
        pytest.param('continuous', 'y ~ x + (1 + x | g) + (1 | h)', id='gaussian with a correlated slope'),
        pytest.param('binary', 'y ~ x + (1 | g) + (1 | h)', id='bernoulli over two crossed factors'),
        pytest.param('count', 'y ~ x + (1 + x | g) + (1 | h)', id='poisson with a correlated slope'),
    ],
)  # fmt: skip
def test_r2_matches_performance_on_the_same_fit(tmp_path, rows, response_type, formula):
    """performance (Lüdecke et al. 2021) computes Nakagawa's R² apart from this pass.
    An uncorrelated slope `(1 + x || g)` is no case: insight 1.5.2 keeps only the first of a
    factor's terms, here the intercept, in the fit's and the null model's random variance."""
    table = simulated(response_type)
    row = parsed(rows[0] | {
        'response': 'y', 'response_type': response_type, 'grouping_factors': 'g;h',
        'covariates': 'x', 'types': '', 'formula': formula,
    })  # fmt: skip
    family = {'continuous': 'gaussian', 'binary': 'bernoulli', 'count': 'poisson'}[response_type]

    [record, _] = measure(row, fit(table, formula, family, tmp_path, 60), table)

    assert record['status'] == 'ok'
    expected = nakagawa(tmp_path, formula, response_type)
    assert (record['r2_marginal'], record['r2_conditional']) == pytest.approx(expected, abs=1e-4)


def mergedHerds(merger, formula: str, counted: str = ''):
    """The scratch registry of the herds rows, the gaussian one's formula replaced: a fitter over
    it fits that row and not the binomial one, unless `counted` names a formula for its cases
    as a count."""
    rows = readRows(FIXTURES / 'registry_herds.csv')
    rows[0]['formula'] = formula
    if counted:
        rows[1] |= {'response_type': 'count', 'trials': '', 'formula': counted}
    shard = merger.survey / 'shards' / 'registry_fits.csv'
    writeCsv(pd.DataFrame(rows), shard)
    mergeShard(merger, shard)
    return merger


def test_the_pass_collects_a_row_per_factor_of_every_row_it_fits(merger, tmp_path):
    """One run per row with a continuous, binary or count response, its records in a directory
    of its own until the collect writes them into fits.csv in registry order."""
    registry = mergedHerds(merger, 'weight by breed, a herd nested in its region').registry
    fitter = Fitter(registry, merger.loader, tmp_path / 'fits')

    fitter.run(0)
    fitter.collect()

    fits = readCsv(registry / 'fits.csv')
    assert list(fits.columns) == list(FIT_COLUMNS)
    assert fits[['model_index', 'factor', 'status', 'family']].values.tolist() == [
        ['1', 'region', 'no_formula', 'gaussian'],
        ['1', 'herd', 'no_formula', 'gaussian'],
    ]


def test_the_collect_refuses_a_row_never_run(merger, tmp_path):
    """Every row the pass fits is accounted for: a missing run is no row to leave out."""
    registry = mergedHerds(merger, 'weight by breed, a herd nested in its region').registry

    with pytest.raises(FileNotFoundError):
        Fitter(registry, merger.loader, tmp_path / 'fits').collect()


@pytest.mark.lme4
def test_a_run_fits_the_rows_loaded_table_by_its_formula_and_family(merger, tmp_path):
    """The herds row's own `(1 | region/herd)` on its 14 loaded rows, beside a count row
    documented in words: the counts stay integers beside the blanks."""
    formula = 'weight ~ breed + feed + (1 | region/herd)'
    registry = mergedHerds(merger, formula, counted='cases by breed within herds').registry
    fitter = Fitter(registry, merger.loader, tmp_path / 'fits')

    fitter.run(0)
    fitter.run(1)
    fitter.collect()

    fits = readCsv(registry / 'fits.csv')
    assert fits[['model_index', 'factor', 'n_obs', 'family', 'q']].values.tolist() == [
        ['1', 'herd', '14', 'gaussian', '1'],
        ['1', 'region', '14', 'gaussian', '1'],
        ['2', 'herd', '', 'poisson', ''],
    ]
