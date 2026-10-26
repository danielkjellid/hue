from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Button, Kbd, Popover, Tooltip

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def on_an_icon_button() -> Tooltip:
    return (
        Tooltip()
        .content("Dismiss")
        .trigger(Button().variant("ghost").icon_only("Dismiss").content(Icon("x")))
    )


# Placements


def top() -> Tooltip:
    return (
        Tooltip()
        .placement("top")
        .content("Above")
        .trigger(Button().variant("outline").size("sm").content("top"))
    )


def bottom() -> Tooltip:
    return (
        Tooltip()
        .placement("bottom")
        .content("Below")
        .trigger(Button().variant("outline").size("sm").content("bottom"))
    )


def start() -> Tooltip:
    return (
        Tooltip()
        .placement("start")
        .content("Before")
        .trigger(Button().variant("outline").size("sm").content("start"))
    )


def end() -> Tooltip:
    return (
        Tooltip()
        .placement("end")
        .content("After")
        .trigger(Button().variant("outline").size("sm").content("end"))
    )


# Anatomy


def label_only() -> Tooltip:
    return (
        Tooltip()
        .content("Copy to clipboard")
        .trigger(Button().variant("ghost").size("sm").content(Icon("copy"), "Copy"))
    )


def with_its_keys() -> Tooltip:
    return (
        Tooltip()
        .content("Search")
        .keys(Kbd("mod", "K"))
        .trigger(Button().variant("ghost").icon_only("Search").content(Icon("search")))
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Tooltip` wraps the control it describes. `content()` is the text "
            "of the bubble and `trigger()` is the control. The bubble shows "
            "about 400ms after the pointer enters, at once when the control "
            "takes keyboard focus, and hides when the pointer leaves or focus "
            "moves on."
        ),
        pr.code(
            "(\n"
            "    Tooltip()\n"
            '    .content("Dismiss")\n'
            '    .trigger(Button().variant("ghost").icon_only("Dismiss")'
            '.content(Icon("x")))\n'
            ")"
        ),
        pr.h3("The trigger keeps its own name"),
        pr.p(
            "The `Tooltip` sets `aria-describedby` on the trigger, pointing at the "
            "bubble, so the bubble's text is read as a description after the "
            "control's own name. An icon-only `Button` still needs its label in "
            "`icon_only()`, because the `Tooltip` describes the control and does not "
            "name it. `trigger()` takes a hue component for this reason, since an "
            "attribute on a wrapper around the control describes nothing."
        ),
        pr.h3("Showing keys"),
        pr.p(
            "`keys()` shows keys after the label. Pass a `Kbd`, which renders `kbd` "
            "elements and gives each modifier a spoken name. `keys()` only "
            "shows them; bind the keys where the action lives, in the app's "
            "shortcut registry or as a `Command`'s hotkey."
        ),
        pr.h3("Placement"),
        pr.p(
            '`placement()` takes `"top"` (the default), `"bottom"`, `"start"` or '
            '`"end"`, with an arrow pointing at the trigger. `"start"` and `"end"` '
            "are logical, so "
            "they swap sides in a right-to-left page. The bubble does not "
            "flip to stay inside the viewport."
        ),
        pr.h2("What a Tooltip cannot hold"),
        pr.p(
            "Never put a link or a button inside a `Tooltip`. The bubble closes "
            "when focus leaves the trigger, so the keyboard cannot reach "
            "anything in it. For content to interact with, use a `Popover`."
        ),
    )


PAGE = ComponentPage(
    Tooltip,
    lede=(
        "A `Tooltip` is a short label for the control it wraps, shown on hover "
        "and on keyboard focus. Keyboard focus cannot reach anything inside "
        "the bubble, so it holds text and keys only."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            on_an_icon_button,
            layout="center",
            min_height=180,
            hint="Hover it, or tab to it",
        ),
        panel(
            "Placements",
            top,
            bottom,
            start,
            end,
            layout="center",
            min_height=200,
            captions=False,
        ),
        panel("Anatomy", label_only, with_its_keys, layout="center", min_height=200),
    ],
    notes=[
        Note(
            "a11y",
            'The bubble has `role="tooltip"` and an id the trigger points at '
            "with `aria-describedby`, so a screen reader reads it after the "
            "trigger's name.",
        ),
        Note(
            "a11y",
            "The bubble opens on focus as well as hover, because a keyboard "
            "never hovers. The pointer can move onto the bubble without "
            "closing it.",
        ),
        Note(
            "a11y",
            "Escape hides the bubble. The listener is on the window, so it "
            "also hides a bubble opened by hover while focus is elsewhere.",
        ),
        Note(
            "warn",
            "A touch device has no hover, so what a `Tooltip` says must also be "
            "available somewhere else.",
        ),
    ],
    related=[Popover, Kbd],
)
