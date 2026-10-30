"""
Prose every chart page shares, since every chart is drawn by the same loader
from the same kind of spec. Each section names its chart, so it still reads on
its own when search lands a reader in the middle of the page.
"""

from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import Note


def _a(name: str, *, start: bool = False) -> str:
    """
    The chart's name after its article: an AreaChart, a BarChart. start
    capitalises the article to open a sentence.
    """
    article = "an" if name[0] in "AEIOU" else "a"
    return f"{article.title() if start else article} `{name}`"


def formats(name: str, modifiers: str, *, axis: bool = True) -> list[ComponentType]:
    where = (
        "The tooltip and the table of values"
        if axis
        else f"{_a(name, start=True)} has no axis. Its tooltip and its table of values"
    )
    verb = "take" if " and " in modifiers else "takes"
    return [
        pr.h2(f"How {name} writes numbers"),
        pr.p(
            f'{modifiers} {verb} one of three formats: `"number"` (the default), '
            '`"percent"` and `"currency"`. A percent is given as a fraction, so `0.42` '
            "is written 42%. `currency` is an ISO 4217 code, read only by the "
            "currency format and upper-cased. A code that is not three letters "
            "raises a `ValueError` when the modifier is called. Left to the "
            "browser, it would leave the chart blank."
        ),
        pr.p(
            f"{where} get their text from Python, so both read exactly the "
            "same. A number has up to two decimals and no trailing zeros, with "
            "commas between thousands. A currency always has two decimals and "
            "ends in its code, as in 4,829.00 USD. A value that rounds to zero "
            "is written `0`, never `-0`."
            + (
                " Axis ticks are written by the browser, since they are not "
                "known until the chart is laid out, in compact notation "
                "(such as 4.8K) and with the currency's code."
                if axis
                else ""
            )
        ),
    ]


def loading(name: str) -> list[ComponentType]:
    return [
        pr.h2(f"How {name} loads Chart.js"),
        pr.p(
            f"{_a(name, start=True)} is drawn by Chart.js, which is larger "
            "than the rest of "
            "hue's JavaScript put together, so it is kept out of the Alpine "
            "bundle in a file of its own, `chart-bundle.js`. The first chart to "
            "appear on a page fetches it, and every other chart on that page "
            "waits on the same request."
        ),
        pr.p(
            "The URL is resolved against the Alpine bundle's own, so the two "
            "files have to sit side by side. `hue-django`'s `HueAssetsMiddleware` "
            "and `hue-fastapi`'s asset routes already serve them that way. If "
            "you serve the bundle yourself, copy the file at "
            "`hue.assets.chart_bundle_path()` next to it."
        ),
        pr.h3(f"When {name} cannot load"),
        pr.p(
            'If the request fails, the chart shows the message "Unable to load chart." '
            "with "
            "a Retry button, and the error is logged to the console once, "
            "however many charts were waiting. Retry asks again under a new "
            "URL, because a failed module import can stay failed for the life "
            "of the page, and every chart that retries shares that attempt."
        ),
    ]


def theme(name: str) -> list[ComponentType]:
    return [
        pr.h2(f"{name} in dark mode"),
        pr.p(
            f"{_a(name, start=True)} paints with the `chart-1` to `chart-6` "
            "tokens, read at the "
            "moment it is drawn. A canvas holds colours, not the tokens they "
            "came from, so the chart watches `data-theme` on the `html` element "
            "and draws itself again, without animation, when the value "
            "changes. Animation is also off for anyone whose system asks for "
            "reduced motion."
        ),
    ]


def size(name: str, *, min_height: int | None = None) -> list[ComponentType]:
    floor = (
        f" The drawing area is never less than {min_height}px tall, so in a "
        f"container narrower than {min_height * 5 // 2}px it stops getting "
        "shorter and is taller than 5:2."
        if min_height
        else ""
    )
    return [
        pr.h2(f"How big {name} draws"),
        pr.p(
            f"The drawing area of {_a(name)} fills the width of its container "
            "at a 5:2 ratio, so its height follows its width."
            + floor
            + " A legend, where the chart has one, sits below it. `class_()` "
            "lands on the figure around both, which is where a width "
            "constraint goes."
        ),
    ]


def notes(name: str) -> list[Note]:
    return [
        Note(
            "a11y",
            "The canvas is `aria-hidden`. A screen reader gets a visually hidden "
            "table of every value instead, captioned by `description()`, and "
            f"the figure is named by that caption. Rendering {_a(name)} without "
            "a `description()` raises a `ValueError`.",
        ),
        Note(
            "a11y",
            "The tooltip appears on pointer hover only. The table carries the "
            "same text, so keyboard and screen reader users read the values "
            "there.",
        ),
        Note(
            "a11y",
            'The Retry button is described by the "Unable to load chart." message. '
            "Pressing "
            "it moves focus to the figure while it hides, and back to Retry if "
            "the second attempt fails as well.",
        ),
        Note(
            "note",
            "A value that is `NaN` or infinite raises a `ValueError` where it is "
            "given, because JSON cannot carry it to the browser.",
        ),
    ]


