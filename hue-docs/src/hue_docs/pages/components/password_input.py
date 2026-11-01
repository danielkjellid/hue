from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import EmailInput, Form, PasswordInput, TextInput

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def revealable() -> PasswordInput:
    return (
        PasswordInput()
        .name("password")
        .label("Password")
        .value("correct horse")
        .revealable()
    )


# Anatomy


def plain() -> PasswordInput:
    return PasswordInput().name("current_password").label("Password")


def new_password() -> PasswordInput:
    return (
        PasswordInput()
        .name("new_password")
        .label("New password")
        .autocomplete("new-password")
        .hint("At least 12 characters.")
        .revealable()
    )


# Error


def wrong_password() -> PasswordInput:
    return (
        PasswordInput()
        .name("confirm_password")
        .label("Password")
        .error("That password is not right.")
        .revealable()
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `PasswordInput` is a ",
            pr.link("TextInput", "/components/text-input/"),
            ' with `type="password"` and `autocomplete` preset to '
            '`"current-password"`. '
            "Label, hint, error, sizes and the other shared modifiers work as "
            "the `TextInput` page shows. `PasswordInput` adds `revealable()`.",
        ),
        pr.code('PasswordInput().name("password").label("Password").revealable()'),
        pr.h2("Showing the password with revealable()"),
        pr.p(
            "`revealable()` attaches an icon-only toggle inside the field. "
            'Pressing it switches the input between `type="password"` and '
            '`type="text"`. The toggle keeps one name, "Show password", and reports '
            "its state through `aria-pressed` instead of renaming itself."
        ),
        pr.p(
            "`revealable()` fills the input's action slot only when nothing "
            "else is in it, so an `action()` set on the same `PasswordInput` "
            "replaces the toggle."
        ),
        pr.h2("New passwords"),
        pr.p(
            'The `"current-password"` preset is the one for signing in. On a '
            'sign-up or change-password form, set `autocomplete("new-password")`, '
            "which is the token password managers look for when they offer "
            "to generate one."
        ),
        pr.code(
            "(\n"
            "    PasswordInput()\n"
            '    .name("new_password")\n'
            '    .label("New password")\n'
            '    .autocomplete("new-password")\n'
            "    .revealable()\n"
            ")"
        ),
    )


PAGE = ComponentPage(
    PasswordInput,
    lede=(
        "A `TextInput` for a password. It presets `autocomplete` to "
        '`"current-password"`, and `revealable()` adds a toggle that shows what was '
        "typed."
    ),
    usage=_usage,
    panels=[
        panel("Live", revealable, layout="stack", hint="Press the eye"),
        panel("Anatomy", plain, new_password, layout="stack"),
        panel("Error", wrong_password, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            'The reveal toggle is a real button named "Show password". Its '
            "`aria-pressed` turns `true` while the password is visible, so a "
            "screen reader hears one control changing state rather than a new "
            "control each time.",
        ),
        Note(
            "a11y",
            "The toggle is in the tab order after the input, so a keyboard "
            "user reaches it with Tab and presses it with Enter or Space.",
        ),
        Note(
            "note",
            "The type switch is done in Alpine, so before Alpine loads the "
            "toggle does nothing and the input stays a password field.",
        ),
    ],
    related=[TextInput, EmailInput, Form],
)
