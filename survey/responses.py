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
    from mixedbench.registry.row import Row

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
    kind = KINDS[row.response_type]
    values = codeResponse(measurer.loaded, row)
    levels = '' if kind == 'continuous' else values.nunique()
    ranked = measurer.column_types | {row.response: (kind, levels)}
    table = measurer.table.assign(**{row.response: values})  # aligned to the measured rows
    rho = columns.measureMaxAbsRho(table, ranked)[row.response]
    measured = {'response': row.response, 'response_type': row.response_type, 'K': levels}
    return measurer.identity | measured | columns.measureShape(values, kind) | {'max_abs_rho': rho}


def codeResponse(table: pd.DataFrame, row: Row) -> pd.Series:
    """The response as measured: a binomial one as its successes' share of the trials, an
    ordinal one as ordered levels, in the order the contract codes them."""
    values = table[row.response]
    if row.response_type == 'binomial':
        return values / table[row.trials]
    if row.response_type == 'ordinal':  # a plain column orders as the loader orders a declared one
        return values.astype('category').cat.as_ordered()
    return values
