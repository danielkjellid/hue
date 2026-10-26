from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import NumberInput, Slider

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def team_seats() -> Slider:
    return Slider().name("seats").label("Team seats").min(1).max(50).value(12)


# Anatomy


def ticks() -> Slider:
    return (
        Slider()
        .name("ticked_seats")
        .label("Team seats")
        .min(1)
        .max(50)
        .value(25)
        .ticks("1", "25", "50")
    )


def prefix_and_step() -> Slider:
    return (
        Slider()
        .name("budget")
        .label("Monthly budget cap")
        .min(0)
        .max(2000)
        .step(50)
        .value(600)
        .prefix("$")
        .hint("Billing pauses when the cap is reached.")
    )


def suffix() -> Slider:
    return Slider().name("opacity").label("Opacity").value(80).suffix("%")


def no_readout() -> Slider:
    return Slider().name("volume").label("Volume").value(70).show_value(False)


# States


def enabled() -> Slider:
    return Slider().name("state_enabled").label("Retention in days").value(30)


def disabled() -> Slider:
    return (
        Slider()
        .name("state_disabled")
        .label("Managed by your plan")
        .value(25)
        .disabled()
    )


# Error


def field_error() -> Slider:
    return (
        Slider()
        .name("replicas")
        .label("Replicas")
        .min(1)
        .max(10)
        .value(9)
        .error("Your plan runs up to 5 replicas.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Slider` is a native range input with its label, hint and the "
            "number it is set to. `min()` and `max()` default to `0` and `100`, and "
            "`value()` defaults to `min()`. `step()` is left to the browser unless "
            "you set it."
        ),
        pr.code('Slider().name("seats").label("Team seats").min(1).max(50).value(12)'),
        pr.h2("The Slider readout"),
        pr.p(
            "The current value is shown at the end of the label row and "
            "follows the thumb as it moves. It is on by default. "
            "`show_value(False)` removes it, for a row that already shows the "
            "number somewhere else."
        ),
        pr.p(
            "`prefix()` and `suffix()` wrap the number in the readout, such as `$` "
            "or `%`. They are plain text and never part of an expression, so a "
            "quote or an apostrophe in one is safe. "
            "With either one set, the range input also gets `aria-valuetext`, "
            "so a screen reader hears $600 rather than 600."
        ),
        pr.code(
            'Slider().name("budget").label("Budget").max(2000).step(50).prefix("$")'
        ),
        pr.h2("Slider ticks"),
        pr.p(
            "`ticks()` takes labels and spreads them evenly under the track, "
            "from the first at the start to the last at the end. They are "
            "labels only. They do not snap the thumb, and they are not placed "
            "by value, so pass ones that sit at even intervals."
        ),
        pr.h2("Keyboard"),
        pr.p(
            "The range input is native, so the browser handles the keys: the "
            "arrow keys move it by one step, Home and End jump to `min()` and "
            "`max()`, and Page Up and Page Down take larger steps. The readout "
            "follows every change."
        ),
    )


PAGE = ComponentPage(
    Slider,
    lede=(
        "A range input paired with the number it is set to. The readout sits "
        "in the label row and follows the thumb, and `prefix()` and `suffix()` "
        "give it a unit."
    ),
    usage=_usage,
    panels=[
        panel("Live", team_seats, layout="stack", hint="Drag it, or use the arrows"),
        panel("Anatomy", ticks, prefix_and_step, suffix, no_readout, layout="stack"),
        panel("States", enabled, disabled, layout="stack"),
        panel("Error", field_error, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            'The track is a native `input type="range"` with a `label` element, so '
            "it is announced as a slider with its value, and every key the "
            "browser supports works.",
        ),
        Note(
            "a11y",
            "With a prefix or suffix, `aria-valuetext` carries the same text as "
            "the readout, so the spoken value includes the unit.",
        ),
        Note(
            "note",
            "`disabled()` sets the native `disabled` attribute, so the slider leaves "
            "the tab order and is not submitted with the form.",
        ),
    ],
    related=[NumberInput],
)
