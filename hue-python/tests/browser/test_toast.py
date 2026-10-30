from playwright.sync_api import expect

from hue.ui import ToastRegion
from tests.browser.conftest import Show


def test_a_stack_taller_than_the_window_scrolls(show: Show) -> None:
    page = show(ToastRegion(), height=400)
    page.evaluate(
        """() => {
            const region = document.getElementById('hue-toasts');
            const toast = Alpine.evaluate(region, '$toast');
            for (let i = 0; i < 12; i++) toast.info(`Toast ${i}`, { duration: null });
        }"""
    )
    expect(page.get_by_text("Toast 11")).to_be_visible()
    # Scrolled all the way back, the oldest is on screen rather than above it.
    stack = page.locator("#hue-toasts").locator("..")
    stack.evaluate("el => el.scrollBy(0, -10000)")
    expect(page.get_by_text("Toast 0")).to_be_in_viewport()
