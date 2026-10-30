import pytest

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


@pytest.mark.parametrize("value", [33.33333, 100])
def test_the_readout_fits_inside_the_ring(show: Show, value: float) -> None:
    page = show(ProgressRing().value(value).show_value())
    # The text itself, measured against the hole the 5px stroke leaves.
    width = page.get_by_text("%").evaluate(
        "span => { const range = document.createRange();"
        " range.selectNodeContents(span); return range.getBoundingClientRect().width }"
    )
    assert width < 2 * (21 - 2.5) - 4
