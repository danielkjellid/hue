from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Installation"),
        pr.lead("Add Hue to your project and wire up its bundled assets."),
        pr.h2("Install the package"),
        pr.p("Using uv:"),
        pr.code("uv add hue", language="bash"),
        pr.p("Or with pip:"),
        pr.code("pip install hue", language="bash"),
        pr.p(
            "Using Django? Install the integration package, which depends on "
            "Hue and adds views and a router:"
        ),
        pr.code("uv add hue-django", language="bash"),
        pr.h2("Serve the assets"),
        pr.p(
            "Hue ships a pre-built Tailwind stylesheet and an Alpine.js bundle "
            "inside the package. Point your pages at them, or copy them into "
            "your own static pipeline. The paths are available from "
            "hue.assets:"
        ),
        pr.code(
            "from hue.assets import css_built_path, js_bundle_path\n\n"
            "css_built_path()  # -> .../hue/static/styles/tailwind.css\n"
            "js_bundle_path()  # -> .../hue/static/js/alpine-bundle.js"
        ),
        pr.p(
            "The Alpine bundle is an ES module that exports a configureAlpine "
            "helper; Hue's page scaffolding wires this up for you (see ",
            pr.link("Usage", "/usage/"),
            ").",
        ),
    )


PAGE = ProsePage(
    slug="installation",
    title="Installation",
    nav_label="Installation",
    group="Get started",
    order=1,
    build=_build,
)
