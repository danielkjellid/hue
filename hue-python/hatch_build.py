"""
Refuse to build a *distribution* that would install as a component library with
no CSS. Editable installs are exempt: they build the assets after syncing.

tailwind.css and the Alpine bundle are both generated, and the stylesheet is
not committed, so a build from a clean checkout has nothing to ship. Left
alone that produces a wheel which imports fine, renders fine, and styles
nothing - and the consumer cannot run the build themselves, because the
sources it needs live in this repo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Every asset a consumer gets no second chance at, and how to produce it.
_REQUIRED: dict[str, str] = {
    "src/hue/static/styles/tailwind.css": "make build-css",
    "src/hue/static/js/alpine-bundle.js": "make build-js",
}


class AssetsBuildHook(BuildHookInterface):
    PLUGIN_NAME = "hue-assets"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if version == "editable":
            # A development install builds the assets after syncing, not
            # before, so demanding them here only breaks the step that would
            # have produced them. Nothing leaves the repo either way.
            return

        root = Path(self.root)
        missing = {
            path: command
            for path, command in _REQUIRED.items()
            if not (root / path).is_file()
        }
        if missing:
            steps = "\n".join(
                f"  {command}    # produces {path}"
                for path, command in sorted(missing.items())
            )
            raise RuntimeError(
                "hue's built assets are missing, so this distribution would "
                "install with no styling at all. Run these in hue-python "
                f"first:\n{steps}"
            )