def series_data(name: str) -> list[ComponentType]:
    """
    LineChart, AreaChart and BarChart take their data the same way.
    """
    return [
        pr.h2(f"Giving {name} its data"),
        pr.p(
            f"{_a(name, start=True)} takes ordered labels along the bottom and "
            "one value per "
            "label. `labels()` names the points, `series()` gives the values the "
            "chart is about, drawn in the accent, and `compare()` adds a second "
            "series to read the first against, drawn in the muted grey of "
            "`chart-6`. Each series takes a `label`, which names it in the legend, "
            "the tooltip and the table."
        ),
        pr.code(
            f"{name}()\n"
            '    .labels(["Q1", "Q2", "Q3", "Q4"])\n'
            '    .series([48, 52, 61, 70], label="2026")\n'
            '    .compare([41, 45, 50, 58], label="2025")\n'
            '    .description("Every quarter of 2026 beat the same quarter of 2025.")'
        ),
        pr.p(
            "The legend only appears with `compare()`, since a single series has "
            "nothing to tell apart. The value axis starts at zero, and the "
            "tooltip lists every series at the label under the pointer."
        ),
        pr.h3(f"What {name} refuses"),
        pr.bullets(
            [
                "A `series()` or `compare()` label that is empty or only whitespace, "
                "when it is given.",
                "Rendering without `labels()` and a `series()`.",
                "Rendering with a series whose length differs from the "
                "number of labels.",
            ]
        ),
        pr.p("Each raises a `ValueError` that names the problem."),
    ]


def slice_data(name: str) -> list[ComponentType]:
    """
    PieChart and DoughnutChart take their data the same way.
    """
    return [
        pr.h2(f"Giving {name} its data"),
        pr.p(
            f"`slices()` takes each part of {_a(name)} as a label and a value, in "
            "the order they go round. Each slice gets its own colour from the "
            "chart palette, and the legend below the chart names every slice "
            "it draws with its swatch."
        ),
        pr.code(
            f"{name}()\n"
            '    .slices([("Card", 412), ("Invoice", 191), ("Transfer", 107)])\n'
            '    .description("Card is the most used way to pay, at 58%.")'
        ),
        pr.p(
            "The tooltip gives each value with its share of the whole, as in "
            "412 (58%), and the table gives the share a column of its own. A "
            "share below half a percent is written <1% rather than 0%. With "
            '`value_format("percent")` the values already are shares, so the '
            "tooltip and the table leave the share out."
        ),
        pr.h3(f"More than six slices in {_a(name).replace('`', '')}"),
        pr.p(
            "The chart palette has six colours. Past six slices, the five "
            "largest are drawn in place and the rest are added up into one "
            "slice called `Other`. A slice you named `Other` joins that one rather "
            "than appearing twice. The table a screen reader is given still "
            "lists every slice on its own."
        ),
        pr.h3(f"What {name} refuses"),
        pr.bullets(
            [
                "A negative value, two slices with the same label, or a label "
                "that is empty, when `slices()` is called.",
                "Rendering with slices that add up to zero, or with none.",
            ]
        ),
        pr.p(
            "Each raises a `ValueError`. A slice of zero is allowed. It has no "
            "area, so it is left out of the drawing and the legend and only "
            "appears in the table."
        ),
    ]


def point_data(name: str, shape: str) -> list[ComponentType]:
    """
    ScatterChart and BubbleChart take their data the same way.
    """
    return [
        pr.h2(f"Giving {name} its data"),
        pr.p(
            f"`series()` adds one set of {shape} points to {_a(name)}, with a "
            "label that names it in the tooltip and the table. Call it again "
            "for another set, drawn in the next colour of the chart palette, "
            "up to five. The sixth colour is the grey other charts mute a "
            "comparison with, so it is not offered as a series."
        ),
        pr.p(
            "`x_label()` and `y_label()` name the axes and are required. They are "
            "drawn as axis titles and head the table's columns. The legend "
            "appears once there are two series or more."
        ),
        pr.p(
            "Both axes are numeric and leave 5% of headroom past the largest "
            "and smallest values, so a point at the edge of the range is not "
            "cut in half. Neither axis is forced to start at zero."
        ),
        pr.h3(f"What {name} refuses"),
        pr.bullets(
            [
                "A `series()` with no points, a point of the wrong shape, or an "
                "empty label, when it is called.",
                "Rendering without a `series()`, with more than five, with two "
                "series of the same label, or without both axis labels.",
            ]
        ),
        pr.p("Each raises a `ValueError` that names the problem."),
    ]
