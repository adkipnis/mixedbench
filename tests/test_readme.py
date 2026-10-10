"""The README's loading examples run as printed (#3, #33), in order in one namespace, since the
problem's builds on the object's; they fetch lme4 from CRAN, so they are marked network.
Its counts block is the summary's Corpus paragraph (#52), checked offline."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
README = ROOT / 'README.md'
SUMMARY = ROOT / 'registry' / 'SUMMARY.md'


@pytest.mark.network
def test_readme_examples_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    examples = re.findall(r'```python\n(.*?)```', README.read_text(), re.DOTALL)
    monkeypatch.chdir(tmp_path)  # the examples' cache lands in the temporary directory
    namespace = {}
    for example in examples:
        exec(example, namespace)
    assert namespace['problem'].id == 'lme4/sleepstudy/1'


def test_readme_counts_block_is_the_summary_corpus_paragraph() -> None:
    """Every count in the README comes from SUMMARY.md, which merge.py rewrites with the block;
    a hand edit of the block or a README restored from an older commit fails here."""
    readme = README.read_text()
    summary = SUMMARY.read_text()
    block = re.search(r'<!-- corpus: .*? -->\n(.*?)\n<!-- /corpus -->', readme, re.DOTALL)
    corpus = re.search(r'^\*\*Corpus\.\*\*.*?(?=\n\n)', summary, re.MULTILINE | re.DOTALL)
    assert block.group(1) == corpus.group(0)
