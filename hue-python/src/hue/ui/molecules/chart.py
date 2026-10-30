from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

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


class Chart(ChainableComponent):
    """
    The base of every chart: the figure the loader draws into, the Retry
    overlay for when it cannot, and the table that is the text alternative.

    Charts are drawn by Chart.js, which is fetched when the first chart on a
    page appears. If that fails, the chart offers to try again.
    """

    category = "Charts"
    # A floor under the 5:2 box, for charts that cannot be read when short.
    _MIN_HEIGHT: ClassVar[str | None] = None

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
                # Out of flow, because Chart.js writes a pixel width on the
                # canvas that would hold any flex or grid cell around the
                # chart open at its widest. The box takes its size from its
                # aspect ratio instead.
                html.canvas(
                    aria_hidden="true",
                    class_="absolute inset-0",
                    **{"x-ref": "canvas"},
                ),
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
                class_=classnames("relative aspect-[5/2] w-full", self._MIN_HEIGHT),
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


class _SeriesChart(Chart):
    """
    One value per label along the bottom, with an optional second series.
    """

    _KIND: ClassVar[str]

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

    def y_format(self, value: ChartFormat, *, currency: str = "USD") -> Self:
        """
        How values are written on the axis, in the tooltip and in the table.
        A percent is given as a fraction, so 0.42 is 42%. currency is an ISO
        4217 code, and only read by the currency format.
        """
        self._props["y_format"] = _format(value, currency)
        return self

    def _highlight(self) -> str | None:
        """
        The label of the bar to accent; only a bar chart has one.
        """
        return None

    def _render(self, context: Context) -> Component:
        name = type(self).__name__
        y: _Format = self._get_prop("y_format", _Format())
        labels: list[str] = self._get_prop("labels", [])
        series: tuple[str, list[float]] | None = self._get_prop("series")
        compare: tuple[str, list[float]] | None = self._get_prop("compare")
        highlight = self._highlight()

        if series is None or not labels:
            raise ValueError(f"{name} needs labels() and a series() to draw.")
        drawn = [series] if compare is None else [series, compare]
        for label, values in drawn:
            if len(values) != len(labels):
                raise ValueError(
                    f"{name} series {label!r} has {len(values)} values for "
                    f"{len(labels)} labels; give one value per label."
                )
        if highlight is not None and (compare is not None or highlight not in labels):
            raise ValueError(
                f"{name} can only highlight one of its labels, and not with "
                f"compare(): {highlight!r}."
            )

        displays = [[y.write(v) for v in values] for _, values in drawn]
        return self._figure(
            {
                "kind": self._KIND,
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


class LineChart(_SeriesChart):
    """
    How a value moves across ordered labels, such as days, as a line.

    labels() names the points along the bottom and series() gives one value
    per label. compare() adds a second series, dashed and muted. description()
    is required and captions the table of values a screen reader is given
    instead of the drawing.
    """

    _KIND = "line"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            .series([212, 240, 198, 260, 251, 305, 330], label="This week")
            .compare([190, 205, 201, 222, 230, 260, 270], label="Last week")
            .description("Sign-ups rose from 212 to 330, above last week every day.")
        )


class AreaChart(_SeriesChart):
    """
    A line chart with the area under the main series filled, for a total
    whose size matters as much as its direction.

    It takes the same labels(), series() and compare() as LineChart, and
    description() is required.
    """

    _KIND = "area"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            .series([3100, 3400, 3200, 4100, 3900, 4600, 4829], label="This week")
            .compare([2900, 3000, 2800, 3300, 3100, 3600, 3700], label="Last week")
            .y_format("currency", currency="USD")
            .description(
                "Revenue rose from 3,100.00 USD to 4,829.00 USD, above last week "
                "every day."
            )
        )


class BarChart(_SeriesChart):
    """
    One bar per label, for comparing amounts side by side.

    It takes the same labels(), series() and compare() as LineChart.
    highlight() accents one bar and mutes the rest, and cannot be combined
    with compare(). description() is required.
    """

    _KIND = "bar"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .labels(["Paid", "Pending", "Draft", "Declined", "Refunded"])
            .series([92, 31, 14, 8, 3], label="Invoices")
            .highlight("Paid")
            .description("Most invoices in September are paid: 92 of 148.")
        )

    def highlight(self, label: str) -> Self:
        """
        Accent the bar with this label and mute the others.
        """
        self._props["highlight"] = label
        return self

    def _highlight(self) -> str | None:
        return self._get_prop("highlight")


class PieChart(Chart):
    """
    How a whole divides into parts, as a pie.

    slices() gives each part's label and value. Each slice gets a colour of
    its own from the chart palette, which has six: past six slices, the five
    largest are drawn and the rest are grouped as Other. The table a screen
    reader is given still lists every slice, with its share of the whole.
    """

    _KIND: ClassVar[str] = "pie"

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
            raise ValueError(f"{type(self).__name__} slices cannot be negative.")
        # The legend and the table name slices by label alone.
        if len(set(labels)) != len(labels):
            raise ValueError(
                f"{type(self).__name__} slice labels must differ from each other."
            )
        self._props["slices"] = list(zip(labels, numbers, strict=True))
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
        format_: _Format = self._get_prop("value_format", _Format())

        total = sum(number for _, number in slices)
        if total <= 0:
            raise ValueError(
                f"{type(self).__name__} needs slices() with a total above zero."
            )

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

        # Values already given as percentages would only say it twice.
        percent = format_.kind == "percent"

        def written(number: float) -> str:
            if percent:
                return format_.write(number)
            return f"{format_.write(number)} ({share(number)})"

        return self._figure(
            {
                "kind": self._KIND,
                "labels": [label for label, _ in drawn],
                "series": [
                    {
                        "values": [number for _, number in drawn],
                        "display": [written(number) for _, number in drawn],
                    }
                ],
            },
            headers=["", "Value"] if percent else ["", "Value", "Share"],
            rows=[
                [label, format_.write(number)] + ([] if percent else [share(number)])
                for label, number in slices
            ],
            legend=[
                (label, swatch)
                for (label, _), swatch in zip(drawn, _SWATCHES, strict=False)
            ],
        )


