"""Tier D of the frame: every deposit of `deposits.csv` resolved through its repository's API
(Dryad, Zenodo, figshare, OSF), its files listed in `deposit_files.csv`, the data and
documentation files fetched once into the cache and pinned, one deposit page per deposit under
`help/deposits/` for the reading agents, and the Tier D block of `sources.yaml` rewritten.

The practice survey's rules apply: each location is tried once by script, the run stops at a
bot wall, nobody solves a CAPTCHA. A `?view_only=` key the paper prints is part of the
location and travels along. Every API answer is cached under the untracked `cache/deposits/`,
so rerunning the listing fetches nothing. Without `--fetch` only the listing runs, so that the
sizes and formats of a tier are known before a byte of data is pulled; with it the kept files
land under `cache/url/<sha256>/<name>` where the loader looks for a `url` source, the
repository's own checksum is checked, and `sources.yaml` gets one entry per data file,
labelled `<paper_id>_<repository>` and `_2`, `_3` for a paper's further files of that
repository (decided 2026-10-08). Run from the repo root:

    uv run python packages/glmm/surveys/dimensions/resolve.py [--fetch]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from mixedbench.datasets import docs
from mixedbench.datasets.readers import R_FILES, TABLE_FILES

HERE = Path(__file__).parent
DRYAD = 'https://datadryad.org/api/v2'
ZENODO = 'https://zenodo.org/api/records'
FIGSHARE = 'https://api.figshare.com/v2/articles'
OSF = 'https://api.osf.io/v2'
PAUSE = 0.2  # seconds between API calls
MAX_DATA_BYTES = 50_000_000  # beyond this the listing held only posterior draws, fitted models and simulation output (2026-10-08)
MAX_DOC_BYTES = 20_000_000  # a codebook PDF beyond this is left out of the page
MAX_SCRIPT_CHARS = 40_000  # of each analysis script rendered on the deposit page
MAX_DOC_CHARS = 40_000  # of each codebook or README rendered on the deposit page
MAX_PAGE_CHARS = 250_000  # of a deposit page; further documentation is only named
ARCHIVES = {'.zip', '.tar.gz', '.tgz', '.tar', '.gz'}
DOC_SUFFIXES = {'.md', '.rst', '.pdf', '.docx', '.rtf', '.html', '.htm'}
SCRIPT_SUFFIXES = {
    '.r',
    '.rmd',
    '.qmd',
    '.py',
    '.ipynb',
    '.do',
    '.sps',
    '.sas',
    '.jl',
    '.m',
    '.stan',
}
PRACTICE_FIELDS = (
    'model_index', 'family', 'link', 'outcome_type', 'formula_verbatim', 'n_grouping_factors',
    'grouping_relation', 'n_obs', 'n_groups_per_factor', 'quote_model', 'notes',
)  # fmt: skip
COLUMNS = (
    'paper_id', 'stratum', 'repository', 'link', 'deposit', 'kind', 'status', 'title', 'licence',
    'file', 'size', 'checksum', 'url', 'role', 'label', 'pin', 'reason',
)  # fmt: skip


@dataclass
class File:
    path: str  # inside the deposit: `<component>/<folder>/<name>` on OSF
    size: int
    checksum: str  # `md5:<hex>` or `sha256:<hex>` as the repository states it, '' when none
    url: str  # the download
    role: str  # data / documentation / script / other
    label: str = ''  # the `sources.yaml` label of a data file
    pin: str = ''  # sha256 of the fetched file
    reason: str = ''  # why the file was not fetched


@dataclass
class Deposit:
    paper_id: str
    stratum: str
    repository: str
    link: str  # as `deposits.csv` names it
    context: str  # the paper's text around the link
    id: str = ''  # canonical: Dryad DOI, Zenodo record, figshare article, OSF guid
    kind: str = ''  # dataset / project / registration / file / preprint / article
    status: str = ''  # ok / not found / restricted / no files / bot wall / unresolved
    title: str = ''
    licence: str = ''
    description: str = ''
    files: list[File] = field(default_factory=list)


def role(path: str) -> str:
    """What a deposit file is for the survey, by its name: a table or archive the loader reads
    is `data`, a README or codebook `documentation`, an analysis script `script`."""
    file = Path(path)
    suffix = file.suffix.lower()
    if suffix in DOC_SUFFIXES or (suffix in ('.txt', '') and docs.isDoc(file)):
        return 'documentation'
    if suffix in SCRIPT_SUFFIXES:
        return 'script'
    bare = file.name.lower().removesuffix('.zip').removesuffix('.gz')
    if suffix in ARCHIVES or Path(bare).suffix in TABLE_FILES | R_FILES:
        return 'data'
    return 'other'


def stripHtml(text: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))


# =====================================================================================
# resolver
# =====================================================================================
class Resolver:
    def __init__(self, root: Path, practice: Path) -> None:
        self.root, self.practice = root, practice
        self.cache = root / 'cache' / 'deposits'
        self.deposits: list[Deposit] = []
        self.seen: set[str] = (
            set()
        )  # canonical ids, so a paper's two links to one deposit list once
        self.viewOnly = ''  # the `?view_only=` key of the OSF deposit being resolved
        self.ingested: dict[str, bytes] = {}  # md5 -> bytes of a file downloaded by hand

    def readDeposits(self) -> None:
        """One `Deposit` per link of `deposits.csv`, in file order."""
        with (self.root / 'deposits.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                links = row['url'].split(';')
                repositories = row['repository'].split(';')
                contexts = row['context'].split(' || ')
                for repository, link, context in zip(repositories, links, contexts):
                    self.deposits.append(
                        Deposit(row['paper_id'], row['stratum'], repository, link, context)
                    )

    def resolve(self) -> None:
        """Every deposit through its repository's API; a repeated deposit (a figshare private
        link beside its DOI) is listed once."""
        for deposit in self.deposits:
            self._resolve(deposit)
            if deposit.id in self.seen and deposit.status == 'ok':
                deposit.status = 'repeated'
                deposit.files = []
            self.seen.add(deposit.id)
            print(
                f'{deposit.paper_id} {deposit.repository} {deposit.link}: {deposit.status}, {len(deposit.files)} files'
            )

    def label(self) -> None:
        """The `sources.yaml` labels of the data files: `<paper_id>_<repository>`, then `_2`,
        `_3` over the paper's further data files of that repository in listing order."""
        counts: dict[tuple[str, str], int] = {}
        for deposit in self.deposits:
            for file in deposit.files:
                if file.role != 'data':
                    continue
                if file.size > MAX_DATA_BYTES:
                    file.reason = 'too large'
                    continue
                if any(part.startswith('.') for part in Path(file.path).parts):
                    file.reason = 'hidden path'  # RStudio's `.Rproj.user` notebook chunks
                    continue
                key = (deposit.paper_id, deposit.repository)
                counts[key] = counts.get(key, 0) + 1
                file.label = f'{deposit.paper_id}_{deposit.repository}'
                if counts[key] > 1:
                    file.label += f'_{counts[key]}'

    def ingest(self, dir: Path) -> None:
        """Files Alex downloaded through the browser (Dryad refuses the script), by the md5 the
        repository reported: every file under `dir` and every member of a zip there."""
        self.ingested = {}
        for path in sorted(dir.rglob('*')):
            if path.is_file() and path.suffix.lower() != '.zip':
                self._remember_ingested(path.read_bytes())
            elif path.is_file():
                with zipfile.ZipFile(path) as z:
                    for member in z.namelist():
                        self._remember_ingested(z.read(member))
        print(f'{len(self.ingested)} files ingested from {dir}')

    def _remember_ingested(self, data: bytes) -> None:
        """Under both digests the repositories report (Dryad: md5 for older datasets, sha-256
        for newer ones)."""
        self.ingested[hashlib.md5(data).hexdigest()] = data
        self.ingested[hashlib.sha256(data).hexdigest()] = data

    def fetch(self) -> None:
        """The labelled data files and the documentation into the cache, each once, checked
        against the repository's checksum; then one page per deposit and the Tier D block."""
        for deposit in self.deposits:
            for file in deposit.files:
                self._fetchFile(deposit, file)
        self.writePages()
        self.writeSources()

    def writePages(self) -> None:
        """`help/deposits/<paper_id>_<repository>_<id>.txt`: what the reading agent gets above
        each object of the deposit, the paper's filed models included."""
        dir = self.root / 'help' / 'deposits'
        dir.mkdir(parents=True, exist_ok=True)
        for deposit in self.deposits:
            if deposit.status != 'ok':
                continue
            (dir / f'{pageName(deposit)}.txt').write_text(self._page(deposit))

    def writeSources(self) -> None:
        """The Tier D block of `sources.yaml` replaced whole, one `url` entry per fetched data
        file; the rest of the file untouched."""
        lines = ['  D:  # the deposits of `deposits.csv`, written by resolve.py (#26)']
        for deposit in self.deposits:
            for file in deposit.files:
                if file.label and file.pin:
                    lines.append(self._entry(deposit, file))
        text = (self.root / 'sources.yaml').read_text()
        pattern = re.compile(r'^  D:.*?(?=^  O:)', re.MULTILINE | re.DOTALL)
        assert pattern.search(text), 'sources.yaml has no `D:` block before `O:`'
        text = pattern.sub('\n'.join(lines) + '\n', text)
        (self.root / 'sources.yaml').write_text(text)

    def flush(self) -> None:
        """`deposit_files.csv` whole: one row per file of every resolved deposit, one row for
        a deposit without files, in `deposits.csv` order."""
        rows = []
        for deposit in self.deposits:
            head = {
                'paper_id': deposit.paper_id, 'stratum': deposit.stratum,
                'repository': deposit.repository, 'link': deposit.link, 'deposit': deposit.id,
                'kind': deposit.kind, 'status': deposit.status, 'title': deposit.title,
                'licence': deposit.licence,
            }  # fmt: skip
            if not deposit.files:
                rows.append(head)
            for file in deposit.files:
                rows.append({
                    **head, 'file': file.path, 'size': file.size, 'checksum': file.checksum,
                    'url': file.url, 'role': file.role, 'label': file.label, 'pin': file.pin,
                    'reason': file.reason,
                })  # fmt: skip
        with (self.root / 'deposit_files.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, COLUMNS, quoting=csv.QUOTE_ALL, restval='')
            writer.writeheader()
            writer.writerows(rows)
        statuses = {}
        for deposit in self.deposits:
            statuses[deposit.status] = statuses.get(deposit.status, 0) + 1
        print(f'{len(self.deposits)} links, status {statuses}')

    # ---------------------------------------------------------------------------------
    # pipeline: link -> api -> deposit and files -> cache -> page -> yaml
    # ---------------------------------------------------------------------------------

    def _resolve(self, deposit: Deposit) -> None:
        resolvers = {
            'dryad': self._dryad, 'zenodo': self._zenodo, 'figshare': self._figshare, 'osf': self._osf,
        }  # fmt: skip
        try:
            resolvers[deposit.repository](deposit)
        except urllib.error.HTTPError as e:
            deposit.status = {
                401: 'restricted',
                403: 'restricted',
                404: 'not found',
                410: 'not found',
            }.get(e.code, f'http {e.code}')
        except BotWall:
            deposit.status = 'bot wall'
        if deposit.status == 'ok' and not deposit.files:
            deposit.status = 'no files'

    def _dryad(self, deposit: Deposit) -> None:
        doi = urllib.parse.quote(f'doi:{deposit.link}', safe='')
        if deposit.link.startswith('datadryad.org/'):  # a landing URL names the DOI in its path
            match = re.search(
                r'doi:?(10\.5061/dryad\.[a-z0-9.]+)',
                urllib.parse.unquote(deposit.link),
                re.IGNORECASE,
            )
            if match is None:
                deposit.status = 'unresolved'
                return
            doi = urllib.parse.quote(f'doi:{match.group(1).lower()}', safe='')
        record = self._json(f'{DRYAD}/datasets/{doi}', f'dryad/{doi}')
        deposit.id = record['identifier']
        deposit.kind = 'dataset'
        deposit.title = record.get('title', '')
        deposit.licence = record.get('license', '') or 'not stated'
        deposit.description = (
            stripHtml(record.get('abstract', ''))
            + '\n'
            + stripHtml(record.get('usageNotes', '') or '')
        )
        if record.get('curationStatus') != 'Published':
            deposit.status = 'restricted'
            return
        deposit.status = 'ok'
        url = f'https://datadryad.org{record["_links"]["stash:version"]["href"]}/files'
        page = 0
        while url:
            page += 1
            listing = self._json(url, f'dryad/{doi}_files_{page}')
            for entry in listing['_embedded']['stash:files']:
                download = entry['_links'].get('stash:download', {}).get('href', '')
                deposit.files.append(File(
                    entry['path'], int(entry.get('size') or 0),
                    f'{entry.get("digestType", "").replace("-", "")}:{entry.get("digest", "")}'.strip(':'),
                    f'https://datadryad.org{download}' if download else '', role(entry['path']),
                ))  # fmt: skip
            url = listing['_links'].get('next', {}).get('href', '')
            if url:
                url = f'https://datadryad.org{url}'

    def _zenodo(self, deposit: Deposit) -> None:
        number = re.search(r'(\d+)$', deposit.link).group(1)
        record = self._json(
            f'{ZENODO}/{number}', f'zenodo/{number}'
        )  # a concept DOI resolves to the latest version
        deposit.id = f'zenodo.{record["id"]}'
        deposit.kind = record['metadata'].get('resource_type', {}).get('type', 'record')
        deposit.title = record['metadata'].get('title', '')
        deposit.licence = (record['metadata'].get('license') or {}).get('id', '') or 'not stated'
        deposit.description = stripHtml(record['metadata'].get('description', ''))
        if record['metadata'].get('access_right') != 'open':
            deposit.status = 'restricted'
            return
        deposit.status = 'ok'
        for entry in record.get('files', []):
            deposit.files.append(File(
                entry['key'], int(entry.get('size') or 0), entry.get('checksum', ''),
                entry['links']['self'], role(entry['key']),
            ))  # fmt: skip

    def _figshare(self, deposit: Deposit) -> None:
        match = re.search(r'figshare\.(\d+)', deposit.link)
        if match is None:  # a private `/s/` link without the article's DOI beside it
            deposit.status = 'unresolved'
            return
        number = match.group(1)
        record = self._json(f'{FIGSHARE}/{number}', f'figshare/{number}')
        deposit.id = f'figshare.{number}'
        deposit.kind = record.get('defined_type_name', 'article')
        deposit.title = record.get('title', '')
        deposit.licence = (record.get('license') or {}).get('name', '') or 'not stated'
        deposit.description = stripHtml(record.get('description', ''))
        deposit.status = 'ok'
        for entry in record.get('files', []):
            if entry.get('is_link_only'):
                continue
            checksum = entry.get('computed_md5') or entry.get('supplied_md5') or ''
            deposit.files.append(File(
                entry['name'], int(entry.get('size') or 0), f'md5:{checksum}' if checksum else '',
                entry['download_url'], role(entry['name']),
            ))  # fmt: skip

    def _osf(self, deposit: Deposit) -> None:
        """A guid is a project or component (walked with its folders and children), a
        registration (the same, read-only), a single file, or a preprint (its PDF)."""
        guid = deposit.link.split('/')[-1]
        self.viewOnly = ''
        match = re.search(r'view_only=([0-9a-f]+)', deposit.context)
        if match is not None:
            self.viewOnly = match.group(1)
        record = self._json(f'{OSF}/guids/{guid}/', f'osf/{guid}')['data']
        deposit.id = f'osf.{guid}'
        if record['type'] not in ('nodes', 'registrations', 'files', 'preprints'):
            deposit.kind = record['type']  # a user profile (ip_2020 cites osf.io/zyfah)
            deposit.status = 'not a deposit'
            return
        deposit.kind = {
            'nodes': 'project',
            'registrations': 'registration',
            'files': 'file',
            'preprints': 'preprint',
        }.get(record['type'], record['type'])
        attributes = record['attributes']
        deposit.title = attributes.get('title') or attributes.get('name') or ''
        deposit.description = attributes.get('description', '') or ''
        deposit.status = 'ok'
        if record['type'] == 'files':
            deposit.files.append(self._osfFile(record, ''))
            return
        if record['type'] == 'preprints':
            primary = (
                record['relationships']
                .get('primary_file', {})
                .get('links', {})
                .get('related', {})
                .get('href')
            )
            if primary:
                deposit.files.append(
                    self._osfFile(self._json(primary, f'osf/{guid}_primary')['data'], '')
                )
            return
        deposit.licence = self._osfLicence(record)
        if attributes.get('category') == 'project' and attributes.get('registration'):
            deposit.kind = 'registration'
        self._osfNode(deposit, record, '')

    def _osfNode(self, deposit: Deposit, record: dict, prefix: str) -> None:
        """The node's files from every storage provider, its wiki as documentation, then its
        child components under their titles."""
        guid = record['id']
        providers = self._osfPages(
            record['relationships']['files']['links']['related']['href'], f'osf/{guid}_providers'
        )
        for provider in providers:
            folder = provider['relationships']['files']['links']['related']['href']
            self._osfFolder(
                deposit, folder, f'osf/{guid}_{provider["attributes"]["provider"]}', prefix
            )
        wikis = (
            record['relationships'].get('wikis', {}).get('links', {}).get('related', {}).get('href')
        )
        if wikis and record['attributes'].get('wiki_enabled'):  # a disabled wiki answers 404
            for wiki in self._osfPages(wikis, f'osf/{guid}_wikis'):
                name = f'{prefix}wiki/{wiki["attributes"]["name"]}.md'
                deposit.files.append(
                    File(
                        name,
                        int(wiki['attributes'].get('size') or 0),
                        '',
                        wiki['links']['download'],
                        'documentation',
                    )
                )
        children = (
            record['relationships']
            .get('children', {})
            .get('links', {})
            .get('related', {})
            .get('href')
        )
        if not children:
            return
        for child in self._osfPages(children, f'osf/{guid}_children'):
            self._osfNode(deposit, child, f'{prefix}{child["attributes"]["title"]}/')

    def _osfFolder(self, deposit: Deposit, url: str, key: str, prefix: str) -> None:
        for entry in self._osfPages(url, key):
            if entry['attributes']['kind'] == 'folder':
                inner = entry['relationships']['files']['links']['related']['href']
                self._osfFolder(
                    deposit,
                    inner,
                    f'{key}_{entry["id"].replace("/", "_")}',
                    f'{prefix}{entry["attributes"]["name"]}/',
                )
            else:
                deposit.files.append(self._osfFile(entry, prefix))

    @staticmethod
    def _osfFile(entry: dict, prefix: str) -> File:
        attributes = entry['attributes']
        hashes = (attributes.get('extra') or {}).get('hashes') or {}
        checksum = ''
        if hashes.get('sha256'):
            checksum = f'sha256:{hashes["sha256"]}'
        elif hashes.get('md5'):
            checksum = f'md5:{hashes["md5"]}'
        path = f'{prefix}{attributes["name"]}'
        return File(
            path, int(attributes.get('size') or 0), checksum, entry['links']['download'], role(path)
        )

    def _osfLicence(self, record: dict) -> str:
        licence = record['relationships'].get('license', {}).get('data')
        if not licence:
            return 'not stated'
        answer = self._json(f'{OSF}/licenses/{licence["id"]}/', f'osf/licence_{licence["id"]}')
        return answer['data']['attributes']['name']

    def _osfPages(self, url: str, key: str) -> list[dict]:
        """Every entry of a paginated OSF listing."""
        entries = []
        page = 0
        while url:
            page += 1
            answer = self._json(url, f'{key}_{page}')
            entries.extend(answer['data'])
            url = answer['links'].get('next')
        return entries

    # ---- cache -> page -> yaml ------------------------------------------------------

    def _json(self, url: str, key: str) -> dict:
        """The cached API answer; a view-only key the paper prints is sent along."""
        file = self.cache / f'{key}.json'
        if not file.exists():
            if self.viewOnly and 'api.osf.io' in url:
                joiner = '&' if '?' in url else '?'
                url = f'{url}{joiner}view_only={self.viewOnly}'
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self._get(url))
            time.sleep(PAUSE)
        return json.loads(file.read_text())

    @staticmethod
    def _get(url: str) -> bytes:
        """One answer; a 429 waits `Retry-After` and tries again, a 5xx once; an HTML page
        where none was asked for is a bot wall."""
        req = urllib.request.Request(url, headers={'User-Agent': 'metabeta-survey'})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = r.read()
                    if 'text/html' in r.headers.get(
                        'Content-Type', ''
                    ) and not url.lower().endswith(('.html', '.htm')):
                        raise BotWall(url)
                    return data
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(int(e.headers.get('Retry-After', 30)))
                elif e.code >= 500 and attempt == 0:
                    time.sleep(5)
                else:
                    raise
        raise RuntimeError(f'{url}: still rate-limited after six attempts')

    def _fetchFile(self, deposit: Deposit, file: File) -> None:
        """A labelled data file or a documentation file into `cache/url/<sha256>/<name>`, once;
        the repository's checksum confirmed."""
        wanted = file.label or (
            file.role in ('documentation', 'script') and file.size <= MAX_DOC_BYTES
        )
        if not wanted or file.reason or not file.url:
            return
        done = self._cached(file)
        if done is not None:
            file.pin = done
            return
        algorithm, _, expected = file.checksum.partition(':')
        data = self.ingested.get(expected)
        if data is None:
            try:
                data = self._get(file.url)
            except urllib.error.HTTPError as e:
                file.reason = f'http {e.code}'
                return
            except BotWall:
                file.reason = 'bot wall'
                return
        digest = hashlib.sha256(data).hexdigest()
        if expected and hashlib.new(algorithm, data).hexdigest() != expected:
            raise ValueError(f"{deposit.id} {file.path}: {algorithm} differs from the repository's")
        out = self.root / 'cache' / 'url' / digest / Path(file.path).name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        file.pin = digest
        self._remember(file.url, digest)
        print(f'  fetched {deposit.paper_id} {file.path} ({file.size} bytes)')

    def _cached(self, file: File) -> str | None:
        """The pin of a file fetched before, from the index the fetch keeps by download URL."""
        index = self.cache / 'fetched.json'
        fetched = json.loads(index.read_text()) if index.exists() else {}
        return fetched.get(file.url)

    def _remember(self, url: str, pin: str) -> None:
        index = self.cache / 'fetched.json'
        fetched = json.loads(index.read_text()) if index.exists() else {}
        fetched[url] = pin
        index.write_text(json.dumps(fetched, indent=1))

    def _page(self, deposit: Deposit) -> str:
        """Deposit metadata, the paper's text around the link, the paper's models as the
        practice survey filed them, the file listing, then the documentation and scripts."""
        parts = [
            f'# deposit {deposit.id} ({deposit.repository} {deposit.kind}) of {deposit.paper_id}',
            f'title: {deposit.title}\nlicence: {deposit.licence}',
            f'## description\n{deposit.description.strip()}',
            f'## the paper around the link\n{deposit.context}',
            f"## the paper's models as the practice survey filed them\n{self._practiceRows(deposit.paper_id)}",
            '## files\n'
            + '\n'.join(
                f'{f.path}  {f.size} bytes  {f.role}  {f.label}  {f.reason}'.rstrip()
                for f in deposit.files
            ),
        ]
        length = sum(len(part) for part in parts)
        for file in deposit.files:
            if file.role not in ('documentation', 'script') or not file.pin:
                continue
            if length > MAX_PAGE_CHARS:  # johannes_2021b's bookdown site: 20 knitted pages
                parts.append(f'## {file.path}\n[not rendered: the page is full]')
                continue
            part = f'## {file.path}\n{self._text(file)}'
            parts.append(part)
            length += len(part)
        return '\n\n'.join(parts) + '\n'

    def _practiceRows(self, paperId: str) -> str:
        lines = []
        with (self.practice / 'papers.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                if row['paper_id'] != paperId:
                    continue
                lines.append('\n'.join(f'{k}: {row[k]}' for k in PRACTICE_FIELDS))
        return '\n\n'.join(lines)

    def _text(self, file: File) -> str:
        """A documentation file as text: PDF through pdftotext, docx through its document
        XML, everything else as it is; a script cut to its first characters."""
        path = self.root / 'cache' / 'url' / file.pin / Path(file.path).name
        suffix = path.suffix.lower()
        if suffix == '.pdf':
            text = subprocess.run(
                ['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, check=True
            ).stdout
        elif suffix == '.docx':
            with zipfile.ZipFile(path) as z:
                text = stripHtml(z.read('word/document.xml').decode('utf8', errors='replace'))
        elif suffix in ('.html', '.htm'):  # a knitted report: its scripts and styles dropped
            raw = re.sub(
                r'<(script|style)[^>]*>.*?</\1>',
                ' ',
                path.read_text(errors='replace'),
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(r'\s+\n', '\n', stripHtml(raw))
        else:
            text = path.read_text(errors='replace')
        limit = MAX_DOC_CHARS
        if file.role == 'script':
            limit = MAX_SCRIPT_CHARS
        if len(text) > limit:
            text = text[:limit] + '\n[cut]'
        return text

    @staticmethod
    def _entry(deposit: Deposit, file: File) -> str:
        name = Path(file.path).name
        fields = f'kind: url, name: {json.dumps(file.url)}, pin: {file.pin}, file: {json.dumps(name)}, licence: {json.dumps(deposit.licence)}'
        return f'    {file.label}: {{{fields}}}  # {deposit.id}: {file.path}'


class BotWall(Exception):
    pass


def pageName(deposit: Deposit) -> str:
    return f'{deposit.paper_id}_{deposit.repository}_{deposit.id.split(".")[-1].replace("/", "_")}'


def depositPages(root: Path) -> dict[str, Path]:
    """Label -> deposit page, for the pull to prepend to every Tier D help page; none
    before the listing ran."""
    pages = {}
    if not (root / 'deposit_files.csv').exists():
        return pages
    with (root / 'deposit_files.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if row['label']:
                deposit = Deposit(
                    row['paper_id'],
                    row['stratum'],
                    row['repository'],
                    row['link'],
                    '',
                    row['deposit'],
                )
                pages[row['label']] = root / 'help' / 'deposits' / f'{pageName(deposit)}.txt'
    return pages


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    # fmt: off
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, default=HERE, help='survey folder holding deposits.csv')
    parser.add_argument('--practice', type=Path, default=HERE.parent / 'practice', help='practice survey root')
    parser.add_argument('--fetch', action='store_true', help='fetch the listed files, write the pages and the sources.yaml block')
    parser.add_argument('--ingest', type=Path, help='folder of files downloaded by hand, matched by md5 before any download')
    args = parser.parse_args()
    # fmt: on
    resolver = Resolver(args.root, args.practice)
    resolver.readDeposits()
    resolver.resolve()
    resolver.label()
    if args.ingest:
        resolver.ingest(args.ingest)
    if args.fetch:
        resolver.fetch()
    resolver.flush()
