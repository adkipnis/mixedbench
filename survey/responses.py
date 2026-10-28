"""responses.py measures responses.csv: a row per registry row, the marginal of its response.
The response is measured as the kind its type gives, by the statistics columns.csv defines for
that kind.

pipeline:
---------
a measurer
-> the response's kind, by its type                     KINDS
-> its missing share and the quirk statistics it takes  columns.measureShape
-> its largest rank correlation with a covariate        columns.measureMaxAbsRho
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import columns
import pandas as pd
from columns import COLUMN_STATISTICS
from schema import IDENTITY

if TYPE_CHECKING:  # only a type: measure.py imports this module
    from measure import Measurer

# =====================================================================================
# globals
# =====================================================================================
RESPONSE_COLUMNS = (*IDENTITY, 'response', 'response_type', 'K', 'missing_share', *COLUMN_STATISTICS)  # fmt: skip
# the column kind a response type is measured as
KINDS = {
    'continuous': 'continuous',
    'count': 'continuous',
    'binomial': 'continuous',
    'binary': 'binary',
    'ordinal': 'ordered',
    'categorical': 'categorical',
}


# =====================================================================================
# responses.csv: kind -> missing share and quirk statistics -> rank correlation
# =====================================================================================
def measure(measurer: Measurer) -> dict:
    row = measurer.row
    values = codeResponse(measurer.loaded, row.response, row.response_type, row.trials)
    measured = measureResponse(values, row.response_type, measurer.table, measurer.column_types)
    return measurer.identity | measured


def measureResponse(
    values: pd.Series, response_type: str, table: pd.DataFrame, column_types: dict[str, tuple]
) -> dict:
    """A coded response's marginal, which flat.py measures too: its levels, missing share and
    quirk statistics by the kind its type gives, and its largest rank correlation with a column
    of `column_types` over the table's rows."""
    response = values.name
    kind = KINDS[response_type]
    levels = '' if kind == 'continuous' else values.nunique()
    ranked = column_types | {response: (kind, levels)}
    table = table.assign(**{response: values})  # aligned to the table's rows
    rho = columns.measureMaxAbsRho(table, ranked)[response]
    measured = {'response': response, 'response_type': response_type, 'K': levels}
    return measured | columns.measureShape(values, kind) | {'max_abs_rho': rho}


def codeResponse(table: pd.DataFrame, response: str, response_type: str, trials: str) -> pd.Series:
    """The response as measured, under its column's name: a binomial one as its successes' share
    of the trials, an ordinal one as ordered levels, in the order the contract codes them."""
    values = table[response]
    if response_type == 'binomial':
        return (values / table[trials]).rename(response)
    if response_type == 'ordinal':  # a plain column orders as the loader orders a declared one
        return values.astype('category').cat.as_ordered()
    return values
