"""Skips a test that fits with R where R or its packages are absent, in the package's tests and the
survey's alike, before its fixtures fit anything."""

from __future__ import annotations

import functools
import shutil
import subprocess

import pytest

# per marker, R code that fails where its packages are absent (CI's runners have R, not cmdstanr)
PROBES = {
    'brms': 'cmdstanr::cmdstan_version()',
    'lme4': 'library(lme4); library(jsonlite); library(performance)',
}


def pytest_runtest_setup(item: pytest.Item) -> None:
    for marker in PROBES:
        if item.get_closest_marker(marker) is None:
            continue
        missing = _probe(marker)
        if missing:
            pytest.skip(missing)


@functools.cache
def _probe(marker: str) -> str:
    """What of R and the marker's packages is absent, empty where both are there."""
    rscript = shutil.which('Rscript')
    if rscript is None:
        return 'no Rscript'
    probe = subprocess.run([rscript, '-e', PROBES[marker]], capture_output=True)
    if probe.returncode != 0:
        return f'no R packages for {marker}: {PROBES[marker]} fails'
    return ''
