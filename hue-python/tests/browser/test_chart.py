from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import BarChart, BubbleChart, LineChart, ScatterChart
from tests.browser.conftest import Show

_GRID = "display:grid;grid-template-columns:1fr 1fr;gap:16px"


def _drawn(page: Page) -> None:
    # Chart.js sets display on a canvas once it has laid the chart out.
    page.wait_for_function(
        "() => [...document.querySelectorAll('figure canvas')]"
        ".every(canvas => canvas.style.display === 'block')"
    )


def _settled(page: Page) -> None:
    # Chart.js follows its holder on the next resize observation.
    page.wait_for_function(
        "() => [...document.querySelectorAll('figure canvas')].every(c =>"
        " Math.abs(c.getBoundingClientRect().width"
        " - c.parentElement.getBoundingClientRect().width) < 1)"
    )


def _holder_size(page: Page, index: int = 0) -> dict[str, float]:
    return (
        page.locator("figure canvas")
        .nth(index)
        .evaluate("canvas => canvas.parentElement.getBoundingClientRect().toJSON()")
    )


def _overflows(page: Page) -> bool:
    return page.evaluate(
        "() => document.documentElement.scrollWidth > window.innerWidth"
    )


def test_a_chart_shrinks_back_to_five_by_two_after_being_wide(show: Show) -> None:
    page = show(LineChart.example())
    _drawn(page)
    page.set_viewport_size({"width": 500, "height": 800})
    page.wait_for_function("() => window.innerWidth === 500")
    _settled(page)
    box = _holder_size(page)
    assert abs(box["height"] - box["width"] * 2 / 5) < 1


def test_a_chart_in_a_flex_row_shrinks_with_its_cell(show: Show) -> None:
    page = show(
        html.div(
            html.div(LineChart.example(), class_="flex-1"),
            html.div(BarChart.example(), class_="flex-1"),
            class_="flex gap-4",
        )
    )
    _drawn(page)
    for width in (768, 390):
        page.set_viewport_size({"width": width, "height": 800})
        page.wait_for_function(f"() => window.innerWidth === {width}")
        _settled(page)
        assert not _overflows(page)


def test_a_chart_in_a_grid_cell_shrinks_with_it(show: Show) -> None:
    page = show(html.div(LineChart.example(), BarChart.example(), style=_GRID))
    _drawn(page)
    for width in (768, 390):
        page.set_viewport_size({"width": width, "height": 800})
        page.wait_for_function(f"() => window.innerWidth === {width}")
        _settled(page)
        assert not _overflows(page)


def test_the_table_for_screen_readers_does_not_widen_a_phone_page(show: Show) -> None:
    chart = (
        LineChart()
        .labels(["The first day of a long reporting period"] * 3)
        .series([1, 2, 3], label="A series named at some considerable length")
        .compare([3, 2, 1], label="Another series with a similarly long name")
        .description("Two long-named series.")
    )
    page = show(chart, width=390)
    _drawn(page)
    assert not _overflows(page)


def test_point_charts_stay_readable_at_phone_width(show: Show) -> None:
    page = show(ScatterChart.example(), BubbleChart.example(), width=390)
    _drawn(page)
    assert _holder_size(page, 0)["height"] >= 192
    assert _holder_size(page, 1)["height"] >= 192


def test_a_point_chart_shares_a_grid_row_evenly(show: Show) -> None:
    # Below 480px wide a 5:2 box with a 192px floor used to hold its cell
    # open, which squashed the cell beside it.
    page = show(html.div(ScatterChart.example(), LineChart.example(), style=_GRID))
    _drawn(page)
    for width in (1280, 768, 390):
        page.set_viewport_size({"width": width, "height": 800})
        page.wait_for_function(f"() => window.innerWidth === {width}")
        _settled(page)
        assert not _overflows(page)
        point, line = _holder_size(page, 0), _holder_size(page, 1)
        assert abs(point["width"] - line["width"]) < 1


def test_a_point_chart_is_five_by_two_when_that_is_tall_enough(show: Show) -> None:
    page = show(ScatterChart.example(), LineChart.example())
    _drawn(page)
    for index in (0, 1):
        box = _holder_size(page, index)
        assert abs(box["height"] - box["width"] * 2 / 5) < 1


def test_the_retry_overlay_stays_inside_a_short_chart(show: Show) -> None:
    page = show(html.div(LineChart.example(), style="width:80px"))
    _drawn(page)
    # Failing for real logs a console error, which fails the test.
    page.evaluate(
        "() => { Alpine.$data(document.querySelector('figure')).failed = true }"
    )
    retry = page.get_by_role("button", name="Retry")
    expect(retry).to_be_visible()
    holder = _holder_size(page)
    for part in (page.get_by_text("Unable to load chart."), retry):
        box = part.bounding_box()
        assert box is not None
        assert holder["top"] <= box["y"]
        assert box["y"] + box["height"] <= holder["bottom"]
    # Neither squashed: a small control is 32px tall.
    assert retry.bounding_box()["height"] >= 32  # type: ignore[index]
    # Nor under the canvas, which would take the click.
    retry.click(trial=True, timeout=2000)
