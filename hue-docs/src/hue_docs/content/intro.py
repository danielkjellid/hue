from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Hue"),
        pr.lead(
            "Hue is a component library for Python. You build server-rendered "
            "UI by composing chainable components — no template language, just "
            "Python."
        ),
        pr.p(
            "It is built on ",
            pr.link("htmy", "https://github.com/volfpeter/htmy"),
            ", styled with Tailwind CSS, and made interactive with Alpine.js. "
            "Components are AJAX-first: they pair with a small router so parts "
            "of a page can update without a full reload.",
        ),
        pr.h2("Why Hue"),
        pr.bullets(
            [
                "Chainable, fully typed components — your editor autocompletes "
                "every variant.",
                "Server-rendered HTML with no build step for your markup.",
                "Tailwind for styling and Alpine for interactivity, bundled and "
                "ready to use.",
                "Framework-agnostic core with a first-class Django integration "
                "(hue-django).",
            ]
        ),
        pr.h2("A quick taste"),
        pr.p("Every component reads as a fluent chain of modifiers:"),
        pr.code(
            "from hue.ui import Button, Stack, Text\n\n"
            'Stack().spacing("md").content(\n'
            '    Text("Welcome back").variant("title-2"),\n'
            '    Button().variant("primary").content("Get started"),\n'
            ")"
        ),
        pr.p(
            "Browse the components in the sidebar to see every variant, or head to ",
            pr.link("Installation", "/installation/"),
            " to get set up.",
        ),
    )


PAGE = ProsePage(
    slug="",
    title="Introduction",
    nav_label="Introduction",
    group="Get started",
    order=0,
    build=_build,
)
