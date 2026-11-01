from __future__ import annotations

from hue.js import close
from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Dialog,
    Drawer,
    NativeSelect,
    Radio,
    RadioGroup,
    Stack,
    Text,
)

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def filters() -> Drawer:
    return (
        Drawer()
        .title("Filters")
        .description("3 filters applied, 148 of 2,481 records")
        .trigger(Button().variant("outline").content("Open filters"))
        .content(
            Stack().content(
                RadioGroup()
                .name("status")
                .legend("Status")
                .value("paid")
                .content(
                    Radio().value("paid").label("Paid (1,904)"),
                    Radio().value("pending").label("Pending (412)"),
                    Radio().value("refunded").label("Refunded (118)"),
                ),
                NativeSelect()
                .name("period")
                .label("Period")
                .options(
                    [
                        ("30", "Last 30 days"),
                        ("90", "Last 90 days"),
                        ("ytd", "Year to date"),
                    ]
                ),
            )
        )
        .footer(Button().content("Show 148 records").on_click(close()))
    )


# Sides


def end() -> Drawer:
    return (
        Drawer()
        .side("end")
        .title("Activity")
        .trigger(Button().variant("outline").content("End"))
        .content(Text("Arrives from the right in a left-to-right page."))
    )


def start() -> Drawer:
    return (
        Drawer()
        .side("start")
        .title("Navigation")
        .trigger(Button().variant("outline").content("Start"))
        .content(Text("Arrives from the left in a left-to-right page."))
    )


def bottom() -> Drawer:
    return (
        Drawer()
        .side("bottom")
        .title("INV-2048")
        .description("$1,200.00, paid 12 Sep 2026")
        .trigger(Button().variant("outline").content("Bottom"))
        .footer(Button().variant("outline").content("Close").on_click(close()))
    )


# Sizes


def sm() -> Drawer:
    return (
        Drawer()
        .size("sm")
        .title("320px wide")
        .trigger(Button().variant("outline").content("Small"))
    )


def md() -> Drawer:
    return (
        Drawer()
        .size("md")
        .title("420px wide")
        .trigger(Button().variant("outline").content("Medium"))
    )


def lg() -> Drawer:
    return (
        Drawer()
        .size("lg")
        .title("560px wide")
        .trigger(Button().variant("outline").content("Large"))
    )


# States


def must_be_answered() -> Drawer:
    return (
        Drawer()
        .dismissible(False)
        .title("Unsaved changes")
        .description("Keep editing, or throw the changes away.")
        .trigger(Button().variant("outline").content("Leave editor"))
        .footer(
            # First, because the trap focuses the first control when the
            # Drawer opens, and Enter there should keep the changes.
            Button().content("Keep editing").on_click(close()),
            Button().variant("ghost").content("Discard").on_click(close()),
        )
    )


def named_by_label() -> Drawer:
    return (
        Drawer()
        .label("Notifications")
        .trigger(Button().variant("outline").content("Notifications"))
        .content(Text("No new notifications."))
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Drawer` is a `Dialog` that slides in from an edge of the screen. "
            "It takes the same `title()`, `description()`, `content()`, "
            "`footer()`, `trigger()`, `dismissible()` and `open()` as a "
            "`Dialog`, and adds `side()` and `size()`."
        ),
        pr.code(
            "from hue.js import close\n\n"
            "(\n"
            "    Drawer()\n"
            '    .title("Filters")\n'
            '    .trigger(Button().variant("outline").content("Open filters"))\n'
            "    .content(...)\n"
            '    .footer(Button().content("Apply").on_click(close()))\n'
            ")"
        ),
        pr.p(
            "Pass `close()` from `hue.js` to `on_click()` on a footer button to close "
            "the `Drawer`. A button with no handler leaves it open."
        ),
        pr.h2("Drawer sides and widths"),
        pr.p(
            '`side()` takes `"end"`, `"start"` or `"bottom"`, and defaults to '
            '`"end"`. The sides '
            'are logical: `"end"` is the right edge in a left-to-right page and '
            "the left edge in a right-to-left one. `size()` sets the width of a "
            'side `Drawer`, 320px, 420px or 560px, and defaults to `"md"`. A bottom '
            "`Drawer` is as wide as the screen, so `size()` does nothing there."
        ),
        pr.h3("Below the md breakpoint"),
        pr.p(
            "Below `md` (768px) every `Drawer` is a bottom sheet with a grab "
            "handle, whatever `side()` says, at most 85% of the screen tall. "
            "Drag the Sides panel narrower than `md` to see all three become "
            "the same sheet."
        ),
        pr.h2("Drawer that has to be answered"),
        pr.p(
            "`dismissible(False)` removes the close button and the click on the "
            "dimmed page that would close the `Drawer`, so the footer actions "
            "are the way out. Escape still closes it."
        ),
        pr.p(
            "When a `Drawer` opens, its focus trap moves focus to the first "
            "control inside it. The States example puts Keep editing first in "
            "the footer, so pressing Enter as soon as it opens keeps the changes."
        ),
    )


PAGE = ComponentPage(
    Drawer,
    lede=(
        "A `Drawer` is a modal panel that slides in from an edge, for a list or "
        "a form too long for a centred `Dialog`. Below the `md` breakpoint every "
        "`Drawer` becomes a bottom sheet."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            filters,
            layout="center",
            min_height=520,
            width="lg",
            hint="Open it, tab through it, press Escape",
        ),
        panel(
            "Sides",
            end,
            start,
            bottom,
            min_height=360,
            width="lg",
            hint="Below md every side is a bottom sheet",
        ),
        panel(
            "Sizes",
            sm,
            md,
            lg,
            min_height=320,
            width="lg",
            hint="Wider than md only",
        ),
        panel("States", must_be_answered, named_by_label, min_height=320, width="lg"),
    ],
    notes=[
        Note(
            "a11y",
            'The panel is an `aside` with `role="dialog"` and `aria-modal`, named by '
            "its title through `aria-labelledby`, or by `label()` when it has no "
            "title.",
        ),
        Note(
            "a11y",
            "Focus is trapped inside while the `Drawer` is open and the page "
            "behind is inert. Closing gives focus back to the control that "
            "opened it.",
        ),
        Note(
            "a11y",
            "Escape closes only the innermost overlay, so a `Popover` inside a "
            "`Drawer` closes before the `Drawer` does.",
        ),
        Note(
            "note",
            "A `Drawer` with neither `title()` nor `label()` raises an error when it "
            "renders.",
        ),
        Note(
            "warn",
            "Escape closes a `Drawer` even with `dismissible(False)`.",
        ),
    ],
    related=[Dialog],
)
