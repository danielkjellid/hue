"""Curated showcases for the bring-your-own :class:`~hue.ui.Icon` component.

Icon has no enum/bool axes for the auto-grid to introspect — what matters is how
you *bind* an icon source and how the inlined SVG responds to utility classes. So
we curate the examples here, rendering them against a small demo icon set that
ships alongside this module (``showcase/icons/``).

Two kinds of example appear below:

* ``_variant`` — the snippet is both rendered and shown, so the two can't drift.
  It runs against ``Icon`` already bound to the demo directory.
* ``_setup`` — shows the real ``create_icon_base`` / ``directory_resolver`` setup
  code (with an illustrative path) while previewing the icon it would produce.
  The setup is a multi-statement snippet, so the preview is evaluated separately.
"""

from __future__ import annotations

import os
import textwrap
from typing import Callable

from hue.types.core import ComponentType
from hue.ui import create_icon_base

from hue_docs.registry import Showcase, Variant

# A handful of icons that live next to this module, used purely to render the
# previews below. In a real app this directory is wherever you keep your SVGs.
_ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")

# ``Icon`` here is a demo base bound to that directory. Snippets reference it by
# this name, which is exactly what a user writes after create_icon_base().
Icon = create_icon_base(icons_dir=_ICONS_DIR)

_NS = {"Icon": Icon}


def _build(expr: str) -> Callable[[], ComponentType]:
    return lambda: eval(expr, dict(_NS))


def _variant(label: str, source: str) -> Variant:
    """An example whose code is rendered verbatim — preview and code stay in sync."""
    code = textwrap.dedent(source).strip()
    return Variant(label=label, build=_build(code), code=code)


def _setup(label: str, code: str, preview: str) -> Variant:
    """An example that shows setup *code* while previewing what it produces."""
    return Variant(
        label=label,
        build=_build(textwrap.dedent(preview).strip()),
        code=textwrap.dedent(code).strip(),
    )


SHOWCASES: list[Showcase] = [
    Showcase(
        title="Binding an icon source",
        layout="stack",
        description=(
            "Call create_icon_base once to bind a source, then reuse the "
            "returned Icon class by name. icons_dir is shorthand for "
            "resolver=directory_resolver(path); reach for directory_resolver "
            "directly only when you want the resolver as a value to compose."
        ),
        variants=[
            _setup(
                "From a directory",
                """
                from hue.ui import create_icon_base

                Icon = create_icon_base(icons_dir="assets/icons")
                Icon("calendar").class_("size-8")
                """,
                'Icon("calendar").class_("size-8")',
            ),
            _setup(
                "With directory_resolver",
                """
                from hue.ui import create_icon_base, directory_resolver

                resolve = directory_resolver("assets/icons")
                Icon = create_icon_base(resolver=resolve)
                Icon("bell").class_("size-8")
                """,
                'Icon("bell").class_("size-8")',
            ),
            _setup(
                "A custom resolver",
                """
                from importlib.resources import files
                from hue.ui import create_icon_base

                def resolve(name: str) -> str:
                    return (files("my_app.icons") / f"{name}.svg").read_text()

                Icon = create_icon_base(resolver=resolve)
                Icon("star").class_("size-8")
                """,
                'Icon("star").class_("size-8")',
            ),
        ],
    ),
    Showcase(
        title="Sizing",
        layout="row",
        description=(
            "The SVG is inlined, so size it with the same size-* utilities you "
            "use on anything else. Dimensions baked into the file are ignored."
        ),
        variants=[
            _variant("size-4", 'Icon("calendar").class_("size-4")'),
            _variant("size-6", 'Icon("calendar").class_("size-6")'),
            _variant("size-8", 'Icon("calendar").class_("size-8")'),
            _variant("size-12", 'Icon("calendar").class_("size-12")'),
        ],
    ),
    Showcase(
        title="Colour",
        layout="row",
        description=(
            "Icons that paint with currentColor inherit text colour, so text-* "
            "utilities recolour them — strokes and fills alike."
        ),
        variants=[
            _variant("Default", 'Icon("bell").class_("size-8")'),
            _variant("Primary", 'Icon("bell").class_("size-8 text-primary")'),
            _variant("Destructive", 'Icon("heart").class_("size-8 text-destructive")'),
            _variant("Muted", 'Icon("star").class_("size-8 text-surface-400")'),
        ],
    ),
    Showcase(
        title="A few icons",
        layout="grid",
        description=(
            "The whole SVG is preserved, so any set works regardless of which "
            "elements it uses. These demo icons are Feather-style strokes."
        ),
        variants=[
            _variant("check", 'Icon("check").class_("size-8")'),
            _variant("plus", 'Icon("plus").class_("size-8")'),
            _variant("arrow-right", 'Icon("arrow-right").class_("size-8")'),
            _variant("trash", 'Icon("trash").class_("size-8")'),
            _variant("star", 'Icon("star").class_("size-8")'),
            _variant("heart", 'Icon("heart").class_("size-8")'),
        ],
    ),
]
