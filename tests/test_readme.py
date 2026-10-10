"""The README's loading examples run as printed (#3, #33), in order in one namespace, since the
problem's builds on the object's; they fetch lme4 from CRAN, so they are marked network.
Its one count is the registry's, checked offline."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]
README = ROOT / 'README.md'
QUANTILES = ROOT / 'registry' / 'quantiles.yaml'


@pytest.mark.network
def test_readme_examples_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    examples = re.findall(r'```python\n(.*?)```', README.read_text(), re.DOTALL)
    monkeypatch.chdir(tmp_path)  # the examples' cache lands in the temporary directory
    namespace = {}
    for example in examples:
        exec(example, namespace)
    assert namespace['problem'].id == 'lme4/sleepstudy/1'


def test_readme_dataset_count_is_the_registry_count() -> None:
    """The README types one count; a merge that changes the number of datasets fails here
    until the README follows."""
    typed = re.search(r'(\d+) public tabular datasets', README.read_text())
    counted = yaml.safe_load(QUANTILES.read_text())['n_objects']
    assert int(typed.group(1)) == counted
