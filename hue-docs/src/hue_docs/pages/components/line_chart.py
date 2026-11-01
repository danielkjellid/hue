from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import AreaChart, BarChart, LineChart

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, panel
from hue_docs.pages.components import _charts

# Live


def sign_ups() -> LineChart:
    return (
        LineChart()
        .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        .series([212, 240, 198, 260, 251, 305, 330], label="This week")
        .compare([190, 205, 188, 222, 230, 260, 270], label="Last week")
        .description("Sign-ups rose from 212 to 330, above last week every day.")
    )


# Anatomy


def one_series() -> LineChart:
    return (
        LineChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([1840, 2010, 1960, 2240, 2380, 2510], label="Active users")
        .description("Active users grew from 1,840 to 2,510 over six months.")
    )


def with_compare() -> LineChart:
    return (
        LineChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([1840, 2010, 1960, 2240, 2380, 2510], label="2026")
        .compare([1620, 1700, 1810, 1790, 1900, 2050], label="2025")
        .description("Active users were above 2025 in every month of 2026.")
    )


# Formats


def number() -> LineChart:
    return (
        LineChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([12400, 13100, 12900, 14800, 15200, 16900], label="Page views")
        .y_format("number")
        .description("Page views rose from 12,400 to 16,900.")
    )


def percent() -> LineChart:
    return (
        LineChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([0.92, 0.94, 0.91, 0.96, 0.97, 0.98], label="Uptime")
        .y_format("percent")
        .description("Uptime climbed from 92% to 98% over six months.")
    )


def currency() -> LineChart:
    return (
        LineChart()
        .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
        .series([18.5, 19.2, 21.0, 20.4, 22.8, 24.1], label="Average order")
        .y_format("currency", currency="EUR")
        .description("The average order grew from 18.50 to 24.10 EUR.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.series_data("LineChart"),
        pr.h2("How LineChart draws its series"),
        pr.p(
            "The main series is a solid 2px line in the accent. A `compare()` "
            "series is a thinner dashed line in the muted grey, painted "
            "beneath the main one. Only the last point of each line is marked, "
            "which also keeps a series of a single value from drawing nothing."
        ),
        *_charts.formats("LineChart", "`y_format()`"),
        *_charts.size("LineChart"),
        *_charts.loading("LineChart"),
        *_charts.theme("LineChart"),
    )


PAGE = ComponentPage(
    LineChart,
    lede=(
        "A line chart shows how one value moves across ordered labels, such as "
        "the days of a week. A second series, dashed and muted, can sit behind "
        "it for comparison."
    ),
    usage=_usage,
    panels=[
        panel("Live", sign_ups, layout="stack", hint="Hover it for the tooltip"),
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
    notes=_charts.notes("LineChart"),
    related=[AreaChart, BarChart],
)
