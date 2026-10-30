"""
Review tests for the chart rework: bar labels across widths and label sets,
a chart tooltip's Escape among the overlays around it, and the dialog-aware
focus hand-off.
"""

import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import (
    Alert,
    BarChart,
    Button,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    Popover,
    Toast,
)
from tests.browser.conftest import Show
from tests.browser.test_chart import _active, _chart_handle, _hover_middle

# Bar labels

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


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width", [390, 414, 768, 1280])
def test_drawn_bar_labels_never_overlap(show: Show, width: int, theme: str) -> None:
    faults = label_faults(show(*_bar_charts(), width=width, theme=theme))
    assert {k: v["overlaps"] for k, v in faults.items() if v["overlaps"]} == {}
    assert [k for k, v in faults.items() if v["clipped"]] == []


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width", [360, 390, 1280])
def test_no_bar_label_is_dropped_when_all_would_fit(
    show: Show, width: int, theme: str
) -> None:
    faults = label_faults(show(*_bar_charts(), width=width, theme=theme))
    assert {k: v["dropped"] for k, v in faults.items() if v["dropped"]} == {}


# A chart tooltip and Escape


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


# Focus hand-off


def test_dismissing_in_a_drawer_keeps_focus_in_the_drawer(show: Show) -> None:
    page = show(
        Drawer().title("Holder").open().content(Alert().title("Saved").dismissible()),
        Button().content("Outside"),
    )
    panel = page.get_by_role("dialog", name="Holder")
    expect(panel).to_be_visible()
    page.get_by_role("button", name="Dismiss").last.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(panel).to_be_visible()
    page.wait_for_function(
        "() => { const el = document.activeElement;"
        " return document.querySelector('[role=dialog]').contains(el)"
        " && el.getClientRects().length > 0 }",
        timeout=3000,
    )


def test_dismissing_in_a_popover_stays_in_the_popover(show: Show) -> None:
    popover = (
        Popover()
        .title("Notes")
        .trigger(Button().content("Notes"))
        .content(Alert().title("Saved").dismissible(), Button().content("Inside"))
    )
    page = show(popover, Button().content("After"))
    page.get_by_role("button", name="Notes").click()
    expect(page.get_by_role("dialog", name="Notes")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Inside")).to_be_focused()


def test_dismissing_outside_any_dialog_still_reaches_the_page(show: Show) -> None:
    # A dialog elsewhere on the page is not the one the alert sits in.
    page = show(
        Alert().title("Saved").dismissible(),
        html.div(Button().content("Next")),
        Dialog().title("Elsewhere").trigger(Button().content("Open")),
    )
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Next")).to_be_focused()


def test_a_dismissed_toast_hands_focus_to_its_neighbour(show: Show) -> None:
    page = show(
        Toast().title("First").duration(None),
        Toast().title("Second").duration(None),
    )
    close = page.get_by_role("button", name="Dismiss")
    expect(close).to_have_count(2)
    close.first.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("First")).to_have_count(0)
    expect(page.get_by_role("button", name="Dismiss")).to_be_focused()
