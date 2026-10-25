from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import BarChart, DoughnutChart, PieChart

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, panel
from hue_docs_v2.pages.components import _charts

# Live


def invoices_by_status() -> PieChart:
    return (
        PieChart()
        .slices([("Paid", 92), ("Pending", 31), ("Draft", 14), ("Declined", 8)])
        .description("Most invoices this month are paid: 92 of 145.")
    )


# Grouping


def eight_regions() -> PieChart:
    return (
        PieChart()
        .slices(
            [
                ("North", 340),
                ("South", 280),
                ("East", 190),
                ("West", 160),
                ("Central", 90),
                ("Islands", 30),
                ("Coast", 20),
                ("Valley", 12),
            ]
        )
        .description("North and South bring in over half of the sales.")
    )


# Formats


def number() -> PieChart:
    return (
        PieChart()
        .slices([("Desktop", 1840), ("Mobile", 1290), ("Tablet", 310)])
        .value_format("number")
        .description("Desktop brings the most visits, at 1,840 of 3,440.")
    )


def percent() -> PieChart:
    return (
        PieChart()
        .slices([("Desktop", 0.53), ("Mobile", 0.38), ("Tablet", 0.09)])
        .value_format("percent")
        .description("Just over half of visits come from desktop.")
    )


def currency() -> PieChart:
    return (
        PieChart()
        .slices([("Hosting", 4200), ("Payroll", 18600), ("Tools", 1350)])
        .value_format("currency", currency="EUR")
        .description("Payroll is most of the monthly spend, at 18,600 EUR.")
    )


def _usage() -> ComponentType:
    return pr.page(
        *_charts.slice_data("PieChart"),
        *_charts.formats("PieChart", "value_format()", axis=False),
        *_charts.size("PieChart"),
        *_charts.loading("PieChart"),
        *_charts.theme("PieChart"),
    )


PAGE = ComponentPage(
    PieChart,
    lede=(
        "A pie chart shows how a whole divides into parts. Each slice has a "
        "colour of its own, and past six slices the smallest are grouped into "
        "one called Other."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            invoices_by_status,
            layout="stack",
            hint="Hover a slice for its value and share",
        ),
        panel(
            "Grouping",
            eight_regions,
            layout="stack",
            hint="Eight slices: the five largest, then Other",
        ),
        panel(
            "Formats",
            number,
            percent,
            currency,
            layout="stack",
            hint="value_format() writes the tooltip and the table",
        ),
    ],
    notes=_charts.notes("PieChart"),
    related=[DoughnutChart, BarChart],
)
