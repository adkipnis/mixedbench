"""responses.csv from `fixtures/herds.csv`: a registry row's response measured by the kind its
type gives, each expected value worked by hand or by scipy."""

import pandas as pd
import responses
from conftest import parsed
from measure import Measurer
from responses import RESPONSE_COLUMNS


def measuredResponse(table: pd.DataFrame, cells: dict) -> pd.Series:
    """The responses.csv row of one registry row; a statistic left out is blank."""
    measured = responses.measure(Measurer(table, parsed(cells)))
    return pd.Series(measured).reindex(RESPONSE_COLUMNS)


def test_a_continuous_response_takes_the_statistics_of_a_continuous_column(herds, rows):
    """Weight under model 1 against scipy.stats.skew and kurtosis with bias=False; its minimum
    and maximum occur once each, zero never. Its largest |Spearman| is with sick, 0.6841, against
    parity's 0.3029; breed and feed are categoricals of more than two levels."""
    weight = measuredResponse(herds, rows[0])
    assert tuple(weight[['response', 'response_type', 'K']]) == ('weight', 'continuous', '')
    assert tuple(weight[['skewness', 'excess_kurtosis', 'outlier_share']]) == (0.5207, -0.6651, 0)
    assert (weight['zero_share'], weight['min_share'], weight['max_share']) == (0, 0.0714, 0.0714)
    assert tuple(weight[['missing_share', 'unique_share', 'max_abs_rho']]) == (0, 1, 0.6841)
    assert pd.isna(weight['rare_level_share'])
    assert weight['tier'] == 'D' and weight['model_index'] == 1


def test_a_binomial_response_is_measured_as_its_successes_share_of_the_trials(herds, rows):
    """Cases out of trials under model 2: two zero shares of fourteen, which are also the
    minimum, and one maximum, 7/9. scipy gives G1 0.6362 and G2 -0.4856 of the shares, and their
    largest |Spearman| is with weight, 0.8921, against sick's 0.7598 and parity's 0.394."""
    cases = measuredResponse(herds, rows[1])
    assert (cases['response'], cases['response_type'], cases['K']) == ('cases', 'binomial', '')
    assert (cases['skewness'], cases['excess_kurtosis']) == (0.6362, -0.4856)
    assert (cases['zero_share'], cases['min_share'], cases['max_share']) == (0.1429, 0.1429, 0.0714)
    assert (cases['unique_share'], cases['max_abs_rho']) == (0.8571, 0.8921)


def test_an_ordinal_response_is_measured_by_its_levels_however_it_loads(herds, rows):
    """Parity as an ordinal response loads as integers, which the columns rule would call
    continuous: as ordered, it has four levels and no moments. Five rows sit at its lowest level,
    one at its highest, and it ranks 0.4864 with sick, 0.3029 with weight. Named levels keep
    their loaded order, not the alphabet's, and leave the zero share blank."""
    row = rows[0] | {'response': 'parity', 'response_type': 'ordinal', 'ignore': 'id;cases;trials'}  # fmt: skip
    parity = measuredResponse(herds, row)
    assert (parity['K'], parity['zero_share'], parity['min_share'], parity['max_share']) == (4, 0, 0.3571, 0.0714)  # fmt: skip
    assert (parity['unique_share'], parity['rare_level_share'], parity['max_abs_rho']) == (0.2857, 0.0714, 0.4864)  # fmt: skip
    assert parity[['skewness', 'excess_kurtosis', 'outlier_share']].isna().all()
    names = ['first', 'second', 'third', 'fourth']
    named = herds.assign(parity=pd.Categorical(herds['parity'].map(dict(zip([1, 2, 3, 4], names))), names))  # fmt: skip
    parity = measuredResponse(named, row)
    assert (parity['min_share'], parity['max_share'], parity['max_abs_rho']) == (0.3571, 0.0714, 0.4864)  # fmt: skip
    assert pd.isna(parity['zero_share'])


def test_binary_and_categorical_responses_count_their_levels(herds, rows):
    """Sick as a binary response: two levels, five rows ill, and it ranks 0.6841 with weight.
    Breed as a categorical one: four levels, the smallest held by three rows; a categorical of
    more than two levels has no order to rank."""
    row = rows[0] | {'response': 'sick', 'response_type': 'binary', 'ignore': 'id;cases;trials'}
    sick = measuredResponse(herds, row)
    assert (sick['K'], sick['unique_share'], sick['rare_level_share'], sick['max_abs_rho']) == (2, 0.1429, 0.3571, 0.6841)  # fmt: skip
    row = rows[0] | {'response': 'breed', 'response_type': 'categorical', 'covariates': 'feed'}
    breed = measuredResponse(herds, row)
    assert (breed['K'], breed['unique_share'], breed['rare_level_share']) == (4, 0.2857, 0.2143)
    assert pd.isna(breed['max_abs_rho'])


def test_the_missing_share_counts_the_loaded_rows_without_a_response(herds, rows):
    """The measured files count only rows with a response, but the response's own missing share
    counts the rows as loaded: one weight missing in fourteen. A binomial row of zero trials has
    no share, so it counts as missing, and the thirteen others hold one zero share."""
    unweighed = herds.copy()
    unweighed.loc[0, 'weight'] = float('nan')
    weight = measuredResponse(unweighed, rows[0])
    assert (weight['missing_share'], weight['unique_share']) == (0.0714, 1)
    untried = herds.copy()
    untried.loc[5, 'trials'] = 0  # its cases are 0 too
    cases = measuredResponse(untried, rows[1])
    assert (cases['missing_share'], cases['zero_share']) == (0.0714, 0.0769)
