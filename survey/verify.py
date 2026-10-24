"""verify.py defines the second hand sample of suite 1.1's candidates: the draw, a batch's handoff
and the agreement table (#61).

The sample is 100 of suite 1.1's candidates not yet hand-checked, stratified by tier × `verified`.
Alex reads it at the source in four batches of 25, and his corrections reach the registry as
shards through `merge.py`. The agreement table then gives, per field, the share of rows whose
reading at draw time the merged registry still holds. The first hand sample's script and files
are at tag `survey-archive-3`.

pipeline:
---------
the registry and the candidate list
-> 100 unchecked candidates in batches of 25             draw
-> one batch as Markdown with page and download URLs      handoff
-> the share of readings that stood, per field and pool   agree

Run from the repo root:

    uv run python survey/verify.py draw
    uv run python survey/verify.py handoff --batch 1
    uv run python survey/verify.py agree
"""

from __future__ import annotations

import argparse
import csv
import posixpath
import re
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
from schema import REGISTRY
from sources import readFrame

from mixedbench.registry.row import (
    COLUMN_LIST_COLUMNS,
    TERM_COLUMNS,
    Row,
    parts,
    readCsv,
    splitList,
)

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
TIERS = ('R', 'E', 'T', 'O')  # Tier D is all `hand`: Alex read every one of its rows
VERIFIED = ('high', 'second-reading')
SAMPLE_SIZE = 100
BATCH_SIZE = 25
SEED = 1  # the first hand sample's was 0
# the fields the agreement step compares, recorded at draw time
COMPARED = ('response', 'response_type', 'trials', 'grouping_factors', 'covariates', 'interactions', 'random_slopes', 'formula', 'published_model')  # fmt: skip
SAMPLE_COLUMNS = ('source', 'object', 'model_index', 'stratum', 'batch', *COMPARED)
# the strata in the order their ties are allocated, then the agreement table's rows: the
# strata, each tier pooled, each `verified` pooled, then all
STRATA = tuple(f'{t}/{v}' for t in TIERS for v in VERIFIED)
POOLS = (*STRATA, *TIERS, *VERIFIED, 'all')
# the reading a handoff shows per row
READING = (*COMPARED, 'confidence', 'notes')
# The page of a url source, by label prefix: `sources.yaml` names only the download. `{rest}`
# is the label after the prefix. Checked by hand on 2026-10-09; a url label of the sample
# missing here stops the handoff.
PAGES = {
    'bambi_': 'https://bambinos.github.io/bambi/notebooks/',
    'stata_': 'https://www.stata-press.com/data/r18/',
    'mixedmodels_jl': 'https://osf.io/djaqb/',
    'snijders_bosker': 'https://www.stats.ox.ac.uk/~snijders/mlbook.htm',
    'goldstein_': 'https://www.bristol.ac.uk/cmm/team/hg/msm-3rd-ed/datasets.html',
    'cmm_': 'https://www.bristol.ac.uk/cmm/learning/support/datasets/',
    'rabe_hesketh': 'https://www.stata-press.com/data/mlmus4.html',
    'alda': 'https://stats.oarc.ucla.edu/other/examples/alda/',
    'zuur_mixed': 'https://www.highstat.com/index.php?view=article&id=17:mixed-effects-models-and-extensions-in-ecology-with-r&catid=18',
    'zuur_glmglmm': 'https://www.highstat.com/index.php?view=article&id=21:beginners-guide-to-glm-and-glmm-with-r&catid=18',
    'zuur_zim': 'https://www.highstat.com/index.php?view=article&id=23:beginners-guide-to-zero-inflated-models-with-r&catid=18',
    'fitzmaurice_': 'https://content.sph.harvard.edu/fitzmaur/ala2e/',
    'diggle_': 'https://www.lancaster.ac.uk/staff/diggle/APTS-data-sets/',
    'pmlb_': 'https://epistasislab.github.io/pmlb/',
    'openml_': 'https://www.openml.org/d/{rest}',
    'uci_': 'https://archive.ics.uci.edu/dataset/{rest}',
}  # fmt: skip
DOI = re.compile(r'10\.\d{4,}/\S+')  # a DOI anywhere in a deposit's link
HELP_CHARACTERS = 20_000  # a help page can hold a whole table, which would drown a handoff
HANDOFF_HEAD = """# Hand sample 2, batch {batch}

{n} rows of the second seeded hand sample (#61). Per row, open the page and the
download, find the documented model in the source and answer with bullets: `stands`, or the
corrected fields with a one-line reason. The fields: the response, its type and binomial trials;
the grouping factors; the covariates and interactions; the random slopes; the formula as
documented; published_model, whether the source fits or states this model. The help page is the
one the reader saw.
"""


