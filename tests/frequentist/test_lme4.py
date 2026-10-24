"""The fitter's seam: a table, a formula and a family in, lme4's fit read back."""

from __future__ import annotations

import subprocess

import numpy as np
import pandas as pd
import pytest
from mixedbench.frequentist import Fit, fit, lme4

TIMEOUT = 60  # seconds, far above what these fits take


def balancedOneWay() -> pd.DataFrame:
    """Six groups of five rows, the groups spread well beyond the rows within them."""
    rng = np.random.default_rng(1)
    g = np.repeat([f'g{j}' for j in range(6)], 5)
    y = rng.normal(0, 1.5, 6).repeat(5) + rng.normal(10, 1, 30)
    return pd.DataFrame({'g': g, 'y': y})


def flatGroups() -> pd.DataFrame:
    """Six groups of the same five responses, so the groups spread by nothing: τ² is 0.
    `z` is negative beside each group's mean, so a log drops those rows and leaves the means."""
    g = np.repeat([f'g{j}' for j in range(6)], 5)
    y = np.tile([8.0, 9.0, 10.0, 11.0, 12.0], 6)
    z = np.tile([1.0, 2.0, -1.0, 3.0, 4.0], 6)
    return pd.DataFrame({'g': g, 'y': y, 'z': z})


def crossedLarge() -> pd.DataFrame:
    """20,000 rows over two crossed factors of 2,000 and 500 groups, a slope on the first:
    seconds of lme4's work."""
    rng = np.random.default_rng(2)
    n = 20_000
    g = rng.integers(0, 2000, n)
    h = rng.integers(0, 500, n)
    x = rng.normal(0, 1, n)
    y = x + rng.normal(0, 1, 2000)[g] * (1 + x) + rng.normal(0, 1, 500)[h] + rng.normal(0, 1, n)
    return pd.DataFrame({'g': g, 'h': h, 'x': x, 'y': y})


def generalized(family: str) -> pd.DataFrame:
    """Ten groups of 20 rows, a covariate and a group intercept on the link scale."""
    rng = np.random.default_rng(3)
    g = np.repeat(np.arange(10), 20)
    x = rng.normal(0, 1, len(g))
    eta = -0.3 + 0.8 * x + rng.normal(0, 0.7, 10)[g]
    if family == 'bernoulli':
        y = rng.binomial(1, 1 / (1 + np.exp(-eta)))
    else:
        y = rng.poisson(np.exp(eta))
    return pd.DataFrame({'g': [f'g{j}' for j in g], 'x': x, 'y': y})


def insightDistributionVariance(dir, formula: str, family: str) -> float:
    """insight's distribution variance of the same model, fitted to the table `fit` wrote."""
    script = (
        'args <- commandArgs(trailingOnly = TRUE); '
        'table <- read.csv(file.path(args[[1]], "table.csv")); '
        f'model <- lme4::glmer({formula}, data = table, family = {family}); '
        'cat(insight::get_variance_distribution(model))'
    )
    process = subprocess.run(
        ['Rscript', '-e', script, dir], capture_output=True, text=True, check=True
    )
    return float(process.stdout)


@pytest.mark.lme4
def test_a_balanced_one_way_design_returns_the_closed_form_reml_estimates(tmp_path):
    """REML of a balanced one-way design has a closed form (Searle, Casella and McCulloch 1992,
    chapter 3): σ²_ε is the within mean square MSW, τ² = (MSB − MSW) / n, and the intercept is the
    grand mean with variance MSB / (m n). The random variance is τ², a constant predictor carries
    no fixed variance, and η adds each group's shrunken deviation to the grand mean."""
    table = balancedOneWay()
    m, n = 6, 5
    group_means = table['g'].map(table.groupby('g')['y'].mean())
    grand = table['y'].mean()
    msw = ((table['y'] - group_means) ** 2).sum() / (m * (n - 1))
    msb = ((group_means - grand) ** 2).sum() / (m - 1)  # a row per member: n Σ (ȳⱼ − ȳ)²
    tau2 = (msb - msw) / n
    eta = grand + tau2 / (tau2 + msw / n) * (group_means - grand)

    fitted = fit(table, 'y ~ 1 + (1 | g)', 'gaussian', tmp_path, TIMEOUT)

    assert (fitted.status, fitted.message, fitted.n_obs) == ('ok', '', m * n)
    assert fitted.fixed == {'(Intercept)': pytest.approx((grand, np.sqrt(msb / (m * n))), rel=1e-4)}
    [term] = fitted.terms
    assert (term.factor, term.columns, term.correlations) == ('g', ('(Intercept)',), ((1.0,),))
    assert term.variances == pytest.approx((tau2,), rel=1e-4)
    assert fitted.variances == pytest.approx({'g': tau2}, rel=1e-4)
    assert fitted.sigma == pytest.approx(np.sqrt(msw), rel=1e-4)
    assert fitted.sigma2_fixed == pytest.approx(0, abs=1e-12)
    assert fitted.sd_eta == pytest.approx(eta.std(), rel=1e-4)
    assert fitted.sigma2_distribution == 0


