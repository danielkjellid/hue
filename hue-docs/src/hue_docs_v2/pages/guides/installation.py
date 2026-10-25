from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage


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
            "from hue.assets import (\n"
            "    chart_bundle_path,\n"
            "    css_built_path,\n"
            "    js_bundle_path,\n"
            ")\n\n"
            "css_built_path()  # -> .../hue/static/styles/tailwind.css\n"
            "js_bundle_path()  # -> .../hue/static/js/alpine-bundle.js\n"
            "chart_bundle_path()  # -> .../hue/static/js/chart-bundle.js"
        ),
        pr.p(
            "The chart library is a file of its own, because it is larger "
            "than the rest of Hue's JavaScript put together. The Alpine bundle "
            "fetches it the first time a page shows a chart, so a page without "
            "a chart never downloads it. It looks in its own directory for a "
            "file named chart-bundle.js, so serve it there under that exact "
            "name: a static pipeline that keeps only hashed copies, such as "
            "WhiteNoise with WHITENOISE_KEEP_ONLY_HASHED_FILES, would leave "
            "charts nothing to load. The Alpine bundle itself can be served "
            "under any name."
        ),
        pr.p(
            "The Alpine bundle is an ES module that exports a configureAlpine "
            "helper; Hue's page scaffolding wires this up for you (see ",
            pr.link("Usage", "/usage/"),
            ").",
        ),
    )


PAGE = GuidePage(
    slug="installation",
    title="Installation",
    nav_label="Installation",
    group="Get started",
    order=1,
    build=_build,
)
