from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

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

# The chart palette, as utilities for the legend. chart-draw.js paints with
# the same tokens; spelled out because Tailwind only sees literal class names.
_SWATCHES = (
    "bg-chart-1",
    "bg-chart-2",
    "bg-chart-3",
    "bg-chart-4",
    "bg-chart-5",
    "bg-chart-6",
)

_ERROR_ID = "$id('hue-chart-error')"
_CAPTION_ID = "$id('hue-chart-caption')"


def _named(label: str, what: str) -> str:
    # The label heads a column or a row in the table a screen reader is given.
    if not label.strip():
        raise ValueError(f"Chart {what} needs a label to name it.")
    return label


def _numbers(values: Sequence[float], what: str) -> list[float]:
    numbers = [float(value) for value in values]
    # json.dumps writes NaN and Infinity as bare words, which JSON.parse and
    # Chart.js both reject, so the chart would fail with no hint of why.
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError(f"Chart {what} values must be finite numbers.")
    return numbers


def _currency(code: str) -> str:
    # Checked here because the browser refuses a malformed code by throwing,
    # which would leave the chart blank with nothing to retry.
    if not re.fullmatch(r"[A-Za-z]{3}", code):
        raise ValueError(f"Chart currency must be an ISO 4217 code, not {code!r}.")
    return code.upper()


@dataclass(frozen=True, slots=True)
class _Format:
    """
    How one quantity is written. The tooltip and the table get their text
    from write(), so they read exactly the same; only axis ticks are written
    by the browser, because they are not known until the chart is laid out.
    """

    kind: ChartFormat = "number"
    currency: str | None = None

    def write(self, value: float) -> str:
        if self.kind == "percent":
            value *= 100
        # A small negative would otherwise round to "-0", which reads as a
        # value of its own.
        if round(value, 2) == 0:
            value = 0.0
        if self.kind == "currency":
            return f"{value:,.2f} {self.currency}"
        # Up to two decimals, and none of them trailing zeros.
        number = f"{value:,.2f}".rstrip("0").rstrip(".")
        return f"{number}%" if self.kind == "percent" else number

    def spec(self) -> dict[str, str | None]:
        return {"format": self.kind, "currency": self.currency}


def _format(value: ChartFormat, currency: str) -> _Format:
    return _Format(value, _currency(currency) if value == "currency" else None)


class _ChartBase(ChainableComponent):
    """
    What every chart shares: the figure the loader draws into, the Retry
    overlay for when it cannot, and the table that is the text alternative.
    """

    category = "Data"

    def description(self, value: str) -> Self:
        """
        What the chart shows. It captions the table of values a screen reader
        is given in place of the drawing.
        """
        self._props["description"] = value
        return self

    def _description(self) -> str:
        description: str | None = self._get_prop("description")
        if description is None or not description.strip():
            raise ValueError(
                f"{type(self).__name__} needs a description() to stand in for "
                "the drawing for anyone who cannot see it."
            )
        return description

    def _figure(
        self,
        spec: dict[str, Any],
        *,
        headers: list[str],
        rows: list[list[str]],
        legend: list[tuple[str, str]] | None,
    ) -> Component:
        """
        The chart's markup. headers and rows make the table, each row led by
        a header cell; legend pairs each name with its swatch class.
        """
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
            render_if(legend, _legend),
            _table(self._description(), headers, rows),
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


class Chart(_ChartBase):
    """
    A line, area or bar chart of one series, with an optional second series to
    compare it against.

    labels() names the points along the bottom and series() gives one value
    per label. compare() draws a second series muted, and on a bar chart
    highlight() accents one bar and mutes the rest. description() is required
    and captions the table of values a screen reader is given instead of the
    drawing.

    The chart is drawn by Chart.js, which is fetched when the first chart on
    a page appears. If that fails, the chart offers to try again.
    """

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
        self._props["series"] = (_named(label, "series"), _numbers(values, "series"))
        return self

    def compare(self, values: Sequence[float], *, label: str) -> Self:
        """
        A second series to read the first against, such as the previous
        period, drawn muted so the first stays the one that stands out.
        """
        self._props["compare"] = (_named(label, "compare"), _numbers(values, "compare"))
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
        self._props["y_format"] = _format(value, currency)
        return self

    def _render(self, context: Context) -> Component:
        kind: ChartKind = self._get_prop("kind", "area")
        y: _Format = self._get_prop("y_format", _Format())
        labels: list[str] = self._get_prop("labels", [])
        series: tuple[str, list[float]] | None = self._get_prop("series")
        compare: tuple[str, list[float]] | None = self._get_prop("compare")
        highlight: str | None = self._get_prop("highlight")

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

        displays = [[y.write(v) for v in values] for _, values in drawn]
        return self._figure(
            {
                "kind": kind,
                "labels": labels,
                "series": [
                    {"label": label, "values": values, "display": display}
                    for (label, values), display in zip(drawn, displays, strict=True)
                ],
                "highlight": None if highlight is None else labels.index(highlight),
                "y": y.spec(),
            },
            headers=["", *(label for label, _ in drawn)],
            rows=[
                [label, *(display[i] for display in displays)]
                for i, label in enumerate(labels)
            ],
            # The muted swatch is chart-6, the same grey as fg-subtle.
            legend=None
            if compare is None
            else [(series[0], _SWATCHES[0]), (compare[0], _SWATCHES[5])],
        )


