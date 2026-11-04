"""fits.py measures fits.csv: the documented model of each registry row with a continuous, binary
or count response, fitted by lme4, and its variance components, R² and ICC per grouping factor.

A cluster job fits one row, named by its index among the rows fitted, as a scheduler array task
knows it, into a directory of its own; the collect writes every row's records into fits.csv.
The merge leaves fits.csv as it is, and `measure.py` renders the summary from it.

pipeline:
---------
a registry row and its loaded table                    Fitter.run
-> the rows its source fitted                          Preparations.prepare
-> its formula fitted as written                       frequentist.fit
-> the variance components, R² and ICC per factor      measureFit
-> each factor named as the registry names it          nameFactor
-> the row's records in its run directory              Fitter.run
-> fits.csv, in registry order                         Fitter.collect

Run from the repo root:

    uv run python survey/fits.py run 17
    uv run python survey/fits.py collect
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd
from mixedbench import registry
from mixedbench.contract import FAMILY, digestId, findHolders, withComposites
from mixedbench.datasets import Loader
from mixedbench.frequentist import Fit, fit
from mixedbench.registry.installed import Preparations
from mixedbench.registry.row import Row, parts, writeCsv
from schema import IDENTITY
from sources import readFrame

HERE = Path(__file__).parent

# =====================================================================================
# globals
# =====================================================================================
RESPONSE_TYPES = ('continuous', 'binary', 'count')  # the families lme4 fits by the contract's rule
TIMEOUT = 60 * 60  # seconds per fit
ESTIMATED = ('ok', 'singular', 'warning')  # the statuses a fit's components are written for
ROW_STATISTICS = (
    'sigma2_fixed', 'sigma2_random', 'sigma2_residual', 'sigma2_distribution', 'sd_eta',
    'r2_marginal', 'r2_conditional',
)  # fmt: skip
FACTOR_STATISTICS = ('q', 'sigma2', 'icc', 'icc_adjusted')
FIT_STATISTICS = ROW_STATISTICS + FACTOR_STATISTICS
# max |η̂| follows the released columns and is no summary axis: it flags a saturated link for tabdgp
FIT_COLUMNS = (
    *IDENTITY, 'factor', 'status', 'message', 'seconds', 'n_obs', 'family', 'family_doc',
    *FIT_STATISTICS, 'max_abs_eta',
)  # fmt: skip


# =====================================================================================
# the pass: a row -> its fit -> its records -> fits.csv
# =====================================================================================
class Fitter:
    """The fits of a registry's rows with a fitted response type, a directory each under `dir`."""

    def __init__(self, root: Path, loader: Loader, dir: Path) -> None:
        self.root = root
        self.loader = loader
        self.dir = dir
        self.sources = readFrame(root).sources
        rows = registry.rows(root / 'registry.csv')
        self.rows = [row for row in rows if row.response_type in RESPONSE_TYPES]
        fitted = {row.id for row in self.rows}
        self.preparations = Preparations(root / 'fits_preparation.csv')
        for id in self.preparations.listed:
            if id not in fitted:
                raise ValueError(f'fits_preparation.csv prepares {id}, which no fit takes')

    def run(self, index: int) -> None:
        """Fits the row at `index` among the rows fitted, replacing an earlier run of it."""
        row = self.rows[index]
        dir = self.findDir(row)
        if dir.exists():  # no file of an earlier run stays beside this run's records
            shutil.rmtree(dir)
        dir.mkdir(parents=True)
        loaded = self.loader.load(self.sources[row.source], row.object, row.types)
        table = self.preparations.prepare(row, loaded)
        fitted = fit(table, row.formula, FAMILY[row.response_type][0], dir, TIMEOUT)
        records = measureFit(row, fitted, table)
        (dir / 'records.json').write_text(json.dumps(records, indent=2))

    def collect(self) -> None:
        """Writes every row's records into fits.csv; raises where a row was never run."""
        fits = []
        for row in self.rows:
            fits += json.loads((self.findDir(row) / 'records.json').read_text())
        # Int64: a blank would make the counts floats
        table = pd.DataFrame(fits, columns=FIT_COLUMNS).astype({'n_obs': 'Int64', 'q': 'Int64'})
        writeCsv(table, self.root / 'fits.csv')

    def findDir(self, row: Row) -> Path:
        return self.dir / digestId(row.id)


# =====================================================================================
# fits.csv: a fit -> its components -> a row per factor
# =====================================================================================
def measureFit(row: Row, fitted: Fit, table: pd.DataFrame) -> list[dict]:
    """A row per factor of the fit, its variance partition rounded.
    A fit without estimates leaves a row per registry factor, its statistics blank."""
    identity = {k: getattr(row, k) for k in IDENTITY}
    shared = {
        'status': fitted.status,
        'message': fitted.message,
        'seconds': None if fitted.seconds is None else round(fitted.seconds, 4),
        'n_obs': fitted.n_obs,
        'family': FAMILY[row.response_type][0],
        'family_doc': row.family,
    }
    if fitted.status not in ESTIMATED:
        return [identity | {'factor': factor} | shared for factor in row.grouping_factors]
    residual = fitted.sigma2_residual
    shared |= {
        'sigma2_fixed': round(fitted.sigma2_fixed, 4),
        'sigma2_random': round(fitted.sigma2_random, 4),
        'sigma2_residual': None if residual is None else round(residual, 4),
        'sigma2_distribution': round(fitted.sigma2_distribution, 4),
        'sd_eta': round(fitted.sd_eta, 4),
        'max_abs_eta': round(fitted.max_abs_eta, 4),
        'r2_marginal': round(fitted.r2_marginal, 4),
        'r2_conditional': round(fitted.r2_conditional, 4),
    }
    widths = {}
    for term in fitted.terms:
        widths[term.factor] = widths.get(term.factor, 0) + len(term.columns)
    fits = []
    for factor, sigma2 in fitted.variances.items():
        per_factor = {
            'factor': nameFactor(factor, row, table),
            'q': widths[factor],
            'sigma2': round(sigma2, 4),
            'icc': round(fitted.icc[factor], 4),
            'icc_adjusted': round(fitted.icc_adjusted[factor], 4),
        }
        fits.append(identity | shared | per_factor)
    return fits


def nameFactor(fitted: str, row: Row, table: pd.DataFrame) -> str:
    """The registry's grouping factor that groups the rows as the fitted factor does, else the
    fitted factor's own name. lme4 names a factor by its columns, `herd:region` for
    `(1 | region/herd)`, which groups the rows as `herd` does where every herd lies in one region."""
    if not set(parts(fitted)) <= set(table.columns):  # an expression, such as `factor(year)`
        return fitted
    for factor in row.grouping_factors:
        if groupsAlike(table, factor, fitted):
            return factor
    return fitted


def groupsAlike(table: pd.DataFrame, a: str, b: str) -> bool:
    """Whether two factors split the rows that observe both into the same groups."""
    if set(parts(a)) == set(parts(b)):
        return True
    composed = withComposites(table, (a, b))
    return len(findHolders(composed, a, b)) == 2


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('run', 'collect'), help='fit one row, or collect every row into fits.csv')
    parser.add_argument('index', type=int, nargs='?', help='the row to fit, by its 0-based index among the rows fitted')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--dir', type=Path, default=HERE.parent / 'fits', help='folder of the run directories')
    args = parser.parse_args()
    # fmt: on
    fitter = Fitter(args.registry, Loader(args.registry / 'cache'), args.dir)
    if args.command == 'run':
        fitter.run(args.index)
    else:
        fitter.collect()
