"""verify.py defines the second hand sample of suite 1.1's candidates: the draw, a batch's handoff
and the agreement table (#61).

The sample is 100 of suite 1.1's candidates not yet hand-checked, stratified by tier × `verified`.
Alex reads it at the source in four batches of 25, and his corrections reach the registry as
shards through `merge.py`. The agreement table then gives, per field, the share of rows whose
reading at draw time the merged registry still holds. The first hand sample's script and files
are at tag `survey-archive-3`.

A sample holds what its handoff shows, so a survey pass's rows and exclusions, written into a
sample of their own under `--survey`, are checked the same way before their merge (#162).

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
from schema import EXCLUSION_REASONS, REGISTRY
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
# the reading a handoff shows per registry row, and per excluded table
READING = (*COMPARED, 'confidence', 'notes')
EXCLUSION = ('reason', 'detail')
# what a pass adds per row: the `;`-list of URLs that document its design, and the reader's
# judgment call as a question to answer first
GUIDES = ('documentation', 'call')
SAMPLE_COLUMNS = ('source', 'object', 'model_index', 'stratum', 'batch', 'file', *READING, *EXCLUSION, *GUIDES)  # fmt: skip
# the strata in the order their ties are allocated, then the agreement table's rows: the
# strata, each tier pooled, each `verified` pooled, then all
STRATA = tuple(f'{t}/{v}' for t in TIERS for v in VERIFIED)
POOLS = (*STRATA, *TIERS, *VERIFIED, 'all')
# The page of a url source, by label prefix: `sources.yaml` names only the download. `{rest}`
# is the label after the prefix. Checked by hand on 2026-10-09 and 2026-11-01.
# A url label of the sample missing here stops the handoff.
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
    'osf_8rjxu': 'https://osf.io/8rjxu/',
    'osf_dha2j': 'https://osf.io/dha2j/',
    'osf_r4j2w': 'https://osf.io/r4j2w/',
    'osf_xrqae': 'https://osf.io/xrqae/',
    'mendeley_oasis_longitudinal': 'https://data.mendeley.com/datasets/tsy6rbc5d4/1',
    'census_acs_pums_2018': 'https://www.census.gov/programs-surveys/acs/microdata/documentation.2018.html',
    'bodowinter_politeness': 'https://bodowinter.com/tutorial/bw_LME_tutorial2.pdf',
    'embrace_': 'https://osf.io/d48ce/',
    'osf_confidence_': 'https://osf.io/s46pr/',
    'osf_blp': 'https://osf.io/b5sdk/',
    'osf_dlp1': 'https://osf.io/uw7t6/',
    'osf_dlp2_': 'https://osf.io/jfkvw/',
    'osf_manybabies1': 'https://osf.io/arnms/',
    'osf_manylabs1': 'https://osf.io/pqf9r/',
    'osf_manylabs3': 'https://osf.io/ct89g/',
}  # fmt: skip
# the hosts whose download names its page: a Kaggle dataset's page, a Hugging Face or raw
# GitHub file's folder at its commit
KAGGLE_DOWNLOAD = 'https://www.kaggle.com/api/v1/datasets/download/'
KAGGLE_PAGE = 'https://www.kaggle.com/datasets/'
HUGGING_FACE = 'https://huggingface.co/datasets/'
RAW_GITHUB = 'https://raw.githubusercontent.com/'
DOI = re.compile(r'10\.\d{4,}/\S+')  # a DOI anywhere in a deposit's link
HELP_CHARACTERS = 20_000  # a help page can hold a whole table, which would drown a handoff
# the host's description of a source (an OpenML, UCI or Kaggle page), fetched by a survey pass
# into the source's help directory
SOURCE_PAGE = '_source.md'
# the pull opens a deposit's help page with the local path of its deposit page, which the
# deposit's page URL replaces in a handoff
DEPOSIT_LINE = re.compile(r'^# deposit page: [^\n]*\n\n')
# a batch's handoff opens with a prompt that a checker who knows neither the survey nor the
# repository can act on
HANDOFF_HEAD = """# Grouped tables, hand check, batch {batch}

