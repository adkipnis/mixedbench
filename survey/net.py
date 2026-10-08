"""The Tier O keyword net (#24): OpenML, UCI and PMLB searched for tables whose column names
document a clustering unit, as `nets` in `sources.yaml` says.

Every repository is enumerated through its public API and every table's column names are
matched against the keywords: a column name tokenised on case and punctuation is the keyword
alone, or the keyword with an id-like token (`SubjectID`, `patient_nbr`, `subject#`); a name
that merely contains one (`family_history`, `time_in_hospital`) is no hit. OpenML's synthetic
derivatives (`BNG(...)`, seeded resamples) are left out before the draw. Every API answer is
cached under the untracked `registry/cache/net/`, so rerunning fetches nothing. The hits over the three
repositories together are capped with a seeded draw. The script writes `survey/net_hits.csv` (every
hit, kept or not, with its description) and prints the `sources.yaml` entries of the kept hits,
pinned by the sha256 of the download, which are pasted under tier `O` by hand. Run from the
repo root:

    uv run python survey/net.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).parent
OPENML = 'https://www.openml.org/api/v1/json'
UCI = 'https://archive.ics.uci.edu/api'
PMLB = 'https://raw.githubusercontent.com/EpistasisLab/pmlb'
PMLB_MEDIA = 'https://media.githubusercontent.com/media/EpistasisLab/pmlb'  # Git LFS content
PMLB_PIN = '7c1f4bdc00136dc2e55c87fa6b8ba6e8af6d1a68'  # PMLB master on 2026-10-07, as Tier O's four
MIN_ROWS = 10
MAX_ROWS = 1_000_000  # beyond this the table is `too large` for the survey anyway
MAX_COLUMNS = 500  # image and text matrices
PAUSE = 0.1  # seconds between API calls
WORKERS = 4  # parallel fetches into the cache; eight draw 429s from OpenML
ID_TOKENS = {'id', 'ids', 'no', 'num', 'number', 'nbr', 'code', 'key', 'idx', 'index'}
HIT_COLUMNS = (
    'repository', 'id', 'name', 'version', 'n_rows', 'n_cols', 'matched', 'licence', 'url',
    'page', 'kept', 'description',
)  # fmt: skip


def tokens(column: str) -> list[str]:
    """`SchoolID` -> school, id; `subject_id` -> subject, id; `patient_nbr` -> patient, nbr."""
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', column)
    return [t for t in re.split(r'[^a-zA-Z]+', spaced.lower()) if t]


def matches(columns: list[str], keywords: list[str]) -> list[str]:
    """The columns whose name is a keyword, alone or with id-like tokens (`SubjectID`,
    `subject#`, `patient_nbr`); `family_history` is no hit."""
    hits = []
    for column in columns:
        named = [t for t in tokens(column) if t not in ID_TOKENS]
        if len(named) == 1 and named[0] in keywords:
            hits.append(column)
    return hits


# =====================================================================================
# net
# =====================================================================================
class Net:
    def __init__(self, registry: Path, survey: Path) -> None:
        self.registry, self.survey = Path(registry), Path(survey)
        frame = yaml.safe_load((self.registry / 'sources.yaml').read_text())
        self.keywords: list[str] = frame['nets']['keywords']
        self.cap: int = frame['nets']['cap']
        self.seed: int = frame['seed']
        self.cache = self.registry / 'cache' / 'net'
        self.hits: list[dict] = []
        self.unavailable: list[str] = []  # datasets whose API answer was a server error

    def searchOpenml(self) -> None:
        """Every active dataset at its lowest version, within the size bounds, its feature
        names from the features endpoint; the licence, description and parquet download from
        the description endpoint for the hits only."""
        listing = self._json(
            f'{OPENML}/data/list/status/active/limit/10000/offset/0', 'openml/list'
        )
        datasets = self._lowestVersions(listing['data']['dataset'])
        datasets = [d for d in datasets if self._inBounds(d) and not self._derived(d['name'])]
        self._prefetch(
            [
                (f'{OPENML}/data/features/{d["did"]}', f'openml/features_{d["did"]}')
                for d in datasets
            ]
        )
        for dataset in datasets:
            n_rows, n_cols = self._size(dataset)
            did = dataset['did']
            features = self._json(f'{OPENML}/data/features/{did}', f'openml/features_{did}')
            if features is None:  # the server failed on this dataset
                self.unavailable.append(f'openml:{did}')
                continue
            features = features['data_features']['feature']
            if isinstance(features, dict):  # a single feature comes unlisted
                features = [features]
            columns = [f['name'] for f in features]
            matched = matches(columns, self.keywords)
            if not matched:
                continue
            description = self._json(f'{OPENML}/data/{did}', f'openml/data_{did}')
            description = description['data_set_description']
            self.hits.append({
                'repository': 'openml',
                'id': did,
                'name': dataset['name'],
                'version': dataset['version'],
                'n_rows': int(n_rows),
                'n_cols': int(n_cols),
                'matched': ';'.join(matched),
                'licence': description.get('licence', ''),
                'url': description['parquet_url'],  # the csv endpoint 404s on newer datasets
                'page': f'https://www.openml.org/d/{did}',
                'kept': '',
                'description': description.get('description', ''),
            })  # fmt: skip

    def searchUci(self) -> None:
        """Every dataset of the catalogue, its variable names from the dataset endpoint; the
        download is the repository's csv rendering, the licence its CC BY 4.0 default."""
        listing = self._json(f'{UCI}/datasets/list', 'uci/list')
        ids = [entry['id'] for entry in listing['data']]
        self._prefetch([(f'{UCI}/dataset?id={uci_id}', f'uci/dataset_{uci_id}') for uci_id in ids])
        for uci_id in ids:
            payload = self._json(f'{UCI}/dataset?id={uci_id}', f'uci/dataset_{uci_id}')
            if payload is None:
                self.unavailable.append(f'uci:{uci_id}')
                continue
            dataset = payload.get('data')
            if dataset is None or not dataset.get('variables'):
                continue
            n_rows = dataset.get('num_instances')
            if n_rows is None or not (MIN_ROWS <= n_rows <= MAX_ROWS):
                continue
            columns = [v['name'] for v in dataset['variables']]
            matched = matches(columns, self.keywords)
            if not matched:
                continue
            variables = '\n'.join(
                f'{v["name"]} ({v["role"]}, {v["type"]}): {v.get("description") or ""}'
                for v in dataset['variables']
            )
            self.hits.append({
                'repository': 'uci',
                'id': uci_id,
                'name': dataset['name'],
                'version': '',
                'n_rows': n_rows,
                'n_cols': len(columns),
                'matched': ';'.join(matched),
                'licence': 'CC BY 4.0',  # the repository's licence for every dataset
                'url': dataset.get('data_url') or '',
                'page': dataset.get('repository_url') or '',
                'kept': '',
                'description': f'{dataset.get("abstract") or ""}\n\n{variables}',
            })  # fmt: skip

    def searchPmlb(self) -> None:
        """Every dataset of the summary table at the pinned commit, its feature names from
        `metadata.yaml`; the download is the Git LFS content at that commit."""
        summary = self._text(f'{PMLB}/{PMLB_PIN}/pmlb/all_summary_stats.tsv', 'pmlb/summary.tsv')
        rows = list(csv.DictReader(summary.splitlines(), delimiter='\t'))
        for row in rows:
            name = row['dataset']
            n_rows = int(row['n_instances'])
            if not (MIN_ROWS <= n_rows <= MAX_ROWS):
                continue
            metadata = self._text(
                f'{PMLB}/{PMLB_PIN}/datasets/{name}/metadata.yaml', f'pmlb/{name}.yaml'
            )
            columns = re.findall(r'^\s*- name: (.+)$', metadata, flags=re.MULTILINE)
            matched = matches(columns, self.keywords)
            if not matched:
                continue
            self.hits.append({
                'repository': 'pmlb',
                'id': name,
                'name': name,
                'version': PMLB_PIN[:7],
                'n_rows': n_rows,
                'n_cols': int(row['n_features']) + 1,
                'matched': ';'.join(matched),
                'licence': 'MIT',  # the repository's licence; the data's provenance varies
                'url': f'{PMLB_MEDIA}/{PMLB_PIN}/datasets/{name}/{name}.tsv.gz',
                'page': f'https://epistasislab.github.io/pmlb/profile/{name}.html',
                'kept': '',
                'description': metadata,
            })  # fmt: skip

    def draw(self) -> None:
        """The cap over the three repositories together: a seeded draw over the hits in
        repository order, all of them when they fit."""
        keys = [f'{hit["repository"]}:{hit["id"]}' for hit in self.hits]
        kept = set(keys)
        if len(keys) > self.cap:
            kept = set(random.Random(self.seed).sample(keys, self.cap))
        for key, hit in zip(keys, self.hits):
            hit['kept'] = 'yes' if key in kept else 'no'

    def flush(self) -> None:
        """The `sources.yaml` entries of the kept hits on stdout, each pinned by the sha256 of
        its download (a hit whose download is gone is marked `unavailable`), then
        `net_hits.csv` whole."""
        entries = [self._entry(hit) for hit in self.hits if hit['kept'] == 'yes']
        with open(self.survey / 'net_hits.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=HIT_COLUMNS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(self.hits)
        counts = {
            repo: sum(h['repository'] == repo for h in self.hits)
            for repo in ('openml', 'uci', 'pmlb')
        }
        kept = sum(h['kept'] == 'yes' for h in self.hits)
        print(f'# hits {counts}, kept {kept}')
        print(f'# unavailable ({len(self.unavailable)}): {", ".join(self.unavailable)}')
        print('\n'.join(entry for entry in entries if entry))

    # ---------------------------------------------------------------------------------
    # pipeline: api -> cache -> hit -> draw -> csv and yaml
    # ---------------------------------------------------------------------------------

    @staticmethod
    def _derived(name: str) -> bool:
        """OpenML's synthetic derivatives of a dataset: the Bayesian Network Generator's
        `BNG(anneal, ...)` tables and the seeded `_seed_<k>_nrows_` resamples; the original is
        in the listing itself."""
        return name.startswith('BNG(') or bool(re.search(r'_seed_\d+_nrows_', name))

    @staticmethod
    def _size(dataset: dict) -> tuple[float | None, float | None]:
        """Rows and columns from the listing's qualities; None where OpenML has not computed them."""
        qualities = {q['name']: float(q['value']) for q in dataset.get('quality', [])}
        return qualities.get('NumberOfInstances'), qualities.get('NumberOfFeatures')

    @staticmethod
    def _inBounds(dataset: dict) -> bool:
        n_rows, n_cols = Net._size(dataset)
        if n_rows is None or n_cols is None:
            return False
        return MIN_ROWS <= n_rows <= MAX_ROWS and n_cols <= MAX_COLUMNS

    def _prefetch(self, requests: list[tuple[str, str]]) -> None:
        """Fills the cache for many small API calls in parallel; the loop then reads it."""
        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(lambda r: self._text(r[0], f'{r[1]}.json'), requests))

    def _json(self, url: str, key: str) -> dict | None:
        text = self._text(url, f'{key}.json')
        if text == '':
            return None
        return json.loads(text)

    def _text(self, url: str, key: str) -> str:
        """The cached answer; a server error (OpenML answers 500 on a few datasets, twice) is
        cached as an empty file so the run goes on and the dataset is listed as unavailable."""
        file = self.cache / key
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._fetch(url))
            time.sleep(PAUSE)
        return file.read_text()

    @staticmethod
    def _fetch(url: str) -> bytes:
        """One API answer; a 429 waits `Retry-After` (else 15 s) and tries again, a 5xx is
        retried once and then recorded as an empty answer."""
        req = urllib.request.Request(url, headers={'User-Agent': 'mixedbench'})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(int(e.headers.get('Retry-After', 15)))
                elif e.code >= 500 and attempt == 0:
                    time.sleep(2)
                elif e.code >= 500:
                    return b''
                else:
                    raise
        raise RuntimeError(f'{url}: still rate-limited after six attempts')

    @staticmethod
    def _lowestVersions(datasets: list[dict]) -> list[dict]:
        """OpenML lists every version of a dataset; the lowest active one stands for it."""
        lowest: dict[str, dict] = {}
        for dataset in datasets:
            name = dataset['name']
            if name not in lowest or int(dataset['version']) < int(lowest[name]['version']):
                lowest[name] = dataset
        return sorted(lowest.values(), key=lambda d: int(d['did']))

    def _entry(self, hit: dict) -> str:
        """One `sources.yaml` line: label `<repository>_<id>`, the download pinned; '' and the
        hit marked `unavailable` when the repository no longer serves the file."""
        label = f'{hit["repository"]}_{hit["id"]}'.replace('-', '_').replace('.', '_')
        try:
            data = self._fetch(hit['url'])
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            hit['kept'] = 'unavailable'
            return ''
        digest = hashlib.sha256(data).hexdigest()
        file = ''
        if not Path(hit['url'].split('?')[0]).suffix:
            file = f', file: {hit["name"]}.csv'
        licence = json.dumps(hit['licence'])  # quoted: OpenML licences hold colons and commas
        fields = f'kind: url, name: {hit["url"]}, pin: {digest}{file}, licence: {licence}'
        return f'    {label}: {{{fields}}}  # {hit["name"]}, {hit["matched"]}'


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--registry', type=Path, default=HERE.parent / 'registry', help='folder holding sources.yaml and cache/')
    parser.add_argument('--survey', type=Path, default=HERE, help='folder of net_hits.csv')
    args = parser.parse_args()
    # fmt: on
    net = Net(args.registry, args.survey)
    net.searchOpenml()
    net.searchUci()
    net.searchPmlb()
    net.draw()
    net.flush()
