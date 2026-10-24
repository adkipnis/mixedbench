"""fits.py measures fits.csv: the documented model of each registry row with a continuous, binary
or count response, fitted by lme4, and its variance components, R² and ICC per grouping factor.

A cluster job fits one row, named by its index among the rows fitted, as a scheduler array task
knows it, into a directory of its own; the collect writes every row's records into fits.csv.
The merge leaves fits.csv as it is.

pipeline:
---------
a registry row and its loaded table                    Fitter.run
-> the rows its source fitted                          Fitter.prepareTable
-> its formula fitted as written                       frequentist.fit
-> the variance components, R² and ICC per factor      measure
-> each factor named as the registry names it          nameFactor
-> the row's records in its run directory              Fitter.run
-> fits.csv, in registry order                         Fitter.collect

Run from the repo root, then the summary:

    uv run python survey/fits.py run 17
    uv run python survey/fits.py collect
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
from measure import Measurer
from mixedbench import registry
from mixedbench.contract import FAMILY, withComposites
from mixedbench.datasets import Loader
from mixedbench.frequentist import Fit, fit
from mixedbench.registry.row import Row, parts, readCsv, writeCsv
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
FIT_COLUMNS = (
    *IDENTITY, 'factor', 'status', 'message', 'seconds', 'n_obs', 'family', 'family_doc',
    *ROW_STATISTICS, *FACTOR_STATISTICS,
)  # fmt: skip
# fits_preparation.csv: a row whose source fits a subset (a pandas query) or repeats each row by
# a frequency weight (its column), and why
PREPARATION_COLUMNS = ('source', 'object', 'model_index', 'subset', 'frequency', 'reason')


# =====================================================================================
# the pass: a row -> its fit -> its records -> fits.csv
# =====================================================================================
class Fitter:
    """The fits of a registry's rows with a fitted response type, a directory each under `dir`."""

    def __init__(self, root: Path, survey: Path, loader: Loader, dir: Path) -> None:
        self.root = root
        self.loader = loader
        self.dir = dir
        self.sources = readFrame(root).sources
        rows = registry.rows(root / 'registry.csv')
        self.rows = [row for row in rows if row.response_type in RESPONSE_TYPES]
        self.preparations = {}
        for preparation in readCsv(survey / 'fits_preparation.csv').to_dict('records'):
            id = f'{preparation["source"]}/{preparation["object"]}/{preparation["model_index"]}'
            self.preparations[id] = preparation

    def run(self, index: int) -> None:
        """Fits the row at `index` among the rows fitted, replacing an earlier run of it."""
        row = self.rows[index]
        dir = self.findDir(row)
        if dir.exists():  # no file of an earlier run stays beside this run's records
            shutil.rmtree(dir)
        dir.mkdir(parents=True)
        loaded = self.loader.load(self.sources[row.source], row.object, row.types)
        table = self.prepareTable(row, loaded)
        fitted = fit(table, row.formula, FAMILY[row.response_type][0], dir, TIMEOUT)
        records = measure(row, fitted, table)
        (dir / 'records.json').write_text(json.dumps(records, indent=2))

    def prepareTable(self, row: Row, table: pd.DataFrame) -> pd.DataFrame:
        """The rows the source fitted: its subset, each row repeated by its frequency weight."""
        preparation = self.preparations.get(row.id)
        if preparation is None:
            return table
        if preparation['subset']:
            table = table.query(preparation['subset'])
        if preparation['frequency']:
            repeats = table[preparation['frequency']].astype(int)
            table = table.loc[table.index.repeat(repeats)]
        return table.reset_index(drop=True)

    def collect(self) -> None:
        """Writes every row's records into fits.csv; raises where a row was never run."""
        fits = []
        for row in self.rows:
            fits += json.loads((self.findDir(row) / 'records.json').read_text())
        table = pd.DataFrame(fits, columns=FIT_COLUMNS)
        counts = table.astype({'n_obs': 'Int64', 'q': 'Int64'})  # a blank would make them floats
        writeCsv(counts, self.root / 'fits.csv')

    def findDir(self, row: Row) -> Path:
        """An id may hold `/`, `!` and spaces, so the directory is named by its hash."""
        digest = hashlib.sha256(row.id.encode()).hexdigest()
        return self.dir / digest[:16]


