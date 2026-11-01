from __future__ import annotations

from hue import toast
from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Combobox,
    Command,
    CommandGroup,
    CommandItem,
    Dialog,
    DropdownMenu,
)

from hue_docs.icons import Icon
from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def navigation_and_actions() -> Command:
    return (
        Command()
        .hotkey("/")
        .trigger(Button().variant("outline").content(Icon("search"), "Search"))
        .content(
            CommandGroup()
            .label("Navigate")
            .content(
                CommandItem()
                .label("Go to Billing")
                .icon(Icon("credit-card"))
                .href("#billing"),
                CommandItem()
                .label("Go to Members")
                .icon(Icon("users"))
                .href("#members"),
            ),
            CommandGroup()
            .label("Actions")
            .content(
                CommandItem()
                .label("Create invoice")
                .icon(Icon("file-text"))
                .action(toast.js.success("Invoice created")),
                CommandItem()
                .label("Copy invoice link")
                .icon(Icon("copy"))
                .keywords("share", "url")
                .action(toast.js.success("Link copied")),
                CommandItem()
                .label("Delete workspace")
                .icon(Icon("trash-2"))
                .disabled(),
            ),
            CommandGroup()
            .label("Recent")
            .content(
                CommandItem()
                .label("INV-2048 Northwind Traders")
                .icon(Icon("file-text"))
                .meta("$1,200.00")
                .href("#inv-2048"),
                CommandItem()
                .label("INV-2049 Contoso Ltd")
                .icon(Icon("file-text"))
                .meta("$840.00")
                .href("#inv-2049"),
            ),
        )
    )


# Anatomy


def with_descriptions() -> Command:
    return (
        Command()
        .label("Find a person")
        .placeholder("Search people")
        .empty_message("Nobody by that name.")
        .trigger(Button().variant("outline").content(Icon("user"), "Find a person"))
        .content(
            CommandItem()
            .label("Ada Lovelace")
            .icon(Icon("user"))
            .description("Engineering, ada@example.com")
            .href("#ada"),
            CommandItem()
            .label("Grace Hopper")
            .icon(Icon("user"))
            .description("Platform, grace@example.com")
            .href("#grace"),
            CommandItem()
            .label("Edsger Dijkstra")
            .icon(Icon("user"))
            .description("Research, edsger@example.com")
            .keywords("algorithms")
            .href("#edsger"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Command` is a search field over a list of things to go to or "
            "do, in a modal panel. The items are `CommandItem`, optionally in a "
            "labelled `CommandGroup`. `hotkey()` opens it from anywhere on the "
            "page, and `trigger()` adds a control that opens it as well. While "
            "the palette is open, focus is in its search field, so only a hotkey "
            "with Command or Control closes it again. A bare key such as `/` is "
            "typed into the field."
        ),
        pr.code(
            "(\n"
            "    Command()\n"
            '    .hotkey("mod+k")\n'
            '    .trigger(Button().variant("outline").content("Search"))\n'
            "    .content(\n"
            '        CommandGroup().label("Navigate").content(\n'
            '            CommandItem().label("Go to Billing").href("/billing/"),\n'
            "        ),\n"
            "    )\n"
            ")"
        ),
        pr.h3("Hotkeys"),
        pr.p(
            "`hotkey()` takes keys written the way a `Shortcut` writes them, so "
            '`"mod+k"` '
            "is Command-K on Apple platforms and Control-K elsewhere. When the "
            "app has a shortcut registry in the render context, the hotkey is "
            "checked against it, and keys a registered shortcut already has "
            "raise an error."
        ),
        pr.h2("CommandItem actions and links"),
        pr.p(
            "`href()` makes a `CommandItem` a link, so it can also be opened in a "
            "new tab. `action()` takes an Alpine expression, such as one from "
            "`toast.js` or `ajax()`, and the palette closes before it runs. "
            "`keywords()` are searched as well as the label, for an item people "
            "look for by another name. `description()` adds a line under the "
            "label, and `meta()` a short note at the end of the row."
        ),
        pr.p(
            "`disabled()` leaves a `CommandItem` in the list, dimmed, and the "
            "arrow keys skip it. A disabled item with an `href()` renders without "
            "the link."
        ),
        pr.h3("Searching"),
        pr.p(
            "An item stays in the list when its label or one of its keywords "
            "contains what was typed. Items whose label starts with the text "
            "rank first in their group, then items with a word that starts "
            "with it, then the rest, and a group with no match left is "
            "hidden. With nothing left, the list shows `empty_message()`, "
            '"No matching commands." by default.'
        ),
        pr.h3("The app's shortcuts in a Command"),
        pr.p(
            "`CommandShortcuts` lists the app's shortcuts as items, grouped by "
            "each shortcut's group, with their keys. It needs the shortcut "
            "registry in the render context and raises an error without one. "
            "`CommandItem().shortcut()` does the same for a single shortcut."
        ),
        pr.code(
            'Command().hotkey("mod+k").content(CommandShortcuts())',
        ),
        pr.h2("Command keyboard"),
        pr.p(
            "Focus stays in the search field the whole time. Up and Down move "
            "the active item and stop at either end, Control-Home and "
            "Control-End jump to the first and last, and Enter runs the "
            "active item. Escape clears the text "
            "when there is some, and closes the palette when the field is "
            "empty. Closing gives focus back to the control that opened it."
        ),
    )


PAGE = ComponentPage(
    Command,
    lede=(
        "A `Command` is a command palette, a search field over a list of "
        "places to go and actions to run, opened with a hotkey from anywhere "
        "on the page. The arrow keys move through the matches while focus "
        "stays in the field."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            navigation_and_actions,
            layout="center",
            min_height=560,
            hint="Click inside the frame and press /, then type",
        ),
        panel(
            "Anatomy",
            with_descriptions,
            layout="center",
            min_height=420,
            hint="Type a name that is not there to see the empty message",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The panel is a `role="dialog"` with `aria-modal`. The field is a '
            "combobox that controls a listbox and points at the active option "
            "with `aria-activedescendant`, so focus never leaves the field.",
        ),
        Note(
            "a11y",
            'The empty message is in a `role="status"` region that is always on '
            "the page, so it is announced when it appears.",
        ),
        Note(
            "a11y",
            "Focus is trapped in the palette while it is open, and the page "
            "behind is inert. Closing returns focus to the trigger.",
        ),
        Note(
            "note",
            "While a modal is open, the page's shortcuts do not run, except "
            "inside a `Command`, whose items can run them.",
        ),
        Note(
            "warn",
            "The first Escape clears the search text and the second closes the "
            "palette, so a palette with text in it takes two presses to close.",
        ),
    ],
    parts=[CommandGroup, CommandItem],
    related=[DropdownMenu, Combobox, Dialog],
)
