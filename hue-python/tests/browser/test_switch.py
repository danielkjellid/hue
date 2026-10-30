import pytest
from playwright.sync_api import expect

from hue.ui import Switch
from tests.browser.conftest import Show


@pytest.mark.parametrize(
    ("state", "text"),
    [("success", "Saved"), ("error", "Not saved"), ("pending", "Saving")],
)
def test_status_region_says_the_outcome_in_text(
    show: Show, state: str, text: str
) -> None:
    switch = Switch().name("notify").label("Notify").settle_after(None)
    page = show(switch.submission_state(state))  # type: ignore[arg-type]
    expect(page.get_by_role("status")).to_have_text(text)
