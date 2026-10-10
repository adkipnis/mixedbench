"""The README's loading examples run as printed (#3, #33), in order in one namespace, since the
problem's builds on the object's; they fetch lme4 from CRAN, so they are marked network."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).parents[1] / 'README.md'


@pytest.mark.network
def test_readme_examples_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    examples = re.findall(r'```python\n(.*?)```', README.read_text(), re.DOTALL)
    monkeypatch.chdir(tmp_path)  # the examples' cache lands in the temporary directory
    namespace = {}
    for example in examples:
        exec(example, namespace)
    assert namespace['problem'].id == 'lme4/sleepstudy/1'
