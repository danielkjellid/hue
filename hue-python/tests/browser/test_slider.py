from itertools import groupby

from playwright.sync_api import Page, expect

from hue.ui import Slider
from tests.browser._fields import row_of_pixels, still, token
from tests.browser.conftest import Show


def _invalid() -> Slider:
    return Slider().name("seats").label("Seats").value(50).error("Too many")


def _tone_after_thumb(page: Page, tone: str) -> int:
    """
    How many pixels of tone lie just past the thumb's right edge, along the
    middle of the track: the thumb's border, and a focus ring if it has one.
    """
    box = page.get_by_role("slider").bounding_box()
    assert box is not None
    row = row_of_pixels(page, box["x"], box["y"] + box["height"] / 2, int(box["width"]))
    runs = [(colour, len(list(run))) for colour, run in groupby(row)]
    # The thumb's face is the one long run of white inside the track.
    surface = token(page, "surface")
    face = next(i for i, (colour, n) in enumerate(runs) if colour == surface and n > 8)
    edge = sum(n for _, n in runs[: face + 1])
    return sum(_near(colour, tone) for colour in row[edge : edge + 8])


def _near(colour: str, tone: str) -> bool:
    # Within a margin, since how an edge is anti-aliased differs by platform.
    def channels(rgb: str) -> list[int]:
        return [int(c) for c in rgb[4:-1].split(",")]

    pairs = zip(channels(colour), channels(tone), strict=True)
    return all(abs(a - b) <= 48 for a, b in pairs)


def test_invalid_slider_is_red_and_keyboard_focus_draws_a_two_pixel_ring(
    show: Show,
) -> None:
    page = still(show(_invalid()))
    slider = page.get_by_role("slider")
    # The fill to the left of the thumb.
    box = slider.bounding_box()
    assert box is not None
    start = row_of_pixels(page, box["x"] + 4, box["y"] + box["height"] / 2, 1)
    assert start == [token(page, "danger")]
    danger = token(page, "danger")
    resting = _tone_after_thumb(page, danger)
    page.keyboard.press("Tab")
    expect(page.get_by_role("slider")).to_be_focused()
    # A 1px line would add one pixel to the border; the ring adds two.
    assert _tone_after_thumb(page, danger) >= resting + 2
