"""
Components rendered into a real page in Chrome, driven with real keys and
pointer moves.

The tests that read markup pass every keyboard, focus and overlay bug hue has
had, so behaviour is checked here. Each page is served from memory through
Playwright's routing, with hue's stylesheet and bundles read from the package,
so no server runs.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from htmy import html
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from hue import assets
from hue.context import HueContextArgs
from hue.pages import create_page_base
from hue.renderer import render_tree
from hue.types.core import ComponentType

ORIGIN = "http://hue.test"

_Page = create_page_base(
    css_url=assets.CSS_URL,
    js_url=assets.JS_URL,
    html_title_factory=lambda title: title,
)

type Show = Callable[..., Page]


class _Request:
    """
    Bare request stand-in for rendering pages.
    """


def render_page(*components: ComponentType, dir: str | None = None) -> str:
    coroutine = render_tree(
        _Page(title="Test", body=html.main(*components, class_="p-8")),
        context_args=HueContextArgs(request=_Request(), csrf_token="tok"),
    )
    # Playwright's sync API keeps an event loop running on this thread.
    with ThreadPoolExecutor(1) as pool:
        document = pool.submit(asyncio.run, coroutine).result()
    return document if dir is None else document.replace("<html>", f'<html dir="{dir}">', 1)


@pytest.fixture(scope="session")
def fresh_stylesheet() -> None:
    """
    Rebuild the stylesheet once per run.

    A class added since the last build would otherwise be missing from it, and
    the browser would test the old styles.
    """
    package_root = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["make", "build-css"], cwd=package_root, check=True, capture_output=True
    )


# Per module, not per session: the sync API keeps an event loop running on
# this thread while it is open, which the async component tests cannot share.
@pytest.fixture(scope="module")
def playwright() -> Iterator[Playwright]:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def browser(playwright: Playwright, fresh_stylesheet: None) -> Iterator[Browser]:
    # The installed Chrome, which GitHub's runners carry too, so nothing is
    # downloaded.
    browser = playwright.chromium.launch(channel="chrome")
    yield browser
    browser.close()


@pytest.fixture
def show(browser: Browser) -> Iterator[Show]:
    """
    Open components on a fresh page and return it once Alpine has started.

    width and height set the viewport, theme the colour scheme, and dir the
    page's direction. An uncaught error or console error on the page fails
    the test.
    """
    pages: list[Page] = []
    errors: list[str] = []

    def _show(
        *components: ComponentType,
        width: int = 1280,
        height: int = 800,
        theme: str = "light",
        dir: str | None = None,
    ) -> Page:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            color_scheme="dark" if theme == "dark" else "light",
        )
        page = context.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )
        document = render_page(*components, dir=dir)

        def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
            path = request.url.removeprefix(ORIGIN).split("?")[0]
            if path in assets.ASSET_ROUTES:
                content, _ = assets.served_asset(path)
                route.fulfill(body=content, content_type=assets.ASSET_ROUTES[path][1])
            elif path == "/":
                route.fulfill(body=document, content_type="text/html")
            else:
                route.fulfill(status=404)

        # Registered first, so a test's own route.on, added later, wins for
        # the URLs it handles.
        page.route(f"{ORIGIN}/**", fulfil)
        page.goto(f"{ORIGIN}/")
        page.wait_for_function("() => window.Alpine && document.body._x_dataStack")
        pages.append(page)
        return page

    yield _show
    for page in pages:
        page.context.close()
    assert not errors, errors
