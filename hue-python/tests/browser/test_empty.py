from htmy import html

from hue.ui import Button, Empty
from tests.browser.conftest import Show


def test_actions_wrap_inside_a_narrow_box(show: Show) -> None:
    empty = (
        Empty()
        .compact()
        .title("Could not load")
        .actions(Button().content("Try again"), Button().content("Contact support"))
    )
    page = show(html.div(empty, style="width:180px"))
    box = page.locator("main > div").bounding_box()
    assert box is not None
    for button in page.get_by_role("button").all():
        part = button.bounding_box()
        assert part is not None
        assert box["x"] <= part["x"]
        assert part["x"] + part["width"] <= box["x"] + box["width"]


def test_empty_actions_stay_on_one_centred_line_when_wide(show: Show) -> None:
    empty = (
        Empty()
        .title("No invoices")
        .actions(Button().content("Create invoice"), Button().content("Import"))
    )
    page = show(html.div(empty, style="width:800px"))
    box = page.locator("main > div > div").bounding_box()
    buttons = [b.bounding_box() for b in page.get_by_role("button").all()]
    assert box is not None and all(buttons)
    assert buttons[0]["y"] == buttons[1]["y"]  # type: ignore[index]
    left = buttons[0]["x"] - box["x"]  # type: ignore[index]
    right = box["x"] + box["width"] - (buttons[1]["x"] + buttons[1]["width"])  # type: ignore[index]
    assert abs(left - right) < 1
