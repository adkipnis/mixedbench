"""Tier D of the frame: the practice survey's papers that name a Dryad, OSF, Zenodo or figshare
deposit, and the seeded draw of them into `deposits.csv`.

The match is mechanical, a regex over the practice survey's `texts/<paper_id>.txt` (in
metabeta-v3), so it also catches
preregistrations and deposits the paper merely cites; the window around each match travels
along as `context`, and #26 excludes what is no data of the paper, never replacing it. One
row per drawn paper, several deposits as `;`-lists, `n_frame` the deposit-naming papers of
the stratum. The draw is `random.Random(seed).sample` over the sorted paper ids of each
stratum, so rerunning reproduces the file byte for byte. Run from the repo root:

    uv run python survey/deposits.py --practice <metabeta-v3>/packages/glmm/surveys/practice
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
COLUMNS = ['paper_id', 'stratum', 'repository', 'url', 'context', 'seed', 'n_frame']
PER_STRATUM = 15  # 60 over the practice survey's four strata
WINDOW = 80  # characters of context either side of a match

# one alternation, named by repository, so that matches arrive in text order
PATTERN = re.compile(
    r'(?P<dryad>10\.5061/dryad\.[a-z0-9.]+|datadryad\.org/[^\s)\]>"\']+)'
    r'|(?P<osf>(?:10\.17605/)?osf\.io/(?P<osf_id>[a-z0-9]{5})\b)'
    r'|(?P<zenodo>10\.5281/zenodo\.\d+|zenodo\.org/records?/\d+)'
    r'|(?P<figshare>10\.6084/m9\.figshare\.\d+(?:\.v\d+)?|figshare\.com/[^\s)\]>"\',]+)',
    re.IGNORECASE,
)
TRAILING = '.,;:)]\'"'


def normalise(match: re.Match[str]) -> tuple[str, str]:
    """The repository and one canonical identifier per deposit: the OSF five-character id,
    `zenodo.org/records/<n>` for either URL form, otherwise the match without trailing
    punctuation, DOIs in lower case."""
    repository = match.lastgroup if match.lastgroup != 'osf_id' else 'osf'
    link = match.group(repository).rstrip(TRAILING)
    if repository == 'osf':
        link = f'osf.io/{match.group("osf_id").lower()}'
    elif repository == 'zenodo':
        link = re.sub(r'zenodo\.org/record/', 'zenodo.org/records/', link, flags=re.IGNORECASE)
    if link.startswith('10.'):
        link = link.lower()
    return repository, link


def scan(text: str) -> list[tuple[str, str, str]]:
    """Every distinct deposit a text names, as (repository, link, context), in text order;
    the context is the window around the first mention, whitespace collapsed."""
    found: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in PATTERN.finditer(text):
        deposit = normalise(match)
        if deposit in seen:
            continue
        seen.add(deposit)
        window = text[max(0, match.start() - WINDOW) : match.end() + WINDOW]
        found.append((*deposit, ' '.join(window.split())))
    return found


def findDeposits(text: str) -> list[tuple[str, str]]:
    return [(repository, link) for repository, link, _ in scan(text)]


# =====================================================================================
# drawer
# =====================================================================================
class Drawer:
    def __init__(
        self, practice: Path, out: Path, perStratum: int = PER_STRATUM, seed: int = 0
    ) -> None:
        self.practice, self.out, self.perStratum, self.seed = practice, out, perStratum, seed

    def run(self) -> None:
        self.readPapers()
        self.findFrame()
        self.draw()
        self.flush()
        print(
            f'{len(self.rows)} deposits drawn from {sum(len(ids) for ids in self.frame.values())} papers'
        )
        for stratum, ids in sorted(self.frame.items()):
            print(f'  {stratum}: {len(ids)} papers name a deposit')

    # ---- papers.csv -> frame -> draw -> deposits.csv --------------------------------
    def readPapers(self) -> None:
        """Each paper once with its stratum; `papers.csv` holds one row per model."""
        self.strata: dict[str, str] = {}
        with (self.practice / 'papers.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                self.strata.setdefault(row['paper_id'], row['stratum'])

    def findFrame(self) -> None:
        self.deposits: dict[str, list[tuple[str, str, str]]] = {}
        self.frame: dict[str, list[str]] = {}
        for paperId in sorted(self.strata):
            text = (self.practice / 'texts' / f'{paperId}.txt').read_text(errors='ignore')
            found = scan(text)
            if not found:
                continue
            self.deposits[paperId] = found
            self.frame.setdefault(self.strata[paperId], []).append(paperId)

    def draw(self) -> None:
        self.rows: list[dict[str, str]] = []
        for stratum, ids in sorted(self.frame.items()):
            k = min(self.perStratum, len(ids))
            drawn = sorted(random.Random(self.seed).sample(ids, k))
            for paperId in drawn:
                self.rows.append(self.row(paperId, stratum, len(ids)))

    def row(self, paperId: str, stratum: str, nFrame: int) -> dict[str, str]:
        found = self.deposits[paperId]
        return {
            'paper_id': paperId,
            'stratum': stratum,
            'repository': ';'.join(repository for repository, _, _ in found),
            'url': ';'.join(link for _, link, _ in found),
            'context': ' || '.join(context for _, _, context in found),
            'seed': str(self.seed),
            'n_frame': str(nFrame),
        }

    def flush(self) -> None:
        with self.out.open('w', newline='') as f:
            writer = csv.DictWriter(f, COLUMNS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(self.rows)


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--practice', type=Path, required=True, help="practice survey root (metabeta-v3's packages/glmm/surveys/practice)")
    parser.add_argument('--out', type=Path, default=HERE / 'deposits.csv')
    parser.add_argument('--per-stratum', type=int, default=PER_STRATUM)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    # fmt: on
    drawer = Drawer(args.practice, args.out, args.per_stratum, args.seed)
    drawer.run()
