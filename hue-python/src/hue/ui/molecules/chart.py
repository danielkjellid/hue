from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from typing import Literal, TypedDict

from htmy import Context, html
from typing_extensions import Self

from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type ChartKind = Literal["line", "area", "bar"]
type ChartFormat = Literal["number", "percent", "currency"]


def _named(label: str, what: str) -> str:
    # The label heads the series' column in the table a screen reader is given.
    if not label.strip():
        raise ValueError(f"Chart {what} needs a label to name it.")
    return label


def _values(values: Sequence[float], what: str) -> list[float]:
    numbers = [float(value) for value in values]
    # json.dumps writes NaN and Infinity as bare words, which JSON.parse and
    # Chart.js both reject, so the chart would fail with no hint of why.
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError(f"Chart {what} values must be finite numbers.")
    return numbers


def _formatted(value: float, format_: ChartFormat, currency: str | None) -> str:
    if format_ == "percent":
        value *= 100
    # A small negative would otherwise round to "-0", which reads as a value
    # of its own.
    if round(value, 2) == 0:
        value = 0.0
    if format_ == "currency":
        return f"{value:,.2f} {currency}"
    # Up to two decimals, and none of them trailing zeros.
    number = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{number}%" if format_ == "percent" else number


_ERROR_ID = "$id('hue-chart-error')"
_CAPTION_ID = "$id('hue-chart-caption')"


class _Series(TypedDict):
    label: str
    values: list[float]
    # Each value as the tooltip and the table write it.
    display: list[str]


