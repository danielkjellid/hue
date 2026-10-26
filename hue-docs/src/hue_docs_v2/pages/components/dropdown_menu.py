from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Command,
    DropdownMenu,
    MenuItem,
    MenuLabel,
    MenuSeparator,
    Popover,
)

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def project_actions() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Project actions")
        .trigger(
            Button().variant("outline").content("Project actions", Icon("chevron-down"))
        )
        .content(
            MenuLabel().content("Project"),
            MenuItem().icon(Icon("copy")).content("Duplicate"),
            MenuItem().icon(Icon("file-text")).content("Export as CSV"),
            MenuSeparator(),
            MenuLabel().content("Sharing"),
            MenuItem().checkable().checked().content("Public link"),
            MenuItem().checkable().content("Allow comments"),
            MenuSeparator(),
            MenuItem().disabled().icon(Icon("users")).content("Transfer ownership"),
            MenuItem().variant("danger").icon(Icon("trash-2")).content("Delete"),
        )
    )


# Placements


def bottom_start() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("bottom-start")
        .placement("bottom-start")
        .trigger(Button().variant("outline").size("sm").content("bottom-start"))
        .content(MenuItem().content("Rename"), MenuItem().content("Archive"))
    )


def bottom_end() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("bottom-end")
        .placement("bottom-end")
        .trigger(Button().variant("outline").size("sm").content("bottom-end"))
        .content(MenuItem().content("Rename"), MenuItem().content("Archive"))
    )


def top_start() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("top-start")
        .placement("top-start")
        .trigger(Button().variant("outline").size("sm").content("top-start"))
        .content(MenuItem().content("Rename"), MenuItem().content("Archive"))
    )


def top_end() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("top-end")
        .placement("top-end")
        .trigger(Button().variant("outline").size("sm").content("top-end"))
        .content(MenuItem().content("Rename"), MenuItem().content("Archive"))
    )


# Anatomy


def account_menu() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Account")
        .placement("bottom-end")
        .trigger(
            Button().variant("ghost").icon_only("Account").content(Icon("ellipsis"))
        )
        .content(
            MenuItem().href("#profile").icon(Icon("user")).content("Profile"),
            MenuItem().href("#billing").icon(Icon("credit-card")).content("Billing"),
            MenuSeparator(),
            MenuItem().icon(Icon("log-out")).content("Sign out"),
        )
    )


def item_variants() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Row actions")
        .trigger(Button().variant("outline").content("Variants"))
        .content(
            MenuItem().variant("default").icon(Icon("copy")).content("Default"),
            MenuItem().variant("danger").icon(Icon("trash-2")).content("Danger"),
        )
    )


def checkable_items() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Columns")
        .trigger(Button().variant("outline").content("Columns"))
        .content(
            MenuLabel().content("Show columns"),
            MenuItem().checkable().checked().content("Status"),
            MenuItem().checkable().checked().content("Amount"),
            MenuItem().checkable().content("Due date"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `DropdownMenu` renders its trigger and a menu anchored to it. "
            "The items are `MenuItem`, with `MenuLabel` for a heading over a run "
            "of items and `MenuSeparator` for a rule between two runs. `label()` "
            "names the menu for a screen reader."
        ),
        pr.code(
            "(\n"
            "    DropdownMenu()\n"
            '    .label("Project actions")\n'
            '    .trigger(Button().variant("outline").content("Project actions"))\n'
            "    .content(\n"
            '        MenuItem().icon(Icon("copy")).content("Duplicate"),\n'
            "        MenuSeparator(),\n"
            '        MenuItem().variant("danger").content("Delete project"),\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "`trigger()` takes a hue component rather than plain markup, because "
            "the `DropdownMenu` writes the click handler, the Down key handler, "
            "`aria-expanded` and the anchor onto that control."
        ),
        pr.h2("MenuItem actions and links"),
        pr.p(
            "A `MenuItem` is a button, or a link when it has `href()`. Give it "
            "something to do with `on_click()` or an AJAX action. Picking an item "
            'closes the menu. `variant()` takes `"default"` or `"danger"`; `"danger"` '
            "colours the item's text and icon."
        ),
        pr.h3("Checkable items"),
        pr.p(
            "`checkable()` makes a `MenuItem` a `menuitemcheckbox` with a tick in "
            "the gutter, and `checked()` starts it ticked. Picking a checkable "
            "item toggles the tick and leaves the menu open. The tick is "
            "client state; bind it with `x_model()` or an AJAX action to keep it."
        ),
        pr.h3("Disabled items"),
        pr.p(
            "`disabled()` dims a `MenuItem` and sets `aria-disabled`, and leaves it "
            "in the menu where the arrow keys still reach it. A disabled item "
            "has no click handler, its own or the caller's, so Enter does "
            "nothing on it. A disabled link loses its `href`."
        ),
        pr.h3("Items that run a shortcut"),
        pr.p(
            "`shortcut()` makes a `MenuItem` a way to run one of the app's "
            "shortcuts: it shows the keys and does what the shortcut does, and "
            "takes the shortcut's label and icon when it has none of its own. "
            "It needs the app's shortcut registry in the render context, and "
            "raises an error if the item also has an `href` or a handler."
        ),
        pr.code(
            "MenuItem().shortcut(Shortcuts.copy_link)",
        ),
        pr.h2("DropdownMenu keyboard"),
        pr.p(
            "Down on the trigger opens the menu, as a click does, and focus "
            "goes to the first item. Up and Down move between items and wrap "
            "at the ends, Home and End jump to the first and last. Escape "
            "closes the menu and puts focus back on the trigger. Tab closes "
            "it and moves on to whatever follows the trigger."
        ),
        pr.h3("Placement"),
        pr.p(
            "`placement()` names the corner of the trigger the menu hangs from: "
            '`"bottom-start"` (the default), `"bottom-end"`, `"top-start"` or '
            '`"top-end"`. The menu flips and shifts to stay inside the viewport.'
        ),
    )


PAGE = ComponentPage(
    DropdownMenu,
    lede=(
        "A `DropdownMenu` is a list of actions that hangs off a control and is "
        "walked with the arrow keys. A list of links that navigates is not a "
        "menu; put it in a plain list instead."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            project_actions,
            layout="center",
            min_height=480,
            hint="Open it with Down, walk it with the arrow keys",
        ),
        panel(
            "Placements",
            bottom_start,
            bottom_end,
            top_start,
            top_end,
            layout="center",
            min_height=280,
            captions=False,
            hint="Flips when there is no room",
        ),
        panel(
            "Anatomy",
            account_menu,
            item_variants,
            checkable_items,
            min_height=300,
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The menu has `role="menu"` and each item `role="menuitem"`, or '
            "`menuitemcheckbox` with `aria-checked` when it is checkable. The "
            'trigger gets `aria-haspopup="menu"` and `aria-expanded`.',
        ),
        Note(
            "a11y",
            'Items are out of the tab order (`tabindex="-1"`): focus moves between '
            "them with the arrow keys, and hovering an item focuses it, so the "
            "pointer and the keys share one active item.",
        ),
        Note(
            "a11y",
            "Escape closes only the innermost overlay and returns focus to the "
            "trigger, so a `DropdownMenu` in a `Dialog` leaves the `Dialog` open.",
        ),
        Note(
            "note",
            "`label()` names the menu. The trigger's own name is read first, so "
            "the label names the group the items belong to.",
        ),
    ],
    parts=[MenuItem, MenuLabel, MenuSeparator],
    related=[Popover, Command],
)
