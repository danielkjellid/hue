from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Button, ButtonGroup, SegmentedControl

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def split_button() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("outline").size("sm").content("Export"),
        Button()
        .variant("outline")
        .size("sm")
        .icon_only("Export options")
        .content(Icon("chevron-down")),
    )


# Anatomy


def two_actions() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("outline").content("Export"),
        Button().variant("outline").content("Schedule"),
    )


def labelled() -> ButtonGroup:
    return (
        ButtonGroup()
        .label("Row actions")
        .content(
            Button().variant("outline").content("Edit"),
            Button().variant("outline").content("Duplicate"),
            Button().variant("danger-outline").content("Delete"),
        )
    )


def icon_only() -> ButtonGroup:
    return (
        ButtonGroup()
        .label("Selection")
        .content(
            Button().variant("outline").icon_only("Add").content(Icon("plus")),
            Button().variant("outline").icon_only("Copy").content(Icon("copy")),
            Button().variant("outline").icon_only("Delete").content(Icon("trash")),
        )
    )


# Variants


def primary() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("primary").content("Publish"),
        Button().variant("primary").icon_only("More").content(Icon("chevron-down")),
    )


def secondary() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("secondary").content("Save"),
        Button().variant("secondary").icon_only("More").content(Icon("chevron-down")),
    )


def outline() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("outline").content("Preview"),
        Button().variant("outline").icon_only("More").content(Icon("chevron-down")),
    )


def danger() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("danger").content("Delete"),
        Button().variant("danger").icon_only("More").content(Icon("chevron-down")),
    )


def danger_outline() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("danger-outline").content("Delete"),
        Button()
        .variant("danger-outline")
        .icon_only("More")
        .content(Icon("chevron-down")),
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A ButtonGroup joins the buttons inside it into one row. It squares "
            "off the inner corners, keeps the outer ones rounded and pulls each "
            "button 1px onto its neighbour, so two borders meet as one line. "
            "Each button keeps its own variant, size and click handler, so give "
            "them all the same variant and size."
        ),
        pr.code(
            "ButtonGroup().content(\n"
            '    Button().variant("outline").size("sm").content("Export"),\n'
            '    Button().variant("outline").size("sm").content("Schedule"),\n'
            ")"
        ),
        pr.h3("Naming a ButtonGroup"),
        pr.p(
            'label() adds role="group" and an aria-label, so a screen reader '
            "announces the name as focus enters the group. Without label() the "
            "ButtonGroup is a plain div with no role, since a group with no name "
            'is announced as only "group".'
        ),
        pr.code(
            'ButtonGroup().label("Row actions").content(\n'
            '    Button().variant("outline").content("Edit"),\n'
            '    Button().variant("danger-outline").content("Delete"),\n'
            ")"
        ),
        pr.h3("Variants a ButtonGroup accepts"),
        pr.p(
            "The shared edge is made of the buttons' borders, so only variants "
            "with a border can join: primary, secondary, outline, danger and "
            "danger-outline. A ghost or link Button placed directly in a "
            "ButtonGroup raises a ValueError when the group renders."
        ),
        pr.h3("A choice between options"),
        pr.p(
            "A ButtonGroup holds actions, and none of its buttons is ever on. "
            "For a row where exactly one option is selected, use "
            "SegmentedControl."
        ),
    )


PAGE = ComponentPage(
    ButtonGroup,
    lede=(
        "A button group joins related buttons into one control. The buttons "
        "share their edges and nothing else, so each one keeps its own action. "
        "A split button is the common case: an action and a button beside it "
        "for its options."
    ),
    usage=_usage,
    panels=[
        panel("Live", split_button, layout="center", hint="Tab through it"),
        panel("Anatomy", two_actions, labelled, icon_only, layout="stack"),
        panel(
            "Variants",
            primary,
            secondary,
            outline,
            danger,
            danger_outline,
            hint="The Button variants with a border",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'label() renders role="group" with an aria-label. Without it the '
            "group is a div with no role.",
        ),
        Note(
            "a11y",
            "Every button stays its own Tab stop. The group adds no arrow-key "
            "navigation.",
        ),
        Note(
            "a11y",
            "A focused button is lifted above its neighbours, so its focus ring "
            "is not hidden under the button beside it.",
        ),
        Note(
            "warn",
            "A ghost or link Button placed directly in the group raises a "
            "ValueError at render, because those variants have no border to "
            "share.",
        ),
    ],
    related=[Button, SegmentedControl],
)