class PieChart(_ChartBase):
    """
    How a whole divides into parts, as a pie or, with doughnut(), a ring.

    slices() gives each part's label and value. Each slice gets a colour of
    its own from the chart palette, which has six: past six slices, the five
    largest are drawn and the rest are grouped as Other. The table a screen
    reader is given still lists every slice, with its share of the whole.
    """

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .slices([("Paid", 92), ("Pending", 31), ("Draft", 14), ("Declined", 8)])
            .description("Most invoices this month are paid: 92 of 145.")
        )

    def slices(self, value: Sequence[tuple[str, float]]) -> Self:
        """
        Each part as a label and a value, in the order they go round.
        """
        labels = [_named(label, "slice") for label, _ in value]
        numbers = _numbers([number for _, number in value], "slice")
        if any(number < 0 for number in numbers):
            raise ValueError("PieChart slices cannot be negative.")
        # The legend and the table name slices by label alone.
        if len(set(labels)) != len(labels):
            raise ValueError("PieChart slice labels must differ from each other.")
        self._props["slices"] = list(zip(labels, numbers, strict=True))
        return self

    def doughnut(self, value: bool = True) -> Self:
        """
        Draw a ring rather than a disc.
        """
        self._props["doughnut"] = value
        return self

    def value_format(self, value: ChartFormat, *, currency: str = "USD") -> Self:
        """
        How values are written in the tooltip and the table. A percent is
        given as a fraction, and currency is an ISO 4217 code read only by
        the currency format.
        """
        self._props["value_format"] = _format(value, currency)
        return self

    def _render(self, context: Context) -> Component:
        slices: list[tuple[str, float]] = self._get_prop("slices", [])
        doughnut: bool = self._get_prop("doughnut", False)
        format_: _Format = self._get_prop("value_format", _Format())

        total = sum(number for _, number in slices)
        if total <= 0:
            raise ValueError("PieChart needs slices() with a total above zero.")

        # A slice of nothing has no area to colour, so only the table lists it.
        drawn = [(label, number) for label, number in slices if number > 0]
        if len(drawn) > len(_SWATCHES):
            # One colour is kept back for Other, and a slice the caller called
            # Other joins it rather than appearing twice.
            room = len(_SWATCHES) - 1
            candidates = [i for i, (label, _) in enumerate(drawn) if label != "Other"]
            largest = sorted(candidates, key=lambda i: -drawn[i][1])[:room]
            rest = sum(n for i, (_, n) in enumerate(drawn) if i not in largest)
            drawn = [*(drawn[i] for i in sorted(largest)), ("Other", rest)]

        def share(number: float) -> str:
            # Rounding a sliver down to "0%" would read as nothing at all.
            if 0 < number / total < 0.005:
                return "<1%"
            return f"{number / total:.0%}"

        def written(number: float) -> str:
            # Values already given as percentages would only say it twice.
            if format_.kind == "percent":
                return format_.write(number)
            return f"{format_.write(number)} ({share(number)})"

        return self._figure(
            {
                "kind": "doughnut" if doughnut else "pie",
                "labels": [label for label, _ in drawn],
                "series": [
                    {
                        "values": [number for _, number in drawn],
                        "display": [written(number) for _, number in drawn],
                    }
                ],
            },
            headers=["", "Value", "Share"],
            rows=[
                [label, format_.write(number), share(number)]
                for label, number in slices
            ],
            legend=[
                (label, swatch)
                for (label, _), swatch in zip(drawn, _SWATCHES, strict=False)
            ],
        )


type _Point = tuple[float, float] | tuple[float, float, float]


