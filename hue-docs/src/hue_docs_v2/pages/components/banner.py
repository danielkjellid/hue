from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Alert, Banner, Button, Stack, Toast

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def trial_ending() -> ComponentType:
    return (
        Stack()
        .align_items("items-stretch")
        .class_("w-full")
        .content(
            Banner()
            .variant("warning")
            .title("Your trial ends on Friday")
            .actions(Button().variant("outline").size("sm").content("Add billing"))
            .dismissible(),
            html.div(
                html.p("Invoices").class_("text-md font-bold"),
                Button().variant("outline").content("New invoice"),
            ).class_("flex flex-col items-start gap-3 px-4"),
        )
    )


# Variants


def neutral() -> Banner:
    return Banner().class_("w-full").title("You are viewing the workspace as a guest")


def info() -> Banner:
    return (
        Banner()
        .class_("w-full")
        .variant("info")
        .title("Scheduled maintenance on Sunday")
        .content("The API is read-only between 02:00 and 04:00 UTC.")
    )


def success() -> Banner:
    return (
        Banner()
        .class_("w-full")
        .variant("success")
        .title("Your plan was upgraded to Pro")
    )


def warning() -> Banner:
    return (
        Banner().class_("w-full").variant("warning").title("Your trial ends on Friday")
    )


def danger() -> Banner:
    return (
        Banner()
        .class_("w-full")
        .variant("danger")
        .title("Payments are paused")
        .content("Your card expired. Update it to resume billing.")
    )


# Anatomy


def title_only() -> Banner:
    return Banner().class_("w-full").variant("info").title("A new version is available")


def with_content() -> Banner:
    return (
        Banner()
        .class_("w-full")
        .variant("info")
        .title("Scheduled maintenance on Sunday")
        .content("The API is read-only between 02:00 and 04:00 UTC.")
    )


def with_actions() -> Banner:
    return (
        Banner()
        .class_("w-full")
        .variant("danger")
        .title("Payments are paused")
        .content("Your card expired. Update it to resume billing.")
        .actions(Button().variant("danger").size("sm").content("Update card"))
    )


def dismissible() -> Banner:
    return (
        Banner().variant("success").title("Your plan was upgraded to Pro").dismissible()
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Banner` is an `Alert` with square corners and no side borders, so "
            "it can run across the full width of a page. Every modifier is the "
            "`Alert` one. `variant()`, `title()`, `content()`, `actions()`, `icon()` "
            "and "
            "`dismissible()` behave the same way, and the roles and the focus "
            "handling on dismiss are the same too."
        ),
        pr.code(
            "Banner()\n"
            '.variant("warning")\n'
            '.title("Your trial ends on Friday")\n'
            '.actions(Button().variant("outline").size("sm").content("Add billing"))\n'
            ".dismissible()"
        ),
        pr.h3("Placing a Banner"),
        pr.p(
            "A `Banner` sets no position and no width of its own. Put it first "
            "in the page body, outside the padded content column, so it spans "
            "the page. Inside a padded container it stops at the padding like "
            "any other block. A flex parent that does not stretch its children, "
            "such as a column with `items-start`, shrinks it to its text, so the "
            'examples on this page set `class_("w-full")`.'
        ),
        pr.h3("Dismissing a Banner"),
        pr.p(
            "`dismissible()` hides the `Banner` in the browser and sends no "
            "request, so a reload renders the `Banner` again. To keep it gone, "
            "record the dismissal on the server and stop rendering the `Banner`."
        ),
    )


PAGE = ComponentPage(
    Banner,
    lede=(
        "A `Banner` is a message about the whole page or account, run edge to "
        "edge across the top, such as a trial that ends on Friday. "
        "It is an `Alert` in a different shape, so it has the same variants, "
        "roles and dismiss behaviour."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            trial_ending,
            layout="stack",
            hint="Tab to Dismiss and press Enter, and focus moves to the next button",
        ),
        panel("Variants", neutral, info, success, warning, danger, layout="stack"),
        panel(
            "Anatomy",
            title_only,
            with_content,
            with_actions,
            dismissible,
            layout="stack",
        ),
    ],
    notes=[
        Note(
            "a11y",
            '`"danger"` renders `role="alert"` and the other variants `role="status"`, '
            "the same as `Alert`.",
        ),
        Note(
            "a11y",
            "Dismissing moves focus to the next focusable element, else the "
            "previous one, else the `Banner`'s container, before the `Banner` hides.",
        ),
        Note(
            "note",
            "A `Banner` is not a landmark. It renders a `div` with the variant's "
            "role, so it does not appear in a screen reader's list of regions.",
        ),
    ],
    related=[Alert, Toast],
)
