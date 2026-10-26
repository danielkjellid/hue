"""
The docs as a FastAPI app.

In development it serves every page live. For a deploy, freeze.py requests
each page and frame from it once and writes the answers to dist-v2, and only
the demo routes, under /demos/, run in a Worker.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from hue_fastapi import configure_hue

from hue_docs_v2.layout.component import component_main
from hue_docs_v2.layout.panel import frame_href, frame_page
from hue_docs_v2.layout.shell import shell
from hue_docs_v2.model import ComponentPage, GuidePage, NavGroup, Panel
from hue_docs_v2.nav import build_nav
from hue_docs_v2.pages import COMPONENTS, GUIDES
from hue_docs_v2.render import render_html
from hue_docs_v2.shortcuts import Shortcuts
from hue_docs_v2.site import url

STATIC = Path(__file__).parent / "static"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Figtree:wght@500;600;700"
    "&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
)

# Guides folded into a component's page, kept reachable at their old URLs.
REDIRECTS = {"/toasts/": "/components/toast/"}

type Endpoint = Callable[[Request], Awaitable[HTMLResponse]]


def _page_endpoint(page: GuidePage | ComponentPage, nav: list[NavGroup]) -> Endpoint:
    async def endpoint(request: Request) -> HTMLResponse:
        # A guide is all prose, so it takes the prose's measure as a column.
        prose = isinstance(page, GuidePage)
        main = (
            page.build()
            if isinstance(page, GuidePage)
            else component_main(page, COMPONENTS)
        )
        document = shell(
            title=page.title, nav=nav, current=page.href, main=main, prose=prose
        )
        return HTMLResponse(
            await render_html(document, request=request, shortcuts=Shortcuts)
        )

    return endpoint


def _frame_endpoint(page: ComponentPage, panel: Panel) -> Endpoint:
    async def endpoint(request: Request) -> HTMLResponse:
        return HTMLResponse(
            await render_html(await frame_page(page, panel, request), request=request)
        )

    return endpoint


def _redirect(to: str) -> Callable[[], Awaitable[RedirectResponse]]:
    async def endpoint() -> RedirectResponse:
        return RedirectResponse(to, status_code=301)

    return endpoint


def page_paths() -> list[str]:
    """
    Every page the site has, which is every path freeze writes and search
    indexes. Frames are listed apart, since they are not pages to land on.
    """
    return [guide.href for guide in GUIDES] + [page.href for page in COMPONENTS]


def frame_paths() -> list[str]:
    return [frame_href(page, panel) for page in COMPONENTS for panel in page.panels]


def demo_app() -> FastAPI:
    """
    Only the demo routes, which is all the Worker runs: every other request
    is a file the freeze wrote.
    """
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    configure_hue(
        app,
        csrf=None,
        css_url=url("/styles/tailwind.css"),
        js_url=url("/js/alpine-bundle.js"),
        extra_css_urls=[FONTS],
        html_title_factory=lambda title: f"{title} · Hue",
        shortcuts=Shortcuts,
    )
    for page in COMPONENTS:
        for view in page.views:
            app.include_router(view.api_router, prefix=f"/demos/{page.slug}")
    return app


def create_app(*, static_dir: Path | None = None) -> FastAPI:
    """
    static_dir is the built site, served under everything else in development
    so the stylesheet, scripts and search index the build wrote are found.
    """
    app = demo_app()
    nav = build_nav(GUIDES, COMPONENTS)
    for guide in GUIDES:
        app.add_api_route(guide.href, _page_endpoint(guide, nav), methods=["GET"])
    for page in COMPONENTS:
        app.add_api_route(page.href, _page_endpoint(page, nav), methods=["GET"])
        for panel in page.panels:
            app.add_api_route(
                frame_href(page, panel),
                _frame_endpoint(page, panel),
                methods=["GET"],
            )

    for old, new in REDIRECTS.items():
        app.add_api_route(old, _redirect(url(new)), methods=["GET"])

    app.mount("/static", StaticFiles(directory=STATIC), name="docs-static")
    if static_dir is not None:
        app.mount("/", StaticFiles(directory=static_dir), name="site")
    return app
