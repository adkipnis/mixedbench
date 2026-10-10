"""The help page of a data object, which the pull copies for the reading agents: what documents
the object in its source's tree (an Rd page, the text files named after it or beside it) and
the codebook a file carries itself (a Stan data dict's dropped entries, Stata and SPSS labels,
a workbook's contents sheet, a banner of `#` lines)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pyreadstat
from mixedbench.datasets import Loader, Source, readers

DOC_FILES = {'.md', '.txt', '.rst', ''}  # text beside a data file


# =====================================================================================
# help page
# =====================================================================================
class HelpPage:
    def __init__(self, loader: Loader) -> None:
        self.loader = loader

    def page(self, source: Source, name: str) -> str:
        """The Rd page of a CRAN object; otherwise the text files named after the object's stem
        in its folder or a sibling folder (posteriordb's `data/info/radon.info.json` beside
        `data/data/`), else those in the file's folder or the nearest folder above it within the
        pinned path that has any; then the file's own codebook, and in a repository that is an
        R package (rethinking, ROS's `rpackage/`) the Rd page named after the file's stem."""
        tree = self.loader.tree(source)
        if source.kind == 'cran':
            page = self._rdPage(tree / 'man', name)
            if page is None:
                raise KeyError(f'{source.name} {source.pin} has no help page for {name!r}')
            return page
        objects = {o.name: o for o in self.loader.objects(source)}
        file = tree / objects[name].file
        root = tree / (source.path or '')  # documentation is sought within the pinned path
        if root.is_file():
            root = root.parent
        found = self._sameStemDocs(tree, file) or self._docsBeside(root, file)
        pages = [
            f'# {f.relative_to(tree).as_posix()}\n{f.read_text(encoding="utf-8", errors="replace")}'
            for f in found
        ]
        pages.append(self._selfNote(file))
        for man in sorted(tree.rglob('man')):
            pages.append(self._rdPage(man, readers.bare(file).stem))
        return '\n'.join(page for page in pages if page)

    # ---------------------------------------------------------------------------------
    # pipeline: tree -> documentation files -> the file's own codebook -> Rd pages
    # ---------------------------------------------------------------------------------
    @staticmethod
    def _rdPage(man: Path, alias: str) -> str | None:
        """The raw Rd page under `man/` whose alias is `alias`, None where there is none."""
        pattern = rf'\\alias\{{{re.escape(alias)}\}}'
        for page in sorted(man.glob('*.Rd')):
            text = page.read_text(encoding='utf-8')
            if re.search(pattern, text):
                return text
        return None

    @staticmethod
    def _sameStemDocs(tree: Path, file: Path) -> list[Path]:
        stem = readers.bare(file).stem
        names = {f'{stem}{suffix}' for suffix in DOC_FILES} | {f'{stem}.info.json'}
        candidates = file.parent.parent.glob('*/*')  # the file's folder and its siblings
        if file.parent == tree:
            candidates = tree.glob('*')
        return sorted(f for f in candidates if f.is_file() and f.name.lower() in names and f != file)  # fmt: skip

    @staticmethod
    def _docsBeside(root: Path, file: Path) -> list[Path]:
        folders = [file.parent, *file.parent.parents]
        for folder in folders[: folders.index(root) + 1]:
            files = sorted(f for f in folder.iterdir() if f.is_file())
            docs = [f for f in files if readers.isDoc(f)]
            if docs:
                return docs
        return []

    @staticmethod
    def _selfNote(file: Path) -> str:
        """The codebook a file carries itself, by format; empty where the format carries none."""
        suffix = readers.bare(file).suffix
        if suffix == '.json':
            return HelpPage._stanNote(file)
        if suffix == '.dta':
            _, meta = pyreadstat.read_dta(str(file), metadataonly=True)
            return HelpPage._labels('# Stata labels', meta)
        if suffix == '.sav':
            _, meta = pyreadstat.read_sav(str(file), metadataonly=True)
            return HelpPage._labels('# SPSS labels', meta)
        if suffix in ('.xlsx', '.xls'):
            return HelpPage._workbookNotes(file)
        if suffix in ('.csv', '.tsv', '.tab', '.txt', '.dat'):
            return HelpPage._bannerNote(file)
        return ''

    @staticmethod
    def _stanNote(file: Path) -> str:
        """The entries of a Stan data dict that are no column: scalars and group-level arrays;
        and the matrices the table holds as numbered columns."""
        content = json.loads(readers.JsonFile.unwrap(file))
        if not isinstance(content, dict):
            return ''
        n = readers.JsonFile.observationLength(content)
        others, matrices = [], []
        for name, value in content.items():
            if not isinstance(value, list):
                others.append(f'{name} (scalar)')
            elif len(value) != n:
                others.append(f'{name} (length {len(value)})')
            elif readers.JsonFile.arrayDepth(value) > 2:
                shape = ' x '.join(map(str, readers.JsonFile.arrayShape(value)))
                others.append(f'{name} ({shape} array)')
            elif readers.JsonFile.arrayDepth(value) == 2:
                matrices.append(f'{name} is a {n} x {len(value[0])} matrix')
        return '; '.join([f'# not in the table: {", ".join(others)}', *matrices])

    @staticmethod
    def _labels(title: str, meta: pyreadstat.metadata_container) -> str:
        """A Stata or SPSS file's label, one line per variable with its label, then each
        variable's value labels in code order."""
        lines = [meta.file_label or '']
        for variable, label in meta.column_names_to_labels.items():
            if label is not None:  # pyreadstat lists every variable, labelled or not
                lines.append(f'{variable}: {label}')
        for variable, values in meta.variable_value_labels.items():
            ordered = ', '.join(str(values[code]) for code in sorted(values))
            lines.append(f'{variable} values: {ordered}')
        return title + '\n' + '\n'.join(lines)

    @staticmethod
    def _workbookNotes(file: Path) -> str:
        """The sheets named like documentation (`Contents`), cell by cell, tab-separated."""
        sheets = pd.read_excel(file, sheet_name=None, header=None)
        pages = []
        for name, table in sheets.items():
            if not readers.PandasFile.isNoteSheet(name):
                continue
            rows = table.fillna('').astype(str)
            lines = ['\t'.join(row).rstrip() for row in rows.itertuples(index=False)]
            pages.append(f'# sheet {name}\n' + '\n'.join(lines))
        return '\n'.join(pages)

    @staticmethod
    def _bannerNote(file: Path) -> str:
        """The `#` lines a text file opens with (Diggle's course files describe their columns
        there), which the reader skips."""
        lines, _ = readers.PandasFile.banner(file)
        if not lines:
            return ''
        return '# banner\n' + '\n'.join(lines)
