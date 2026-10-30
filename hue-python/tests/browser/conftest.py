"""
Components rendered into a real page in Chrome, driven with real keys and
pointer moves.

The tests that read markup pass every keyboard, focus and overlay bug hue has
had, so behaviour is checked here. Each page is served from memory through
Playwright's routing, with hue's stylesheet and bundles read from the package,
so no server runs.
"""

import asyncio
import json
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

# A modal's trap hides the rest of the page a tick after it takes focus, and
# Alpine never undoes a hide that lands after the modal closed. Wait for it
# before closing one: the page would stay hidden from a screen reader for good.
TRAPPED = "!!document.querySelector('body > [aria-hidden=true]')"

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
    return document if dir is None else document.replace("<html", f'<html dir="{dir}"', 1)


# Per module, not per session: the sync API keeps an event loop running on
# this thread while it is open, which the async component tests cannot share.
@pytest.fixture(scope="module")
def playwright() -> Iterator[Playwright]:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def browser(playwright: Playwright) -> Iterator[Browser]:
    # The installed Chrome, which GitHub's runners carry too, so nothing is
    # downloaded.
    browser = playwright.chromium.launch(channel="chrome")
    yield browser
    browser.close()


@pytest.fixture
def show(browser: Browser) -> Iterator[Show]:
    """
    Open components on a fresh page and return it once Alpine has started.

    width and height set the viewport, theme the colour scheme, dir the
    page's direction, and platform what navigator.platform says, a Mac unless
    told otherwise. An uncaught error or console error on the page fails
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
        platform: str = "MacIntel",
    ) -> Page:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            color_scheme="dark" if theme == "dark" else "light",
        )
        page = context.new_page()
        # Pinned, so a test of what a Mac or a PC is shown gives the same
        # answer on whatever machine runs it.
        page.add_init_script(
            "Object.defineProperty(Navigator.prototype, 'platform', "
            f"{{ get: () => {json.dumps(platform)} }})"
        )
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
        # The direction goes in by text replacement, so make sure it landed.
        assert page.evaluate("document.dir") == (dir or "")
        pages.append(page)
        return page

    yield _show
    for page in pages:
        page.context.close()
    assert not errors, errors
