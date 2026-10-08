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


def test_the_manifest_names_the_file_of_every_registry_object() -> None:
    """A user's loader fetches an object only through its manifest row (#4), so a registry
    object without one, or under a source label sources.yaml lacks, could never load."""
    rows = pd.read_csv(registry.path('registry.csv'), dtype=str, keep_default_na=False)
    sources = registry.sources()
    manifest = registry.manifest()
    keys = {(sources[label], name) for label, name in zip(rows['source'], rows['object'])}
    assert keys <= set(manifest)
