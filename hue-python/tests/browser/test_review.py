"""
Review tests for the chart and feedback fixes: the promises their docs make,
in the combinations the fixes did not test themselves.
"""

import pytest
from htmy import html
from playwright.sync_api import Browser, Page, expect

from hue import assets
from hue.js import unsafe
from hue.ui import (
    Alert,
    Banner,
    BarChart,
    Button,
    Dialog,
    DoughnutChart,
    Empty,
    LineChart,
    PieChart,
    Popover,
    Stack,
    TextInput,
)
from tests.browser.conftest import ORIGIN, Show, render_page
from tests.browser.test_chart import _chart_handle
from tests.browser.test_datatable import _table

# Charts


def _hover_middle(page: Page, index: int = 0) -> None:
    box = page.locator("figure canvas").nth(index).bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_function(
        "i => chartAt(i).tooltip.getActiveElements().length", arg=index
    )


def _active(page: Page, index: int = 0) -> int:
    return page.evaluate("i => chartAt(i).tooltip.getActiveElements().length", index)


def test_escape_closes_a_dialog_in_one_press_over_a_chart_tooltip(show: Show) -> None:
    page = show(Dialog().title("Holder").open().content(BarChart.example()))
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    _chart_handle(page)
    _hover_middle(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


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
    expect(dialog).to_be_hidden()
    expect(trigger).to_be_focused()
    page.keyboard.press("Enter")
    expect(dialog).to_be_visible()
    assert _active(page) == 0


_LONG = [
    "Customer success",
    "Professional services",
    "Research and development",
    "Sales and marketing",
    "General administration",
    "Infrastructure",
]


def test_long_bar_labels_at_phone_width_fit_the_canvas(show: Show) -> None:
    chart = BarChart().labels(_LONG).series([5, 9, 3, 7, 2, 4], label="Spend")
    page = show(chart.description("Spend by team."), width=320)
    _chart_handle(page)
    assert page.evaluate("() => document.documentElement.scrollWidth") <= 320
    # Every label is kept, and the longest, at the angle it is drawn, fits
    # in the space the axis was given below the plot.
    fits = page.evaluate(
        """() => {
            const chart = chartAt(0), x = chart.scales.x;
            const angle = x.labelRotation * Math.PI / 180;
            const ctx = chart.ctx;
            ctx.save();
            ctx.font = x._resolveTickFontOptions(0).string;
            const widest = Math.max(...chart.data.labels.map(
                l => ctx.measureText(l).width));
            ctx.restore();
            const needed = widest * Math.sin(angle);
            return { ticks: x.ticks.length, needed, room: chart.height - x.top };
        }"""
    )
    assert fits["ticks"] == len(_LONG)
    assert fits["needed"] <= fits["room"] + 1, fits


def test_a_compared_bar_chart_keeps_every_label_at_phone_width(show: Show) -> None:
    labels = [f"W{i}" for i in range(1, 13)]
    chart = (
        BarChart()
        .labels(labels)
        .series(list(range(12)), label="This year")
        .compare(list(range(12, 0, -1)), label="Last year")
        .description("Weekly.")
    )
    page = show(chart, width=320)
    _chart_handle(page)
    assert page.evaluate("() => chartAt(0).scales.x.ticks.length") == 12


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


_BORDER = "() => chartAt(0).getDatasetMeta(0).data[0].options.borderWidth"


@pytest.mark.parametrize("cls", [PieChart, DoughnutChart])
@pytest.mark.parametrize(
    "slices", [[("Only", 3)], [("Only", 3), ("Nothing", 0)]], ids=["one", "and-zero"]
)
def test_a_lone_slice_draws_no_seam(
    show: Show, cls: type[PieChart], slices: list[tuple[str, float]]
) -> None:
    page = show(cls().slices(slices).description("One."))
    _chart_handle(page)
    assert page.evaluate(_BORDER) == 0


def test_a_lone_slice_draws_no_seam_after_a_theme_change(show: Show) -> None:
    page = show(PieChart().slices([("Only", 3)]).description("One."))
    _chart_handle(page)
    first = page.evaluate("() => chartAt(0).id")
    page.evaluate("() => { document.documentElement.dataset.theme = 'dark' }")
    page.wait_for_function(f"() => chartAt(0) && chartAt(0).id !== {first}")
    assert page.evaluate(_BORDER) == 0


def test_two_slices_keep_their_gap(show: Show) -> None:
    page = show(PieChart().slices([("a", 1), ("b", 2)]).description("Two."))
    _chart_handle(page)
    assert page.evaluate(_BORDER) == 2


def test_the_other_slice_tooltip_gives_its_grouped_share(show: Show) -> None:
    slices = [(f"s{i}", 10) for i in range(8)]
    page = show(PieChart().slices(slices).description("Eight."))
    _chart_handle(page)
    displays = page.evaluate("() => chartAt(0).data.labels")
    assert displays[-1] == "Other"
    # Three slices of ten out of eighty: 37.5, rounded to its nearest percent.
    other = page.evaluate(
        "() => { const c = chartAt(0); const i = c.data.labels.length - 1;"
        " c.tooltip.setActiveElements([{ datasetIndex: 0, index: i }], { x: 0, y: 0 });"
        " c.update('none'); return c.tooltip.body.flatMap(b => b.lines) }"
    )
    assert other == [" 30 (38%)"]


def test_a_percent_pie_tooltip_does_not_repeat_the_share(show: Show) -> None:
    chart = (
        PieChart()
        .slices([("Yes", 0.62), ("No", 0.38)])
        .value_format("percent")
        .description("Votes.")
    )
    page = show(chart)
    _chart_handle(page)
    lines = page.evaluate(
        "() => { const c = chartAt(0);"
        " c.tooltip.setActiveElements([{ datasetIndex: 0, index: 0 }], { x: 0, y: 0 });"
        " c.update('none'); return c.tooltip.body.flatMap(b => b.lines) }"
    )
    assert lines == [" 62%"]
    assert "Share" not in page.locator("thead").inner_text()


# Alert and Banner


@pytest.mark.parametrize("cls", [Alert, Banner])
def test_a_caller_x_data_and_x_show_still_work_with_dismiss(
    show: Show, cls: type[Alert]
) -> None:
    alert = (
        cls()
        .x_data("{ note: 'from the caller' }")
        .x_show(unsafe("true"))
        .title("Saved")
        .content(html.span(**{"x-text": "note"}))
        .dismissible()
    )
    page = show(alert, Button().content("Next"))
    expect(page.get_by_text("from the caller")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Next")).to_be_focused()


def test_an_alert_the_caller_reveals_later_can_still_be_dismissed(show: Show) -> None:
    holder = html.div(
        Button().content("Show").on_click(unsafe("shown = true")),
        Alert().x_show(unsafe("shown")).x_cloak().title("Saved").dismissible(),
        Button().content("After"),
        **{"x-data": "{ shown: false }"},
    )
    page = show(holder)
    expect(page.get_by_text("Saved")).to_be_hidden()
    page.get_by_role("button", name="Show").click()
    expect(page.get_by_text("Saved")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="After")).to_be_focused()


@pytest.mark.parametrize("cls", [Alert, Banner])
def test_dismissing_in_a_stack_leaves_one_gap(show: Show, cls: type[Alert]) -> None:
    page = show(
        Stack().content(
            Button().content("Before"),
            cls().title("Saved").dismissible(),
            Button().content("After"),
        )
    )
    before = page.get_by_role("button", name="Before").bounding_box()
    alert = page.get_by_role("status").bounding_box()
    assert before is not None and alert is not None
    gap = alert["y"] - (before["y"] + before["height"])
    page.get_by_role("button", name="Dismiss").click()
    expect(page.get_by_text("Saved")).to_be_hidden()
    after = page.get_by_role("button", name="After").bounding_box()
    assert after is not None
    assert abs(after["y"] - (before["y"] + before["height"]) - gap) < 1


@pytest.mark.parametrize("cls", [Alert, Banner])
def test_a_dismissible_alert_takes_flex_1(show: Show, cls: type[Alert]) -> None:
    page = show(
        html.div(
            cls().class_("flex-1").title("Saved").dismissible(),
            Button().content("Undo"),
            style="display:flex;gap:8px;width:600px",
        )
    )
    alert = page.get_by_role("status").bounding_box()
    button = page.get_by_role("button", name="Undo").bounding_box()
    assert alert is not None and button is not None
    assert abs(alert["width"] + 8 + button["width"] - 600) < 1


@pytest.mark.parametrize("cls", [Alert, Banner])
def test_dismissing_with_nothing_else_focusable_focuses_the_holder(
    show: Show, cls: type[Alert]
) -> None:
    page = show(html.div(cls().title("Saved").dismissible(), id="holder"))
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.locator("#holder")).to_be_focused()
    expect(page.locator("#holder")).to_have_attribute("tabindex", "-1")


def test_dismissing_one_of_two_alerts_moves_to_the_other(show: Show) -> None:
    page = show(
        Alert().title("First").dismissible(),
        Alert().title("Second").dismissible(),
    )
    page.get_by_role("button", name="Dismiss").first.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("First")).to_be_hidden()
    expect(page.get_by_text("Second")).to_be_visible()
    expect(page.get_by_role("button", name="Dismiss")).to_be_focused()


def test_dismissing_with_focus_elsewhere_leaves_focus_alone(show: Show) -> None:
    page = show(
        TextInput().name("note").label("Note"),
        Alert().title("Saved").dismissible(),
        Button().content("After"),
    )
    page.get_by_label("Note").focus()
    page.get_by_role("button", name="Dismiss").dispatch_event("click")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_label("Note")).to_be_focused()


# Empty


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
