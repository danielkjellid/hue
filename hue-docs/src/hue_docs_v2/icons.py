"""
The icons the docs' examples draw, which are the docs' own: hue ships only the
handful its components need. Named Icon so an example reads the way a reader's
code does, with an Icon they bound to their own set.
"""

from __future__ import annotations

from pathlib import Path

from hue.assets import icons_path
from hue.ui import create_icon_base
from hue.ui.atoms.icon import directory_resolver

_docs_icon = directory_resolver(str(Path(__file__).parent / "icons"))
_hue_icon = directory_resolver(str(icons_path()))


def _resolve(name: str) -> str:
    try:
        return _docs_icon(name)
    except RuntimeError:
        # Falls back to hue's own, which the docs' set does not repeat.
        return _hue_icon(name)


Icon = create_icon_base(resolver=_resolve)
