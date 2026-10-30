from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import AreaChart, BarChart, LineChart

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, panel
from hue_docs.pages.components import _charts

# Live


def revenue() -> AreaChart:
    return (
        AreaChart()
        .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        .series([3100, 3400, 3200, 4100, 3900, 4600, 4829], label="This week")
        .compare([2900, 3000, 2800, 3300, 3100, 3600, 3700], label="Last week")
        .y_format("currency", currency="USD")
        .description(
            "Revenue rose from 3,100.00 USD to 4,829.00 USD, above last week every day."
        )
    )


# Anatomy


def one_series() -> AreaChart:
    return (
        AreaChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([420, 510, 480, 620, 690, 760], label="Storage used")
        .description("Storage grew from 420 to 760 GB over six months.")
    )


def with_compare() -> AreaChart:
    return (
        AreaChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([420, 510, 480, 620, 690, 760], label="2026")
        .compare([310, 340, 400, 390, 450, 520], label="2025")
        .description("Storage used was above 2025 in every month of 2026.")
    )


# Formats


def number() -> AreaChart:
    return (
        AreaChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([8200, 9100, 8800, 10400, 11900, 12600], label="Requests")
        .y_format("number")
        .description("Requests rose from 8,200 to 12,600.")
    )


def percent() -> AreaChart:
    return (
        AreaChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([0.31, 0.36, 0.42, 0.45, 0.52, 0.58], label="Disk used")
        .y_format("percent")
        .description("The disk went from 31% to 58% full.")
    )


def currency() -> AreaChart:
    return (
        AreaChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([12800, 14100, 13700, 16900, 18200, 21400], label="Recurring revenue")
        .y_format("currency", currency="EUR")
        .description("Recurring revenue grew from 12,800 to 21,400 EUR.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.series_data("AreaChart"),
        pr.h2("How AreaChart draws its series"),
        pr.p(
            "An `AreaChart` is a `LineChart` with the area under the main series "
            "filled. The fill runs down to zero as a gradient of the accent, "
            "fading out toward the bottom. A `compare()` series is not filled. "
            "It is a thinner dashed line in the muted grey, painted beneath "
            "the main one. Only the last point of each line is marked."
        ),
        *_charts.formats("AreaChart", "`y_format()`"),
        *_charts.size("AreaChart"),
        *_charts.loading("AreaChart"),
        *_charts.theme("AreaChart"),
    )


PAGE = ComponentPage(
    AreaChart,
    lede=(
        "An area chart is a line chart with the space under its main series "
        "filled, for a total whose size matters as much as its direction. Like "
        "a line chart, it can draw a muted second series to compare against."
    ),
    usage=_usage,
    panels=[
        panel("Live", revenue, layout="stack", hint="Hover it for the tooltip"),
        panel(
            "Anatomy",
            one_series,
            with_compare,
            layout="stack",
            hint="The legend appears with `compare()`",
        ),
        panel(
            "Formats",
            number,
            percent,
            currency,
            layout="stack",
            hint="`y_format()` writes the axis, the tooltip and the table",
        ),
    ],
    notes=_charts.notes("AreaChart"),
    related=[LineChart, BarChart],
)
