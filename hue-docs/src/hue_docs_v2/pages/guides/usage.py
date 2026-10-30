from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Usage"),
        pr.lead("Compose components, render them to HTML, and serve a page."),
        pr.h2("Render a component"),
        pr.p(
            "`render_tree` renders components to an HTML string. It takes the "
            "request and the CSRF token and passes them down through the "
            "render context:"
        ),
        pr.code(
            "from hue.context import HueContextArgs\n"
            "from hue.renderer import render_tree\n"
            "from hue.ui import Button\n\n"
            "html = await render_tree(\n"
            '    Button().variant("primary").content("Save"),\n'
            "    context_args=HueContextArgs(request=request, csrf_token=token),\n"
            ")"
        ),
        pr.h2("Render a full page"),
        pr.p(
            "`create_page_base` builds a `Page` class bound to your asset URLs "
            "and title format. An instance renders a complete HTML document, "
            "including the Alpine setup:"
        ),
        pr.code(
            "from hue.pages import create_page_base\n"
            "from hue.ui import Stack, Text\n\n"
            "Page = create_page_base(\n"
            '    css_url="/static/hue/styles/tailwind.css",\n'
            '    js_url="/static/hue/js/alpine-bundle.js",\n'
            '    html_title_factory=lambda title: f"{title} | My App",\n'
            ")\n\n"
            "page = Page(\n"
            '    title="Home",\n'
            '    body=Stack().content(Text("Hello").variant("title-1")),\n'
            ")\n"
            "# render_tree(page, context_args=...) -> full HTML document"
        ),
        pr.p(
            "The chart library, `chart-bundle.js`, has to sit beside the bundle "
            "`js_url` points at (see ",
            pr.link("Installation", "/installation/"),
            ").",
        ),
        pr.h2("With a web framework"),
        pr.p(
            "The integrations do the wiring above for you. Each adds a "
            "`HueView` that renders a full page, a `Router` whose routes "
            "answer AJAX requests with fragments, CSRF handling, and routes "
            "that serve Hue's stylesheet and scripts from the package."
        ),
        pr.bullets(
            [
                pr.p(
                    "`hue-django` for Django: ",
                    pr.link("Views and Router", "/django/views/"),
                    " and ",
                    pr.link("CSS and assets", "/django/css/"),
                    ".",
                ),
                pr.p(
                    "`hue-fastapi` for FastAPI: ",
                    pr.link("Setup and CSRF", "/fastapi/setup/"),
                    " and ",
                    pr.link("Views and Router", "/fastapi/views/"),
                    ".",
                ),
            ]
        ),
        pr.p(
            "This site is built with Hue, on `hue-fastapi`: every page on it "
            "is rendered with the same `render_tree` and page scaffolding "
            "shown above."
        ),
    )


PAGE = GuidePage(
    slug="usage",
    title="Usage",
    nav_label="Usage",
    group="Get started",
    order=2,
    build=_build,
)
