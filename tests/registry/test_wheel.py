"""The built wheel installed outside the repository (#3): a benchmark user gets the loader and
the registry files without a checkout. The wheel goes into a fresh --target directory first on
PYTHONPATH; its dependencies come from the test's environment."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import typing
from pathlib import Path

import pytest
from mixedbench import registry

ROOT = Path(__file__).parents[2]
# imports both packages from the target, reports where they, the registry files and the suite's
# list resolve
REPORT = """
import json, typing
import mixedbench.datasets
from mixedbench import registry, suite
files = [registry.path(name) for name in typing.get_args(registry.RegistryFile)]
print(json.dumps({
    'datasets': mixedbench.datasets.__file__,
    'registry': registry.__file__,
    'files': [str(p) for p in files if p.is_file()],
    'suite': str(suite.path('1.1') / 'candidates.csv'),
}))
"""


@pytest.fixture(scope='module')
def installed(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    tmp = tmp_path_factory.mktemp('wheel')
    target = tmp / 'site'
    uv = shutil.which('uv')
    subprocess.run([uv, 'build', '--wheel', '--out-dir', tmp, ROOT], check=True)
    [wheel] = tmp.glob('mixedbench-*.whl')
    install = [uv, 'pip', 'install', '--no-deps', '--python', sys.executable, '--target', target]
    subprocess.run([*install, wheel], check=True)
    env = os.environ | {'PYTHONPATH': str(target)}
    run = subprocess.run(
        [sys.executable, '-P', '-c', REPORT], env=env, cwd=tmp, capture_output=True, text=True
    )
    assert run.returncode == 0, run.stderr
    return target, json.loads(run.stdout)


def test_both_packages_import_from_the_wheel(installed: tuple[Path, dict]) -> None:
    target, report = installed
    assert Path(report['datasets']).is_relative_to(target)
    assert Path(report['registry']).is_relative_to(target)


def test_the_registry_files_resolve_inside_the_install(installed: tuple[Path, dict]) -> None:
    target, report = installed
    files = typing.get_args(registry.RegistryFile)
    assert len(report['files']) == len(files)
    assert all(Path(p).is_relative_to(target) for p in report['files'])


def test_the_suites_list_resolves_inside_the_install(installed: tuple[Path, dict]) -> None:
    target, report = installed
    assert Path(report['suite']).is_file()
    assert Path(report['suite']).is_relative_to(target)


def test_the_metadata_names_both_licences(installed: tuple[Path, dict]) -> None:
    """The wheel bundles code under MIT and registry files under CC BY 4.0."""
    target, _ = installed
    distribution = installedDistribution(target)
    assert distribution.metadata['License-Expression'] == 'MIT AND CC-BY-4.0'


def test_both_licence_files_ship_in_the_wheel(installed: tuple[Path, dict]) -> None:
    target, _ = installed
    distribution = installedDistribution(target)
    licences = {file.name for file in distribution.files if 'licenses' in file.parts}
    assert licences == {'LICENSE', 'LICENSE-CC-BY-4.0'}


def test_the_reference_runners_r_script_and_lock_ship_in_the_wheel(
    installed: tuple[Path, dict],
) -> None:
    """`references.run` calls `run.R` and checks the pins in `renv.lock` from the install."""
    target, _ = installed
    references = target / 'mixedbench' / 'references'
    assert (references / 'run.R').is_file()
    assert (references / 'renv.lock').is_file()


def installedDistribution(target: Path) -> importlib.metadata.Distribution:
    [distribution] = importlib.metadata.distributions(path=[str(target)])
    return distribution
