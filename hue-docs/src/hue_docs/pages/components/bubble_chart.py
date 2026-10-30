from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import BubbleChart, ScatterChart

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel
from hue_docs.pages.components import _charts

# Live


def teams() -> BubbleChart:
    return (
        BubbleChart()
        .series(
            [(2, 40, 120), (5, 55, 340), (8, 48, 90), (11, 70, 410)],
            label="Teams",
        )
        .x_label("Engineers")
        .y_label("Deploys per week")
        .size_label("Incidents fixed")
        .description("Larger teams deploy more and fix more incidents.")
    )


# Series


def two_series() -> BubbleChart:
    return (
        BubbleChart()
        .series([(2, 40, 120), (5, 55, 340), (8, 48, 90)], label="Platform")
        .series([(3, 22, 60), (6, 35, 150), (10, 52, 220)], label="Product")
        .x_label("Engineers")
        .y_label("Deploys per week")
        .size_label("Incidents fixed")
        .description("Platform teams deploy more often than product teams.")
    )


# Formats


def number() -> BubbleChart:
    return (
        BubbleChart()
        .series([(14, 3.2, 40), (32, 4.1, 120), (51, 4.6, 260)], label="Apps")
        .x_label("Releases")
        .y_label("Rating")
        .size_label("Reviews")
        .x_format("number")
        .y_format("number")
        .description("Apps that release more are rated higher.")
    )


def percent() -> BubbleChart:
    return (
        BubbleChart()
        .series(
            [(0.08, 0.31, 1200), (0.15, 0.27, 3400), (0.22, 0.19, 2100)],
            label="Plans",
        )
        .x_label("Discount")
        .y_label("Churn")
        .size_label("Customers")
        .x_format("percent")
        .y_format("percent")
        .description("Deeper discounts come with lower churn.")
    )


def currency() -> BubbleChart:
    return (
        BubbleChart()
        .series(
            [(1200, 8400, 30), (2500, 14100, 55), (5300, 27500, 90)],
            label="Campaigns",
        )
        .x_label("Ad spend")
        .y_label("Revenue")
        .size_label("Orders")
        .x_format("currency", currency="USD")
        .y_format("currency", currency="USD")
        .description("Revenue and orders both grow with ad spend.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.point_data("BubbleChart", "`(x, y, size)`"),
        pr.code(
            "(\n"
            "    BubbleChart()\n"
            '    .series([(2, 40, 120), (5, 55, 340), (8, 48, 90)], label="Teams")\n'
            '    .x_label("Engineers")\n'
            '    .y_label("Deploys per week")\n'
            '    .size_label("Incidents fixed")\n'
            '    .description("Larger teams deploy more and fix more incidents.")\n'
            ")"
        ),
        *_charts.point_refusals("BubbleChart"),
        pr.h2("How BubbleChart sizes its bubbles"),
        pr.p(
            "`size_label()` names what a bubble's size stands for. It is "
            "required, like the axis labels, and heads the size column of the "
            "table. A size cannot be negative. `series()` raises a `ValueError` "
            "for one, and for a point that is not three numbers."
        ),
        pr.p(
            "A bubble's radius is 3px plus up to 17px more, growing with the "
            "square root of its size against the largest size on the chart, so "
            "its area grows roughly with the size and the largest bubble has a "
            "20px radius. The chart keeps a margin around the plot, so a large "
            "bubble at the edge is not cut off."
        ),
        *_charts.formats("BubbleChart", "`x_format()` and `y_format()`"),
        pr.p(
            "The formats cover the two axes only. A `BubbleChart` always writes "
            "the size as a plain number, since it counts something of its own."
        ),
        *_charts.size("BubbleChart", min_height=192),
        *_charts.loading("BubbleChart"),
        *_charts.theme("BubbleChart"),
    )


PAGE = ComponentPage(
    BubbleChart,
    lede=(
        "A bubble chart is a scatter chart whose points carry a third number, "
        "drawn as bubbles that grow with it. It can draw up to five sets of "
        "bubbles, each in its own colour."
    ),
    usage=_usage,
    panels=[
        panel("Live", teams, layout="stack", hint="Hover a bubble for its values"),
        panel(
            "Series",
            two_series,
            layout="stack",
            hint="A second `series()` adds a colour and a legend",
        ),
        panel(
            "Formats",
            number,
            percent,
            currency,
            layout="stack",
            hint="`x_format()` and `y_format()` write the axes. Sizes stay numbers",
        ),
    ],
    notes=[
        *_charts.notes("BubbleChart"),
        Note(
            "note",
            "Sizes are scaled against the largest on the chart, so the same "
            "size draws a different bubble on another chart.",
        ),
    ],
    related=[ScatterChart],
)
