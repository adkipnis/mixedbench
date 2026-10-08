"""The README's loading example runs as printed (#3): it fetches lme4 from CRAN, so it is
marked network."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).parents[1] / 'README.md'


@pytest.mark.network
def test_readme_example_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    example = re.search(r'```python\n(.*?)```', README.read_text(), re.DOTALL).group(1)
    monkeypatch.chdir(tmp_path)  # the example's cache lands in the temporary directory
    exec(example, {})
