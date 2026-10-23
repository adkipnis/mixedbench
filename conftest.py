"""Skips an `lme4` test where R or lme4 is absent, in the package's tests and the survey's alike,
before its fixtures fit anything."""

from __future__ import annotations

import functools
import shutil
import subprocess

import pytest


def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker('lme4') is None:
        return
    missing = _probeLme4()
    if missing:
        pytest.skip(missing)


@functools.cache
def _probeLme4() -> str:
    """What of R and lme4 is absent, empty where both are there."""
    rscript = shutil.which('Rscript')
    if rscript is None:
        return 'no Rscript'
    probe = subprocess.run([rscript, '-e', 'library(lme4)'], capture_output=True)
    if probe.returncode != 0:
        return 'no lme4'
    return ''
