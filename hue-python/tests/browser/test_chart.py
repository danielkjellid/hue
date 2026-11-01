import pytest
from playwright.sync_api import Page

from hue import assets
from hue.ui import (
    BarChart,
    DoughnutChart,
    LineChart,
    PieChart,
)
from tests.browser.conftest import ORIGIN, Show


def _drawn(page: Page) -> None:
    # Chart.js sets display on a canvas once it has laid the chart out.
    page.wait_for_function(
        "() => [...document.querySelectorAll('figure canvas')]"
        ".every(canvas => canvas.style.display === 'block')"
    )


def _overflows(page: Page) -> bool:
    return page.evaluate(
        "() => document.documentElement.scrollWidth > window.innerWidth"
    )


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