# =====================================================================================
# fits.csv: a fit -> its components -> a row per factor
# =====================================================================================
def measure(row: Row, fit: Fit, table: pd.DataFrame) -> list[dict]:
    """A row per factor of the fit (Nakagawa, Johnson and Schielzeth 2017):
    R² and the ICCs over σ²_f + Σ σ²_g + σ²_ε + σ²_d, the adjusted ICC without σ²_f.
    A fit without estimates leaves a row per registry factor, its statistics blank."""
    identity = {k: getattr(row, k) for k in IDENTITY}
    shared = {
        'status': fit.status,
        'message': fit.message,
        'seconds': None if fit.seconds is None else round(fit.seconds, 4),
        'n_obs': fit.n_obs,
        'family': FAMILY[row.response_type][0],
        'family_doc': row.family,
    }
    if fit.status not in ESTIMATED:
        return [identity | {'factor': factor} | shared for factor in row.grouping_factors]
    residual = None if fit.sigma is None else fit.sigma**2
    random = sum(fit.variances.values())
    total = fit.sigma2_fixed + random + (residual or 0) + fit.sigma2_distribution
    shared |= {
        'sigma2_fixed': round(fit.sigma2_fixed, 4),
        'sigma2_random': round(random, 4),
        'sigma2_residual': None if residual is None else round(residual, 4),
        'sigma2_distribution': round(fit.sigma2_distribution, 4),
        'sd_eta': round(fit.sd_eta, 4),
        'r2_marginal': round(fit.sigma2_fixed / total, 4),
        'r2_conditional': round((fit.sigma2_fixed + random) / total, 4),
    }
    widths = {}
    for term in fit.terms:
        widths[term.factor] = widths.get(term.factor, 0) + len(term.columns)
    fits = []
    for factor, sigma2 in fit.variances.items():
        per_factor = {
            'factor': nameFactor(factor, row, table),
            'q': widths[factor],
            'sigma2': round(sigma2, 4),
            'icc': round(sigma2 / total, 4),
            'icc_adjusted': round(sigma2 / (total - fit.sigma2_fixed), 4),
        }
        fits.append(identity | shared | per_factor)
    return fits


def nameFactor(fitted: str, row: Row, table: pd.DataFrame) -> str:
    """The registry's grouping factor that groups the rows as the fitted factor does, else the
    fitted factor's own name. lme4 names a factor by its columns, `herd:region` for
    `(1 | region/herd)`, which groups the rows as `herd` does where every herd lies in one region."""
    if not set(parts(fitted)) <= set(table.columns):  # an expression, such as `factor(year)`
        return fitted
    alike = [factor for factor in row.grouping_factors if groupsAlike(table, factor, fitted)]
    return alike[0] if alike else fitted


def groupsAlike(table: pd.DataFrame, a: str, b: str) -> bool:
    """Whether two factors split the rows that observe both into the same groups."""
    if set(parts(a)) == set(parts(b)):
        return True
    composed = withComposites(table, (a, b))
    levels = composed[[a, b]].dropna().drop_duplicates()
    return Measurer.hasOneParent(levels, a, b) and Measurer.hasOneParent(levels, b, a)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    from summarize import Summarizer  # imported here: summarize imports the measured modules

    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('run', 'collect'), help='fit one row, or collect every row into fits.csv and render the summary')
    parser.add_argument('index', type=int, nargs='?', help='the row to fit, by its 0-based index among the rows fitted')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and the census tables')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder holding fits_preparation.csv and the duplicates and dropped tables')
    parser.add_argument('--dir', type=Path, default=HERE.parent / 'fits', help='folder of the run directories')
    args = parser.parse_args()
    # fmt: on
    fitter = Fitter(args.registry, args.survey, Loader(args.registry / 'cache'), args.dir)
    if args.command == 'run':
        fitter.run(args.index)
    else:
        fitter.collect()
        Summarizer(args.registry, args.survey).flush()
