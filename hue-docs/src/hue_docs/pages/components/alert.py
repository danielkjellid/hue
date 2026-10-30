from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Banner, Button, Empty, Stack, Text, Toast

from hue_docs.icons import Icon
from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def dismiss_it() -> ComponentType:
    return Stack().content(
        Alert()
        .variant("success")
        .title("Workspace created")
        .content("You can invite people from the members page.")
        .dismissible(),
        Button().variant("outline").content("Invite people"),
    )


# Variants


def neutral() -> Alert:
    return (
        Alert()
        .title("Read-only workspace")
        .content("An owner has to approve changes made here.")
    )


def info() -> Alert:
    return (
        Alert()
        .variant("info")
        .title("Scheduled maintenance")
        .content("The API is read-only on Sunday between 02:00 and 04:00 UTC.")
    )


def success() -> Alert:
    return (
        Alert()
        .variant("success")
        .title("Payment received")
        .content("INV-2048 is marked as paid.")
    )


def warning() -> Alert:
    return (
        Alert()
        .variant("warning")
        .title("Two invoices are overdue")
        .content("INV-2050 and INV-2051 were due last week.")
    )


def danger() -> Alert:
    return (
        Alert()
        .variant("danger")
        .title("Payment failed")
        .content("The bank declined the card ending in 4242.")
    )


# Anatomy


def title_only() -> Alert:
    return Alert().variant("warning").title("Two invoices are overdue")


def title_and_content() -> Alert:
    return (
        Alert()
        .variant("info")
        .title("New export format")
        .content("CSV exports now include the tax column.")
    )


def with_actions() -> Alert:
    return (
        Alert()
        .variant("info")
        .title("A new version is available")
        .content("Reload to get the latest changes.")
        .actions(
            Button().variant("outline").size("sm").content("Reload"),
            Button().variant("ghost").size("sm").content("Later"),
        )
    )


def own_icon() -> Alert:
    return (
        Alert()
        .variant("info")
        .icon(Icon("bell"))
        .title("Reminders are on")
        .content("We email you three days before an invoice is due.")
    )


def a_row_as_content() -> Alert:
    return (
        Alert()
        .variant("warning")
        .title("Two invoices are overdue")
        .content(
            Stack()
            .horizontal()
            .justify_content("justify-between")
            .align_items("items-center")
            .content(
                Text().content("INV-2050 and INV-2051"),
                Button().variant("outline").size("sm").content("Pay both"),
            )
        )
    )


def dismissible() -> Alert:
    return (
        Alert()
        .variant("success")
        .title("Settings saved")
        .content("Your changes apply from the next invoice.")
        .dismissible()
    )


# Error


def with_a_way_out() -> Alert:
    return (
        Alert()
        .variant("danger")
        .title("We could not charge your card")
        .content("The bank declined the payment. Nothing was charged.")
        .actions(
            Button().variant("danger").size("sm").content("Try again"),
            Button().variant("ghost").size("sm").content("Use another card"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "An `Alert` is a box with a title, a body and an icon. `variant()` "
            'sets the colour, the icon and the role, and defaults to `"neutral"`. '
            "`title()` is the bold first line, and `content()` is everything "
            "under it."
        ),
        pr.code(
            'Alert().variant("danger").title("Payment failed")'
            '.content("Try again later.")'
        ),
        pr.h3("Content and actions"),
        pr.p(
            "`content()` takes any children, so an `Alert` body can be a sentence "
            "or a row with a button in it. `actions()` puts its children in a "
            "row under the content, with the gap and the space above already "
            "set."
        ),
        pr.code(
            "(\n"
            "    Alert()\n"
            '    .variant("danger")\n'
            '    .title("We could not charge your card")\n'
            '    .content("The bank declined the payment.")\n'
            "    .actions(\n"
            '        Button().variant("danger").size("sm").content("Try again"),\n'
            '        Button().variant("ghost").size("sm")'
            '.content("Use another card"),\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "A ghost `Button` anywhere inside an `Alert` takes the `Alert`'s text "
            "colour and a translucent hover, in `content()` as well as in "
            "`actions()`. Solid and outline buttons keep their own colours."
        ),
        pr.h3("Icons"),
        pr.p(
            'Each variant has its own icon. `"neutral"` and `"info"` get an info '
            "circle, "
            '`"success"` a check, `"warning"` a triangle and `"danger"` a cross. '
            "`icon()` replaces it with one of your own."
        ),
        pr.h2("How an Alert is announced"),
        pr.p(
            'The `"danger"` variant renders `role="alert"`, which interrupts a '
            'screen reader. Every other variant renders `role="status"`, which '
            "waits for a pause. A live region that is on the page with its "
            "content when the page loads is not announced, so a server-rendered "
            "`Alert` is read in document order. The role matters when an `Alert` "
            "arrives later, for example in a fragment swapped in by Alpine "
            "AJAX. `role()` on the `Alert` replaces the one the variant picks."
        ),
        pr.h2("Dismissing an Alert"),
        pr.p(
            "`dismissible()` adds a close button labelled Dismiss. Pressing it "
            "hides the `Alert` in the browser. No request is sent, so the next "
            "render of the page shows the `Alert` again unless your code stops "
            "rendering it."
        ),
        pr.p(
            "When focus is inside the `Alert` at that moment, focus first moves "
            "to the next focusable element on the page, else the previous "
            "one, else the element around the `Alert`, which is made focusable "
            "for the purpose."
        ),
    )


PAGE = ComponentPage(
    Alert,
    lede=(
        "An `Alert` is a message about the content it sits next to, such as a failed "
        "payment above a form or a read-only notice above a table. It stays "
        "until the page changes or the reader dismisses it. For a message "
        "about the whole page, use `Banner`."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            dismiss_it,
            layout="stack",
            hint="Tab to Dismiss and press Enter, and focus moves to the next button",
        ),
        panel("Variants", neutral, info, success, warning, danger, layout="stack"),
        panel(
            "Anatomy",
            title_only,
            title_and_content,
            with_actions,
            own_icon,
            a_row_as_content,
            dismissible,
            layout="stack",
        ),
        panel("Error", with_a_way_out, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            '`"danger"` renders `role="alert"` and the other variants `role="status"`, '
            "so only a failure interrupts what a screen reader is saying.",
        ),
        Note(
            "a11y",
            "The variant icon is `aria-hidden`. The title and content carry the "
            "message, so a reader who cannot see the colour loses nothing.",
        ),
        Note(
            "a11y",
            "Dismissing moves focus to the next focusable element, else the "
            "previous one, else the `Alert`'s container, before the `Alert` hides.",
        ),
        Note(
            "note",
            'The close button\'s accessible name is the fixed English word "Dismiss".',
        ),
        Note(
            "warn",
            "A live region only announces content added after it exists. An "
            "`Alert` rendered with the page is read in order, not announced.",
        ),
    ],
    related=[Banner, Toast, Empty],
)
