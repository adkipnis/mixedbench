"""The built wheel installed outside the repository (#3): a benchmark user gets the loader and
the registry files without a checkout. The wheel goes into a fresh --target directory first on
PYTHONPATH; its dependencies come from the test's environment."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
# imports both packages from the target, reports where they and the registry files resolve
REPORT = """
import json, typing, yaml
import mixedbench.datasets
from mixedbench import registry
files = [registry.path(name) for name in typing.get_args(registry.RegistryFile)]
print(json.dumps({
    'datasets': mixedbench.datasets.__file__,
    'registry': registry.__file__,
    'files': [str(p) for p in files if p.is_file()],
    'quantiles': sorted(yaml.safe_load(registry.path('quantiles.yaml').read_text())),
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
    assert len(report['files']) == 8
    assert all(Path(p).is_relative_to(target) for p in report['files'])


def test_installed_quantiles_parse(installed: tuple[Path, dict]) -> None:
    _, report = installed
    assert 'n_rows' in report['quantiles'] and 'k_distribution' in report['quantiles']
