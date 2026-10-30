from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import (
    Avatar,
    Badge,
    Breadcrumbs,
    Sidebar,
    SidebarBody,
    SidebarDivider,
    SidebarFooter,
    SidebarHeader,
    SidebarHeading,
    SidebarItem,
    SidebarLabel,
    SidebarSection,
    SidebarSpacer,
    Tabs,
)

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def whole_sidebar() -> ComponentType:
    return html.div(
        Sidebar()
        .current("/events/2050")
        .content(
            SidebarHeader().content(
                SidebarItem()
                .icon(Icon("search"))
                .content(SidebarLabel().content("Search")),
            ),
            SidebarBody().content(
                SidebarSection().content(
                    SidebarItem()
                    .href("/")
                    .icon(Icon("house"))
                    .content(SidebarLabel().content("Home")),
                    SidebarItem()
                    .href("/events")
                    .icon(Icon("calendar"))
                    .content(SidebarLabel().content("Events")),
                    SidebarItem()
                    .href("/orders")
                    .icon(Icon("credit-card"))
                    .content(
                        SidebarLabel().content("Orders"),
                        Badge().content("3"),
                    ),
                ),
                SidebarDivider(),
                SidebarSection().content(
                    SidebarHeading().content("Upcoming"),
                    SidebarItem()
                    .href("/events/bear-hug")
                    .content(SidebarLabel().content("Bear Hug: Live")),
                    SidebarItem()
                    .href("/events/six-more")
                    .content(SidebarLabel().content("Six More Weeks")),
                ),
                SidebarSpacer(),
                SidebarSection().content(
                    SidebarItem()
                    .href("/support")
                    .icon(Icon("circle-info"))
                    .content(SidebarLabel().content("Support")),
                ),
            ),
            SidebarFooter().content(
                SidebarItem().content(
                    Avatar().name("Erica Meyers").size("sm").aria_hidden("true"),
                    SidebarLabel().content("Erica Meyers"),
                ),
            ),
        )
    ).class_("h-[560px] overflow-hidden rounded-lg border border-border")


# States


def section_and_page() -> ComponentType:
    return html.div(
        Sidebar()
        .current("/settings/billing")
        .content(
            SidebarBody().content(
                SidebarSection().content(
                    SidebarItem()
                    .href("/settings")
                    .exact()
                    .icon(Icon("user"))
                    .content(SidebarLabel().content("Settings")),
                    SidebarItem()
                    .href("/settings/billing")
                    .icon(Icon("credit-card"))
                    .content(SidebarLabel().content("Billing")),
                    SidebarItem()
                    .href("/settings/notifications")
                    .icon(Icon("bell"))
                    .content(SidebarLabel().content("Notifications")),
                ),
            ),
        )
    ).class_("h-[180px] overflow-hidden rounded-lg border border-border")