class Chart(ChainableComponent):
    """
    A line, area or bar chart of one series, with an optional second series to
    compare it against.

    labels() names the points along the bottom and series() gives one value
    per label. compare() draws a second series muted, and on a bar chart
    highlight() accents one bar and mutes the rest. description() is the
    chart's text alternative and is required, since a canvas says nothing to
    a screen reader; the values are also given to one as a table.

    The chart is drawn by Chart.js, which is fetched when the first chart on
    a page appears. If that fails, the chart offers to try again.
    """

    category = "Data"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .kind("area")
            .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            .series([3100, 3400, 3200, 4100, 3900, 4600, 4829], label="This week")
            .compare([2900, 3000, 2800, 3300, 3100, 3600, 3700], label="Last week")
            .y_format("currency", currency="USD")
            .description(
                "Revenue rose from $3,100 to $4,829, above last week every day."
            )
        )

    def kind(self, value: ChartKind) -> Self:
        self._props["kind"] = value
        return self

    def labels(self, value: Sequence[str]) -> Self:
        """
        What each point is, in order along the bottom: days, months, statuses.
        """
        self._props["labels"] = [str(label) for label in value]
        return self

    def series(self, values: Sequence[float], *, label: str) -> Self:
        """
        The values the chart is about, one per label, drawn in the accent.
        """
        self._props["series"] = (_named(label, "series"), _values(values, "series"))
        return self

    def compare(self, values: Sequence[float], *, label: str) -> Self:
        """
        A second series to read the first against, such as the previous
        period, drawn muted so the first stays the one that stands out.
        """
        self._props["compare"] = (_named(label, "compare"), _values(values, "compare"))
        return self

    def highlight(self, label: str) -> Self:
        """
        On a bar chart of one series, accent the bar with this label and mute
        the others. Not with compare(), whose bars are already the muted ones.
        """
        self._props["highlight"] = label
        return self

    def y_format(self, value: ChartFormat, *, currency: str = "USD") -> Self:
        """
        How values are written on the axis, in the tooltip and in the table.
        A percent is given as a fraction, so 0.42 is 42%. currency is an ISO
        4217 code, and only read by the currency format.
        """
        # Checked here because the browser refuses a malformed code by
        # throwing, which would leave the chart blank with nothing to retry.
        if not re.fullmatch(r"[A-Za-z]{3}", currency):
            raise ValueError(
                f"Chart currency must be an ISO 4217 code, not {currency!r}."
            )
        self._props["y_format"] = value
        self._props["currency"] = currency.upper()
        return self

    def description(self, value: str) -> Self:
        """
        What the chart shows. It captions the table of values a screen reader
        is given in place of the drawing.
        """
        self._props["description"] = value
        return self

    def _render(self, context: Context) -> Component:
        kind: ChartKind = self._get_prop("kind", "area")
        format_: ChartFormat = self._get_prop("y_format", "number")
        currency: str | None = self._get_prop("currency")
        labels: list[str] = self._get_prop("labels", [])
        series: tuple[str, list[float]] | None = self._get_prop("series")
        compare: tuple[str, list[float]] | None = self._get_prop("compare")
        highlight: str | None = self._get_prop("highlight")
        description: str | None = self._get_prop("description")

        if description is None or not description.strip():
            raise ValueError(
                "Chart needs a description() to stand in for the drawing for "
                "anyone who cannot see it."
            )
        if series is None or not labels:
            raise ValueError("Chart needs labels() and a series() to draw.")
        drawn = [series] if compare is None else [series, compare]
        for label, values in drawn:
            if len(values) != len(labels):
                raise ValueError(
                    f"Chart series {label!r} has {len(values)} values for "
                    f"{len(labels)} labels; give one value per label."
                )
        if highlight is not None and (
            kind != "bar" or compare is not None or highlight not in labels
        ):
            raise ValueError(
                "Chart can only highlight one of the labels of a bar chart with "
                f"no compare(), not {highlight!r}."
            )

        # Written here rather than by the browser, so the tooltip and the
        # table read exactly the same. The axis is the one thing the browser
        # formats, because its ticks are only known once the chart is laid out.
        shown: list[_Series] = [
            {
                "label": label,
                "values": values,
                "display": [_formatted(v, format_, currency) for v in values],
            }
            for label, values in drawn
        ]
        spec = {
            "kind": kind,
            "labels": labels,
            "series": shown,
            "highlight": None if highlight is None else labels.index(highlight),
            "format": format_,
            "currency": currency,
        }

        return html.figure(
            html.div(
                # The table below is the text alternative, captioned by the
                # description, so the drawing is kept from saying it twice.
                html.canvas(aria_hidden="true", **{"x-ref": "canvas"}),
                html.div(
                    html.p("Unable to load chart.", **{":id": _ERROR_ID}),
                    # Focus comes back here when a retry fails as well, so the
                    # button carries the message rather than leaving it unread.
                    Button()
                    .variant("secondary")
                    .size("sm")
                    .content("Retry")
                    .x_ref("retry")
                    .x_bind("aria-describedby", unsafe(_ERROR_ID))
                    .on_click(call("retry")),
                    class_=(
                        "absolute inset-0 flex flex-col items-center justify-center "
                        "gap-2 text-sm text-fg-muted"
                    ),
                    # hidden rather than x-show, which only reveals an element on
                    # the next frame: too late for the loader to focus Retry.
                    hidden=True,
                    **{":hidden": "!failed"},
                ),
                class_="relative aspect-[5/2] w-full",
            ),
            render_if(compare, lambda _: _legend(shown)),
            _table(description, labels, shown),
            class_=classnames(
                "m-0 flex w-full flex-col gap-2.5 rounded-md",
                FOCUS_RING,
                self._get_prop("class_"),
            ),
            **{
                **self._get_base_html_attrs(),
                "x-data": f"hueChart({json.dumps(spec)})",
                "x-id": "['hue-chart-error', 'hue-chart-caption']",
                # Named, so focus landing here after a retry announces more
                # than "figure".
                ":aria-labelledby": _CAPTION_ID,
                # Somewhere for focus to go when Retry hides itself.
                "tabindex": "-1",
            },
        )


def _legend(series: list[_Series]) -> ComponentType:
    # The same tokens chart-draw.js paints the series with.
    swatches = ("bg-accent", "bg-fg-subtle")
    return html.ul(
        *(
            html.li(
                html.span(
                    class_=f"size-2.5 flex-none rounded-xs {swatch}", aria_hidden="true"
                ),
                s["label"],
                class_="inline-flex items-center gap-1.5",
            )
            for s, swatch in zip(series, swatches, strict=True)
        ),
        class_="m-0 flex list-none flex-wrap gap-4 p-0 text-xs text-fg-muted",
    )


def _table(description: str, labels: list[str], series: list[_Series]) -> ComponentType:
    # The numbers behind the drawing, for a screen reader to step through.
    return html.table(
        html.caption(description, **{":id": _CAPTION_ID}),
        html.thead(
            html.tr(html.td(), *(html.th(s["label"], scope="col") for s in series))
        ),
        html.tbody(
            *(
                html.tr(
                    html.th(label, scope="row"),
                    *(html.td(s["display"][i]) for s in series),
                )
                for i, label in enumerate(labels)
            )
        ),
        class_="sr-only",
    )
