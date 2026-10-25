from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import BarChart, DoughnutChart, LineChart, PieChart

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel
from hue_docs_v2.pages.components import _charts

# Live


def invoices_by_status() -> BarChart:
    return (
        BarChart()
        .labels(["Paid", "Pending", "Draft", "Declined", "Refunded"])
        .series([92, 31, 14, 8, 3], label="Invoices")
        .highlight("Paid")
        .description("Most invoices in September are paid: 92 of 148.")
    )


# Anatomy


def one_series() -> BarChart:
    return (
        BarChart()
        .labels(["Mon", "Tue", "Wed", "Thu", "Fri"])
        .series([38, 52, 47, 61, 44], label="Tickets closed")
        .description("Thursday closed the most tickets, at 61.")
    )


def highlighted() -> BarChart:
    return (
        BarChart()
        .labels(["Mon", "Tue", "Wed", "Thu", "Fri"])
        .series([38, 52, 47, 61, 44], label="Tickets closed")
        .highlight("Thu")
        .description("Thursday closed the most tickets, at 61.")
    )


def with_compare() -> BarChart:
    return (
        BarChart()
        .labels(["Q1", "Q2", "Q3", "Q4"])
        .series([48, 52, 61, 70], label="2026")
        .compare([41, 45, 50, 58], label="2025")
        .description("Every quarter of 2026 beat the same quarter of 2025.")
    )


# Formats


def number() -> BarChart:
    return (
        BarChart()
        .labels(["North", "South", "East", "West"])
        .series([1240, 980, 1530, 710], label="Orders")
        .y_format("number")
        .description("East took the most orders, at 1,530.")
    )


def percent() -> BarChart:
    return (
        BarChart()
        .labels(["North", "South", "East", "West"])
        .series([0.042, 0.031, 0.058, 0.024], label="Return rate")
        .y_format("percent")
        .description("East has the highest return rate, at 5.8%.")
    )


def currency() -> BarChart:
    return (
        BarChart()
        .labels(["North", "South", "East", "West"])
        .series([48200, 39100, 61800, 27400], label="Revenue")
        .y_format("currency", currency="GBP")
        .description("East brought in the most, at 61,800 GBP.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.series_data("BarChart"),
        pr.h2("Highlighting one bar of a BarChart"),
        pr.p(
            "highlight() takes the label of one bar, draws that bar in the "
            "accent and mutes the others to grey. Without it, every bar of the "
            "series is in the accent."
        ),
        pr.code(
            'BarChart().labels(["Paid", "Pending", "Draft"])'
            '.series([92, 31, 14], label="Invoices").highlight("Paid")'
        ),
        pr.p(
            "The label has to be one of the chart's labels, and highlight() "
            "cannot be combined with compare(), whose bars are already muted. "
            "Either mistake raises a ValueError when the chart renders. The "
            "highlight is drawn only, so the table a screen reader reads does "
            "not mark it: say what it stands for in description()."
        ),
        pr.h2("How BarChart draws its series"),
        pr.p(
            "With compare(), the two series stand side by side at each label, "
            "the main series in the accent and the comparison in the muted "
            "grey. Bars have slightly rounded corners and are at most 44px "
            "wide, however few labels there are."
        ),
        *_charts.formats("BarChart", "y_format()"),
        *_charts.size("BarChart"),
        *_charts.loading("BarChart"),
        *_charts.theme("BarChart"),
    )


PAGE = ComponentPage(
    BarChart,
    lede=(
        "A bar chart draws one bar per label, for comparing amounts side by "
        "side. It can accent a single bar, or set a muted second series beside "
        "the first."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live", invoices_by_status, layout="stack", hint="Hover it for the tooltip"
        ),
        panel(
            "Anatomy",
            one_series,
            highlighted,
            with_compare,
            layout="stack",
            hint="highlight() and compare() do not combine",
        ),
        panel(
            "Formats",
            number,
            percent,
            currency,
            layout="stack",
            hint="y_format() writes the axis, the tooltip and the table",
        ),
    ],
    notes=[
        *_charts.notes("BarChart"),
        Note(
            "warn",
            "highlight() is only drawn. The table a screen reader reads lists "
            "every bar alike, so description() has to say what the accented "
            "bar stands for.",
        ),
    ],
    related=[LineChart, PieChart, DoughnutChart],
)