def action_rows() -> ComponentType:
    return html.div(
        Sidebar().content(
            SidebarBody().content(
                SidebarSection().content(
                    SidebarItem()
                    .icon(Icon("plus"))
                    .content(SidebarLabel().content("New project")),
                    SidebarItem()
                    .icon(Icon("log-out"))
                    .content(SidebarLabel().content("Sign out")),
                ),
            ),
        )
    ).class_("h-[140px] overflow-hidden rounded-lg border border-border")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("The parts of a Sidebar"),
        pr.p(
            "A `Sidebar` is a 16rem column with its own background, and it is "
            "built from parts. Each part is optional."
        ),
        pr.bullets(
            [
                "`SidebarHeader` sits at the top and does not scroll.",
                "`SidebarBody` is the `nav` element, and the only part that "
                'scrolls. Its `label()` names the `nav`, `"Main"` by default.',
                "`SidebarFooter` sits at the bottom and does not scroll.",
                "`SidebarSection` groups items, `SidebarHeading` names a section, "
                "and `SidebarDivider` draws a rule between two sections.",
                "`SidebarSpacer` pushes everything after it to the bottom of the "
                "body. Those items stay inside the scrolling body.",
            ]
        ),
        pr.p(
            "The `Sidebar` fills the height of its container, so give the "
            "container a height, such as the full height of the app shell."
        ),
        pr.h2("Links and actions in a SidebarItem"),
        pr.p(
            "A `SidebarItem` with `href()` is a link, so opening it in a new "
            "browser tab works. Without `href()` it is a button, for a row that "
            "does something instead of going somewhere, and it takes "
            "`on_click()`. `icon()` puts an icon before the content."
        ),
        pr.p(
            "Wrap the text in `SidebarLabel` when something else shares the "
            "row, such as a `Badge`. `SidebarLabel` truncates its text so the "
            "other content keeps its room."
        ),
        pr.code(
            "SidebarItem()\n"
            '.href("/orders")\n'
            '.icon(Icon("credit-card"))\n'
            '.content(SidebarLabel().content("Orders"), Badge().content("3"))'
        ),
        pr.h2("Marking the current page in a Sidebar"),
        pr.p(
            "`current()` on the `Sidebar` takes the path of the page you are on. "
            "Each `SidebarItem` compares its own `href()` with it and marks "
            "itself when they match, or when the path is inside the item's "
            "own, so `/events` stays marked on `/events/2050`. The mark is a "
            "bar at the sidebar's edge and full-strength text. Pass the "
            "request's path, which is `request.path` in Django and "
            "`request.url.path` in FastAPI."
        ),
        pr.bullets(
            [
                "`SidebarItem.exact()` marks a row only on its own path, for a "
                "row with rows of its own under it.",
                "`SidebarItem.current()` marks a row by hand.",
            ]
        ),
        pr.code(
            "Sidebar().current(request.url.path).content(\n"
            "    SidebarBody().content(\n"
            "        SidebarSection().content(\n"
            '            SidebarItem().href("/settings").exact()'
            '.content("Settings"),\n'
            '            SidebarItem().href("/settings/billing")'
            '.content("Billing"),\n'
            "        )\n"
            "    )\n"
            ")"
        ),
        pr.h2("How the current page reaches a SidebarItem"),
        pr.p(
            "`Sidebar().current(path)` offers the path "
            "as a `CurrentPage` context to everything rendered inside the "
            "`Sidebar`, and each `SidebarItem` reads it and marks itself. An "
            "item can sit at any depth: in a `SidebarSection`, in a wrapper of "
            "your own, or in a row built by one of your own components. "
            "To read more about "
            "contexts, see ",
            pr.link("Contexts", "/contexts/"),
            ".",
        ),
        pr.p(
            "A `SidebarItem` matches its `href()` against the path with "
            "trailing slashes ignored on both. It marks itself on its own path "
            "and on every page under it. An `href()` of `/` marks only `/`, "
            "because every path starts with it, and `exact()` applies that "
            "rule to any other item. A `SidebarItem` without an `href()` is "
            "never matched, and one rendered outside a `Sidebar` finds no "
            "current page and stays unmarked."
        ),
        pr.p(
            "`current()` on a `SidebarItem` overrides the match. `current()` "
            "marks the row whatever the path is, and `current(False)` leaves "
            "it unmarked."
        ),
        pr.p(
            "Contexts nest, and the nearest provider wins. A `Sidebar` or a "
            "`Tabs` inside the `Sidebar` offers its own `CurrentPage` to the "
            "items inside it and leaves the rest alone. It offers one even "
            "without `current()`, and the items under it then match nothing."
        ),
    )


PAGE = ComponentPage(
    Sidebar,
    lede=(
        "A `Sidebar` is the app's navigation down the side of the screen. It "
        "has a header and a footer that stay put and a body between them "
        "that scrolls, and it marks the link to the page you are on."
    ),
    usage=_usage,
    panels=[
        panel("Live", whole_sidebar, layout="stack"),
        panel(
            "States",
            section_and_page,
            action_rows,
            layout="stack",
            hint="On `/settings/billing`, with Settings set to `exact()`",
        ),
    ],
    notes=[
        Note(
            "a11y",
            '`SidebarBody` is a `nav` element named `"Main"` by default. Set its '
            "`label()` when a page has more than one `nav`.",
        ),
        Note(
            "a11y",
            'The current item carries `aria-current="page"`. A row without an '
            "`href()` is a button and never carries it.",
        ),
        Note(
            "a11y",
            "The bar beside the current item is `aria-hidden`; `aria-current` "
            "is what a screen reader hears.",
        ),
    ],
    parts=[
        SidebarHeader,
        SidebarBody,
        SidebarFooter,
        SidebarSection,
        SidebarHeading,
        SidebarDivider,
        SidebarSpacer,
        SidebarItem,
        SidebarLabel,
    ],
    related=[Tabs, Breadcrumbs],
)
