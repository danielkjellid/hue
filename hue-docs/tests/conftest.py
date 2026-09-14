"""Shared fixtures for the docs tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def built_css(tmp_path_factory: pytest.TempPathFactory) -> str:
    """
    The stylesheet the docs site ships, built for this test session.

    Built rather than read as found, so the style tests assert against what the
    current source produces instead of whatever was last left on disk. It comes
    from docs.input.css, which names its source roots explicitly - hue's
    components and this package - so the build needs nothing outside hue-docs.

    Through the Makefile, because that is what pins the Tailwind version.
    """
    out = tmp_path_factory.mktemp("styles") / "tailwind.css"
    subprocess.run(
        ["make", "build-css", f"CSS_OUT={out}"],
        cwd=DOCS,
        check=True,
        capture_output=True,
    )
    return out.read_text()
