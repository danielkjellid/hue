from htmy import html

from hue.ui import Button, Empty
from tests.browser.conftest import Show


def test_actions_wrap_when_narrow_and_centre_on_one_line_when_wide(
    show: Show,
) -> None:
    narrow = (
        Empty()
        .compact()
        .title("Could not load")
        .actions(Button().content("Try again"), Button().content("Contact support"))
    )
    wide = (
        Empty()
        .title("No invoices")
        .actions(Button().content("Create invoice"), Button().content("Import"))
    )
    page = show(
        html.div(narrow, style="width:180px", id="narrow"),
        html.div(wide, style="width:800px", id="wide"),
    )
    box = page.locator("#narrow").bounding_box()
    assert box is not None
    for button in page.locator("#narrow").get_by_role("button").all():
        part = button.bounding_box()
        assert part is not None
        assert box["x"] <= part["x"]
        assert part["x"] + part["width"] <= box["x"] + box["width"]

    box = page.locator("#wide > div").bounding_box()
    first, second = (b.bounding_box() for b in page.locator("#wide button").all())
    assert box is not None and first is not None and second is not None
    assert first["y"] == second["y"]
    left = first["x"] - box["x"]
    right = box["x"] + box["width"] - (second["x"] + second["width"])
    assert abs(left - right) < 1
