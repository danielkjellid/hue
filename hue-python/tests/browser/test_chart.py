from htmy import html
from playwright.sync_api import Page, expect

from hue import assets
from hue.ui import BarChart, BubbleChart, LineChart, PieChart, ScatterChart
from tests.browser.conftest import ORIGIN, Show

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


# The chart behind a canvas, through the Chart class the bundle draws with.
# A throwaway chart hands over the class, which the bundle does not export.
_CHART_OF = f"""async index => {{
    const {{ draw }} = await import({ORIGIN + assets.CHART_JS_URL!r});
    const holder = document.createElement("div");
    holder.append(document.createElement("canvas"));
    document.body.append(holder);
    const probe = draw(holder.firstChild, {{
        kind: "pie", labels: ["a"], series: [{{ values: [1], display: ["1"] }}]
    }});
    const Chart = probe.constructor;
    probe.destroy();
    holder.remove();
    window.chartAt = i => Chart.getChart(document.querySelectorAll("figure canvas")[i]);
}}"""


def _chart_handle(page: Page) -> None:
    _drawn(page)
    page.evaluate(_CHART_OF, 0)


def _tooltip_lines(page: Page, index: int = 0) -> list[str]:
    return page.evaluate(
        "i => { const t = chartAt(i).tooltip;"
        " return t.opacity ? t.body.flatMap(b => b.lines) : [] }",
        index,
    )


def _hover_first_slice(page: Page) -> None:
    # A point just inside the top of the pie, which is the first slice's.
    box = page.locator("figure canvas").first.bounding_box()
    assert box is not None
    point = page.evaluate(
        "() => { const arc = chartAt(0).getDatasetMeta(0).data[0];"
        " const angle = (arc.startAngle + arc.endAngle) / 2;"
        " const r = (arc.innerRadius + arc.outerRadius) / 2;"
        " return [arc.x + r * Math.cos(angle), arc.y + r * Math.sin(angle)] }"
    )
    page.mouse.move(box["x"] + point[0], box["y"] + point[1])


def test_hovering_a_slice_shows_the_share_the_table_gives(show: Show) -> None:
    slices = [("Pro", 60), ("Starter", 220), ("Legacy", 15), ("Team", 845)]
    page = show(PieChart().slices(slices).description("Plans."))
    _chart_handle(page)
    _hover_first_slice(page)
    page.wait_for_function("() => chartAt(0).tooltip.opacity === 1")
    share = page.locator("tbody tr").first.locator("td").nth(1).inner_text()
    assert _tooltip_lines(page) == [f" 60 ({share})"]


def test_hovering_a_bar_chart_lists_the_series_at_that_label(show: Show) -> None:
    page = show(BarChart.example())
    _chart_handle(page)
    box = page.locator("figure canvas").first.bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_function("() => chartAt(0).tooltip.opacity === 1")
    assert len(_tooltip_lines(page)) == 1
