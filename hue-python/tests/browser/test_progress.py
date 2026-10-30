from hue.ui import ProgressRing
from tests.browser.conftest import Show


def test_a_ring_keeps_its_gap_and_its_readout_inside(show: Show) -> None:
    page = show(
        ProgressRing().value(97).label("Upload").id("gap"),
        ProgressRing().value(33.33333).show_value(),
        ProgressRing().value(100).show_value(),
    )
    # The drawn arc plus a round cap at each end, half the stroke each, has
    # to leave part of the circle bare short of complete.
    bare = (
        page.locator("#gap circle")
        .nth(1)
        .evaluate(
            "circle => { const style = getComputedStyle(circle); return"
            " parseFloat(style.strokeDashoffset) - parseFloat(style.strokeWidth) }"
        )
    )
    assert bare >= 2
    # The text itself, measured against the hole the 5px stroke leaves.
    for readout in page.get_by_text("%").all():
        width = readout.evaluate(
            "span => { const range = document.createRange();"
            " range.selectNodeContents(span);"
            " return range.getBoundingClientRect().width }"
        )
        assert width < 2 * (21 - 2.5) - 4
