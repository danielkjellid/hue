from __future__ import annotations

from fastapi import HTTPException, Request
from hue import html
from hue.context import HueContext
from hue.types.core import ComponentType
from hue.ui import Badge, SegmentedControl, Sidebar, Stack, Tab, Tabs
from hue_fastapi import HueFragmentsView, Page, Router

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

_SECTIONS = {
    "account": "Your name, email address and password.",
    "team": "Who is in the workspace, and what each of them can do.",
    "billing": "Your plan, payment method and past invoices.",
}


class TabsDemo(HueFragmentsView):
    """
    The sections behind the live example. A page route rather than a
    fragment, so a reload of the URL the swap pushed still answers with the
    whole page.
    """

    router = Router[Request]()

    @router.page("{section}/")
    async def section(
        self, request: Request, context: HueContext[Request], section: str
    ) -> ComponentType:
        if section not in _SECTIONS:
            raise HTTPException(status_code=404)
        return Page(
            title=section.title(),
            body=Stack()
            .class_("p-6")
            .content(
                Tabs()
                .id("settings-tabs")
                .label("Settings")
                .target("settings-panel")
                .current(f"/demos/tabs/{section}/")
                .content(
                    Tab().href("/demos/tabs/account/").content("Account"),
                    Tab().href("/demos/tabs/team/").content("Team"),
                    Tab().href("/demos/tabs/billing/").content("Billing"),
                ),
                html.p(_SECTIONS[section])
                .id("settings-panel")
                .class_("text-base text-fg-muted"),
            ),
        )


# Live


def swapping_a_panel() -> ComponentType:
    return Stack().content(
        Tabs()
        .id("settings-tabs")
        .label("Settings")
        .target("settings-panel")
        .current("/demos/tabs/account/")
        .content(
            Tab().href("/demos/tabs/account/").content("Account"),
            Tab().href("/demos/tabs/team/").content("Team"),
            Tab().href("/demos/tabs/billing/").content("Billing"),
        ),
        html.p("Your name, email address and password.")
        .id("settings-panel")
        .class_("text-base text-fg-muted"),
    )


# Variants


def underline() -> Tabs:
    return (
        Tabs()
        .label("Invoice sections")
        .current("/invoices/2050/lines")
        .content(
            Tab().href("/invoices/2050").exact().content("Overview"),
            Tab().href("/invoices/2050/lines").content("Line items"),
            Tab().href("/invoices/2050/history").content("History"),
        )
    )


def segmented() -> Tabs:
    return (
        Tabs()
        .segmented()
        .label("Report range")
        .current("/reports/week")
        .content(
            Tab().href("/reports/day").content("Day"),
            Tab().href("/reports/week").content("Week"),
            Tab().href("/reports/month").content("Month"),
        )
    )


# Anatomy


def with_badges() -> Tabs:
    return (
        Tabs()
        .label("Inbox")
        .current("/inbox/open")
        .content(
            Tab().href("/inbox/open").badge(Badge().content("12")).content("Open"),
            Tab().href("/inbox/snoozed").badge(Badge().content("3")).content("Snoozed"),
            Tab().href("/inbox/closed").content("Closed"),
        )
    )


# States


def inside_a_section() -> Tabs:
    return (
        Tabs()
        .label("Project")
        .current("/projects/atlas/issues/42")
        .content(
            Tab().href("/projects/atlas").exact().content("Overview"),
            Tab().href("/projects/atlas/issues").content("Issues"),
            Tab().href("/projects/atlas/settings").content("Settings"),
        )
    )


def disabled_tab() -> Tabs:
    return (
        Tabs()
        .label("Invoice")
        .current("/invoices/2050")
        .content(
            Tab().href("/invoices/2050").exact().content("Overview"),
            Tab().href("/invoices/2050/history").content("History"),
            Tab().href("/invoices/2050/disputes").disabled().content("Disputes"),
        )
    )


def marked_by_hand() -> Tabs:
    return (
        Tabs()
        .label("Views")
        .content(
            Tab().href("?view=board").current().content("Board"),
            Tab().href("?view=list").content("List"),
            Tab().href("?view=calendar").content("Calendar"),
        )
    )


# Width


