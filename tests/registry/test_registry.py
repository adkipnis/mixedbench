"""The registry accessor (#3): the only way the package and metabeta read the registry files,
in the editable install and in the wheel alike."""

from __future__ import annotations

import pandas as pd
import yaml
from mixedbench import registry

FILES = [
    'sources.yaml',
    'registry.csv',
    'excluded.csv',
    'dimensions.csv',
    'columns.csv',
    'quantiles.yaml',
    'SUMMARY.md',
    'manifest.csv',
]
# the normalised licences of ADR 0003, extended by #7 where CRAN's DESCRIPTIONs needed it
LICENCES = {
    'CC0-1.0',
    'CC-BY-4.0',
    'CC-BY-NC-4.0',
    'CC-BY-NC-SA-4.0',
    'ODbL-1.0',
    'GPL-2.0-or-later',
    'GPL-2.0',
    'GPL-3.0-or-later',
    'GPL-3.0',
    'AGPL-3.0',
    'MIT',
    'BSD-3-Clause',
    'public-domain',
    'other',
    'not stated',
}
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


def test_every_registry_file_resolves_to_an_existing_file() -> None:
    paths = [registry.path(name) for name in FILES]
    assert all(p.is_file() for p in paths)


def test_the_directory_holds_exactly_the_registry_files() -> None:
    """cache/ and help/ beside the files in the repository never reach the package."""
    dir = registry.path()
    assert sorted(p.name for p in dir.iterdir()) == sorted(FILES)


def test_quantiles_parse_with_the_keys_metabeta_asserts() -> None:
    quantiles = yaml.safe_load(registry.path('quantiles.yaml').read_text())
    assert set(quantiles) == QUANTILES_KEYS


def test_registry_rows_carry_family_documented_prior_and_a_licence() -> None:
    """The contract reads `family` and a later track `documented_prior` by name; the mirror
    fallback of ADR 0003 decides by `licence`, so no row may lack one."""
    rows = pd.read_csv(registry.path('registry.csv'), dtype=str, keep_default_na=False)
    columns = list(rows.columns)
    assert columns[columns.index('trials') + 1] == 'family'
    assert columns[columns.index('formula') + 1] == 'documented_prior'
    assert columns[columns.index('reader') + 1] == 'licence'
    assert set(rows['licence']) <= LICENCES


def test_the_manifest_names_the_file_of_every_registry_object() -> None:
    """A user's loader fetches an object only through its manifest row (#4), so a registry
    object without one, or under a source label sources.yaml lacks, could never load."""
    rows = pd.read_csv(registry.path('registry.csv'), dtype=str, keep_default_na=False)
    sources = registry.sources()
    manifest = registry.manifest()
    keys = {(sources[label], name) for label, name in zip(rows['source'], rows['object'])}
    assert keys <= set(manifest)


def test_every_dryad_source_of_the_registry_has_a_mirror() -> None:
    """Dryad refuses scripted downloads, so a registry object from Dryad loads only from the
    package's mirror of its CC0 file (ADR 0003)."""
    rows = pd.read_csv(registry.path('registry.csv'), dtype=str, keep_default_na=False)
    sources = registry.sources()
    dryad = {label for label in rows['source'] if 'datadryad.org' in sources[label].name}
    unmirrored = {label for label in dryad if sources[label].mirror is None}
    assert dryad and not unmirrored


def test_a_url_sources_pin_is_its_checksum() -> None:
    """A URL has no version: the file's sha256 is its pin, so the loader always checks it."""
    entry = {'kind': 'url', 'name': 'https://example.org/deposit.zip', 'pin': 'ab' * 32}
    deposit = registry.source('deposit', entry)
    assert deposit.checksum == deposit.pin == 'ab' * 32