You check {n} rows of a registry of public tables with a grouping structure.
Each row is a table and the mixed model a language model read for it from the documentation,
or the reason it filed the table out of the registry.
Open each row's page, download and documentation, find the documented model or design in the
source, and check the reading field by field.

## Fields

- **response, response_type, trials:** the response column; what it holds (`continuous`,
  `binary`, `count`, `binomial`, `ordinal` or `categorical`), not the family; the trials column
  of a `binomial` response.
- **grouping_factors:** the columns whose levels index random effects, `;`-separated, `a:b`
  for a factor on two columns.
- **covariates, interactions:** the main-effect columns; the `a:b` interaction terms.
- **random_slopes:** `x|g` for a slope correlated with the intercept of `g`, `x||g` for an
  uncorrelated one; blank for intercepts only.
- **formula:** the documented model in lme4 syntax, its columns named as the table names them
  and a derived variable written as its expression (`I(age - 12)`).
- **published_model:** `yes` when the source, or a paper, package or tutorial on this table,
  fits or states this model, else `no`. A benchmark's group column documents the design, not a
  model.
- **notes:** what the reader read; `RESPONSE INFERRED:` where no documented model names the
  response.
- **reason, detail:** why an excluded table has no row ({reasons}), and what the reader saw.

These rules settle what groups:

- **Levels:** a grouping factor no documented model fits needs at least five levels sampled
  from a larger population (Harrison et al. 2018; Bolker et al. 2009). Fewer levels, or a few
  exhaustive ones (a city's boroughs, a country's regions), make a design factor.
- **Plots:** coordinates that identify one plot observed on several occasions on the same land
  group as `row:col`, even where some plots are observed once.
- **Waves:** a wave that a documented model fits as fixed, or separately per wave, groups
  nothing.
- **Wide:** grouped data stored wide, its repeated measures as columns, has no row, whether or
  not a column also groups its rows.
- **One label per group:** a factor whose groups each hold a single value of the response
  carries no random effect on it. A table grouped only by such factors has no grouping
  structure, unless another documented response varies within the groups.
- **Derived units:** a unit the source names but no column holds (a mixture built from
  ingredient amounts, a scaffold computed from a molecule's structure, a respondent known only
  by a combination of answers) is no grouping factor.
- **Several files:** a file that is a piece of the analysis table (one scenario of a capture,
  half of a national file) is read as a table of its own. A lookup or codebook table, one row
  per unit, has no grouping structure; a summary of another file is a derived or duplicated
  table.
- **Size:** a large table is read like any other and never filed `too large`.

## Per row

- **page, download:** the source at the version the reader read; the file names the table
  inside an archive.
- **documentation:** the papers, code and codebooks that state the table's design or model.
- **check first:** a question on a reading the rules above do not settle; answer it in the
  reason.
- **help page:** what the reader saw of the file, ending with the table's column types and
  first rows.
- **source documentation:** the host's description of the dataset, as the reader saw it.

Both pages are cut at {characters:,} characters.

## Answer

One bullet per row in this order, then one per documented model a table's rows miss, nothing
else:

- `<n> · <source> · <object> · model <k>: stands - <the source's model in one line>`
- `<n> · <source> · <object> · model <k>: <field> <corrected value>; ... - <the reason>`
- `<n> · <source> · <object> · model <k>: no grouping, flat or wide - <the reason>`
- `<n> · <source> · <object> · new model: <response>; <grouping_factors>; <formula> - <where the source states it>`
- `<n> · <source> · <object> · excluded: stands - <why the reason holds>`
- `<n> · <source> · <object> · excluded: grouped <response>; <grouping_factors>; <formula> - <the documentation>`
- `<n> · <source> · <object> · excluded: <another reason> - <why>`