@pytest.mark.lme4
@pytest.mark.parametrize(
    ('ordered', 'names'),
    [
        pytest.param(False, ['(Intercept)', 'xa', 'xb'], id='a factor contrasts its first level'),
        pytest.param(True, ['(Intercept)', 'x.L', 'x.Q'], id='an ordered one its polynomials'),
    ],
)
def test_a_categorical_column_reaches_lme4_with_its_levels_in_order(tmp_path, ordered, names):
    """R would sort `c`, `a`, `b` itself and take `a` as the reference."""
    table = balancedOneWay()
    levels = pd.CategoricalDtype(['c', 'a', 'b'], ordered=ordered)
    categorical = table.assign(x=pd.Series(['a', 'b', 'c'] * 10).astype(levels))

    fitted = fit(categorical, 'y ~ x + (1 | g)', 'gaussian', tmp_path, TIMEOUT)

    assert list(fitted.fixed) == names


@pytest.mark.lme4
@pytest.mark.parametrize(
    ('table', 'formula', 'timeout', 'status', 'message', 'estimated'),
    [
        pytest.param(flatGroups, 'y ~ 1 + (1 | g)', TIMEOUT, 'singular', '', True, id='a variance at its bound is singular, lme4\'s note muffled'),
        pytest.param(flatGroups, 'y ~ log(z) + (1 | g)', TIMEOUT, 'warning', 'NaNs produced', True, id='a warning outranks the singular fit it comes with'),
        pytest.param(flatGroups, 'y ~ s(z) + (1 | g)', TIMEOUT, 'error', 'could not find function "s"', False, id='a formula lme4 refuses is an error with its message'),
        pytest.param(crossedLarge, 'y ~ x + (x | g) + (1 | h)', 0.1, 'timeout', 'reached elapsed time limit', False, id='a fit stopped at its limit is a timeout'),
    ],
)  # fmt: skip
def test_a_fit_ends_with_the_worst_status_that_applies_and_its_message(
    tmp_path, table, formula, timeout, status, message, estimated
):
    fitted = fit(table(), formula, 'gaussian', tmp_path, timeout)

    assert (fitted.status, fitted.message) == (status, message)
    assert (fitted.seconds >= timeout) == (status == 'timeout')
    assert (fitted.n_obs is not None) == estimated
    assert bool(fitted.fixed) == estimated
    assert (fitted.sd_eta is not None) == estimated


def test_a_formula_without_a_random_term_is_recorded_without_a_fit(tmp_path):
    """A model documented in words names no grouping factor, so R never runs."""
    fitted = fit(balancedOneWay(), 'y ~ a nonlinear model in time', 'gaussian', tmp_path, TIMEOUT)

    assert fitted == Fit('no_formula')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.lme4
@pytest.mark.parametrize(
    ('family', 'r_family'),
    [
        pytest.param('bernoulli', 'binomial', id='bernoulli: the logistic variance'),
        pytest.param('poisson', 'poisson', id='poisson: ln(1 + 1/lambda) of the null model'),
    ],
)
def test_a_generalized_fit_has_no_residual_sd_and_adds_the_family_variance(
    tmp_path, family, r_family
):
    """Nakagawa, Johnson and Schielzeth (2017): π²/3 for the logit,
    ln(1 + 1/λ) for the log with λ the mean count of the model with an intercept and the same
    random effects."""
    formula = 'y ~ x + (1 | g)'

    fitted = fit(generalized(family), formula, family, tmp_path, TIMEOUT)

    assert (fitted.status, fitted.sigma) == ('ok', None)
    expected = insightDistributionVariance(tmp_path, formula, r_family)
    assert fitted.sigma2_distribution == pytest.approx(expected, rel=1e-6)


@pytest.mark.lme4
def test_a_model_without_fixed_effects_has_none_and_no_fixed_variance(tmp_path):
    """`y ~ 0 + (1 | g)` leaves the mean to the groups, as rethinking's Prussian horse kicks do."""
    fitted = fit(balancedOneWay(), 'y ~ 0 + (1 | g)', 'gaussian', tmp_path, TIMEOUT)

    assert (fitted.status, fitted.fixed, fitted.sigma2_fixed) == ('ok', {}, 0)


@pytest.mark.lme4
def test_a_binary_response_of_text_fits_as_its_0_1_coding(tmp_path):
    """A source may store a binary response as `N` and `Y`, which glmer takes only as a factor."""
    coded = generalized('bernoulli')
    text = coded.assign(y=coded['y'].map({0: 'N', 1: 'Y'}))

    expected = fit(coded, 'y ~ x + (1 | g)', 'bernoulli', tmp_path / 'coded', TIMEOUT)
    fitted = fit(text, 'y ~ x + (1 | g)', 'bernoulli', tmp_path / 'text', TIMEOUT)

    assert fitted.status == 'ok'
    assert fitted.fixed['x'] == pytest.approx(expected.fixed['x'], rel=1e-9)
    assert fitted.variances == pytest.approx(expected.variances, rel=1e-9)


