from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import BubbleChart, LineChart, ScatterChart

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, panel
from hue_docs.pages.components import _charts

# Live


def margin_by_basket() -> ScatterChart:
    return (
        ScatterChart()
        .series(
            [(12, 0.18), (25, 0.22), (31, 0.35), (44, 0.41), (58, 0.47)],
            label="Orders",
        )
        .x_label("Basket size")
        .y_label("Margin")
        .y_format("percent")
        .description("Margin grows with basket size, from 18% to 47%.")
    )


# Series


def two_series() -> ScatterChart:
    return (
        ScatterChart()
        .series(
            [(12, 0.18), (25, 0.22), (31, 0.35), (44, 0.41), (58, 0.47)],
            label="Online",
        )
        .series([(9, 0.12), (20, 0.15), (36, 0.21), (47, 0.26)], label="In store")
        .x_label("Basket size")
        .y_label("Margin")
        .x_format("currency", currency="EUR")
        .y_format("percent")
        .description("Margin grows with basket size, faster online.")
    )


# Formats


def number() -> ScatterChart:
    return (
        ScatterChart()
        .series(
            [(120, 1.4), (240, 1.9), (310, 2.2), (480, 2.6), (650, 3.1)],
            label="Pages",
        )
        .x_label("Kilobytes")
        .y_label("Seconds to load")
        .x_format("number")
        .y_format("number")
        .description("Heavier pages take longer to load, up to 3.1 seconds.")
    )


def percent() -> ScatterChart:
    return (
        ScatterChart()
        .series(
            [(0.12, 0.41), (0.25, 0.37), (0.38, 0.30), (0.51, 0.22), (0.66, 0.18)],
            label="Campaigns",
        )
        .x_label("Discount")
        .y_label("Margin")
        .x_format("percent")
        .y_format("percent")
        .description("Margin falls from 41% to 18% as the discount deepens.")
    )


def currency() -> ScatterChart:
    return (
        ScatterChart()
        .series(
            [(1200, 8400), (2500, 14100), (4100, 19800), (5300, 27500)],
            label="Campaigns",
        )
        .x_label("Ad spend")
        .y_label("Revenue")
        .x_format("currency", currency="USD")
        .y_format("currency", currency="USD")
        .description("Revenue grows with ad spend, to 27,500 USD.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.point_data("ScatterChart", "`(x, y)`"),
        pr.code(
            "(\n"
            "    ScatterChart()\n"
            '    .series([(12, 0.18), (25, 0.22), (31, 0.35)], label="Online")\n'
            '    .series([(9, 0.12), (20, 0.15), (36, 0.21)], label="In store")\n'
            '    .x_label("Basket size")\n'
            '    .y_label("Margin")\n'
            '    .y_format("percent")\n'
            '    .description("Margin grows with basket size, faster online.")\n'
            ")"
        ),
        *_charts.point_refusals("ScatterChart"),
        pr.p(
            "A `ScatterChart` raises a `ValueError` on a point with a third "
            "number, a size. A point with a size belongs on a `BubbleChart`."
        ),
        *_charts.formats("ScatterChart", "`x_format()` and `y_format()`"),
        pr.p(
            "Each axis has its own format, so a `ScatterChart` can put money "
            "along the bottom and a percentage up the side."
        ),
        *_charts.size("ScatterChart", min_height=192),
        *_charts.loading("ScatterChart"),
        *_charts.theme("ScatterChart"),
    )


PAGE = ComponentPage(
    ScatterChart,
    lede=(
        "A scatter chart places points by two numbers, to show how one varies "
        "with the other. It can draw up to five sets of points, each in its own "
        "colour."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live", margin_by_basket, layout="stack", hint="Hover a point to read it"
        ),
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
            hint="`x_format()` and `y_format()` write each axis on its own",
        ),
    ],
    notes=_charts.notes("ScatterChart"),
    related=[BubbleChart, LineChart],
)
