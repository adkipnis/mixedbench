"""Dataset loader for the dimension survey (spec #14): pinned CRAN, git or url source in,
typed DataFrames out. `loader.py` is the pipeline, `readers.py` the formats."""

from mixedbench.datasets.loader import DataObject, Loader, Manifest, ManifestRow, Source, fetch

__all__ = ['DataObject', 'Loader', 'Manifest', 'ManifestRow', 'Source', 'fetch']
