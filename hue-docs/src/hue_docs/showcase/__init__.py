"""Hand-authored showcases for components the auto-grid can't represent.

Most components are documented entirely automatically: their enum/bool axes
become variant grids (see registry.auto_showcases). Compositional components
like Table have no such axes — they're assembled from subcomponents — so an
auto-grid has nothing to show. For those we curate a few representative examples.

Each documented component gets its own module here named after it
(showcase/Table.py, showcase/DataTable.py, ...) exposing a module-level
SHOWCASES: list[Showcase]. curated_showcases loads the module matching a
component's name, if one exists.

Examples are written with variant(), which takes a single source
expression that is both eval-ed to build the live preview and shown verbatim
as the code snippet — so the two can never drift. The strings are trusted,
in-repo literals evaluated at build time against the public hue.ui names;
there is no external input.
"""

from __future__ import annotations

import importlib
import importlib.util
import textwrap
from typing import Any, Callable

from htmy import html
from hue import toast, ui
from hue.js import call, close, unsafe
from hue.types.core import ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.molecules.breadcrumbs import Crumb

from hue_docs.discovery import ComponentDoc
from hue_docs.registry import Showcase, Variant

# The names a curated snippet may reference — the public component surface,
# plus raw elements for the slots that take arbitrary markup, such as CardMedia.
_NS: dict[str, Any] = {name: getattr(ui, name) for name in ui.__all__}
_NS["html"] = html
# plus hue's own icon set, which the components that need a glyph use in their
# example() too (see the Icon page).
_NS["HueIcon"] = HueIcon
# and the named tuple a breadcrumb trail is made of.
_NS["Crumb"] = Crumb
# and the way a snippet raises a toast from the browser.
_NS["toast"] = toast
# and the expression builders, since a snippet that wires an action uses them.
_NS["call"] = call
_NS["close"] = close
_NS["unsafe"] = unsafe


def builder(
    code: str, namespace: dict[str, Any] | None = None
) -> Callable[[], ComponentType]:
    """
    A zero-arg factory that evaluates code against the public component names,
    plus anything the caller adds.

    Added rather than swapped in: a snippet that needs a name of its own - a
    demo icon base, a class list too long to repeat down a page - still needs
    every component name as well.
    """
    names = {**_NS, **(namespace or {})}

    def build() -> ComponentType:
        return eval(code, dict(names))

    return build


def variant(
    label: str, source: str, namespace: dict[str, Any] | None = None
) -> Variant:
    """
    A variant whose preview and code come from one source expression.
    """
    code = textwrap.dedent(source).strip()
    return Variant(label=label, build=builder(code, namespace), code=code)


def curated_showcases(doc: ComponentDoc) -> list[Showcase]:
    """Showcases from showcase/<doc.name>.py, or an empty list if none."""
    module_name = f"{__name__}.{doc.name}"
    if importlib.util.find_spec(module_name) is None:
        return []
    module = importlib.import_module(module_name)
    return list(getattr(module, "SHOWCASES", []))


__all__ = ["Showcase", "builder", "curated_showcases", "variant"]
