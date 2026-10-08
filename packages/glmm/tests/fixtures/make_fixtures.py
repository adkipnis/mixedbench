"""Builds the url and git fixtures for test_datasets.py (#16). Rerun from the repo root:
    uv run python packages/glmm/tests/fixtures/make_fixtures.py

`deposit.zip` is a data deposit: one `.csv` under `data/` and a codebook at the root.
`example-c0ffee1.tar.gz` is a GitHub archive of repository `example` at revision `c0ffee1`:
`data/` holds a `.csv` with its own README, `formats/` an Excel, JSON and Stata file and the
awkward text files met in the pull (whitespace-aligned, latin-1, padded, a banner above the
table, a data `.txt`), `stan/data/` a Stan data dict as `.json` and as `.json.zip` with its
`.info.json` in the sibling `stan/info/` (posteriordb's layout). `schools` is the csv served
from a URL without a suffix (figshare), `apnea.tsv.gz` a gzipped TSV (PMLB), `datasets.tar.gz`
a tarball of Arrow files (MixedModels.jl), `dataset_42.pq` OpenML's parquet rendering.
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
import pyarrow as pa
import pyarrow.feather

FIXTURES = Path(__file__).parent
EPOCH = datetime(2026, 1, 1, tzinfo=UTC)

CODEBOOK = 'school: one of three schools A, B, C\nscore: test score\nsize: class size\n'
SCHOOLS = 'school;score;size\nA;10.5;20\nB;12.0;25\nA;9.5;20\nC;15.0;30\nB;11.0;25\n'
README = '# example\n\nRadon measurements by county.\n'
DATA_README = 'county: county name\nlog_radon: log radon level\nfloor: 0 basement, 1 first floor\n'
RADON = 'county,log_radon,floor\nAnoka,0.8,0\nAnoka,1.1,1\nClay,1.9,0\nClay,1.6,0\nClay,2.1,1\n'
# a Stan data dict: N-length arrays are the table, an N-row matrix its numbered columns,
# J-length arrays, scalars and a 3-d array are not; `meta.json` is a dict without arrays
STAN = (
    '{"N": 5, "J": 2, "county": [1, 1, 2, 2, 2], "log_radon": [0.8, 1.1, 1.9, 1.6, 2.1],'
    ' "floor": [0, 1, 0, 0, 1], "u": [0.5, -0.3], "X": [[1, 0], [1, 1], [1, 0], [1, 0], [1, 1]],'
    ' "Z": [[[1, 2]], [[3, 4]], [[5, 6]], [[7, 8]], [[9, 0]]]}'
)
META = '{"name": "radon", "N": 5}'
INIT = '{"alpha": [0.1, 0.2], "beta": 0.5}'  # Stan initial values beside the data, no data
STAN_INFO = '{"name": "radon", "description": "Radon by county.\\n - county: county id"}'
# whitespace-aligned columns, as the ARM `.dat` files: the sniffer takes one space as the
# separator and then miscounts the fields
SCHOOLS_DAT = 'school estimate sd\nA  28  15\nB   8  10\nC  -3  16\n'
DEGREES = b'temp \xb0C,site\n1.5,A\n2.5,B\n'  # latin-1, not UTF-8
# the first lines of the PyMC examples' ice-core csv, a banner above the table: no reading
# makes a table of it (`notes.csv`, kept beside this script)
NOTES = (FIXTURES / 'notes.csv').read_bytes()
# a header separated by comma and space and values padded with spaces, as the ARM `.dat`
# files, `NA` for missing, and a byte-order mark, as one pingouin csv
PADDED = (
    '\ufeffgroup, recovered, scenario\nNN        ,0        ,Nagoya    \n'
    'NN        ,NA       ,Nagoya    \nPP        ,1        ,Tokyo     \n'
)
APNEA = 'Scorer\tSubject\ttarget\n1\t1\t3.0\n2\t1\t2.5\n1\t2\t4.0\n2\t2\t3.5\n'


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


def records() -> bytes:
    visits = pd.DataFrame({'id': [1, 2, 3, 4], 'visits': [3, 1, 4, 2]})
    return visits.to_json(orient='records').encode()


def stata() -> bytes:
    hospital = pd.Categorical(['north', 'south', 'north', 'south'], categories=['north', 'south'])
    births = pd.DataFrame({'hospital': hospital, 'weight': [3.2, 2.9, 3.5, 3.1]})
    buffer = io.BytesIO()
    labels = {'hospital': 'Hospital of birth', 'weight': 'Birth weight (kg)'}
    births.to_stata(
        buffer, write_index=False, time_stamp=EPOCH, data_label='Births', variable_labels=labels
    )
    return buffer.getvalue()


def arrow() -> bytes:
    kb07 = pd.DataFrame({'subj': ['S1', 'S1', 'S2', 'S2'], 'rt': [500, 520, 610, 590]})
    buffer = io.BytesIO()
    pyarrow.feather.write_feather(pa.Table.from_pandas(kb07, preserve_index=False), buffer)
    return buffer.getvalue()


def parquet() -> bytes:
    """OpenML serves every dataset as parquet (`dataset_<id>.pq`)."""
    pupils = pd.DataFrame({'school': ['GP', 'GP', 'MS'], 'G3': [10, 12, 8]})
    buffer = io.BytesIO()
    pupils.to_parquet(buffer, index=False)
    return buffer.getvalue()


def gzipped(data: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=EPOCH.timestamp()) as gz:
        gz.write(data)
    return buffer.getvalue()


def zipped(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    writeZip(buffer, files)
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
        'deposit/.gitattributes': b'* text=auto\n',  # a dotfile is no documentation
        'deposit/codebook.txt': CODEBOOK.encode(),
        'deposit/data/schools.csv': SCHOOLS.encode(),
    }
    writeZip(FIXTURES / 'deposit.zip', deposit)
    example = {
        'example-c0ffee1/README.md': README.encode(),
        'example-c0ffee1/.gitattributes': b'* text=auto\n',  # no documentation
        'example-c0ffee1/data/README.md': DATA_README.encode(),
        'example-c0ffee1/data/radon.csv': RADON.encode(),
        'example-c0ffee1/formats/trials.xlsx': excel(),
        'example-c0ffee1/formats/visits.json': records(),
        'example-c0ffee1/formats/births.dta': stata(),
        'example-c0ffee1/formats/schools.dat': SCHOOLS_DAT.encode(),
        'example-c0ffee1/formats/degrees.csv': DEGREES,
        'example-c0ffee1/formats/notes.csv': NOTES,
        'example-c0ffee1/formats/padded.csv': PADDED.encode(),
        'example-c0ffee1/formats/Guber1999data.txt': b'a,b\n1,2\n',  # a data file, no documentation
        'example-c0ffee1/stan/data/radon.json': STAN.encode(),
        'example-c0ffee1/stan/data/radon.json.zip': zipped({'radon.json': STAN.encode()}),
        'example-c0ffee1/stan/data/meta.json': META.encode(),
        'example-c0ffee1/stan/data/radon.init.json': INIT.encode(),
        'example-c0ffee1/stan/info/radon.info.json': STAN_INFO.encode(),
    }
    writeTarball(FIXTURES / 'example-c0ffee1.tar.gz', example)
    (FIXTURES / 'schools').write_bytes(SCHOOLS.encode())
    (FIXTURES / 'dataset_42.pq').write_bytes(parquet())
    (FIXTURES / 'apnea.tsv.gz').write_bytes(gzipped(APNEA.encode()))
    writeTarball(FIXTURES / 'datasets.tar.gz', {'kb07.arrow': arrow()})
