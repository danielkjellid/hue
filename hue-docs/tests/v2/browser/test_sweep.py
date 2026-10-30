"""
Every page and every frame of the site, opened in Chrome at a desktop and a
phone width. A script error, a console error or a page wider than the window
fails the run, with every offender listed.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Browser

from hue_docs_v2.app import frame_paths, page_paths

from .conftest import stub_fonts

# The Stack Width demo shows a row that never wraps, and its page says the
# row overflows below its longest word. At 390 that is the point of it.
OVERFLOW_ALLOWED = {"/_frame/stack/width/"}

OVERFLOW = "document.documentElement.scrollWidth - document.documentElement.clientWidth"


@pytest.mark.parametrize("width", [1440, 390])
def test_no_page_or_frame_errors_or_overflows(
    browser: Browser, site: str, width: int
) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900})
    stub_fonts(context)
    page = context.new_page()
    current = ""
    problems: list[str] = []
    page.on("pageerror", lambda exc: problems.append(f"{current}: {exc}"))
    page.on(
        "console",
        lambda msg: (
            problems.append(f"{current}: console {msg.text}")
            if msg.type == "error"
            else None
        ),
    )
    try:
        for path in page_paths() + frame_paths():
            current = path
            page.goto(site + path)
            # Alpine starts on DOMContentLoaded; one frame lets its first
            # render land before the width is read.
            page.evaluate("() => new Promise(requestAnimationFrame)")
            over = page.evaluate(OVERFLOW)
            if over > 1 and path not in OVERFLOW_ALLOWED:
                problems.append(f"{path}: {over}px wider than the window")
    finally:
        context.close()
    assert not problems, f"{len(problems)} problems at {width}px:\n" + "\n".join(
        problems
    )
