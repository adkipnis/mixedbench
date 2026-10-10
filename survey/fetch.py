"""Fetch every source a registry object loads from, with checksum verification, into a scratch
cache: the link-rot detector of ADR 0003. Prints one line per failing source, its label and
the error, and exits non-zero when any failed; the weekly workflow opens an issue per line.
Run from the repo root:

    uv run python survey/fetch.py
"""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Mapping

from mixedbench import registry
from mixedbench.datasets import Loader, Source


# =====================================================================================
# pipeline: manifest -> objects per source -> first error per source
# =====================================================================================
class WeeklyFetch:
    def __init__(self, sources: Mapping[str, Source], loader: Loader) -> None:
        """`loader` carries the manifest: its objects are what is fetched, each file checked
        against the manifest's sha256 and a url's archive against its pin."""
        self.labels = {source: label for label, source in sources.items()}
        self.loader = loader

    def failures(self) -> dict[str, str]:
        """Per failing source, by label, the error of its first object that failed to load."""
        failures = {}
        for source, names in self.objectsBySource().items():
            error = self.firstError(source, names)
            if error is not None:
                failures[self.labels[source]] = error
        return failures

    # ---------------------------------------------------------------------------------
    # pipeline
    # ---------------------------------------------------------------------------------
    def objectsBySource(self) -> dict[Source, list[str]]:
        objects = {}
        for source, name in self.loader.manifest:
            objects.setdefault(source, []).append(name)
        return objects

    def firstError(self, source: Source, names: list[str]) -> str | None:
        """Any exception is the source's verdict, not a crash of the run: a checksum mismatch
        (ValueError), a file the host lacks (FileNotFoundError), an unreachable host."""
        for name in names:
            try:
                self.loader.load(source, name)
            except Exception as error:
                return f'{type(error).__name__}: {error}'
        return None


# =====================================================================================
# main
# =====================================================================================
if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as cache:
        loader = Loader(cache, manifest=registry.manifest())
        failures = WeeklyFetch(registry.sources(), loader).failures()
    for label, error in failures.items():
        print(f'{label}\t{error}')
    sys.exit(1 if failures else 0)
