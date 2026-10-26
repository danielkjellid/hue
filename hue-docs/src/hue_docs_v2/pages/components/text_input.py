from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Button, EmailInput, Field, NumberInput, PasswordInput, TextInput

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def workspace_name() -> TextInput:
    return (
        TextInput()
        .name("workspace")
        .label("Workspace name")
        .placeholder("Acme Inc.")
        .hint("Shown to everyone you invite.")
    )


# Anatomy


def label_and_hint() -> TextInput:
    return (
        TextInput()
        .name("display_name")
        .label("Display name")
        .hint("How your name appears on comments.")
    )


def prefix() -> TextInput:
    return TextInput().name("site").label("Site address").prefix("https://")


def suffix() -> TextInput:
    return TextInput().name("width").label("Width").suffix("px")


def leading_icon() -> TextInput:
    return (
        TextInput()
        .name("query")
        .label("Search")
        .hidden_label()
        .leading_icon(Icon("search"))
        .placeholder("Search invoices")
    )


def action() -> TextInput:
    return (
        TextInput()
        .name("invite_link")
        .label("Invite link")
        .value("https://hue.dev/join/4f2a")
        .readonly()
        .action(Button().variant("outline").content("Copy"))
    )


# Sizes


def sm() -> TextInput:
    return TextInput().name("size_sm").label("Small").size("sm")


def md() -> TextInput:
    return TextInput().name("size_md").label("Medium").size("md")


def lg() -> TextInput:
    return TextInput().name("size_lg").label("Large").size("lg")


# States


def enabled() -> TextInput:
    return TextInput().name("state_enabled").label("Project").value("Atlas")


def required() -> TextInput:
    return TextInput().name("state_required").label("Project").required()


def readonly() -> TextInput:
    return TextInput().name("state_readonly").label("Project").value("Atlas").readonly()


def disabled() -> TextInput:
    return TextInput().name("state_disabled").label("Project").value("Atlas").disabled()


# Error


def field_error() -> TextInput:
    return (
        TextInput()
        .name("handle")
        .label("Handle")
        .value("hue team")
        .hint("Letters, numbers and dashes.")
        .error("A handle cannot contain spaces.")
    )


# Layout


def horizontal() -> TextInput:
    return (
        TextInput()
        .name("company")
        .label("Company")
        .hint("As it appears on invoices.")
        .horizontal()
    )


# Relatives


def email() -> EmailInput:
    return EmailInput().name("email").label("Email")


def password() -> PasswordInput:
    return PasswordInput().name("password").label("Password").revealable()


def number() -> NumberInput:
    return NumberInput().name("seats").label("Seats").min(1).max(50)


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `TextInput` renders its own label, hint and error around the "
            "input, so one chain gives you the whole field. `name()` sets the "
            "submitted name, and the input's id, the label's `for` and the ids "
            "the hint and error hang off are all built from it."
        ),
        pr.code(
            'TextInput().name("email").label("Email").placeholder("you@example.com")'
        ),
        pr.p(
            "A `TextInput` without `label()` uses its name as the label, so the "
            "field is never unnamed. `hidden_label()` keeps the label for screen "
            "readers and hides it visually, for a field whose purpose the "
            "layout already shows, such as a search box."
        ),
        pr.h3("Errors"),
        pr.p(
            "`error()` marks the input invalid with `aria-invalid`, shows the "
            "message in place of the hint, and adds the message to the "
            "input's `aria-describedby`. A `Form` can hand errors to every "
            "control inside it by name with `errors()`; an error set on the "
            "control itself takes precedence."
        ),
        pr.code(
            'Form().errors({"email": "That address is already invited."}).content(\n'
            '    TextInput().name("email").label("Email"),\n'
            ")"
        ),
        pr.h3("Readonly and disabled"),
        pr.p(
            "`readonly()` shows a value that cannot be edited but stays focusable "
            "and copyable. `disabled()` takes the input out of the tab order and "
            "out of the submitted form."
        ),
        pr.h3("Other kinds of input"),
        pr.p(
            "`EmailInput`, `PasswordInput` and `NumberInput` share every modifier "
            "here. `EmailInput` presets `autocomplete` to `email` and `PasswordInput` "
            "to `current-password`; `PasswordInput` adds `revealable()`, and "
            "`NumberInput` adds `min()`, `max()` and `step()`."
        ),
    )


PAGE = ComponentPage(
    TextInput,
    lede=(
        "A single-line text field with its label, hint and error built in. "
        "Prefixes, suffixes, an icon or an attached button extend it without "
        "a wrapper of your own."
    ),
    usage=_usage,
    panels=[
        panel("Live", workspace_name, layout="stack", hint="Type in it"),
        panel(
            "Anatomy",
            label_and_hint,
            prefix,
            suffix,
            leading_icon,
            action,
            layout="stack",
        ),
        panel("Sizes", sm, md, lg, layout="stack"),
        panel("States", enabled, required, readonly, disabled, layout="stack"),
        panel("Error", field_error, layout="stack"),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            hint="The label takes a 180px column at every width",
        ),
        panel("Relatives", email, password, number, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The label is a real `label` element pointing at the input, and the "
            "hint and error are tied to it through `aria-describedby`.",
        ),
        Note(
            "a11y",
            "`error()` sets `aria-invalid`, which is also what draws the red border, "
            "so the colour never carries the meaning alone.",
        ),
        Note(
            "note",
            "`leading_icon()` is decorative and names nothing. A `TextInput` without "
            "`label()` shows its name as the label, so a search field that should "
            "show only its icon uses `hidden_label()`.",
        ),
        Note(
            "warn",
            "Two inputs with the same name on one page get the same id. Give each "
            "its own name, or set `id()` on one of them.",
        ),
    ],
    related=[Field, EmailInput, PasswordInput, NumberInput],
)
