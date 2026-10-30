from playwright.sync_api import Page, expect

from hue.ui import Kbd
from tests.browser.conftest import Show


def _drawn(page: Page) -> list[str]:
    return page.locator("kbd").evaluate_all(
        "keys => keys.map(k => { const glyph = k.querySelector('[aria-hidden]');"
        " return glyph ? getComputedStyle(glyph, '::before').content.slice(1, -1)"
        " : k.textContent })"
    )


def _spoken(page: Page) -> str:
    return " ".join(
        page.locator("kbd").evaluate_all(
            "keys => keys.map(k => (k.querySelector('.sr-only') ?? k).textContent)"
        )
    )


def test_modifiers_take_the_conventional_order_off_apple(show: Show) -> None:
    page = show(Kbd("shift", "alt", "mod", "K"), platform="Win32")
    expect(page.locator("kbd").first).to_have_text("Control")
    assert _drawn(page) == ["Ctrl", "Alt", "Shift", "K"]
    assert _spoken(page) == "Control Alt Shift K"


def test_modifiers_keep_the_written_order_on_apple(show: Show) -> None:
    page = show(Kbd("shift", "alt", "mod", "K"))
    assert _drawn(page) == ["⇧", "⌥", "⌘", "K"]
    assert _spoken(page) == "Shift Alt Command K"
