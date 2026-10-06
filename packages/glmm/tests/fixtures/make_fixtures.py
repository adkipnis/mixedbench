"""Builds the url and git fixtures for test_datasets.py (#16). Rerun from the repo root:
    uv run python packages/glmm/tests/fixtures/make_fixtures.py

`deposit.zip` is a data deposit: one `.csv` under `data/` and a codebook at the root.
`example-c0ffee1.tar.gz` is a GitHub archive of repository `example` at revision `c0ffee1`:
`data/` holds a `.csv` with its own README, `formats/` one Excel, JSON and Stata file each.
Timestamps are fixed so that rebuilding changes no bytes.
"""

from __future__ import annotations

import gzip
import io
import re
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

FIXTURES = Path(__file__).parent
EPOCH = datetime(2026, 1, 1, tzinfo=UTC)

CODEBOOK = 'school: one of three schools A, B, C\nscore: test score\nsize: class size\n'
SCHOOLS = 'school;score;size\nA;10.5;20\nB;12.0;25\nA;9.5;20\nC;15.0;30\nB;11.0;25\n'
README = '# example\n\nRadon measurements by county.\n'
DATA_README = 'county: county name\nlog_radon: log radon level\nfloor: 0 basement, 1 first floor\n'
RADON = 'county,log_radon,floor\nAnoka,0.8,0\nAnoka,1.1,1\nClay,1.9,0\nClay,1.6,0\nClay,2.1,1\n'


def excel() -> bytes:
    trials = pd.DataFrame({'arm': ['control', 'treated', 'control'], 'outcome': [0, 1, 1]})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        trials.to_excel(writer, index=False)
        writer.book.properties.created = EPOCH
    # an .xlsx is a zip; openpyxl dates its members and the `modified` property at save time
    with zipfile.ZipFile(buffer) as workbook:
        members = {info.filename: workbook.read(info) for info in workbook.infolist()}
    modified = re.compile(rb'<dcterms:modified[^>]*>[^<]*</dcterms:modified>')
    stamp = (
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{EPOCH:%Y-%m-%dT%H:%M:%SZ}</dcterms:modified>'
    )
    members['docProps/core.xml'] = modified.sub(stamp.encode(), members['docProps/core.xml'])
    dated = io.BytesIO()
    writeZip(dated, members)
    return dated.getvalue()


def json() -> bytes:
    visits = pd.DataFrame({'id': [1, 2, 3, 4], 'visits': [3, 1, 4, 2]})
    return visits.to_json(orient='records').encode()


def stata() -> bytes:
    hospital = pd.Categorical(['north', 'south', 'north', 'south'], categories=['north', 'south'])
    births = pd.DataFrame({'hospital': hospital, 'weight': [3.2, 2.9, 3.5, 3.1]})
    buffer = io.BytesIO()
    births.to_stata(buffer, write_index=False, time_stamp=EPOCH)
    return buffer.getvalue()


def writeZip(out: Path | io.BytesIO, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=EPOCH.timetuple()[:6])
            archive.writestr(info, data)


def writeTarball(out: Path, files: dict[str, bytes]) -> None:
    gz = gzip.GzipFile(out, 'wb', mtime=EPOCH.timestamp())  # the gzip header dates the file too
    with gz, tarfile.open(fileobj=gz, mode='w') as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = int(EPOCH.timestamp())
            archive.addfile(info, io.BytesIO(data))


if __name__ == '__main__':
    deposit = {
        'deposit/codebook.txt': CODEBOOK.encode(),
        'deposit/data/schools.csv': SCHOOLS.encode(),
    }
    writeZip(FIXTURES / 'deposit.zip', deposit)
    example = {
        'example-c0ffee1/README.md': README.encode(),
        'example-c0ffee1/data/README.md': DATA_README.encode(),
        'example-c0ffee1/data/radon.csv': RADON.encode(),
        'example-c0ffee1/formats/trials.xlsx': excel(),
        'example-c0ffee1/formats/visits.json': json(),
        'example-c0ffee1/formats/births.dta': stata(),
    }
    writeTarball(FIXTURES / 'example-c0ffee1.tar.gz', example)
