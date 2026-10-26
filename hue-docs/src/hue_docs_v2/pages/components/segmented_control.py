from __future__ import annotations

from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import ButtonGroup, SegmentedControl, SegmentedOption, Tabs, ThemeSwitcher

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def date_range() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Date range")
        .value("week")
        .content(
            SegmentedOption().value("day").content("Day"),
            SegmentedOption().value("week").content("Week"),
            SegmentedOption().value("month").content("Month"),
        )
    )


# Sizes


def sm() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Billing period, small")
        .size("sm")
        .value("annual")
        .content(
            SegmentedOption().value("monthly").content("Monthly"),
            SegmentedOption().value("annual").content("Annual"),
        )
    )


def md() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Billing period, medium")
        .size("md")
        .value("annual")
        .content(
            SegmentedOption().value("monthly").content("Monthly"),
            SegmentedOption().value("annual").content("Annual"),
        )
    )


def lg() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Billing period, large")
        .size("lg")
        .value("annual")
        .content(
            SegmentedOption().value("monthly").content("Monthly"),
            SegmentedOption().value("annual").content("Annual"),
        )
    )


# Anatomy


def text_options() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Status")
        .value("open")
        .content(
            SegmentedOption().value("open").content("Open"),
            SegmentedOption().value("closed").content("Closed"),
            SegmentedOption().value("all").content("All"),
        )
    )


def icon_only_options() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("Layout")
        .value("list")
        .content(
            SegmentedOption().value("list").icon_only("List").content(Icon("list")),
            SegmentedOption()
            .value("grid")
            .icon_only("Grid")
            .content(Icon("layout-grid")),
        )
    )


def icon_and_text() -> SegmentedControl:
    return (
        SegmentedControl()
        .label("View")
        .value("grid")
        .content(
            SegmentedOption().value("list").content(Icon("list"), "List"),
            SegmentedOption().value("grid").content(Icon("layout-grid"), "Grid"),
        )
    )


# Driven by Alpine


def selection_in_your_own_state() -> ComponentType:
    return (
        html.div(
            SegmentedControl()
            .label("Sort order")
            .content(
                SegmentedOption()
                .value("newest")
                .content("Newest")
                .x_on("click", unsafe("order = 'newest'"))
                .x_bind("aria-pressed", unsafe("String(order === 'newest')")),
                SegmentedOption()
                .value("oldest")
                .content("Oldest")
                .x_on("click", unsafe("order = 'oldest'"))
                .x_bind("aria-pressed", unsafe("String(order === 'oldest')")),
            ),
            html.p()
            .class_("text-sm text-fg-muted")
            .x_text(unsafe("'Sorted by ' + order")),
        )
        .class_("flex flex-col items-start gap-3")
        .x_data({"order": "newest"})
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `SegmentedControl` is a row of `SegmentedOption` buttons where one "
            "is on. `label()` names the control, `value()` picks the option that "
            "starts selected, and each option's `value()` is what that "
            "selection is matched against. The control sets every option's "
            "size and pressed state itself."
        ),
        pr.code(
            "SegmentedControl()\n"
            '.label("Date range")\n'
            '.value("week")\n'
            ".content(\n"
            '    SegmentedOption().value("day").content("Day"),\n'
            '    SegmentedOption().value("week").content("Week"),\n'
            '    SegmentedOption().value("month").content("Month"),\n'
            ")"
        ),
        pr.h3("Where a SegmentedControl keeps its selection"),
        pr.p(
            "With `value()` set, the control renders an Alpine scope holding "
            "`selected`, and a click on an option sets `selected` to that "
            "option's value. The server renders `aria-pressed` for the starting "
            "option, so the right one is on before Alpine starts. The "
            "selection stays in the browser. The control renders no input, so "
            "a form around it submits nothing for it."
        ),
        pr.h3("Driving a SegmentedControl from your own state"),
        pr.p(
            "Leave `value()` unset and the control keeps no state at all. Give "
            "each option its own click handler and its own `aria-pressed` "
            "binding, and the selection can live in any Alpine scope around "
            "the control, where other elements can read it. `ThemeSwitcher` is "
            "built this way, on the theme store."
        ),
        pr.code(
            "html.div(\n"
            '    SegmentedControl().label("Sort order").content(\n'
            "        SegmentedOption()\n"
            '        .value("newest")\n'
            '        .content("Newest")\n'
            '        .x_on("click", unsafe("order = \'newest\'"))\n'
            '        .x_bind("aria-pressed", '
            "unsafe(\"String(order === 'newest')\")),\n"
            "        ...,\n"
            "    ),\n"
            "    html.p().x_text(unsafe(\"'Sorted by ' + order\")),\n"
            ').x_data({"order": "newest"})'
        ),
        pr.h3("SegmentedControl options that hold only an icon"),
        pr.p(
            "`icon_only()` makes the option square and takes its accessible name "
            "as the argument, because an icon has no text to read. An option "
            "with visible text is named by the text, so it needs no `label()`."
        ),
        pr.h3("SegmentedControl sizes"),
        pr.p(
            "`size()` sets the height of the whole track: 32px for `sm`, 36px for "
            "`md` (the default) and 44px for `lg`. The options sit 8px shorter "
            "than the track, inside its padding and border."
        ),
    )


PAGE = ComponentPage(
    SegmentedControl,
    lede=(
        "A segmented control is a row of options where exactly one is on, "
        "such as a date range or a list and grid view. The control draws its "
        "options and marks the selected one as pressed."
    ),
    usage=_usage,
    panels=[
        panel("Live", date_range, layout="center", hint="Click or tab and press"),
        panel("Sizes", sm, md, lg),
        panel("Anatomy", text_options, icon_only_options, icon_and_text),
        panel(
            "Driven by Alpine",
            selection_in_your_own_state,
            layout="stack",
            captions=False,
            hint="No `value()`; the options bind to a scope around the control",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The control is a `div` with `role="group"` named by `label()`. Each '
            "option is a native button with `aria-pressed`, so a screen reader "
            "hears a toggle button that is pressed or not.",
        ),
        Note(
            "a11y",
            "Every option is its own Tab stop, and Enter or Space presses it. "
            "There is no arrow-key navigation between options.",
        ),
        Note(
            "a11y",
            "`icon_only()` takes the option's accessible name as its argument and "
            "renders it as `aria-label`.",
        ),
        Note(
            "note",
            "The selection is not a form field. A form around the control "
            "submits nothing for it.",
        ),
        Note(
            "warn",
            "With `value()` set, the control writes each option's click handler "
            "itself, so an `on_click()` of your own on an option is replaced. To "
            "run code on a choice, leave `value()` unset and bind the options "
            "yourself, as in the Driven by Alpine panel.",
        ),
    ],
    parts=[SegmentedOption],
    related=[Tabs, ButtonGroup, ThemeSwitcher],
)