class DoughnutChart(PieChart):
    """
    A pie chart drawn as a ring.

    It takes the same slices() and value_format() as PieChart, groups slices
    past six the same way, and needs a description().
    """

    _KIND = "doughnut"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .slices([("Card", 412), ("Invoice", 191), ("Transfer", 107)])
            .description("Card is the most used way to pay, at 58%.")
        )


class _PointChart(Chart):
    """
    Points placed by numbers on both axes, in up to five series.
    """

    _KIND: ClassVar[str]
    # How many numbers make a point, and how to say so when one does not.
    _ARITY: ClassVar[int]
    _SHAPE: ClassVar[str]
    # Two titled axes and a bubble's headroom leave almost no plot in a 5:2
    # box on a phone, so below about 480px wide the chart stops getting shorter.
    _MIN_HEIGHT = "min-h-48"

    def series(self, points: Sequence[Sequence[float]], *, label: str) -> Self:
        """
        One set of points. Call it again for another set, drawn in the next
        colour of the chart palette.
        """
        name = type(self).__name__
        checked = [_numbers(point, "point") for point in points]
        if not checked:
            raise ValueError(f"{name} series() needs at least one point.")
        if any(len(point) != self._ARITY for point in checked):
            raise ValueError(f"{name} points are {self._SHAPE}.")
        if any(len(point) == 3 and point[2] < 0 for point in checked):
            raise ValueError(f"{name} sizes cannot be negative.")
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

    def _size_name(self) -> list[str]:
        """
        The heading of the size column, which only a bubble chart has.
        """
        return []

    def _render(self, context: Context) -> Component:
        name = type(self).__name__
        series: list[tuple[str, list[list[float]]]] = self._get_prop("series", [])
        x_label: str | None = self._get_prop("x_label")
        y_label: str | None = self._get_prop("y_label")
        x: _Format = self._get_prop("x_format", _Format())
        y: _Format = self._get_prop("y_format", _Format())

        if not series:
            raise ValueError(f"{name} needs a series() to draw.")
        # The last colour is the grey a comparison is muted with, which would
        # read as less important rather than as one more series.
        if len(series) > len(_SWATCHES) - 1:
            raise ValueError(
                f"{name} draws at most {len(_SWATCHES) - 1} series, one per "
                "colour of the chart palette."
            )
        if x_label is None or y_label is None:
            raise ValueError(f"{name} needs x_label() and y_label().")
        labels = [label for label, _ in series]
        if len(set(labels)) != len(labels):
            raise ValueError(f"{name} series labels must differ from each other.")
        names = [x_label, y_label, *self._size_name()]

        def cells(point: list[float]) -> list[str]:
            written = [x.write(point[0]), y.write(point[1])]
            # A size is a count or an amount of its own, whatever the axes are.
            return [*written, *(_Format().write(size) for size in point[2:])]

        return self._figure(
            {
                "kind": self._KIND,
                "series": [
                    {
                        "label": label,
                        "points": points,
                        # One line per value, so the tooltip stacks them and
                        # stays narrow enough for a phone.
                        "display": [
                            [
                                f"{name}: {cell}"
                                for name, cell in zip(names, cells(point), strict=True)
                            ]
                            for point in points
                        ],
                    }
                    for label, points in series
                ],
                "x": {**x.spec(), "label": x_label},
                "y": {**y.spec(), "label": y_label},
            },
            headers=["", *names],
            rows=[
                [label, *cells(point)] for label, points in series for point in points
            ],
            legend=None
            if len(series) == 1
            else [
                (label, swatch)
                for (label, _), swatch in zip(series, _SWATCHES, strict=False)
            ],
        )


class ScatterChart(_PointChart):
    """
    Points placed by two numbers, to show how one varies with the other.

    series() adds a set of (x, y) points and can be called again for another
    set. x_label() and y_label() name the axes and are required, since the
    numbers mean nothing without them, and so is description().
    """

    _KIND = "scatter"
    _ARITY = 2
    _SHAPE = "(x, y); a point with a size belongs on a BubbleChart"

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


class BubbleChart(_PointChart):
    """
    A scatter chart whose points carry a third number, drawn as bubbles that
    grow with it.

    series() takes (x, y, size) points. x_label(), y_label() and size_label()
    are required, and so is description().
    """

    _KIND = "bubble"
    _ARITY = 3
    _SHAPE = "(x, y, size)"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .series(
                [(2, 40, 120), (5, 55, 340), (8, 48, 90), (11, 70, 410)],
                label="Teams",
            )
            .x_label("Engineers")
            .y_label("Deploys per week")
            .size_label("Incidents fixed")
            .description("Larger teams deploy more and fix more incidents.")
        )

    def size_label(self, value: str) -> Self:
        """
        What a bubble's size stands for.
        """
        self._props["size_label"] = _named(value, "bubble size")
        return self

    def _size_name(self) -> list[str]:
        size_label: str | None = self._get_prop("size_label")
        if size_label is None:
            raise ValueError("BubbleChart needs size_label().")
        return [size_label]


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
    # sr-only goes on a wrapper because a table box does not shrink to 1px,
    # so on the table itself it widens a narrow page.
    return html.div(
        html.table(
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
                        html.th(row[0], scope="row"),
                        *(html.td(cell) for cell in row[1:]),
                    )
                    for row in rows
                )
            ),
        ),
        class_="sr-only",
    )
