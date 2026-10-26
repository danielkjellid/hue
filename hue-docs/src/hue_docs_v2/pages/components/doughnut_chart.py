from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import BarChart, DoughnutChart, PieChart

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, panel
from hue_docs_v2.pages.components import _charts

# Live


def payment_methods() -> DoughnutChart:
    return (
        DoughnutChart()
        .slices([("Card", 412), ("Invoice", 191), ("Transfer", 107)])
        .description("Card is the most used way to pay, at 58%.")
    )


# Grouping


def eight_plans() -> DoughnutChart:
    return (
        DoughnutChart()
        .slices(
            [
                ("Team", 410),
                ("Business", 260),
                ("Starter", 220),
                ("Enterprise", 140),
                ("Nonprofit", 60),
                ("Education", 25),
                ("Legacy", 15),
                ("Trial", 9),
            ]
        )
        .description("Team and Business make up most subscriptions.")
    )


# Formats


def number() -> DoughnutChart:
    return (
        DoughnutChart()
        .slices([("Open", 38), ("In review", 17), ("Closed", 145)])
        .value_format("number")
        .description("Most pull requests this month are closed: 145 of 200.")
    )


def percent() -> DoughnutChart:
    return (
        DoughnutChart()
        .slices([("Used", 0.64), ("Free", 0.36)])
        .value_format("percent")
        .description("64% of the quota is used.")
    )


def currency() -> DoughnutChart:
    return (
        DoughnutChart()
        .slices([("Compute", 9200), ("Storage", 3100), ("Network", 1700)])
        .value_format("currency", currency="USD")
        .description("Compute is most of the cloud bill, at 9,200 USD.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.p(
            "A `DoughnutChart` is a `PieChart` drawn as a ring. It takes the same "
            "`slices()` and `value_format()`, groups slices past six the same way, "
            "and gives a screen reader the same table."
        ),
        *_charts.slice_data("DoughnutChart"),
        *_charts.formats("DoughnutChart", "`value_format()`", axis=False),
        *_charts.size("DoughnutChart"),
        *_charts.loading("DoughnutChart"),
        *_charts.theme("DoughnutChart"),
    )


PAGE = ComponentPage(
    DoughnutChart,
    lede=(
        "A doughnut chart is a pie chart drawn as a ring, showing how a whole "
        "divides into parts. Each slice has a colour of its own, and past six "
        "slices the smallest are grouped into one called Other."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            payment_methods,
            layout="stack",
            hint="Hover a slice for its value and share",
        ),
        panel(
            "Grouping",
            eight_plans,
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
    notes=_charts.notes("DoughnutChart"),
    related=[PieChart, BarChart],
)
