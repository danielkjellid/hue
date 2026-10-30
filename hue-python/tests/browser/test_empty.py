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