@pytest.mark.lme4
def test_text_columns_of_different_values_compare_in_the_formula(tmp_path):
    """olympics' same-country indicator `I(pcountry == jcountry)`:
    as factors of different levels, R refuses to compare them."""
    table = balancedOneWay()
    table['a'] = ['x', 'y', 'z'] * 10
    table['b'] = ['x', 'w'] * 15

    fitted = fit(table, 'y ~ I(a == b) + (1 | g)', 'gaussian', tmp_path, TIMEOUT)

    assert (fitted.status, list(fitted.fixed)) == ('ok', ['(Intercept)', 'I(a == b)TRUE'])


@pytest.mark.lme4
def test_a_fit_by_another_lme4_than_the_pin_raises(tmp_path, monkeypatch):
    """A pass mixing lme4 versions would mix their optimizers' estimates."""
    monkeypatch.setattr(lme4, 'LME4', '0.0.0')

    with pytest.raises(RuntimeError, match='differs from the pin 0.0.0'):
        fit(balancedOneWay(), 'y ~ 1 + (1 | g)', 'gaussian', tmp_path, TIMEOUT)


@pytest.mark.lme4
def test_a_factor_of_several_terms_carries_the_variance_of_each(tmp_path):
    """`(1 + x || g)` is two terms of `g`, so z'Σz has no covariance:
    its mean over rows is τ₀² + τ₁² mean(x²) (Johnson 2014)."""
    rng = np.random.default_rng(4)
    g = np.repeat(np.arange(10), 20)
    x = rng.normal(0, 1, len(g))
    u = rng.normal(0, 1, (10, 2))[g]  # (n, 2)
    y = 1 + x + u[:, 0] + u[:, 1] * x + rng.normal(0, 0.5, len(g))
    table = pd.DataFrame({'g': [f'g{j}' for j in g], 'x': x, 'y': y})

    fitted = fit(table, 'y ~ x + (1 + x || g)', 'gaussian', tmp_path, TIMEOUT)

    assert fitted.status == 'ok'
    intercept, slope = fitted.terms
    assert (intercept.factor, slope.factor, slope.columns) == ('g', 'g', ('x',))
    expected = intercept.variances[0] + slope.variances[0] * (table['x'] ** 2).mean()
    assert fitted.variances == pytest.approx({'g': expected}, rel=1e-9)


@pytest.mark.lme4
def test_each_factor_carries_its_own_terms_whatever_order_lme4_fits_them_in(tmp_path):
    """lme4 fits the factor of more levels first, here `site:plot` before `site`,
    and its integer columns compose by level, not as R's sequence `site:plot`.
    The slope term stays with `site`: τ₀² + 2 τ₀₁ mean(x) + τ₁² mean(x²) (Johnson 2014)."""
    rng = np.random.default_rng(5)
    site = np.repeat(np.arange(5), 40)
    plot = np.tile(np.repeat(np.arange(4), 10), 5)  # 0 to 3 within each site
    x = rng.normal(1, 1, len(site))
    u = rng.normal(0, 1, (5, 2))[site]  # (n, 2)
    v = rng.normal(0, 0.7, 20)[site * 4 + plot]
    y = 1 + x + u[:, 0] + u[:, 1] * x + v + rng.normal(0, 0.5, len(site))
    table = pd.DataFrame({'site': site, 'plot': plot, 'x': x, 'y': y})

    fitted = fit(table, 'y ~ x + (1 + x | site) + (1 | site:plot)', 'gaussian', tmp_path, TIMEOUT)

    assert (fitted.status, fitted.message) == ('ok', '')
    composite, slopes = fitted.terms
    assert (composite.factor, slopes.factor) == ('site:plot', 'site')
    tau0, tau1 = slopes.variances
    tau01 = slopes.correlations[0][1] * np.sqrt(tau0 * tau1)
    expected = tau0 + 2 * tau01 * table['x'].mean() + tau1 * (table['x'] ** 2).mean()
    assert fitted.variances == pytest.approx(
        {'site:plot': composite.variances[0], 'site': expected}, rel=1e-9
    )


@pytest.mark.lme4
def test_a_message_is_one_line(tmp_path):
    """R's parse error points at the formula over three lines; fits.csv keeps a cell per line."""
    formula = 'y ~ 1 + (1 | g), a note'

    fitted = fit(balancedOneWay(), formula, 'gaussian', tmp_path, TIMEOUT)

    assert fitted.message == "<text>:1:16: unexpected ',' 1: y ~ 1 + (1 | g), ^"
