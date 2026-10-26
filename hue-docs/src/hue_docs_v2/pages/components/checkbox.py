from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Checkbox, RadioGroup, Stack, Switch

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def terms() -> Checkbox:
    return Checkbox().name("terms").label("I accept the terms")


# Anatomy


def label_only() -> Checkbox:
    return Checkbox().name("newsletter").label("Subscribe to the newsletter")


def with_description() -> Checkbox:
    return (
        Checkbox()
        .name("marketing")
        .label("Marketing emails")
        .description("You can unsubscribe at any time.")
    )


def card() -> Checkbox:
    return (
        Checkbox()
        .name("sso")
        .label("Enforce SSO")
        .description("Members sign in through your identity provider.")
        .card()
        .checked()
    )


def hidden_label() -> Checkbox:
    return Checkbox().name("row_select").label("Select INV-2048").hidden_label()


# States


def unchecked() -> Checkbox:
    return Checkbox().name("state_unchecked").label("Archive")


def checked() -> Checkbox:
    return Checkbox().name("state_checked").label("Archive").checked()


def indeterminate() -> Checkbox:
    return Checkbox().name("state_all").label("Select all").indeterminate()


def required() -> Checkbox:
    return Checkbox().name("state_required").label("I agree to the terms").required()


def disabled() -> Checkbox:
    return Checkbox().name("state_disabled").label("Archive").disabled()


def disabled_checked() -> Checkbox:
    return Checkbox().name("state_locked").label("Archive").checked().disabled()


# Error


def field_error() -> Checkbox:
    return (
        Checkbox()
        .name("consent")
        .label("I consent to the processing of my data")
        .required()
        .error("Tick the box to continue.")
    )


# Several under one name


def one_name_several_values() -> ComponentType:
    return Stack().content(
        Checkbox().name("tags").value("billing").label("Billing"),
        Checkbox().name("tags").value("support").label("Support").checked(),
        Checkbox().name("tags").value("sales").label("Sales"),
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Checkbox` is the browser's own checkbox input with a styled box, "
            "inside a `label` element that also holds its text. The whole row is "
            "the hit area, so a click on the words toggles the box. `name()` is "
            "required and sets the submitted name. Without `value()` the browser "
            "submits `on` for a ticked box and nothing for an empty one."
        ),
        pr.code('Checkbox().name("terms").label("I accept the terms").required()'),
        pr.h3("Several boxes under one name"),
        pr.p(
            "Give each `Checkbox` the same `name()` and its own `value()`, and the "
            "form "
            "submits one entry per ticked box. A `Checkbox` with a value builds its "
            "id from the name and the value, so boxes that share a name still "
            "get ids of their own, and each label toggles its own box."
        ),
        pr.code(
            'Checkbox().name("tags").value("billing").label("Billing"),\n'
            'Checkbox().name("tags").value("support").label("Support"),'
        ),
        pr.h3("Description and card"),
        pr.p(
            "`description()` adds a second line under the label. A `Checkbox` has "
            "no `hint()`, because its extra sentence sits beside the box rather than "
            "under the row. `card()` puts the row on a bordered surface that "
            "fills with the accent while the box is ticked."
        ),
        pr.h3("A Checkbox without visible text"),
        pr.p(
            "`hidden_label()` renders the input alone, with no row around it, and "
            "moves the label onto the input as `aria-label`. Use it where the "
            "position already says what the box is for, such as one per row "
            "of a table."
        ),
        pr.h3("Indeterminate"),
        pr.p(
            "`indeterminate()` draws a dash in place of the tick, for a box that "
            "stands for several others that disagree. HTML has no attribute "
            "for the mixed state, so the `Checkbox` sets the `indeterminate` DOM "
            "property when "
            "Alpine starts. The first click clears it, the way the native "
            "control behaves."
        ),
        pr.h3("Errors"),
        pr.p(
            "`error()` sets `aria-invalid` on the input, which draws the box with a "
            "red border, and shows the message under the row. A `Form`'s "
            "`errors()` reaches a `Checkbox` by its name, the same as any other "
            "control."
        ),
    )


PAGE = ComponentPage(
    Checkbox,
    lede=(
        "A checkbox for a yes or no answer, or for one choice among several "
        "that can all be ticked. It is the browser's own input, styled, so the "
        "keyboard, the form and assistive technology all work as they do "
        "natively."
    ),
    usage=_usage,
    panels=[
        panel("Live", terms, layout="center", hint="Click the box or the label"),
        panel(
            "Anatomy",
            label_only,
            with_description,
            card,
            hidden_label,
            layout="stack",
        ),
        panel(
            "States",
            unchecked,
            checked,
            indeterminate,
            required,
            disabled,
            disabled_checked,
        ),
        panel("Error", field_error, layout="stack"),
        panel(
            "Grouped",
            one_name_several_values,
            layout="stack",
            hint="One name, a value each",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "The input points at its label with `aria-labelledby` and at its "
            "description with `aria-describedby`, so a screen reader reads the "
            "label as the name and the description after it, rather than the "
            "whole row as one long name.",
        ),
        Note(
            "a11y",
            "There is no `role` attribute, since the native checkbox already has one, "
            "and Space toggles it as the browser always does.",
        ),
        Note(
            "a11y",
            'The error message has `role="alert"` and is added to the input\'s '
            "`aria-describedby`, and `aria-invalid` draws the red border, so the "
            "colour never carries the meaning alone.",
        ),
        Note(
            "note",
            "`required()` sets the native `required` attribute. The row shows no "
            "asterisk, and the browser blocks the submit until the box is ticked.",
        ),
        Note(
            "warn",
            "Two checkboxes with the same name and no value get the same `id`. "
            "Give each a `value()`, its own `name()` or an `id()`.",
        ),
    ],
    related=[Switch, RadioGroup],
)
