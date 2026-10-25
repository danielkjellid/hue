from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Checkbox, Switch

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def notifications() -> Switch:
    return Switch().name("notify").label("Email notifications").checked()


# Sizes


def sm() -> Switch:
    return Switch().name("size_sm").label("Small").checked().size("sm")


def md() -> Switch:
    return Switch().name("size_md").label("Medium").checked().size("md")


def lg() -> Switch:
    return Switch().name("size_lg").label("Large").checked().size("lg")


# Anatomy


def label_only() -> Switch:
    return Switch().name("dark_mode").label("Dark mode")


def with_description() -> Switch:
    return (
        Switch()
        .name("digest")
        .label("Weekly digest")
        .description("A summary of everything that changed, every Monday.")
        .checked()
    )


def horizontal() -> Switch:
    return (
        Switch()
        .name("two_factor")
        .label("Two-factor authentication")
        .description("Require a code from your authenticator at every sign-in.")
        .horizontal()
        .checked()
    )


# States


def off() -> Switch:
    return Switch().name("state_off").label("Auto-renew")


def on() -> Switch:
    return Switch().name("state_on").label("Auto-renew").checked()


def required() -> Switch:
    return Switch().name("state_required").label("Accept the policy").required()


def disabled() -> Switch:
    return Switch().name("state_disabled").label("Managed by your admin").disabled()


# Submission


def none() -> Switch:
    return Switch().name("sub_none").label("Enforce SSO").checked()


def pending() -> Switch:
    return (
        Switch()
        .name("sub_pending")
        .label("Enforce SSO")
        .checked()
        .submission_state("pending")
    )


def success() -> Switch:
    return (
        Switch()
        .name("sub_success")
        .label("Enforce SSO")
        .checked()
        .submission_state("success")
        .settle_after(None)
    )


def error() -> Switch:
    return (
        Switch()
        .name("sub_error")
        .label("Enforce SSO")
        .submission_state("error")
        .settle_after(None)
    )


# Error


def field_error() -> Switch:
    return (
        Switch()
        .name("public_profile")
        .label("Public profile")
        .error("Add a display name before making your profile public.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Switch is a native checkbox input with role=switch, drawn as a "
            "track and a knob. It submits like a checkbox: the name with on "
            "when it is on, nothing when it is off. The whole row is a label, "
            "so a click on the text flips it too."
        ),
        pr.code('Switch().name("notify").label("Email notifications").checked()'),
        pr.h3("Layout"),
        pr.p(
            "By default the Switch sits before its text. horizontal() puts the "
            "text first and pushes the Switch to the far end of the row, the "
            "order a settings list reads in. description() adds a second line "
            "under the label."
        ),
        pr.h3("Reporting the save"),
        pr.p(
            "submission_state() shows how the write the Switch started is "
            "going, with an icon beside the label:"
        ),
        pr.bullets(
            [
                '"pending" shows a spinner, announced as Saving, and disables '
                "the Switch.",
                '"success" shows a tick, announced as Saved.',
                '"error" shows an alert icon, announced as Not saved.',
                '"none", the default, shows nothing.',
            ]
        ),
        pr.p(
            "A success or error indicator clears itself after 2400ms, and the "
            "countdown starts only if the row is visible when it renders. "
            "settle_after() changes the delay in milliseconds, and "
            "settle_after(None) keeps the indicator until the next render, as "
            "the specimens on this page do."
        ),
        pr.code(
            "(\n"
            "    Switch()\n"
            '    .name("sso")\n'
            '    .label("Enforce SSO")\n'
            "    .checked()\n"
            '    .submission_state("error")\n'
            "    .settle_after(None)\n"
            ")"
        ),
        pr.h3("Errors"),
        pr.p(
            "error() sets aria-invalid on the input and shows the message under "
            "the row, with role=alert. A Switch has no hint(); description() is "
            "its second line."
        ),
    )


PAGE = ComponentPage(
    Switch,
    lede=(
        "An on and off control for a setting that takes effect as soon as it "
        "is flipped. It is a native checkbox with role=switch, so it is "
        "announced as on or off, and it can show whether the change was saved."
    ),
    usage=_usage,
    panels=[
        panel("Live", notifications, layout="center", hint="Click it or press Space"),
        panel("Sizes", sm, md, lg),
        panel("Anatomy", label_only, with_description, horizontal, layout="stack"),
        panel("States", off, on, required, disabled),
        panel(
            "Submission",
            none,
            pending,
            success,
            error,
            hint="submission_state(), held with settle_after(None)",
        ),
        panel("Error", field_error, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "role=switch on a native checkbox: a screen reader says on or off "
            "rather than checked or not checked, and Space flips it.",
        ),
        Note(
            "a11y",
            "The submission indicator has role=status and an aria-label of "
            "Saving, Saved or Not saved, so the outcome is announced and not "
            "only drawn.",
        ),
        Note(
            "a11y",
            "The input is named by its label through aria-labelledby and "
            "described by its description, so the description is not read as "
            "part of the name.",
        ),
        Note(
            "note",
            'submission_state("pending") disables the input, which also takes '
            "it out of the tab order.",
        ),
        Note(
            "warn",
            "A Switch submits nothing while it is off. Read a missing name as "
            "off on the server.",
        ),
    ],
    related=[Checkbox],
)
