"""
What a consumer installing hue from a wheel actually gets.

Every other test in this suite runs from the source tree, where the static
assets are simply there. That is exactly why the wheel shipped none of them
for as long as it did: a component library with no stylesheet imports fine,
renders fine, and styles nothing.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent.parent

# The assets a consumer has no second chance at: they are generated from
# sources that live in this repo, not in the wheel.
REQUIRED = (
    "hue/static/styles/tailwind.css",
    "hue/static/styles/tailwind.input.css",
    "hue/static/js/alpine-bundle.js",
    "hue/py.typed",
)


@pytest.fixture(scope="module")
def wheel_contents(tmp_path_factory) -> set[str]:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out)],
        cwd=PACKAGE,
        check=True,
        capture_output=True,
    )
    (built,) = out.glob("*.whl")
    with zipfile.ZipFile(built) as archive:
        return set(archive.namelist())


@pytest.mark.parametrize("path", REQUIRED)
def test_the_wheel_ships_the_assets(wheel_contents: set[str], path: str) -> None:
    assert path in wheel_contents


def test_the_wheel_ships_the_icons(wheel_contents: set[str]) -> None:
    # hue resolves these by name at render time, so a missing one is a
    # RuntimeError in the consumer's request rather than a build failure.
    source = PACKAGE / "src" / "hue" / "static" / "icons"
    expected = {f"hue/static/icons/{icon.name}" for icon in source.glob("*.svg")}
    assert expected
    assert expected <= wheel_contents
