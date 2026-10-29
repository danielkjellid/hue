from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Sidebar, TableOfContents, Tabs

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def beside_an_article() -> ComponentType:
    return html.div(
        html.article(
            html.h2("Getting started").class_("text-lg font-semibold"),
            html.p("Create a workspace and invite the people you work with."),
            html.p("Every workspace starts on the free plan."),
            html.h3("Inviting people").class_("font-semibold"),
            html.p("Invite by email address, or share a link that expires."),
            html.p("Each invitee chooses their own password."),
            html.h3("Roles").class_("font-semibold"),
            html.p("Owners manage billing. Members manage everything else."),
            html.p("A workspace can have several owners."),
            html.h2("Billing").class_("text-lg font-semibold"),
            html.p("Usage is metered per API call and billed monthly."),
            html.p("Invoices are emailed to every owner."),
            html.h2("Deleting a workspace").class_("text-lg font-semibold"),
            html.p("Only an owner can delete a workspace."),
            html.p("Its data is kept for 30 days, then removed for good."),
        )
        .id("guide")
        .class_("flex h-64 flex-col gap-3 overflow-y-auto pe-4 pb-48 text-base"),
        TableOfContents().of("#guide").title("On this page"),
    ).class_("grid gap-6 sm:grid-cols-[1fr_12rem]")


# Anatomy


def renamed_and_skipped() -> ComponentType:
    return html.div(
        html.article(
            html.h2("Overview"),
            html.h2("Configuring single sign-on with your identity provider").data(
                "toc", "Single sign-on"
            ),
            html.h3("Okta"),
            html.h3("Microsoft Entra ID"),
            html.h2("Changelog").data("toc-skip", ""),
        )
        .id("sso-guide")
        .class_("flex flex-col gap-2 text-base"),
        TableOfContents()
        .of("#sso-guide", headings="h2:not([data-toc-skip]), h3")
        .title("Contents"),
    ).class_("grid gap-6 sm:grid-cols-[1fr_12rem]")


def top_level_only() -> ComponentType:
    return html.div(
        html.article(
            html.h2("Install"),
            html.h3("With uv"),
            html.h2("Configure"),
            html.h3("Settings"),
            html.h2("Deploy"),
        )
        .id("setup-guide")
        .class_("flex flex-col gap-2 text-base"),
        TableOfContents().of("#setup-guide", headings="h2").title("Setup"),
    ).class_("grid gap-6 sm:grid-cols-[1fr_12rem]")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Pointing TableOfContents at the content"),
        pr.p(
            "`TableOfContents` reads its entries from the page in the browser. "
            "`of()` is a CSS selector for the element that holds the content, "
            '`"main"` by default, and every `h2` and `h3` inside it becomes an '
            "entry. You do not list the headings yourself."
        ),
        pr.code('TableOfContents().of("main").title("On this page")'),
        pr.p(
            "Levels nest by their own number, and the shallowest level found "
            "is the top of the list, so a page whose headings start at `h3` is "
            "not indented. When the content changes, for example when a "
            "fragment is swapped in, the list is rebuilt."
        ),
        pr.h3("Links and ids"),
        pr.p(
            "Each entry links to its heading's id. A heading without an id "
            "links to the nearest ancestor with an id that holds no other "
            "listed heading, such as a `section` element around it. Failing "
            "that, `TableOfContents` gives the heading an id made from its text, "
            "with a number added when the id is already taken on the page."
        ),
        pr.h2("Choosing the headings for a TableOfContents"),
        pr.p(
            "The `headings` keyword of `of()` is a selector of its own, `h2` and `h3` "
            "by default. Narrow it to change which levels are listed, or use "
            "it to leave a heading out."
        ),
        pr.code(
            'TableOfContents().of("main", headings="h2")\n'
            'TableOfContents().of("main", headings="h2:not([data-toc-skip]), h3")'
        ),
        pr.p(
            "A `data-toc` attribute on a heading replaces its text in the list "
            "without changing the heading on the page."
        ),
        pr.code(
            'html.h2("Configuring single sign-on with your identity provider")'
            '.data("toc", "Single sign-on")'
        ),
        pr.h2("The reading position in a TableOfContents"),
        pr.p(
            "A rail runs down the side of the entries, bending where the "
            "level changes, and fills in as far as the heading being read. "
            'The link to that heading gets `aria-current="location"`. A heading counts '
            "as reached once it has scrolled to the top of the content, less "
            "its `scroll-margin-top`. Once the content can scroll no further, "
            "the last heading counts as reached."
        ),
        pr.p(
            "The content can scroll with the window or inside its own "
            "container with `overflow` set to `auto` or `scroll`, as in the example "
            "on this page; `TableOfContents` measures from whichever one "
            "scrolls."
        ),
        pr.h2("A TableOfContents with no headings"),
        pr.p(
            "When `of()` matches no headings, `TableOfContents` hides itself, "
            "title included."
        ),
    )


PAGE = ComponentPage(
    TableOfContents,
    lede=(
        "A table of contents lists the headings of the page it sits on and "
        "marks the one the reader has scrolled to. It reads the headings "
        "from the page in the browser, so there is nothing to keep in step "
        "with the content."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            beside_an_article,
            layout="stack",
            hint="Scroll the article, or follow an entry",
        ),
        panel("Anatomy", renamed_and_skipped, top_level_only, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "`TableOfContents` renders a `nav` labelled by its title, so a page "
            "with more than one set of links says which one this is.",
        ),
        Note(
            "a11y",
            'The entry being read carries `aria-current="location"` rather than '
            '`"page"`, because every entry points into the page you are already on.',
        ),
        Note(
            "a11y",
            "The rail and its dots are an `aria-hidden` SVG; the entries are "
            "plain links in an ordered list.",
        ),
        Note(
            "note",
            "The list is built in the browser, so the server-rendered markup "
            "holds no entries and the `nav` stays hidden until Alpine has run.",
        ),
    ],
    related=[Sidebar, Tabs],
)
