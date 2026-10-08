"""Dataset loader for the dimension survey (spec #14): pinned CRAN, git or url source in,
typed DataFrames out. `loader.py` is the pipeline, `readers.py` the formats, `docs.py` the
help pages."""

from metabeta.glmm.datasets.loader import ColumnType, DataObject, Loader, Reader, Source
from metabeta.glmm.datasets.readers import Frames

__all__ = ['ColumnType', 'DataObject', 'Frames', 'Loader', 'Reader', 'Source']
