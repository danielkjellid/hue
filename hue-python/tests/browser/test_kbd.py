from playwright.sync_api import Page, expect

from hue.ui import Kbd
from tests.browser.conftest import Show


def _on_windows(page: Page) -> Page:
    # The platform is read once, as the bundle loads, so the page loads again.
    page.add_init_script(
        "Object.defineProperty(Navigator.prototype, 'platform', { get: () => 'Win32' })"
    )
    page.reload()
    page.wait_for_function("() => window.Alpine && document.body._x_dataStack")
    return page


def _drawn(page: Page) -> list[str]:
    return page.locator("kbd").evaluate_all(
        "keys => keys.map(k => { const glyph = k.querySelector('[aria-hidden]');"
        " return glyph ? getComputedStyle(glyph, '::before').content.slice(1, -1)"
        " : k.textContent })"
    )


def test_modifiers_are_words_off_apple(show: Show) -> None:
    page = _on_windows(show(Kbd("ctrl", "alt", "shift", "K")))
    expect(page.locator("kbd").first).to_have_text("Control")
    assert _drawn(page) == ["Ctrl", "Alt", "Shift", "K"]
