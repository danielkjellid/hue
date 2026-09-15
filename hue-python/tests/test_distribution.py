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

from hatch_build import AssetsBuildHook

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


class TestTheAssetGuard:
    """
    The hook that refuses to build a distribution with no styling in it.

    It has to tell a release apart from a development install: an editable
    install builds the assets *after* syncing, so demanding them up front
    breaks the very step that would have produced them - which is how this
    first went wrong, taking every CI job with it.
    """

    @staticmethod
    def _hook(root: Path) -> AssetsBuildHook:
        metadata = type("Metadata", (), {"name": "hue"})()
        return AssetsBuildHook(str(root), {}, {}, metadata, "", "wheel")

    def test_a_release_without_the_assets_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="no styling at all"):
            self._hook(tmp_path).initialize("standard", {})

    def test_an_editable_install_is_left_alone(self, tmp_path: Path) -> None:
        self._hook(tmp_path).initialize("editable", {})
