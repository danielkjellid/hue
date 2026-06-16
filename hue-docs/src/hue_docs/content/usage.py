from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Usage"),
        pr.lead("Compose components, render them to HTML, and serve a page."),
        pr.h2("Render a component"),
        pr.p(
            "Components are rendered to an HTML string with render_tree. It "
            "needs a request and CSRF token, which it threads through the "
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
            "create_page_base builds a Page class bound to your asset URLs and "
            "title format. Instances render a complete HTML document, including "
            "the Alpine setup:"
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
        pr.h2("With Django"),
        pr.p(
            "hue-django adds a HueView and a Django-aware Router so you can "
            "return component fragments from AJAX endpoints and render full "
            "pages from class-based views. See the hue-django docs in the "
            "repository for the full API."
        ),
        pr.p(
            "This very site is built with Hue — it renders every page on this "
            "site using the same render_tree and page scaffolding shown above."
        ),
    )


PAGE = ProsePage(
    slug="usage",
    title="Usage",
    nav_label="Usage",
    group="Get started",
    order=2,
    build=_build,
)
