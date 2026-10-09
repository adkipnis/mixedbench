"""Verification of the registry's readings (spec #6). The `scan` step searches every registry
row's `notes`, `formula` and cached help page, and every deposit page a Tier D help page points
at, for the family and prior keywords and writes `scan_hits.csv` (row key or deposit page,
field, keyword, snippet) for the hand look that fills `family` and `documented_prior` (#10).
The `draw` step writes the seeded hand sample of ADR 0002 to `sample.csv`, 100 rows in four
batches of 25, each further run one more batch with the next seed; `handoff` prints one batch
as Markdown for Alex's check (#11). Run from the repo root:

    uv run python survey/verify.py scan
    uv run python survey/verify.py draw
    uv run python survey/verify.py handoff --batch 1
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
from summarise import readCsv

from mixedbench.datasets import Source

# =====================================================================================
# globals
# =====================================================================================
HERE = Path(__file__).parent
DEPOSIT_POINTER = '# deposit page: '  # a Tier D help page's first line (pull.py)
HIT_COLUMNS = ('source', 'object', 'model_index', 'field', 'keyword', 'snippet')
# Keyword -> its spellings, matched case-blind. Longer spellings come first in an alternation,
# so `glmer.nb` is one hit, not also an `nb`. "prior to" is a preposition, not a prior.
KEYWORDS = {
    'negative binomial': r'negative[\s-]+binomial|neg\.\s*bin\b\.?|negbin\w*|glmer\.nb|glm\.nb|nbinom\w*|(?-i:\bnb[12]?\b)',  # `NB` is a place code in agridat
    'probit': r'probit',  # Stata's meprobit and oprobit too
    'cloglog': r'cloglog|complementary\s+log',
    'weibull': r'\bweibull',
    'gamma': r'\bgamma\b',
    'lognormal': r'\blog[\s-]?normal',
    'zero-inflated': r'zero[\s-]*inflat\w*|zeroinfl|ziformula|\bzinb\b',
    'hurdle': r'\bhurdle',
    'beta regression': r'beta[\s-]+regression|betareg|beta_family|glmmTMB\s+beta\b|\bbeta\s+GLMM|beta[\s-]+distributed|family\s*=\s*["\']?beta\b',
    'prior': r'set_prior|\bpriors?\b(?!\s+to\b)',
    # a Stan or BUGS sampling statement: `b ~ normal(0, 1)`, `tau ~ dgamma(0.01, 0.01)`
    'distribution call': r'~\s*(?:d(?:norm|mnorm|gamma|unif|t|beta|exp|lnorm|pois|bin|bern|cat)|normal|multi_normal\w*|cauchy|student_t|exponential|inv_gamma|uniform|lkj\w*)\s*\(',
}  # fmt: skip
SNIPPET_CONTEXT = 60  # characters either side of the match
# The hand sample (ADR 0002): Tier D is left out, Alex read every one of its rows (#26).
TIERS = ('R', 'E', 'T', 'O')
CONFIDENCES = ('high', 'medium', 'low')
SAMPLE_SIZE = 100
BATCH_SIZE = 25
SEED = 0
# the fields the agreement step compares, recorded at draw time
COMPARED = ('response', 'response_type', 'trials', 'grouping_factors', 'covariates', 'interactions', 'formula', 'published_model')  # fmt: skip
SAMPLE_COLUMNS = ('source', 'object', 'model_index', 'stratum', 'seed', 'batch', *COMPARED)
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
HANDOFF_HEAD = """# Hand sample, batch {batch}

