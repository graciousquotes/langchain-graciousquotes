"""The version is written in two places. Nothing else checks they agree.

`pyproject.toml` is what gets published — the release workflow reads it, asks
PyPI whether that version exists, and publishes if it does not. It never looks
at `__version__`. So bumping one and not the other ships a package that calls
itself 0.1.0 while PyPI calls it 0.1.1, with no error anywhere: the build
succeeds, the upload succeeds, the tests pass, and the drift surfaces months
later in somebody's bug report where the reported version is a lie.

This is the same defect the GreenCalculus packages guard against too
(GC_VERSION vs the plugin header). One assertion is cheaper than the gate.

`importlib.metadata` reads the INSTALLED distribution's metadata, which is
generated from `pyproject.toml` at build time — so this compares the module's
self-report against the number that will actually reach PyPI, without needing a
TOML parser (`tomllib` is 3.11+; this package supports 3.9+).
"""
from importlib.metadata import PackageNotFoundError, version

import pytest

import langchain_graciousquotes


def test_module_version_matches_the_published_metadata():
    try:
        published = version("langchain-graciousquotes")
    except PackageNotFoundError:  # pragma: no cover - only when run uninstalled
        pytest.fail(
            "langchain-graciousquotes is not installed, so the published version "
            "cannot be read. Run `pip install -e \".[test]\"` first — the release "
            "workflow does."
        )

    assert langchain_graciousquotes.__version__ == published, (
        f"__init__.py says {langchain_graciousquotes.__version__!r} but the package "
        f"metadata (from pyproject.toml) says {published!r}. Bump both, or PyPI "
        f"will serve a release that misreports its own version."
    )