# =====================================================================================
# the stratified draw, shared with the flat pass's hand sample
# =====================================================================================
def drawSample(
    population: pd.DataFrame, strata: tuple[str, ...], size: int, seed: int
) -> pd.DataFrame:
    """`size` rows of `population` in batches of `BATCH_SIZE`, in proportion to the size of each
    stratum. Each stratum takes its first rows in one permutation, so the batches mix strata."""
    quotas = _allocate(population['stratum'].value_counts().to_dict(), strata, size)
    order = np.random.default_rng(seed).permutation(len(population))
    shuffled = population.iloc[order]
    rank = shuffled.groupby('stratum').cumcount()
    picked = shuffled[rank < shuffled['stratum'].map(quotas)]
    return picked.assign(batch=np.arange(len(picked)) // BATCH_SIZE + 1)


def _allocate(sizes: dict[str, int], strata: tuple[str, ...], size: int) -> dict[str, int]:
    """`size` rows in proportion to stratum size by largest remainder (Hamilton's method), ties
    to the order of `strata`."""
    present = [s for s in strata if s in sizes]
    total = sum(sizes.values())
    quotas = {s: size * sizes[s] // total for s in present}
    remainders = {s: size * sizes[s] % total for s in present}
    left = size - sum(quotas.values())
    largest = sorted(present, key=remainders.get, reverse=True)  # stable: ties keep their order
    for stratum in largest[:left]:
        quotas[stratum] += 1
    return quotas


# =====================================================================================
# the links and help pages, shared with the flat pass's handoff
# =====================================================================================
class Links:
    """The page and the download of an object at its source's pin, to open in the browser."""

    def __init__(self, registry: Path, survey: Path) -> None:
        self.sources = readFrame(registry).sources
        deposits = readCsv(survey / 'deposit_files.csv')
        labelled = deposits[deposits['label'] != '']
        self.deposits = dict(zip(labelled['label'], labelled['link']))  # Tier D's labels

    def resolveUrls(self, label: str, object: str, file: str) -> tuple[str, str]:
        """GitHub's CRAN mirror tags every package version; base R's objects sit in the R
        source tarball under src/library/datasets."""
        source = self.sources[label]
        if source.kind == 'cran' and source.name == 'datasets':
            page = f'https://stat.ethz.ch/R-manual/R-patched/library/datasets/html/{object}.html'
            major = source.pin.split('.')[0]
            return page, f'https://cran.r-project.org/src/base/R-{major}/R-{source.pin}.tar.gz'
        if source.kind == 'cran':
            page = f'https://cran.r-project.org/package={source.name}'
            return page, f'https://github.com/cran/{source.name}/blob/{source.pin}/{quote(file)}'
        if source.kind == 'git':
            tree = f'{source.name}/tree/{source.pin}/{quote(posixpath.dirname(file))}'
            return tree, f'{source.name}/blob/{source.pin}/{quote(file)}'
        return self._resolvePage(label), source.name

    def _resolvePage(self, label: str) -> str:
        """A url source's page: a Tier D deposit's, at doi.org where its link holds a DOI, else
        the page its label's prefix names."""
        if label in self.deposits:
            link = self.deposits[label]
            doi = DOI.search(link)
            if doi is not None:
                return f'https://doi.org/{doi.group()}'
            return f'https://{link}'
        prefixes = [prefix for prefix in PAGES if label.startswith(prefix)]
        if not prefixes:
            raise KeyError(f'url source {label!r} has no page; add its prefix to PAGES')
        prefix = prefixes[0]
        return PAGES[prefix].format(rest=label.removeprefix(prefix))


def renderHelpPage(registry: Path, label: str, object: str) -> str:
    """The help page the reader saw, folded; empty where the object has none."""
    path = registry / 'help' / label / f'{object}.txt'
    if not path.exists():
        return ''
    text = path.read_text()
    if len(text) > HELP_CHARACTERS:
        text = f'{text[:HELP_CHARACTERS]}\n[cut at {HELP_CHARACTERS:,} characters]'
    return f'<details><summary>help page</summary>\n\n~~~~\n{text}\n~~~~\n\n</details>\n'


# =====================================================================================
# pipeline: registry and candidates -> draw, handoff, agree
# =====================================================================================
class Verifier:
    def __init__(self, registry: Path, candidates: Path, survey: Path) -> None:
        self.registry = registry
        self.candidates = candidates
        self.survey = survey
        self.rows = readCsv(registry / 'registry.csv').to_dict('records')

    # ---------------------------------------------------------------------------------
    # draw: candidates -> strata -> quotas -> sample
    # ---------------------------------------------------------------------------------
    def draw(self) -> None:
        """Each stratum takes its first rows in one permutation, so the batches mix strata."""
        unchecked = self._listUnchecked()
        sample = drawSample(unchecked, STRATA, SAMPLE_SIZE, SEED)[list(SAMPLE_COLUMNS)]
        sample.to_csv(self.survey / 'sample.csv', index=False, quoting=csv.QUOTE_ALL)
        print(f'draw: {len(sample)} rows of {len(unchecked)}, seed {SEED}')

    def _listUnchecked(self) -> pd.DataFrame:
        """The candidates not hand-checked yet, in registry order, each with its stratum."""
        rows = pd.DataFrame(self.rows)
        ids = pd.Series([Row.parse(cells).id for cells in self.rows], index=rows.index)
        candidate = ids.isin(readCsv(self.candidates)['id'])
        unchecked = rows[candidate & (rows['verified'] != 'hand')]
        return unchecked.assign(stratum=unchecked['tier'] + '/' + unchecked['verified'])

    # ---------------------------------------------------------------------------------
    # handoff: a batch -> its rows -> one section per row
    # ---------------------------------------------------------------------------------
    def handoff(self, batch: int) -> str:
        """One batch as Markdown for Alex's check in the browser: page and download URLs, never
        a local path."""
        rows = self._readBatch(batch)
        links = Links(self.registry, HERE)  # the survey's deposits, whichever --survey
        sections = []
        for number, row in enumerate(rows, start=1):
            sections.append(self._renderSection(number, row, links))
        return HANDOFF_HEAD.format(batch=batch, n=len(sections)) + ''.join(sections)

    def _readBatch(self, batch: int) -> list[dict]:
        """The batch's registry rows in draw order, each with its stratum and its file from the
        manifest."""
        key = list(REGISTRY.key)
        sample = readCsv(self.survey / 'sample.csv')
        drawn = sample.loc[sample['batch'] == str(batch), [*key, 'stratum']]
        manifest = readCsv(self.registry / 'manifest.csv')[['source', 'object', 'file']]
        rows = drawn.merge(pd.DataFrame(self.rows), on=key, validate='one_to_one')
        with_files = rows.merge(manifest, on=['source', 'object'], validate='many_to_one')
        return with_files.to_dict('records')

    def _renderSection(self, number: int, row: dict, links: Links) -> str:
        page, download = links.resolveUrls(row['source'], row['object'], row['file'])
        heading = (
            f'{row["source"]} · {row["object"]} · model {row["model_index"]} ({row["stratum"]})'
        )
        reading = ''.join(f'- {field}: {row[field] or "—"}\n' for field in READING)
        details = renderHelpPage(self.registry, row['source'], row['object'])
        urls = f'- page: {page}\n- download: {download} (file `{row["file"]}`)\n'
        return f'\n## {number}. {heading}\n\n{urls}{reading}\n{details}'

    # ---------------------------------------------------------------------------------
    # agree: sample and registry -> fields that stood -> shares per pool
    # ---------------------------------------------------------------------------------
    def agree(self) -> None:
        """The share of sampled rows whose reading at draw time the merged registry still holds,
        per field and pool."""
        key = list(REGISTRY.key)
        sample = readCsv(self.survey / 'sample.csv')
        registry = pd.DataFrame(self.rows)
        joined = sample.merge(
            registry, on=key, how='left', suffixes=('', '_merged'), indicator=True
        )
        kept = joined['_merge'] == 'both'  # a row the hand check took out stands in no field
        readings = joined.fillna('')
        compared = {}
        for field in COMPARED:
            compared[field] = self._compareField(
                field, readings[field], readings[f'{field}_merged']
            )
        stood = pd.DataFrame(compared).where(kept, False, axis=0)
        strata = readings['stratum']
        tiers = strata.str.partition('/')[0]
        verifications = strata.str.partition('/')[2]
        everything = pd.Series('all', index=readings.index)
        pools = [strata, tiers, verifications, everything]
        pooled = pd.concat([stood.assign(pool=pool) for pool in pools]).groupby('pool')
        table = pooled.mean().round(3)
        table.insert(0, 'rows', pooled.size())
        table = table.loc[[pool for pool in POOLS if pool in table.index]]
        table.to_csv(self.survey / 'agreement.csv', quoting=csv.QUOTE_ALL)
        print(f'agree: {len(sample)} rows')

    @staticmethod
    def _compareField(field: str, drawn: pd.Series, merged: pd.Series) -> pd.Series:
        """A reading rewritten in another order or spacing stands: `;`-lists are sets, `a:b` is
        the term `b:a`, a formula's whitespace carries no meaning."""
        if field in (*COLUMN_LIST_COLUMNS, *TERM_COLUMNS, 'random_slopes'):
            return drawn.map(Verifier._splitTerms) == merged.map(Verifier._splitTerms)
        if field == 'formula':
            spaceless = r'\s+'
            return drawn.str.replace(spaceless, '', regex=True) == merged.str.replace(
                spaceless, '', regex=True
            )
        return drawn == merged

    @staticmethod
    def _splitTerms(value: str) -> frozenset[frozenset[str]]:
        return frozenset(frozenset(parts(term)) for term in splitList(value))


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=('draw', 'handoff', 'agree'), help='the verification step to run')
    parser.add_argument('--batch', type=int, help='handoff: the batch to render')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='directory holding registry.csv and help/')
    parser.add_argument('--candidates', type=Path, default=HERE.parent / 'suite' / '1.1' / 'candidates.csv', help='the candidate list to sample')
    parser.add_argument('--survey', type=Path, default=HERE, help='directory of the sample and agreement files')
    args = parser.parse_args()
    # fmt: on
    verifier = Verifier(args.registry, args.candidates, args.survey)
    if args.step == 'draw':
        verifier.draw()
    if args.step == 'handoff':
        print(verifier.handoff(args.batch))
    if args.step == 'agree':
        verifier.agree()
