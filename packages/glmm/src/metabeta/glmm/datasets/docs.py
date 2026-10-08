"""What documents a data object: the text files named after it or beside it, a CRAN Rd page,
and the codebook a file carries itself (a Stan data dict's dropped entries, Stata and SPSS
labels, a workbook's contents sheet)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pyreadstat
from metabeta.glmm.datasets import readers

DOC_FILES = {'.md', '.txt', '.rst', ''}  # text beside a data file
DOC_STEMS = ('readme', 'codebook', 'description', 'notes', 'metadata', 'variables', 'dictionary')


def sameStemDocs(tree: Path, file: Path) -> list[Path]:
    stem = readers.bare(file).stem
    names = {f'{stem}{suffix}' for suffix in DOC_FILES} | {f'{stem}.info.json'}
    candidates = file.parent.parent.glob('*/*')  # the file's folder and its siblings
    if file.parent == tree:
        candidates = tree.glob('*')
    return sorted(f for f in candidates if f.is_file() and f.name.lower() in names and f != file)


def docsBeside(root: Path, file: Path) -> list[Path]:
    folders = [file.parent, *file.parent.parents]
    for folder in folders[: folders.index(root) + 1]:
        files = sorted(f for f in folder.iterdir() if f.is_file())
        docs = [f for f in files if isDoc(f)]
        if docs:
            return docs
    return []


def isDoc(file: Path) -> bool:
    """Markdown and reST; a `.txt` named like documentation (`codebook.txt`, not a data
    file such as the PyMC examples' `Guber1999data.txt`); a suffix-less file in capitals
    (`README`, `LICENSE`), not a dotfile or a suffix-less data file."""
    suffix = file.suffix.lower()
    if suffix in ('.md', '.rst'):
        return True
    if suffix == '.txt':
        return any(stem in file.stem.lower() for stem in DOC_STEMS)
    return suffix == '' and file.name.isupper()


def describesSibling(file: Path) -> bool:
    """A `.txt` named after a data file of another format beside it (Fitzmaurice's `lead.txt`
    beside `lead.dta`, ROS's `bypass.txt` beside `bypass.csv`) is its description, no data."""
    if file.suffix.lower() != '.txt':
        return False
    siblings = [f for f in file.parent.iterdir() if f.is_file() and f != file]
    return any(readers.bare(f).stem == file.stem.lower() for f in siblings)


# ==============================================================================================
# what a file says about itself
# ==============================================================================================


def selfNote(file: Path) -> str:
    """The codebook a file carries itself, by format; empty where the format carries none."""
    suffix = readers.bare(file).suffix
    if suffix == '.json':
        return stanNote(file)
    if suffix == '.dta':
        return stataLabels(file)
    if suffix == '.sav':
        return spssLabels(file)
    if suffix in ('.xlsx', '.xls'):
        return workbookNotes(file)
    if suffix in ('.csv', '.tsv', '.tab', '.txt', '.dat'):
        return bannerNote(file)
    return ''


def stanNote(file: Path) -> str:
    """The entries of a Stan data dict that are no column: scalars and group-level arrays;
    and the matrices the table holds as numbered columns."""
    content = json.loads(readers.unwrap(file))
    if not isinstance(content, dict):
        return ''
    n = readers.observationLength(content)
    others, matrices = [], []
    for name, value in content.items():
        if not isinstance(value, list):
            others.append(f'{name} (scalar)')
        elif len(value) != n:
            others.append(f'{name} (length {len(value)})')
        elif readers.arrayDepth(value) > 2:
            shape = ' x '.join(map(str, readers.arrayShape(value)))
            others.append(f'{name} ({shape} array)')
        elif readers.arrayDepth(value) == 2:
            matrices.append(f'{name} is a {n} x {len(value[0])} matrix')
    return '; '.join([f'# not in the table: {", ".join(others)}', *matrices])


def stataLabels(file: Path) -> str:
    """A `.dta`'s data label, one line per variable with its label, then each variable's
    value labels in code order."""
    _, meta = pyreadstat.read_dta(str(file), metadataonly=True)
    return labels('# Stata labels', meta)


def spssLabels(file: Path) -> str:
    """A `.sav`'s file label, variable labels and value labels, rendered as the Stata ones."""
    _, meta = pyreadstat.read_sav(str(file), metadataonly=True)
    return labels('# SPSS labels', meta)


def labels(title: str, meta: pyreadstat.metadata_container) -> str:
    lines = [meta.file_label or '']
    for variable, label in meta.column_names_to_labels.items():
        if label is not None:  # pyreadstat lists every variable, labelled or not
            lines.append(f'{variable}: {label}')
    for variable, values in meta.variable_value_labels.items():
        ordered = ', '.join(str(values[code]) for code in sorted(values))
        lines.append(f'{variable} values: {ordered}')
    return title + '\n' + '\n'.join(lines)


def bannerNote(file: Path) -> str:
    """The `#` lines a text file opens with (Diggle's course files describe their columns
    there), which the reader skips."""
    lines, _ = readers.banner(file)
    if not lines:
        return ''
    return '# banner\n' + '\n'.join(lines)


def workbookNotes(file: Path) -> str:
    """The sheets named like documentation (`Contents`), cell by cell, tab-separated."""
    sheets = pd.read_excel(file, sheet_name=None, header=None)
    pages = []
    for name, df in sheets.items():
        if not readers.isNoteSheet(name):
            continue
        rows = df.fillna('').astype(str)
        lines = ['\t'.join(row).rstrip() for row in rows.itertuples(index=False)]
        pages.append(f'# sheet {name}\n' + '\n'.join(lines))
    return '\n'.join(pages)


def rdPage(man: Path, alias: str) -> str | None:
    """The raw Rd page under `man/` whose alias is `alias`, None where there is none."""
    pattern = rf'\\alias\{{{re.escape(alias)}\}}'
    for page in sorted(man.glob('*.Rd')):
        text = page.read_text()
        if re.search(pattern, text):
            return text
    return None