class ScatterChart(_ChartBase):
    """
    Points placed by two numbers, to show how one varies with the other.

    series() adds a set of points, each one (x, y), and can be called again
    for another set in the next colour of the chart palette. A third number,
    (x, y, size), turns the points into bubbles that grow with it.
    x_label() and y_label() name the axes and are required, since the
    numbers mean nothing without them; a bubble chart needs size_label() too.
    """

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .series(
                [(12, 0.18), (25, 0.22), (31, 0.35), (44, 0.41), (58, 0.47)],
                label="Orders",
            )
            .x_label("Basket size")
            .y_label("Margin")
            .y_format("percent")
            .description("Margin grows with basket size, from 18% to 47%.")
        )

    def series(self, points: Sequence[_Point], *, label: str) -> Self:
        """
        One set of points, each (x, y) or, for a bubble, (x, y, size).
        """
        checked = [tuple(_numbers(point, "point")) for point in points]
        if any(len(point) not in (2, 3) for point in checked):
            raise ValueError("ScatterChart points are (x, y) or (x, y, size).")
        if not checked:
            raise ValueError("ScatterChart series() needs at least one point.")
        if any(len(point) == 3 and point[2] < 0 for point in checked):
            raise ValueError("ScatterChart bubble sizes cannot be negative.")
        self._props["series"] = [
            *self._get_prop("series", []),
            (_named(label, "series"), checked),
        ]
        return self

    def x_label(self, value: str) -> Self:
        self._props["x_label"] = _named(value, "x axis")
        return self

    def y_label(self, value: str) -> Self:
        self._props["y_label"] = _named(value, "y axis")
        return self

    def size_label(self, value: str) -> Self:
        """
        What a bubble's size stands for.
        """
        self._props["size_label"] = _named(value, "bubble size")
        return self

    def x_format(self, value: ChartFormat, *, currency: str = "USD") -> Self:
        """
        How x values are written, on the axis, in the tooltip and in the
        table. A percent is given as a fraction, and currency is an ISO 4217
        code read only by the currency format.
        """
        self._props["x_format"] = _format(value, currency)
        return self

    def y_format(self, value: ChartFormat, *, currency: str = "USD") -> Self:
        """
        How y values are written, as x_format() does for x.
        """
        self._props["y_format"] = _format(value, currency)
        return self

    def _render(self, context: Context) -> Component:
        series: list[tuple[str, list[tuple[float, ...]]]] = self._get_prop("series", [])
        x_label: str | None = self._get_prop("x_label")
        y_label: str | None = self._get_prop("y_label")
        size_label: str | None = self._get_prop("size_label")
        x: _Format = self._get_prop("x_format", _Format())
        y: _Format = self._get_prop("y_format", _Format())

        points = [point for _, set_ in series for point in set_]
        if not points:
            raise ValueError("ScatterChart needs a series() with points to draw.")
        # The last colour is the grey Chart mutes a comparison with, which
        # would read as less important rather than as one more series.
        if len(series) > len(_SWATCHES) - 1:
            raise ValueError(
                f"ScatterChart draws at most {len(_SWATCHES) - 1} series, one "
                "per colour of the chart palette."
            )
        if x_label is None or y_label is None:
            raise ValueError("ScatterChart needs x_label() and y_label().")
        names_of_series = [label for label, _ in series]
        if len(set(names_of_series)) != len(names_of_series):
            raise ValueError("ScatterChart series labels must differ from each other.")
        sizes = {len(point) for point in points}
        if sizes == {2, 3}:
            raise ValueError(
                "ScatterChart points either all carry a size, for a bubble "
                "chart, or none do."
            )
        bubble = sizes == {3}
        names = [x_label, y_label]
        if bubble:
            if size_label is None:
                raise ValueError("A bubble ScatterChart needs size_label().")
            names.append(size_label)
        elif size_label is not None:
            raise ValueError("ScatterChart size_label() needs points with a size.")

        def cells(point: tuple[float, ...]) -> list[str]:
            written = [x.write(point[0]), y.write(point[1])]
            return [*written, _Format().write(point[2])] if bubble else written

        return self._figure(
            {
                "kind": "bubble" if bubble else "scatter",
                "series": [
                    {
                        "label": label,
                        "points": [list(point) for point in set_],
                        "display": [
                            ", ".join(
                                f"{name}: {cell}"
                                for name, cell in zip(names, cells(point), strict=True)
                            )
                            for point in set_
                        ],
                    }
                    for label, set_ in series
                ],
                "x": {**x.spec(), "label": x_label},
                "y": {**y.spec(), "label": y_label},
            },
            headers=["", *names],
            rows=[[label, *cells(point)] for label, set_ in series for point in set_],
            legend=None
            if len(series) == 1
            else [
                (label, swatch)
                for (label, _), swatch in zip(series, _SWATCHES, strict=False)
            ],
        )


def _legend(items: list[tuple[str, str]]) -> ComponentType:
    return html.ul(
        *(
            html.li(
                html.span(
                    class_=f"size-2.5 flex-none rounded-xs {swatch}", aria_hidden="true"
                ),
                label,
                class_="inline-flex items-center gap-1.5",
            )
            for label, swatch in items
        ),
        class_="m-0 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-xs text-fg-muted",
    )


def _table(caption: str, headers: list[str], rows: list[list[str]]) -> ComponentType:
    # The numbers behind the drawing, for a screen reader to step through.
    return html.table(
        html.caption(caption, **{":id": _CAPTION_ID}),
        html.thead(
            html.tr(
                *(
                    html.th(header, scope="col") if header else html.td()
                    for header in headers
                )
            )
        ),
        html.tbody(
            *(
                html.tr(
                    html.th(row[0], scope="row"), *(html.td(cell) for cell in row[1:])
                )
                for row in rows
            )
        ),
        class_="sr-only",
    )
