from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import EmailInput, Form, PasswordInput, TextInput

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def work_email() -> EmailInput:
    return (
        EmailInput()
        .name("email")
        .label("Work email")
        .placeholder("you@example.com")
        .hint("We send the invoice here.")
    )


# Anatomy


def sign_in() -> EmailInput:
    return EmailInput().name("login").label("Email").autocomplete("username")


def required() -> EmailInput:
    return EmailInput().name("billing_email").label("Billing email").required()


# Error


def already_invited() -> EmailInput:
    return (
        EmailInput()
        .name("invitee")
        .label("Email")
        .value("ada@example.com")
        .error("That address is already invited.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "An `EmailInput` is a ",
            pr.link("TextInput", "/components/text-input/"),
            ' with `type="email"` and `autocomplete` preset to `"email"`. Label, hint, '
            "error, sizes, prefixes, an attached action, readonly and "
            "horizontal all work the same way, and the `TextInput` page shows "
            "each of them.",
        ),
        pr.code('EmailInput().name("email").label("Email")'),
        pr.h2("Changing the EmailInput autocomplete"),
        pr.p(
            "`autocomplete()` replaces the preset. A sign-in form whose account "
            'key is an email address can ask for `"username"` instead, which is '
            "the token password managers pair with a password."
        ),
        pr.code('EmailInput().name("login").label("Email").autocomplete("username")'),
        pr.h2("Validating an EmailInput"),
        pr.p(
            '`type="email"` lets the browser check the address\'s shape before the '
            "form submits. Anything that posts to your route directly skips "
            "that check, so validate on the server too and hand the message "
            "back with `error()`, or by name through `Form.errors()`."
        ),
        pr.code(
            "from hue.ui import EmailInput, Form\n\n"
            'Form().errors({"email": "That address is already invited."}).content(\n'
            '    EmailInput().name("email").label("Email"),\n'
            ")"
        ),
    )


PAGE = ComponentPage(
    EmailInput,
    lede=(
        'A `TextInput` for an email address. It sets `type="email"` and presets '
        '`autocomplete` to `"email"`, and shares every other modifier with `TextInput`.'
    ),
    usage=_usage,
    panels=[
        panel("Live", work_email, layout="stack", hint="Type in it"),
        panel("Anatomy", sign_in, required, layout="stack"),
        panel("Error", already_invited, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The label, hint and error are wired exactly as on `TextInput`: a "
            "`label` element for the input, and the hint and error in "
            "`aria-describedby`.",
        ),
    ],
    related=[TextInput, PasswordInput, Form],
)
