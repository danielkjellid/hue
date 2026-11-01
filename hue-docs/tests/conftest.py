"""
Fixtures for the docs: the app under a test client, its built stylesheet, and
a whole frozen site.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hue_docs.app import create_app

DOCS = Path(__file__).resolve().parents[1]
SHIKI = DOCS / "src" / "hue_docs" / "highlight" / "node_modules"


@pytest.fixture(scope="session", autouse=True)
def shiki() -> None:
    # Installed when missing, as the stylesheet is built when missing, so a
    # fresh checkout runs the suite with nothing done by hand.
    if not SHIKI.exists():
        subprocess.run(["make", "highlight-deps"], cwd=DOCS, check=True, capture_output=True)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def built_css(tmp_path_factory: pytest.TempPathFactory) -> str:
    dist = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["make", "build-css", f"DIST={dist}"],
        cwd=DOCS,
        check=True,
        capture_output=True,
    )
    return (dist / "styles" / "tailwind.css").read_text()


@pytest.fixture(scope="session")
def frozen(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from hue_docs.freeze import freeze

    out = tmp_path_factory.mktemp("dist")
    freeze(out)
    return out
