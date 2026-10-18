"""The registry accessor (#3): the only way the package and metabeta read the registry files,
in the editable install and in the wheel alike."""

from __future__ import annotations

import typing

import pandas as pd
import yaml
from mixedbench import registry
from mixedbench.registry.row import COLUMNS, readCsv

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