Take the evidence from the source, not from the reading or its notes alone.
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
        return self._resolvePage(label, source.name), source.name

    def _resolvePage(self, label: str, download: str) -> str:
        """A url source's page: a Tier D deposit's, at doi.org where its link holds a DOI; the
        page a host's download names; else the page its label's prefix names."""
        if label in self.deposits:
            link = self.deposits[label]
            doi = DOI.search(link)
            if doi is not None:
                return f'https://doi.org/{doi.group()}'
            return f'https://{link}'
        if download.startswith(KAGGLE_DOWNLOAD):
            return KAGGLE_PAGE + download.removeprefix(KAGGLE_DOWNLOAD)
        if download.startswith(HUGGING_FACE):
            return posixpath.dirname(download.replace('/resolve/', '/tree/', 1))
        if download.startswith(RAW_GITHUB):
            owner, repository, commit, path = download.removeprefix(RAW_GITHUB).split('/', 3)
            return (
                f'https://github.com/{owner}/{repository}/tree/{commit}/{posixpath.dirname(path)}'
            )
        prefixes = [prefix for prefix in PAGES if label.startswith(prefix)]
        if not prefixes:
            raise KeyError(f'url source {label!r} has no page; add its prefix to PAGES')
        prefix = max(prefixes, key=len)  # the longest, should two prefixes match
        return PAGES[prefix].format(rest=label.removeprefix(prefix))


def renderHelpPage(registry: Path, label: str, object: str) -> str:
    """The help page the reader saw, folded."""
    path = registry / 'help' / label / f'{object}.txt'
    text = DEPOSIT_LINE.sub('', path.read_text(), count=1)
    return _foldPage('help page', text)


def _foldPage(summary: str, text: str) -> str:
    if len(text) > HELP_CHARACTERS:
        text = f'{text[:HELP_CHARACTERS]}\n[cut at {HELP_CHARACTERS:,} characters]'
    return f'<details><summary>{summary}</summary>\n\n~~~~\n{text}\n~~~~\n\n</details>\n'


def renderSourcePage(registry: Path, label: str) -> str:
    """The host's description of the source, folded, or nothing where no pass fetched one."""
    path = registry / 'help' / label / SOURCE_PAGE
    if not path.exists():
        return ''
    return _foldPage('source documentation', path.read_text())


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
        """sample.csv: `SAMPLE_SIZE` unchecked candidates over tier × `verified`, each with its
        file from the manifest."""
        unchecked = self._listUnchecked()
        drawn = drawSample(unchecked, STRATA, SAMPLE_SIZE, SEED)
        manifest = readCsv(self.registry / 'manifest.csv')[['source', 'object', 'file']]
        with_files = drawn.merge(manifest, on=['source', 'object'], validate='many_to_one')
        sample = with_files.reindex(columns=SAMPLE_COLUMNS, fill_value='')  # no exclusions
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
        sample = readCsv(self.survey / 'sample.csv')
        rows = sample[sample['batch'] == str(batch)].to_dict('records')
        links = Links(self.registry, HERE)  # the survey's deposits, whichever --survey
        sections = []
        for number, row in enumerate(rows, start=1):
            sections.append(self._renderSection(number, row, links))
        reasons = ', '.join(f'`{reason}`' for reason in EXCLUSION_REASONS)
        head = HANDOFF_HEAD.format(
            batch=batch, n=len(sections), reasons=reasons, characters=HELP_CHARACTERS
        )
        return head + ''.join(sections)

    def _renderSection(self, number: int, row: dict, links: Links) -> str:
        page, download = links.resolveUrls(row['source'], row['object'], row['file'])
        if row['reason']:
            filing = 'excluded'
            fields = EXCLUSION
        else:
            filing = f'model {row["model_index"]}'
            fields = READING
        heading = f'{row["source"]} · {row["object"]} · {filing} ({row["stratum"]})'
        pointers = f'- page: {page}\n- download: {download} (file `{row["file"]}`)\n'
        if row['documentation']:
            documents = ''.join(f'  - {url}\n' for url in splitList(row['documentation']))
            pointers += f'- documentation:\n{documents}'
        if row['call']:
            pointers += f'- check first: {row["call"]}\n'
        reading = ''.join(f'- {field}: {row[field] or "-"}\n' for field in fields)
        help_page = renderHelpPage(self.registry, row['source'], row['object'])
        details = help_page + renderSourcePage(self.registry, row['source'])
        return f'\n## {number}. {heading}\n\n{pointers}{reading}\n{details}'

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
