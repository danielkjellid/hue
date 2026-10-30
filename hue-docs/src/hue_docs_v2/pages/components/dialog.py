from __future__ import annotations

from hue.js import close
from hue.types.core import ComponentType
from hue.ui import Button, Dialog, Drawer, DropdownMenu, MenuItem, Popover, TextInput

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def invite_teammates() -> Dialog:
    return (
        Dialog()
        .title("Invite teammates")
        .description("They will get an email with a join link.")
        .trigger(Button().content(Icon("user"), "Invite"))
        .content(
            TextInput()
            .name("emails")
            .label("Email addresses")
            .placeholder("ada@example.com")
        )
        .footer(
            Button().variant("ghost").content("Cancel").on_click(close()),
            Button().content("Send invites").on_click(close()),
        )
    )


# Sizes


def sm() -> Dialog:
    return (
        Dialog()
        .size("sm")
        .title("Rename project")
        .trigger(Button().variant("outline").content("Small"))
        .content(TextInput().name("size_sm_name").label("Name").value("Atlas"))
        .footer(Button().content("Rename").on_click(close()))
    )


def md() -> Dialog:
    return (
        Dialog()
        .size("md")
        .title("Rename project")
        .trigger(Button().variant("outline").content("Medium"))
        .content(TextInput().name("size_md_name").label("Name").value("Atlas"))
        .footer(Button().content("Rename").on_click(close()))
    )


def lg() -> Dialog:
    return (
        Dialog()
        .size("lg")
        .title("Rename project")
        .trigger(Button().variant("outline").content("Large"))
        .content(TextInput().name("size_lg_name").label("Name").value("Atlas"))
        .footer(Button().content("Rename").on_click(close()))
    )


# States


def destructive() -> Dialog:
    return (
        Dialog()
        .size("sm")
        .destructive()
        .title("Delete this project?")
        .description("Everything in it goes too. This cannot be undone.")
        .trigger(Button().variant("danger").content("Delete project"))
        .footer(
            Button().variant("ghost").content("Keep it").on_click(close()),
            Button().variant("danger").content("Delete").on_click(close()),
        )
    )


def must_be_answered() -> Dialog:
    return (
        Dialog()
        .size("sm")
        .dismissible(False)
        .title("Accept the new terms")
        .description("You need to accept these before continuing.")
        .trigger(Button().variant("outline").content("Review terms"))
        .footer(Button().content("Accept").on_click(close()))
    )


def named_by_label() -> Dialog:
    return (
        Dialog()
        .size("sm")
        .label("Keyboard help")
        .trigger(Button().variant("outline").content("Keyboard help"))
        .content("Press Escape to close any overlay on this page.")
    )


# Nested


