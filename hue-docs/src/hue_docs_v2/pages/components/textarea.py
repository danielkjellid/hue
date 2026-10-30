from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Form, Textarea, TextInput

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def description() -> Textarea:
    return (
        Textarea()
        .name("description")
        .label("Description")
        .placeholder("What does this workspace do?")
        .max_length(280)
    )


# Anatomy


def label_and_hint() -> Textarea:
    return Textarea().name("notes").label("Notes").hint("Only your team can see these.")


def rows() -> Textarea:
    return Textarea().name("address").label("Address").rows(6)


def character_count() -> Textarea:
    return (
        Textarea()
        .name("summary")
        .label("Summary")
        .max_length(120)
        .value("Internal tooling for the logistics team.")
    )


def autosize() -> Textarea:
    return (
        Textarea()
        .name("changelog")
        .label("Changelog")
        .autosize()
        .value("Fixed the export.\nAdded dark mode.\nRenamed seats to members.")
    )


# States


def enabled() -> Textarea:
    return Textarea().name("state_enabled").label("Bio").value("Designer in Oslo.")


def required() -> Textarea:
    return Textarea().name("state_required").label("Bio").required()


def readonly() -> Textarea:
    return (
        Textarea()
        .name("state_readonly")
        .label("Bio")
        .value("Designer in Oslo.")
        .readonly()
    )


def disabled() -> Textarea:
    return (
        Textarea()
        .name("state_disabled")
        .label("Bio")
        .value("Designer in Oslo.")
        .disabled()
    )


# Error


def field_error() -> Textarea:
    return (
        Textarea()
        .name("reason")
        .label("Reason for refund")
        .hint("Tell us what went wrong.")
        .error("Add a reason before you submit.")
    )


def over_the_limit() -> Textarea:
    return (
        Textarea()
        .name("tagline")
        .label("Tagline")
        .max_length(40)
        .value("Internal tooling for the logistics team, built in Oslo.")
    )


# Layout


def horizontal() -> Textarea:
    return (
        Textarea()
        .name("about")
        .label("About")
        .hint("Shown on your public profile.")
        .horizontal()
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Textarea` is the multi-line field. Like ",
            pr.link("TextInput", "/components/text-input/"),
            ", it renders its own label, hint and error, and `name()` sets the "
            "submitted name and the ids that tie them together. It takes "
            "`label()`, `hint()`, `error()`, `placeholder()`, `value()`, `required()`, "
            "`disabled()`, `readonly()`, `hidden_label()` and `horizontal()`, but has "
            "no `size()`, prefix, suffix or action.",
        ),
        pr.code('Textarea().name("bio").label("About you").rows(4)'),
        pr.p(
            "`value()` goes between the tags exactly as given, so the server "
            "gets back what it sent, with no newline added at either end."
        ),
        pr.h2("Counting characters with max_length()"),
        pr.p(
            "`Textarea.max_length()` is a soft limit. It shows a count such as "
            "12 / 280 at the end of the label row and keeps it up to date as "
            "the reader types. Past the limit the count turns red and the "
            "textarea sets `aria-invalid`, but every character is still "
            "accepted. There is no `maxlength` attribute, so nothing stops the "
            "keyboard."
        ),
        pr.p(
            "Because the text is never cut, a submission can still be too "
            "long. Check the length on the server and return the message "
            "with `error()`. While an error is set, the count no longer "
            "toggles `aria-invalid`, because the error already sets it."
        ),
        pr.code('Textarea().name("bio").label("About you").max_length(280)'),
        pr.h2("Growing a Textarea with autosize()"),
        pr.p(
            "`autosize()` makes the textarea as tall as its text, on load and "
            "on every input, instead of scrolling inside a fixed box. `rows()` "
            "makes one that does not autosize taller; a `Textarea` is never "
            "shorter than 84px, so a small `rows()` has no effect. Either "
            "way, the reader can drag the corner to resize it vertically."
        ),
    )


PAGE = ComponentPage(
    Textarea,
    lede=(
        "A multi-line text field with its label, hint and error built in. "
        "`max_length()` adds a live character count that warns past the limit "
        "without cutting the text, and `autosize()` lets it grow with what is "
        "typed."
    ),
    usage=_usage,
    panels=[
        panel("Live", description, layout="stack", hint="Type in it"),
        panel(
            "Anatomy",
            label_and_hint,
            rows,
            character_count,
            autosize,
            layout="stack",
        ),
        panel("States", enabled, required, readonly, disabled, layout="stack"),
        panel("Error", field_error, over_the_limit, layout="stack"),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            min_width=480,
            hint="The label takes a 180px column at every width",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "With `max_length()`, the visible count is hidden from screen "
            'readers. A sentence such as "You have 12 characters remaining" '
            "takes its place. It is part of the textarea's description, and "
            "it is a polite live region that updates a second after typing "
            "stops.",
        ),
        Note(
            "a11y",
            "Past the limit the count turns red and the textarea sets "
            "`aria-invalid`, so the colour never carries the meaning alone.",
        ),
        Note(
            "warn",
            "`max_length()` does not stop input. Enforce the limit on the "
            "server, or a long submission goes through.",
        ),
    ],
    related=[TextInput, Form],
)
