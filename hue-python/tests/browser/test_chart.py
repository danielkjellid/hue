import pytest
from htmy import html
from playwright.sync_api import Browser, Page, expect

from hue import assets
from hue.ui import (
    BarChart,
    BubbleChart,
    Button,
    Dialog,
    DoughnutChart,
    Drawer,
    DropdownMenu,
    LineChart,
    MenuItem,
    PieChart,
    Popover,
    ScatterChart,
)
from tests.browser.conftest import ORIGIN, Show, render_page
from tests.browser.test_datatable import _table

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


def test_escape_hides_a_chart_tooltip(show: Show) -> None:
    page = show(BarChart.example())
    _chart_handle(page)
    box = page.locator("figure canvas").first.bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_function("() => chartAt(0).tooltip.getActiveElements().length")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")
    assert page.evaluate("() => chartAt(0).getActiveElements().length") == 0


def test_a_failed_retry_logs_the_url_it_tried(browser: Browser) -> None:
    page = browser.new_page()
    errors: list[str] = []
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )
    document = render_page(LineChart.example(), LineChart.example())

    def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
        path = request.url.removeprefix(ORIGIN).split("?")[0]
        if path == assets.CHART_JS_URL:
            route.abort()
        elif path in assets.ASSET_ROUTES:
            content, _ = assets.served_asset(path)
            route.fulfill(body=content, content_type=assets.ASSET_ROUTES[path][1])
        else:
            route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/**", fulfil)
    try:
        page.goto(f"{ORIGIN}/")
        expect(page.get_by_role("button", name="Retry")).to_have_count(2)
        retry = page.get_by_role("button", name="Retry").first
        retry.click()
        # Focus comes back to Retry once the second attempt has failed.
        expect(retry).to_be_focused()
        hue_errors = [e for e in errors if e.startswith("hue could not load")]
        # Once per attempt, however many charts were waiting on it.
        assert len(hue_errors) == 2
        assert "chart-bundle.js," in hue_errors[0]
        assert "chart-bundle.js?attempt=1," in hue_errors[1]
    finally:
        page.close()


def _hover_middle(page: Page, index: int = 0) -> None:
    box = page.locator("figure canvas").nth(index).bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_function(
        "i => chartAt(i).tooltip.getActiveElements().length", arg=index
    )


def _active(page: Page, index: int = 0) -> int:
    return page.evaluate("i => chartAt(i).tooltip.getActiveElements().length", index)


def test_escape_hides_a_chart_tooltip_before_its_dialog(show: Show) -> None:
    page = show(Dialog().title("Holder").open().content(BarChart.example()))
    dialog = page.get_by_role("dialog", name="Holder")
    expect(dialog).to_be_visible()
    _chart_handle(page)
    _hover_middle(page)
    # The tooltip takes the first Escape and stops it there, as hue's
    # Tooltip does, so the dialog stays open.
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


def test_escape_over_a_chart_tooltip_keeps_a_table_selection(show: Show) -> None:
    page = show(BarChart.example(), _table("invoices"))
    _chart_handle(page)
    page.get_by_role("checkbox", name="Select all").check()
    expect(page.get_by_role("group", name="Selected rows")).to_be_visible()
    _hover_middle(page)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")
    expect(page.get_by_role("group", name="Selected rows")).to_be_visible()


def test_escape_closes_a_popover_over_a_chart_and_returns_focus(show: Show) -> None:
    popover = (
        Popover()
        .title("Sharing")
        .trigger(Button().content("Share"))
        .content(Button().content("Copy link"))
    )
    page = show(BarChart.example(), popover)
    _chart_handle(page)
    page.get_by_role("button", name="Share").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    page.get_by_role("button", name="Copy link").focus()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("button", name="Share")).to_be_focused()


def test_escape_without_a_tooltip_still_clears_a_table_selection(show: Show) -> None:
    page = show(BarChart.example(), _table("invoices"))
    _chart_handle(page)
    page.get_by_role("checkbox", name="Select all").check()
    expect(page.get_by_role("group", name="Selected rows")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("group", name="Selected rows")).to_be_hidden()
    expect(page.locator("input[type=checkbox]:checked")).to_have_count(0)


def test_escape_hides_only_the_tooltip_that_shows(show: Show) -> None:
    page = show(BarChart.example(), LineChart.example(), PieChart.example())
    _chart_handle(page)
    _hover_middle(page, 1)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(1).tooltip.getActiveElements().length")
    assert _active(page, 0) == 0
    assert _active(page, 2) == 0
    # Moving the pointer brings the tooltip back.
    _hover_middle(page, 0)


def test_escape_hides_a_tooltip_on_a_chart_redrawn_for_the_theme(show: Show) -> None:
    page = show(BarChart.example())
    _chart_handle(page)
    first = page.evaluate("() => chartAt(0).id")
    page.evaluate("() => { document.documentElement.dataset.theme = 'dark' }")
    page.wait_for_function(f"() => chartAt(0) && chartAt(0).id !== {first}")
    _hover_middle(page)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")


def test_escape_on_a_chart_that_failed_to_load_raises_nothing(
    browser: Browser,
) -> None:
    page = browser.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    document = render_page(LineChart.example())

    def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
        path = request.url.removeprefix(ORIGIN).split("?")[0]
        if path == assets.CHART_JS_URL:
            route.abort()
        elif path in assets.ASSET_ROUTES:
            content, _ = assets.served_asset(path)
            route.fulfill(body=content, content_type=assets.ASSET_ROUTES[path][1])
        else:
            route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/**", fulfil)
    try:
        page.goto(f"{ORIGIN}/")
        expect(page.get_by_role("button", name="Retry")).to_be_visible()
        page.keyboard.press("Escape")
        # A second key, so the first one's handler has run by the time the
        # page answers.
        page.keyboard.press("Shift")
        page.evaluate("() => new Promise(requestAnimationFrame)")
        assert errors == []
    finally:
        page.close()


def test_a_chart_tooltip_is_gone_when_its_dialog_reopens(show: Show) -> None:
    page = show(
        Dialog()
        .title("Holder")
        .trigger(Button().content("Open"))
        .content(BarChart.example())
    )
    trigger = page.get_by_role("button", name="Open")
    trigger.click()
    dialog = page.get_by_role("dialog", name="Holder")
    expect(dialog).to_be_visible()
    _chart_handle(page)
    # The panel animates in, and the chart follows its size once it shows.
    page.wait_for_function(
        "() => document.getAnimations().every(a => a.playState !== 'running')"
        " && chartAt(0).width > 0"
    )
    _hover_middle(page)
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(trigger).to_be_focused()
    page.keyboard.press("Enter")
    expect(dialog).to_be_visible()
    assert _active(page) == 0


def test_a_line_chart_still_skips_labels_flat_at_phone_width(show: Show) -> None:
    labels = [f"2026-01-{day:02d}" for day in range(1, 31)]
    chart = (
        LineChart()
        .labels(labels)
        .series(list(range(30)), label="Sign-ups")
        .description("Daily.")
    )
    page = show(chart, width=320)
    _chart_handle(page)
    x = page.evaluate(
        "() => ({ ticks: chartAt(0).scales.x.ticks.length,"
        " rotation: chartAt(0).scales.x.labelRotation })"
    )
    assert x["ticks"] < 30
    assert x["rotation"] == 0


_BORDER = "i => chartAt(i).getDatasetMeta(0).data[0].options.borderWidth"


def test_a_lone_slice_draws_no_seam_and_two_keep_their_gap(show: Show) -> None:
    page = show(
        PieChart().slices([("Only", 3)]).description("One."),
        DoughnutChart().slices([("Only", 3), ("Nothing", 0)]).description("One."),
        PieChart().slices([("a", 1), ("b", 2)]).description("Two."),
    )
    _chart_handle(page)
    assert [page.evaluate(_BORDER, i) for i in range(3)] == [0, 0, 2]
    first = page.evaluate("() => chartAt(0).id")
    page.evaluate("() => { document.documentElement.dataset.theme = 'dark' }")
    page.wait_for_function(f"() => chartAt(0) && chartAt(0).id !== {first}")
    assert page.evaluate(_BORDER, 0) == 0


_TOOLTIP_AT = """([i, index]) => { const c = chartAt(i);
    c.tooltip.setActiveElements([{ datasetIndex: 0, index }], { x: 0, y: 0 });
    c.update('none'); return c.tooltip.body.flatMap(b => b.lines) }"""


def test_a_pie_tooltip_gives_the_share_once(show: Show) -> None:
    page = show(
        PieChart().slices([(f"s{i}", 10) for i in range(8)]).description("Eight."),
        PieChart()
        .slices([("Yes", 0.62), ("No", 0.38)])
        .value_format("percent")
        .description("Votes."),
    )
    _chart_handle(page)
    labels = page.evaluate("() => chartAt(0).data.labels")
    assert labels[-1] == "Other"
    # Three slices of ten out of eighty: 37.5, rounded to its nearest percent.
    assert page.evaluate(_TOOLTIP_AT, [0, len(labels) - 1]) == [" 30 (38%)"]
    # A share already, so it is not repeated.
    assert page.evaluate(_TOOLTIP_AT, [1, 0]) == [" 62%"]


LABEL_SETS = {
    "quarters": ["Q1", "Q2", "Q3", "Q4"],
    "months": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
    "long3": [
        "Professional services and consulting",
        "Research and development",
        "General and administrative",
    ],
    "long6": [
        "Customer success",
        "Professional services",
        "Research and development",
        "Sales and marketing",
        "General administration",
        "Infrastructure",
    ],
    "mixed": [
        "A",
        "Professional services",
        "B2B",
        "Research and development",
        "X",
        "Ops",
        "Sales and marketing department",
    ],
    "numbers40": [str(i) for i in range(1, 41)],
    "days31": [f"Oct {day}" for day in range(1, 32)],
    "cjk": ["東京都", "大阪府", "北海道", "神奈川県", "愛知県", "福岡県", "京都府"],
    "scripts": ["Paris", "القاهرة", "मुंबई", "서울특별시", "São Paulo", "Москва"],
    "status": ["Paid", "Pending", "Draft", "Declined", "Refunded"],
}

# What a drawn chart's x axis gets wrong, if anything. Tilted labels sit a
# tick apart along the axis, which is dx * sin(angle) across their lines;
# flat ones need half of each label's width either side of the tick.
_LABEL_FAULTS = """i => {
    const c = chartAt(i), x = c.scales.x, ctx = c.ctx;
    const font = x._resolveTickFontOptions(0), line = font.lineHeight;
    ctx.save();
    ctx.font = font.string;
    const width = label => ctx.measureText(label).width;
    const angle = x.labelRotation * Math.PI / 180;
    const all = c.data.labels, drawn = x.ticks;
    const at = drawn.map(t => x.getPixelForValue(t.value));
    const overlaps = [];
    for (let j = 1; j < drawn.length; j++) {
        const dx = at[j] - at[j - 1];
        const gap = angle
            ? dx * Math.sin(angle) - line
            : dx - (width(drawn[j].label) + width(drawn[j - 1].label)) / 2;
        if (gap < -0.5) overlaps.push(drawn[j - 1].label + " | " + drawn[j].label);
    }
    const slot = x.width / all.length;
    const fitsFlat = slot >= Math.max(...all.map(width)) + 3;
    const fitsTilted = angle > 0 && slot * Math.sin(angle) >= line + 1;
    const widest = Math.max(...drawn.map(t => width(t.label)));
    const depth = widest * Math.sin(angle) + line * Math.cos(angle);
    ctx.restore();
    return {
        overlaps,
        dropped: (fitsFlat || fitsTilted) ? all.length - drawn.length : 0,
        clipped: depth > c.height - x.top + 1,
        drawn: drawn.length,
    };
}"""


def _bar_charts() -> list[BarChart]:
    charts = []
    for labels in LABEL_SETS.values():
        values = list(range(len(labels)))
        charts.append(BarChart().labels(labels).series(values, label="A"))
        charts.append(
            BarChart()
            .labels(labels)
            .series(values, label="A")
            .compare(values[::-1], label="B")
        )
    return [chart.description("Bars.") for chart in charts]


def label_faults(page: Page) -> dict[str, dict]:
    _chart_handle(page)
    faults = {}
    for i, name in enumerate(n + c for n in LABEL_SETS for c in ("", "+compare")):
        found = page.evaluate(_LABEL_FAULTS, i)
        assert found["drawn"] >= 1, name
        faults[name] = found
    return faults


@pytest.mark.parametrize("width", [320, 1280])
def test_drawn_bar_labels_never_overlap(show: Show, width: int) -> None:
    page = show(*_bar_charts(), width=width)
    faults = label_faults(page)
    assert not _overflows(page)
    assert {k: v["overlaps"] for k, v in faults.items() if v["overlaps"]} == {}
    assert [k for k, v in faults.items() if v["clipped"]] == []


def _settle(page: Page) -> None:
    # Overlays animate in, and the chart follows its holder's size.
    page.wait_for_function(
        "() => document.getAnimations().every(a => a.playState !== 'running')"
        " && chartAt(0).width > 0"
    )


@pytest.mark.parametrize("overlay", ["dialog", "drawer"])
def test_a_tooltip_in_an_overlay_takes_the_first_escape(
    show: Show, overlay: str
) -> None:
    holder = Dialog() if overlay == "dialog" else Drawer().side("end")
    page = show(holder.title("Holder").open().content(BarChart.example()))
    panel = page.get_by_role("dialog", name="Holder")
    expect(panel).to_be_visible()
    _chart_handle(page)
    _settle(page)
    _hover_middle(page)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")
    expect(panel).to_be_visible()
    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()


def test_a_tooltip_in_a_popover_takes_the_first_escape(show: Show) -> None:
    popover = (
        Popover()
        .title("Chart")
        .trigger(Button().content("Show"))
        .content(BarChart.example())
    )
    page = show(popover, Button().content("After"))
    page.get_by_role("button", name="Show").click()
    panel = page.get_by_role("dialog", name="Chart")
    expect(panel).to_be_visible()
    _chart_handle(page)
    _settle(page)
    # Focus inside the panel, off the trigger whose popup is open.
    page.locator("figure").focus()
    _hover_middle(page)
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")
    expect(panel).to_be_visible()
    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(page.get_by_role("button", name="Show")).to_be_focused()


def test_an_open_popup_on_the_focused_trigger_closes_first(show: Show) -> None:
    popover = (
        Popover()
        .title("Sharing")
        .trigger(Button().content("Share"))
        .content(Button().content("Copy link"))
    )
    page = show(BarChart.example(), popover)
    _chart_handle(page)
    page.get_by_role("button", name="Share").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    page.get_by_role("button", name="Share").focus()
    _hover_middle(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    assert _active(page) == 1
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")


def test_escape_sent_to_the_window_hides_a_chart_tooltip(show: Show) -> None:
    page = show(BarChart.example())
    _chart_handle(page)
    _hover_middle(page)
    page.evaluate(
        "() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))"
    )
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")


def test_escape_hides_a_tooltip_in_a_scrolled_box(show: Show) -> None:
    page = show(
        html.div(
            html.div(style="height:900px"),
            BarChart.example(),
            id="box",
            style="height:300px;overflow:auto",
        ),
        html.div(style="height:2000px"),
    )
    _chart_handle(page)
    page.evaluate("() => window.scrollTo(0, 16)")
    page.locator("#box").evaluate("box => { box.scrollTop = 880 }")
    page.wait_for_function("() => document.querySelector('#box').scrollTop === 880")
    # Inside the part of the chart the box shows.
    box = page.locator("#box").bounding_box()
    canvas = page.locator("figure canvas").bounding_box()
    assert box is not None and canvas is not None
    page.mouse.move(canvas["x"] + canvas["width"] / 2, box["y"] + 150)
    page.wait_for_function("() => chartAt(0).tooltip.getActiveElements().length")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !chartAt(0).tooltip.getActiveElements().length")


def test_escape_with_no_tooltip_closes_a_menu_beside_a_chart(show: Show) -> None:
    menu = (
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(MenuItem().content("Rename"), MenuItem().content("Delete"))
    )
    page = show(BarChart.example(), menu)
    _chart_handle(page)
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
    expect(page.get_by_role("button", name="Actions")).to_be_focused()


def test_escape_closes_a_focused_menu_before_a_hovered_chart_tooltip(
    show: Show,
) -> None:
    menu = (
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(MenuItem().content("Rename"), MenuItem().content("Delete"))
    )
    page = show(BarChart.example(), menu)
    _chart_handle(page)
    page.get_by_role("button", name="Actions").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    _hover_middle(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
