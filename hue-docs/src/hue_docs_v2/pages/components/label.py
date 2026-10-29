from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Label, Text, TextInput

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def linked_to_an_input() -> ComponentType:
    return html.div(
        Label("Company name").html_for("company"),
        html.input_()
        .input_type("text")
        .name("company")
        .id("company")
        .class_(
            "h-control-md w-full max-w-64 rounded-md border border-border-input "
            "bg-surface px-3 text-fg shadow-field"
        ),
    ).class_("flex flex-col gap-1.5")


# Anatomy


def text_only() -> Label:
    return Label("Email")


def required() -> Label:
    return Label("Email").required()


# States


def enabled() -> Label:
    return Label("Billing address")


def disabled() -> Label:
    return Label("Billing address").disabled()


def hidden_label() -> ComponentType:
    return html.div(
        Label("Search invoices").html_for("invoice-search").hidden_label(),
        html.input_()
        .input_type("search")
        .name("invoice_search")
        .id("invoice-search")
        .placeholder("Search invoices")
        .class_(
            "h-control-md w-full max-w-64 rounded-md border border-border-input "
            "bg-surface px-3 text-fg shadow-field"
        ),
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "`Label` renders a `label` element holding its text. `html_for()` sets "
            "the `for` attribute to a control's `id`, which ties the two together: "
            "the control takes the label as its accessible name, and a click on "
            "the label focuses the control."
        ),
        pr.code(
            'Label("Company name").html_for("company")\n'
            'html.input_().input_type("text").name("company").id("company")'
        ),
        pr.h3("When to use Label on its own"),
        pr.p(
            "`TextInput` and the other controls laid out by `Field` render a `Label` "
            "from their own `label()` modifier, with the `for` attribute already "
            "set. Use `Label` on its own for a control you build from plain "
            "markup."
        ),
        pr.h3("What the Label modifiers change"),
        pr.p("Each modifier changes the label only, never the control it points at:"),
        pr.bullets(
            [
                pr.p(
                    "`required()` adds an asterisk after the text. The asterisk is "
                    "hidden from screen readers, so set `required` on the control "
                    "as well, which is what announces it."
                ),
                pr.p(
                    "`disabled()` draws the text in the disabled colour and stops "
                    "the label taking clicks. Disable the control itself too."
                ),
                pr.p(
                    "`hidden_label()` hides the label visually and keeps it for "
                    "screen readers, for a control whose purpose shows "
                    "without one, such as a search box."
                ),
            ]
        ),
    )


PAGE = ComponentPage(
    Label,
    lede=(
        "A label names a form control. `Label` renders the `label` element, with "
        "an optional required marker, and links it to its control by id."
    ),
    usage=_usage,
    panels=[
        panel("Live", linked_to_an_input, layout="center", hint="Click the label"),
        panel("Anatomy", text_only, required),
        panel("States", enabled, disabled, hidden_label),
    ],
    notes=[
        Note(
            "a11y",
            "`html_for()` is what gives the control its accessible name. A `Label` "
            "without it is text beside the control and names nothing.",
        ),
        Note(
            "a11y",
            "The required asterisk is `aria-hidden`. A screen reader learns that "
            "a field is required from the control's own `required` attribute.",
        ),
        Note(
            "a11y",
            "`hidden_label()` uses `sr-only`, so the label is still in the "
            "accessibility tree and still names the control.",
        ),
        Note(
            "warn",
            "`disabled()` and `required()` style the label only. They set nothing "
            "on the control.",
        ),
    ],
    related=[TextInput, Text],
)
