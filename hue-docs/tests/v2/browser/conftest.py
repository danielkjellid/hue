"""
The docs in Chrome: the app served on a free port over a frozen build, so the
pages load their real stylesheet, scripts and search index.

Playwright's sync API keeps an event loop running on the thread while it is
open, so it is scoped per module and the async tests elsewhere still run.
"""

from __future__ import annotations

import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from hue_docs_v2.app import create_app

DOCS = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def site(frozen: Path) -> Iterator[str]:
    """
    The live app over the frozen build, as make serve-v2 runs it, on a free
    port. Yields its origin.
    """
    subprocess.run(
        ["make", "build-css-v2", f"DIST_V2={frozen}"],
        cwd=DOCS,
        check=True,
        capture_output=True,
    )
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(static_dir=frozen),
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("The docs server did not start.")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


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


def stub_fonts(context: BrowserContext) -> None:
    # The pages link Google Fonts. An empty stylesheet keeps the run offline
    # and its timing steady.
    context.route(
        "https://fonts.googleapis.com/**",
        lambda route: route.fulfill(body="", content_type="text/css"),
    )


@pytest.fixture
def docs(browser: Browser, site: str) -> Iterator[Page]:
    """
    A fresh page at desktop width with its own storage. An uncaught error or
    console error on it fails the test.
    """
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    stub_fonts(context)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )
    page.set_default_timeout(10_000)
    yield page
    context.close()
    assert not errors, errors