def many_tabs() -> Tabs:
    return (
        Tabs()
        .label("Account")
        .current("/account/profile")
        .content(
            Tab().href("/account/profile").content("Profile"),
            Tab().href("/account/security").content("Security"),
            Tab().href("/account/notifications").content("Notifications"),
            Tab().href("/account/integrations").content("Integrations"),
            Tab().href("/account/billing").content("Billing"),
            Tab().href("/account/api").content("API keys"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Tabs are links"),
        pr.p(
            "Every `Tab` is an anchor with a real `href`, so it opens in a new "
            "browser tab, can be shared, and answers the back button. What a "
            "tab shows is whatever the page at its URL renders. `Tabs` carries "
            "no panels of its own."
        ),
        pr.code(
            "(\n"
            "    Tabs()\n"
            '    .label("Settings")\n'
            "    .current(request.url.path)\n"
            "    .content(\n"
            '        Tab().href("/settings/account/").content("Account"),\n'
            '        Tab().href("/settings/team/").content("Team"),\n'
            "    )\n"
            ")"
        ),
        pr.h2("Marking the current Tab"),
        pr.p(
            "`current()` on `Tabs` takes the path of the page you are on, once. "
            "Each `Tab` compares its own `href()` with it and marks itself with "
            '`aria-current="page"` when they match, or when the path is inside '
            "the tab's own, so `/projects/atlas/issues` stays marked on "
            "`/projects/atlas/issues/42`. Trailing slashes are ignored, and a "
            "tab for the root path `/` only matches itself. Pass the request's "
            "path, which is `request.path` in Django and `request.url.path` in "
            "FastAPI."
        ),
        pr.bullets(
            [
                "`Tab.exact()` marks a tab only on its own path. Use it on an "
                "Overview tab whose path is the prefix of every other tab.",
                "`Tab.current()` marks a tab by hand, for a tab whose `href()` "
                "is not a path, such as a query string. `current(False)` keeps a "
                "tab unmarked whatever the path is.",
                "`Tab.disabled()`, or a `Tab` with no `href()`, renders as an `a` "
                'with no `href`, `role="link"` and `aria-disabled="true"`, '
                "and is never marked.",
            ]
        ),
        pr.h2("What Tabs offers each Tab"),
        pr.p(
            "`Tabs` offers two "
            "contexts to everything rendered inside it, however deep, and "
            "each `Tab` reads them to draw itself:"
        ),
        pr.bullets(
            [
                "`TabsState` holds how the row is drawn and where a tab lands: "
                "whether `segmented()` is set, and the `target()` id a tab "
                "swaps when it is followed.",
                "`CurrentPage` holds the path from `current()`. `Sidebar` "
                "offers the same context, and its items match against it by "
                "the same rule.",
            ]
        ),
        pr.p(
            "Because a `Tab` reads the row from the context, it does not have "
            "to be a direct child of `Tabs`. A tab built inside a component of "
            "your own still joins the row. A `Tab` rendered outside any `Tabs` "
            "finds no `TabsState` and raises a `ValueError`, since nothing "
            "has told it how to draw itself or which tab you are on."
        ),
        pr.p(
            "Contexts nest, and the nearest provider wins. A `Tabs` inside "
            "another `Tabs` offers its own contexts to its own tabs. It "
            "offers a `CurrentPage` even without `current()`, and its tabs "
            "then match nothing. To read more about contexts, see ",
            pr.link("Contexts", "/contexts/"),
            ".",
        ),
        pr.h2("Swapping a region with Tabs"),
        pr.p(
            "`target()` names the id of an element on the page. Each tab then "
            "fetches its URL with Alpine AJAX, swaps that element for the one "
            "with the same id in the response, and pushes the URL. `Tabs` needs "
            "an `id()` of its own as well. It carries `x-sync`, so the same "
            "response moves the mark to the tab you followed. A `target()` "
            "without an `id()` raises an error."
        ),
        pr.code(
            "(\n"
            "    Tabs()\n"
            '    .id("settings-tabs")\n'
            '    .label("Settings")\n'
            '    .target("settings-panel")\n'
            "    .current(request.url.path)\n"
            "    .content(...)\n"
            ")"
        ),
        pr.p(
            "The route behind each tab can return the whole page, so a reload "
            "of the pushed URL renders it in full."
        ),
        pr.h2("Segmented Tabs"),
        pr.p(
            "`segmented()` draws the row as a segmented track instead of an "
            "underline. It is the same track `SegmentedControl` uses, but a "
            "`SegmentedControl` is a set of buttons that choose a value, and "
            "`Tabs` is a set of links to places."
        ),
        pr.h2("Tabs on a narrow screen"),
        pr.p(
            "The row never wraps. When the tabs are wider than the container, "
            "the row scrolls sideways."
        ),
    )


PAGE = ComponentPage(
    Tabs,
    lede=(
        "Tabs are a row of links to the sections of one thing, with the "
        "section you are on marked. Each tab is a link to a real URL, and "
        "with `target()` the row swaps a region of the page in place."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            swapping_a_panel,
            layout="stack",
            min_height=160,
            hint="Each tab fetches its section and swaps the text below",
        ),
        panel("Variants", underline, segmented, layout="stack"),
        panel("Anatomy", with_badges, layout="stack"),
        panel(
            "States",
            inside_a_section,
            disabled_tab,
            marked_by_hand,
            layout="stack",
        ),
        panel("Width", many_tabs, layout="stack", hint="The row scrolls sideways"),
    ],
    notes=[
        Note(
            "a11y",
            "The row is a `nav` named by `label()`, and the current tab carries "
            '`aria-current="page"`. Without `label()` the `nav` has no name.',
        ),
        Note(
            "a11y",
            "`Tabs` is navigation, not the ARIA tabs pattern. There is no "
            '`role="tablist"`, and the Tab key moves through the links as it does '
            "through any others; the arrow keys do nothing.",
        ),
        Note(
            "a11y",
            "A disabled tab is a link with no `href`, so the Tab key skips it. "
            'It keeps `role="link"` and `aria-disabled="true"`, so a screen '
            "reader reads it as a link that is unavailable.",
        ),
        Note(
            "note",
            "Each tab shows a focus ring on keyboard focus only.",
        ),
    ],
    parts=[Tab],
    related=[SegmentedControl, Sidebar],
    views=[TabsDemo],
)
