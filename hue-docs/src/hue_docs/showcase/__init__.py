"""Hand-authored showcases for components the auto-grid can't represent.

Most components are documented entirely automatically: their enum/bool axes
become variant grids (see ``registry.auto_showcases``). Compositional components
like ``Table`` have no such axes — they're assembled from subcomponents — so an
auto-grid has nothing to show. For those we curate a few representative examples.

Each documented component gets its own module here named after it
(``showcase/Table.py``, ``showcase/DataTable.py``, ...) exposing a module-level
``SHOWCASES: list[Showcase]``. ``curated_showcases`` loads the module matching a
component's name, if one exists.

Examples are written with :func:`variant`, which takes a single source
expression that is both ``eval``-ed to build the live preview and shown verbatim
as the code snippet — so the two can never drift. The strings are trusted,
in-repo literals evaluated at build time against the public ``hue.ui`` names;
there is no external input.
"""

from __future__ import annotations

import importlib
import importlib.util
import textwrap
from typing import Any

from hue import ui

from hue_docs.discovery import ComponentDoc
from hue_docs.registry import Showcase, Variant

# The names a curated snippet may reference — the public component surface.
_NS: dict[str, Any] = {name: getattr(ui, name) for name in ui.__all__}


def variant(label: str, source: str) -> Variant:
    """A variant whose preview and code come from one source expression."""
    code = textwrap.dedent(source).strip()
    return Variant(
        label=label,
        build=lambda code=code: eval(code, dict(_NS)),
        code=code,
    )


def curated_showcases(doc: ComponentDoc) -> list[Showcase]:
    """Showcases from ``showcase/<doc.name>.py``, or an empty list if none."""
    module_name = f"{__name__}.{doc.name}"
    if importlib.util.find_spec(module_name) is None:
        return []
    module = importlib.import_module(module_name)
    return list(getattr(module, "SHOWCASES", []))


__all__ = ["Showcase", "curated_showcases", "variant"]
