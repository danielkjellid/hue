from hue.ui import ProgressRing
from tests.browser.conftest import Show


def test_a_ring_short_of_complete_shows_a_gap(show: Show) -> None:
    page = show(ProgressRing().value(97).label("Upload"))
    # The drawn arc plus a round cap at each end, half the stroke each, has
    # to leave part of the circle bare.
    bare = (
        page.locator("circle")
        .nth(1)
        .evaluate(
            "circle => { const style = getComputedStyle(circle); return"
            " parseFloat(style.strokeDashoffset) - parseFloat(style.strokeWidth) }"
        )
    )
    assert bare >= 2
