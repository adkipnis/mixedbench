"""The registry accessor (#3): the only way the package and metabeta read the registry files,
in the editable install and in the wheel alike."""

from __future__ import annotations

import tomllib
import typing
from pathlib import Path

import pandas as pd
import pytest
import yaml
from mixedbench import registry
from mixedbench.registry.installed import Preparations
from mixedbench.registry.row import COLUMNS, readCsv

from .conftest import installedRow

FILES = typing.get_args(registry.RegistryFile)
# the top-level keys metabeta's contract test asserts (packages/glmm/tests/surveys/)
QUANTILES_KEYS = {
    'n_rows',
    'n_objects',
    'n_factor_rows',
    'axes',
    'imbalance',
    'shares',
    'k_distribution',
    'implied_columns',
}


def registryRows() -> pd.DataFrame:
    return readCsv(registry.path('registry.csv'))


def test_the_directory_holds_exactly_the_registry_files() -> None:
    """cache/ and help/ beside the files in the repository never reach the package."""
    entries = list(registry.path().iterdir())
    assert sorted(p.name for p in entries) == sorted(FILES)
    assert all(p.is_file() for p in entries)


def test_the_literal_names_every_file_of_the_repositorys_registry_folder() -> None:
    """A file a survey pass writes into registry/ reaches the package only through the literal,
    so a new one (the flat sample's, #115) cannot be left out; cache/ and help/ are folders."""
    written = [p.name for p in Path('registry').iterdir() if p.is_file()]
    assert sorted(written) == sorted(FILES)


def test_pyproject_ships_exactly_the_registry_files() -> None:
    """The wheel's force-include and the sdist's only-include name the registry files one by
    one; a file added to the literal without them would be missing from the package."""
    pyproject = tomllib.loads(Path('pyproject.toml').read_text())
    build = pyproject['tool']['hatch']['build']['targets']
    wheel = [Path(src).name for src in build['wheel']['force-include'] if src.startswith('registry/')]  # fmt: skip
    sdist = [Path(src).name for src in build['sdist']['only-include'] if src.startswith('registry/')]  # fmt: skip
    assert wheel == sdist == list(FILES)


def test_quantiles_parse_with_the_keys_metabeta_asserts() -> None:
    quantiles = yaml.safe_load(registry.path('quantiles.yaml').read_text())
    assert set(quantiles) == QUANTILES_KEYS


def test_the_installed_registry_has_the_columns_of_row_in_their_order() -> None:
    """`Row` owns the column order; the file the survey's merge wrote must agree with it, or
    `registry.rows()` could not type a single row."""
    rows = registryRows()
    assert tuple(rows.columns) == COLUMNS


def test_the_manifest_names_the_file_of_every_registry_object() -> None:
    """A user's loader fetches an object only through its manifest row (#4), so a registry
    object without one, or under a source label sources.yaml lacks, could never load."""
    rows = registryRows()
    sources = registry.sources()
    manifest = registry.manifest()
    keys = {(sources[label], name) for label, name in zip(rows['source'], rows['object'])}
    assert keys <= set(manifest)


def test_every_dryad_source_of_the_registry_has_a_mirror() -> None:
    """Dryad refuses scripted downloads, so a registry object from Dryad loads only from the
    package's mirror of its CC0 file (ADR 0003)."""
    rows = registryRows()
    sources = registry.sources()
    dryad = {label for label in rows['source'] if 'datadryad.org' in sources[label].name}
    unmirrored = {label for label in dryad if sources[label].mirror is None}
    assert dryad and not unmirrored


def test_a_url_sources_pin_is_its_checksum() -> None:
    """A URL has no version: the file's sha256 is its pin, so the loader always checks it."""
    entry = {'kind': 'url', 'name': 'https://example.org/deposit.zip', 'pin': 'ab' * 32}
    deposit = registry.source('deposit', entry)
    assert deposit.checksum == deposit.pin == 'ab' * 32


# =====================================================================================
# the rows a registry fit read
# =====================================================================================
SLEEPSTUDY = {'Subject': [308, 308], 'Days': [0, 1], 'Reaction': [249.6, 258.7]}


@pytest.mark.parametrize(
    'id, table, expected',
    [
        pytest.param(
            'rabe_hesketh/police.dta/1',
            {'precinct': [1, 1, 2, 2], 'crime': [1, 2, 1, 4], 'stops': [10, 3, 7, 1]},
            {'precinct': [1, 2], 'crime': [1, 1], 'stops': [10, 7]},
            id='the subset its source fits, the other crimes left out',
        ),
        pytest.param(
            'rabe_hesketh/twin_hay.dta/1',
            {'pair': [1, 1, 2, 2], 'h': [0, 1, 1, 1], 'freq': [3, 3, 2, 2]},
            {
                'pair': ['1:0', '1:1', '1:2', '1:0', '1:1', '1:2', '2:0', '2:1', '2:0', '2:1'],
                'h': [0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
                'freq': [3, 3, 3, 3, 3, 3, 2, 2, 2, 2],
            },
            id='a weight of a group repeating it, each copy a group of its own',
        ),
        pytest.param(
            'lme4/sleepstudy/1', SLEEPSTUDY, SLEEPSTUDY, id='no preparation, the whole table',
        ),
    ],
)  # fmt: skip
def test_a_preparation_gives_the_rows_the_source_fitted(
    id: str, table: dict, expected: dict
) -> None:
    """police.dta's documented glmer fits subset(police, crime == 1). twin_hay weights each twin
    pair's response pattern, its weight on both members: repeated alone, the rows of a pattern's
    pairs would fall into one group of 2 × weight twins."""
    row = installedRow(id)

    prepared = Preparations().prepare(row, pd.DataFrame(table))

    pd.testing.assert_frame_equal(prepared, pd.DataFrame(expected))


@pytest.mark.network
def test_tables_load_the_rows_each_fit_read(tmp_path: Path) -> None:
    """A user reproduces a row of fits.csv from the rows its fit read: police.dta's fit takes the
    225 rows of one crime (its `n_obs`), and sleepstudy's fit its whole table."""
    tables = registry.Tables(tmp_path)
    police = installedRow('rabe_hesketh/police.dta/1')
    sleepstudy = installedRow('lme4/sleepstudy/1')

    assert len(tables.loadFitted(police)) == 225
    pd.testing.assert_frame_equal(tables.loadFitted(sleepstudy), tables.load(sleepstudy))


def test_every_preparation_names_a_registry_row() -> None:
    """A preparation of a row the registry lacks, mistyped or of a row since removed, would go
    unused by `loadFitted`; the fits pass refuses it only when it runs."""
    ids = {row.id for row in registry.rows()}
    assert set(Preparations().listed) <= ids
