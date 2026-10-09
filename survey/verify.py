"""Verification of the registry's readings (spec #6). The `scan` step searches every registry
row's `notes`, `formula` and cached help page, and every deposit page a Tier D help page points
at, for the family and prior keywords and writes `scan_hits.csv` (row key or deposit page,
field, keyword, snippet) for the hand look that fills `family` and `documented_prior` (#10).
Run from the repo root:

    uv run python survey/verify.py scan
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd
from summarise import readCsv

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


# =====================================================================================
# pipeline: registry -> scan
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


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=('scan',), help='the verification step to run')
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding registry.csv and help/')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder the hits file is written to')
    args = parser.parse_args()
    # fmt: on
    verifier = Verifier(args.registry, args.survey)
    if args.step == 'scan':
        verifier.scan()
