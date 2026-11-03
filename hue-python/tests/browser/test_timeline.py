from playwright.sync_api import expect

from hue import html
from hue.ui import Timeline, TimelineItem
from tests.browser.conftest import Show


def test_each_item_with_details_opens_its_own_panel_by_key(show: Show) -> None:
    page = show(
        Timeline().content(
            TimelineItem().title("Checks").details({"Commit": "3f9c2a1"}),
            TimelineItem().title("Deploy").details({"Region": "eu-north-1"}),
        )
    )
    checks = page.get_by_role("button", name="Checks")
    expect(checks).to_have_attribute("aria-expanded", "false")
    expect(page.get_by_text("3f9c2a1")).to_be_hidden()
    checks.press("Enter")
    expect(checks).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_text("3f9c2a1")).to_be_visible()
    expect(page.get_by_text("eu-north-1")).to_be_hidden()
    checks.press("Space")
    expect(page.get_by_text("3f9c2a1")).to_be_hidden()


def test_the_times_line_up_whether_or_not_an_item_has_details(show: Show) -> None:
    page = show(
        html.div(
            Timeline().content(
                TimelineItem().title("Checks").time("13:24").details({"Ran": "pyt"}),
                TimelineItem().title("Merged").time("13:12"),
            )
        ).class_("overflow-y-auto"),
        width=320,
    )
    rights = page.locator("time").evaluate_all(
        "times => times.map(t => t.getBoundingClientRect().right)"
    )
    assert abs(rights[0] - rights[1]) < 1
    # And the title starts as high in its row with a button around it.
    tops = page.locator("li").evaluate_all(
        "items => items.map(li => li.querySelector('time').parentElement"
        ".firstElementChild.getBoundingClientRect().top - "
        "li.getBoundingClientRect().top)"
    )
    assert abs(tops[0] - tops[1]) < 1
    # The toggle's tint stays inside the list, or a scrolling panel scrolls.
    box = page.locator("div.overflow-y-auto")
    assert box.evaluate("b => b.scrollWidth === b.clientWidth")


def test_a_long_rail_time_stays_clear_of_its_marker(show: Show) -> None:
    page = show(
        Timeline()
        .rail()
        .content(
            TimelineItem().title("Shipped").time("14:32:05.123"),
            TimelineItem().title("Placed").time("Mon"),
        ),
        width=320,
    )
    time = page.locator("time").first.bounding_box()
    marker = page.locator("li span[aria-hidden]").first.bounding_box()
    assert time and marker
    assert time["x"] + time["width"] <= marker["x"]