{n} rows of the seeded hand sample (ADR 0002). Per row, open the page and the download, find
the documented model in the source and answer with bullets: `stands`, or the corrected fields
with a one-line reason. The fields: the response, its type and binomial trials; the grouping
factors; the covariates and interactions; the formula as documented; published_model, whether
the source fits or states this model. The help page is the one the reader saw.
"""


# =====================================================================================
# pipeline: registry -> scan, draw, handoff
# =====================================================================================
class Verifier:
    def __init__(self, registry: Path, survey: Path) -> None:
        self.registry = registry
        self.survey = survey
        self.rows = readCsv(registry / 'registry.csv').to_dict('records')

    def scan(self) -> None:
        rowHits = [hit for row in self.rows for hit in self.rowHits(row)]
        depositHits = [hit for page in self.depositPages() for hit in self.pageHits(page)]
        frame = pd.DataFrame(rowHits + depositHits, columns=HIT_COLUMNS)
        frame.to_csv(self.survey / 'scan_hits.csv', index=False, quoting=csv.QUOTE_ALL)
        print(f'scan: {len(rowHits)} row hits, {len(depositHits)} deposit hits')

    def draw(self) -> None:
        """The first draw takes 100 rows with seed 0, each further one a batch of 25 with the next
        seed. Each stratum takes its first rows in one permutation, so the batches mix strata."""
        previous = self.previousSample()
        seed = SEED + previous['seed'].nunique()  # seeds run 0, 1, 2, ... one per draw
        size = SAMPLE_SIZE if previous.empty else BATCH_SIZE
        floor = 1 if previous.empty else 0  # the first 100 already give every stratum a row
        eligible = self.eligible(previous)
        quotas = self.allocate(eligible['stratum'].value_counts().to_dict(), size, floor)
        order = np.random.default_rng(seed).permutation(len(eligible))
        shuffled = eligible.iloc[order]
        rank = shuffled.groupby('stratum').cumcount()
        picked = shuffled[rank < shuffled['stratum'].map(quotas)]
        batch = len(previous) // BATCH_SIZE + np.arange(len(picked)) // BATCH_SIZE + 1
        drawn = picked.assign(seed=seed, batch=batch)[list(SAMPLE_COLUMNS)]
        sample = pd.concat([previous, drawn])
        sample.to_csv(self.survey / 'sample.csv', index=False, quoting=csv.QUOTE_ALL)
        print(f'draw: {len(drawn)} rows, seed {seed}')

    def handoff(self, batch: int) -> str:
        """One batch as Markdown for Alex's check in the browser: page and download URLs, never
        a local path."""
        rows = self.batchRows(batch)
        sources = readFrame(self.registry).sources
        sections = [self.section(n, row, sources[row['source']]) for n, row in enumerate(rows, start=1)]  # fmt: skip
        return HANDOFF_HEAD.format(batch=batch, n=len(sections)) + ''.join(sections)

    # ---------------------------------------------------------------------------------
    # scan
    # ---------------------------------------------------------------------------------
    def helpPage(self, row: dict) -> str:
        return (self.registry / 'help' / row['source'] / f'{row["object"]}.txt').read_text()

    def rowHits(self, row: dict) -> list[dict]:
        """A help page belongs to the object, so it is listed under each of the object's
        models: each row gets its own verdict."""
        texts = {'notes': row['notes'], 'formula': row['formula'], 'help': self.helpPage(row)}
        key = {'source': row['source'], 'object': row['object'], 'model_index': row['model_index']}  # fmt: skip
        return [key | {'field': f} | hit for f, text in texts.items() for hit in self.find(text)]

    def depositPages(self) -> list[Path]:
        """A deposit holds many objects, so its page is scanned once, not once per object."""
        pages = []
        for row in self.rows:
            first = self.helpPage(row).partition('\n')[0]
            page = self.registry.parent / first.removeprefix(DEPOSIT_POINTER)
            if first.startswith(DEPOSIT_POINTER) and page not in pages:
                pages.append(page)
        return pages

    def pageHits(self, page: Path) -> list[dict]:
        key = {'source': page.stem, 'object': '', 'model_index': '', 'field': 'deposit'}
        return [key | hit for hit in self.find(page.read_text())]

    @staticmethod
    def find(text: str) -> list[dict]:
        hits = []
        for keyword, pattern in KEYWORDS.items():
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                start = max(match.start() - SNIPPET_CONTEXT, 0)
                context = text[start : match.end() + SNIPPET_CONTEXT]
                hits.append({'keyword': keyword, 'snippet': ' '.join(context.split())})
        return hits

    # ---------------------------------------------------------------------------------
    # draw
    # ---------------------------------------------------------------------------------
    def previousSample(self) -> pd.DataFrame:
        path = self.survey / 'sample.csv'
        if path.exists():
            return readCsv(path)
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    def eligible(self, previous: pd.DataFrame) -> pd.DataFrame:
        """The rows of Tiers R, E, T and O not sampled yet, in registry order."""
        rows = pd.DataFrame(self.rows)
        key = list(REGISTRY.key)
        sampled = rows.set_index(key).index.isin(previous.set_index(key).index)
        rows = rows[rows['tier'].isin(TIERS) & ~sampled]
        return rows.assign(stratum=rows['tier'] + '/' + rows['confidence'])

    @staticmethod
    def allocate(sizes: dict[str, int], size: int, floor: int) -> dict[str, int]:
        """`size` rows in proportion to stratum size by largest remainder (Hamilton's method),
        ties to frame order; a share below `floor` is raised to it."""
        strata = [f'{t}/{c}' for t in TIERS for c in CONFIDENCES if f'{t}/{c}' in sizes]
        total = sum(sizes.values())
        quotas = {s: size * sizes[s] // total for s in strata}
        remainders = {s: size * sizes[s] % total for s in strata}
        left = size - sum(quotas.values())
        largest = sorted(strata, key=remainders.get, reverse=True)  # stable: frame order on ties
        for stratum in largest[:left]:
            quotas[stratum] += 1
        return {s: max(quota, floor) for s, quota in quotas.items()}

    # ---------------------------------------------------------------------------------
    # handoff
    # ---------------------------------------------------------------------------------
    def batchRows(self, batch: int) -> list[dict]:
        """The batch's registry rows in draw order, each with its file from the manifest."""
        sample = readCsv(self.survey / 'sample.csv')
        keys = sample.loc[sample['batch'] == str(batch), list(REGISTRY.key)]
        manifest = readCsv(self.registry / 'manifest.csv')[['source', 'object', 'file']]
        rows = keys.merge(pd.DataFrame(self.rows), on=list(REGISTRY.key), validate='one_to_one')
        with_files = rows.merge(manifest, on=['source', 'object'], validate='many_to_one')
        return with_files.to_dict('records')

    def section(self, number: int, row: dict, source: Source) -> str:
        page, download = self.urls(row, source)
        heading = f'{row["source"]} · {row["object"]} · model {row["model_index"]} ({row["tier"]}/{row["confidence"]})'
        reading = ''.join(f'- {field}: {row[field] or "—"}\n' for field in READING)
        details = f'<details><summary>help page</summary>\n\n~~~~\n{self.helpPage(row)}\n~~~~\n\n</details>\n'
        return f'\n## {number}. {heading}\n\n- page: {page}\n- download: {download} (file `{row["file"]}`)\n{reading}\n{details}'

    @staticmethod
    def urls(row: dict, source: Source) -> tuple[str, str]:
        """The source's page and the object's file at the pin. GitHub's CRAN mirror tags every
        package version; base R's objects sit in the R source tarball under
        src/library/datasets (#8)."""
        file = row['file']
        if source.kind == 'cran' and source.name == 'datasets':
            page = f'https://stat.ethz.ch/R-manual/R-patched/library/datasets/html/{row["object"]}.html'
            major = source.pin.split('.')[0]
            return page, f'https://cran.r-project.org/src/base/R-{major}/R-{source.pin}.tar.gz'
        if source.kind == 'cran':
            page = f'https://cran.r-project.org/package={source.name}'
            return page, f'https://github.com/cran/{source.name}/blob/{source.pin}/{quote(file)}'
        if source.kind == 'git':
            tree = f'{source.name}/tree/{source.pin}/{quote(posixpath.dirname(file))}'
            return tree, f'{source.name}/blob/{source.pin}/{quote(file)}'
        return Verifier.page(row['source']), source.name

    @staticmethod
    def page(label: str) -> str:
        prefixes = [prefix for prefix in PAGES if label.startswith(prefix)]
        if not prefixes:
            raise KeyError(f'url source {label!r} has no page; add its prefix to PAGES')
        prefix = prefixes[0]
        return PAGES[prefix].format(rest=label.removeprefix(prefix))


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=('scan', 'draw', 'handoff'), help='the verification step to run')
    parser.add_argument('--batch', type=int, help='handoff: the batch to render')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding registry.csv and help/')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder of the hits and sample files')
    args = parser.parse_args()
    # fmt: on
    verifier = Verifier(args.registry, args.survey)
    if args.step == 'scan':
        verifier.scan()
    if args.step == 'draw':
        verifier.draw()
    if args.step == 'handoff':
        print(verifier.handoff(args.batch))