def with_a_menu() -> Dialog:
    return (
        Dialog()
        .title("Share Route planner")
        .trigger(Button().variant("outline").content("Share"))
        .content(TextInput().name("invite").label("Invite by email"))
        .footer(
            DropdownMenu()
            .label("More sharing options")
            .placement("top-start")
            .trigger(Button().variant("ghost").content("More"))
            .content(
                MenuItem().icon(Icon("copy")).content("Copy link"),
                MenuItem().icon(Icon("file-text")).content("Export as PDF"),
            ),
            Button().content("Done").on_click(close()),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Dialog` renders its trigger and, hidden until the trigger is "
            "clicked, a panel over a dimmed page. `title()` and `description()` "
            "head the panel, `content()` fills the scrolling body, and `footer()` "
            "puts the actions on a tinted strip along the bottom. `size()` sets "
            'the width from the `sm` breakpoint up and defaults to `"md"`.'
        ),
        pr.code(
            "from hue.js import close\n\n"
            "(\n"
            "    Dialog()\n"
            '    .title("Invite teammates")\n'
            '    .trigger(Button().content("Invite"))\n'
            '    .content(TextInput().name("emails").label("Email addresses"))\n'
            "    .footer(\n"
            '        Button().variant("ghost").content("Cancel").on_click(close()),\n'
            '        Button().content("Send invites").on_click(close()),\n'
            "    )\n"
            ")"
        ),
        pr.h3("The trigger is a hue component"),
        pr.p(
            "`trigger()` takes a hue component, such as a `Button`, and not plain "
            "markup, because the `Dialog` writes the click handler, "
            "`aria-expanded` and `aria-haspopup` onto that control. A click "
            "handler the control already has through `on_click()` stays beside "
            "the `Dialog`'s own."
        ),
        pr.h3("Closing from inside"),
        pr.p(
            "The `Dialog` puts `close()` in scope for everything inside it. Pass "
            "`close()` from `hue.js` to `on_click()` on a footer button. A footer "
            "button with no handler does nothing when clicked, and the `Dialog` "
            "stays open."
        ),
        pr.h3("A Dialog that has to be answered"),
        pr.p(
            "`dismissible(False)` removes the close button and the click on the "
            "dimmed page that would close it, so the footer actions are the "
            "way out. Escape still closes it."
        ),
        pr.h3("A destructive question"),
        pr.p(
            "`destructive()` renders the panel as an `alertdialog` and points its "
            "`aria-describedby` at the description, so a screen reader reads "
            "the description together with the title. A `Dialog` that is not "
            "destructive leaves the description to be read in order."
        ),
        pr.h3("Opened by the server"),
        pr.p(
            "`open()` renders the `Dialog` already open. When it closes, focus "
            "goes to its trigger, since nothing on the page opened it."
        ),
        pr.code(
            'Dialog().open().title("Your trial has ended").trigger(\n'
            '    Button().variant("ghost").content("Plan details")\n'
            ")"
        ),
        pr.h2("Dialog on small screens"),
        pr.p(
            "Below the `sm` breakpoint (640px) a `Dialog` docks to the bottom edge "
            "as a full-width sheet with a grab handle, at most 85% of the "
            "screen tall. From `sm` up it is centred at the width `size()` sets. "
            "Drag the panel narrower on any `Dialog` example to see the switch."
        ),
    )


PAGE = ComponentPage(
    Dialog,
    lede=(
        "A `Dialog` is a modal window over the page. While it is open, the page "
        "behind cannot be tabbed into or scrolled. Use it for a question or a "
        "short form that has to be dealt with before anything else."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            invite_teammates,
            layout="center",
            min_height=440,
            hint="Open it, tab through it, press Escape",
        ),
        panel("Sizes", sm, md, lg, min_height=360, hint="The width from `sm` up"),
        panel(
            "States",
            destructive,
            must_be_answered,
            named_by_label,
            min_height=360,
        ),
        panel(
            "Nested",
            with_a_menu,
            layout="center",
            min_height=420,
            hint="Escape closes the menu first, then the dialog",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The panel has `role="dialog"` (`alertdialog` with `destructive()`) and '
            "`aria-modal`. It is named by its title through `aria-labelledby`, or "
            "by `label()` when it has no title.",
        ),
        Note(
            "a11y",
            "Focus is trapped inside while the `Dialog` is open, and the page "
            "behind is made inert. Closing gives focus back to the control "
            "that opened it.",
        ),
        Note(
            "a11y",
            "Escape closes only the innermost overlay. The listener sits on "
            "the `Dialog` and stops the key there, so a menu or `Popover` inside a "
            "`Dialog` closes on the first press and the `Dialog` on the second.",
        ),
        Note(
            "note",
            "A `Dialog` with neither `title()` nor `label()` raises an error when it "
            "renders, because a modal with no name is announced as just "
            '"dialog".',
        ),
        Note(
            "warn",
            "Escape closes a `Dialog` even with `dismissible(False)`. Do not rely "
            "on the footer being the only way out.",
        ),
    ],
    related=[Drawer, Popover],
)
