from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import (
    Card,
    CardBody,
    EmailInput,
    Field,
    Form,
    PasswordInput,
    Stack,
    TextInput,
)

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Errors


def errors_by_name() -> Form:
    return (
        Form()
        .errors(
            {
                "email": "That address is already registered.",
                "password": "Use at least 12 characters.",
            }
        )
        .content(
            EmailInput().name("email").label("Email").value("ada@example.com"),
            PasswordInput().name("password").label("Password").revealable(),
        )
    )


def nested_controls() -> Form:
    return (
        Form()
        .errors({"company": "Enter the company name as it is registered."})
        .content(
            Card().content(
                CardBody().content(
                    Stack().content(TextInput().name("company").label("Company"))
                )
            )
        )
    )


def own_error_wins() -> Form:
    return (
        Form()
        .errors({"handle": "That handle is taken."})
        .content(
            TextInput()
            .name("handle")
            .label("Handle")
            .value("hue team")
            .error("A handle cannot contain spaces."),
        )
    )


def no_errors() -> Form:
    return Form().content(
        TextInput().name("workspace").label("Workspace name"),
        TextInput().name("workspace_slug").label("Address").prefix("hue.dev/"),
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Form renders a form element that stacks its children with a "
            "gap between them. action() sets where it posts, and method() "
            "defaults to post."
        ),
        pr.code(
            'Form().action("/sign-up/").content(\n'
            '    EmailInput().name("email").label("Email"),\n'
            '    PasswordInput().name("password").label("Password"),\n'
            '    Button().type("submit").content("Create account"),\n'
            ")"
        ),
        pr.h2("Handing errors to the controls in a Form"),
        pr.p(
            "Form.errors() takes a mapping from control name to message. Every "
            "named control inside the form looks up its own name and shows "
            "the message as if error() had been called on it: the red border, "
            "aria-invalid and the message under the field. A control finds "
            "its error however deeply it is nested, inside a Card, a Stack or "
            "a component of your own, because the Form puts the errors in the "
            "render context, where every control below it can read them."
        ),
        pr.code(
            "def sign_up_form(errors: dict[str, str]) -> Form:\n"
            "    return Form().errors(errors).content(\n"
            '        EmailInput().name("email").label("Email"),\n'
            '        PasswordInput().name("password").label("Password"),\n'
            "    )\n\n"
            "# After a failed submission\n"
            'sign_up_form({"email": "That address is already registered."})'
        ),
        pr.p(
            "A name that matches no control is ignored, and a control with "
            "no entry renders as usual. An error set on the control itself "
            "with error() wins over the one from the Form."
        ),
        pr.h3("Answering a failed submission"),
        pr.p(
            "Build the mapping from your validation errors, render the same "
            "form with errors() and send it back. For the values to survive, "
            "set value() on each control from what was posted: Form.errors() "
            "carries only the messages."
        ),
    )


PAGE = ComponentPage(
    Form,
    lede=(
        "A form element that also knows what went wrong with the last "
        "submission. errors() maps control names to messages, and every named "
        "control inside picks up its own."
    ),
    usage=_usage,
    panels=[
        panel("Errors", errors_by_name, layout="stack"),
        panel(
            "Anatomy",
            nested_controls,
            own_error_wins,
            layout="stack",
        ),
        panel("Empty", no_errors, layout="stack", hint="No errors() set"),
    ],
    notes=[
        Note(
            "a11y",
            "A control that gets an error from the Form is wired exactly as "
            "with error(): aria-invalid is set and the message joins its "
            "aria-describedby.",
        ),
        Note(
            "note",
            "Neither Form nor the controls move focus to the first invalid "
            "field when the form renders with errors.",
        ),
        Note(
            "warn",
            "Errors are matched by name(), so two controls with one name in "
            "the same Form both show the message.",
        ),
    ],
    related=[TextInput, Field],
)
