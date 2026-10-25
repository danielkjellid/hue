from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import (
    Badge,
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    CardMedia,
    Panel,
    Text,
)

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Variants


def bordered() -> Card:
    return Card().content(
        CardHeader().title("Monthly revenue").description("Last 30 days"),
        CardBody().content("$48,290"),
    )


def raised() -> Card:
    return (
        Card()
        .variant("raised")
        .content(
            CardHeader().title("Monthly revenue").description("Last 30 days"),
            CardBody().content("$48,290"),
        )
    )


def flat() -> Card:
    return (
        Card()
        .variant("flat")
        .content(
            CardHeader().title("Monthly revenue").description("Last 30 days"),
            CardBody().content("$48,290"),
        )
    )


# Anatomy


def header_and_body() -> Card:
    return Card().content(
        CardHeader()
        .title("Monthly revenue")
        .description("Last 30 days")
        .content(Text().muted().content("+12.4%")),
        CardBody().content("$48,290"),
    )


def body_alone() -> Card:
    return Card().content(
        CardBody().content("Anyone with the link can request access.")
    )


def with_footer() -> Card:
    return Card().content(
        CardHeader()
        .title("Invite teammates")
        .description("They get an email with a join link."),
        CardBody().content("Anyone with the link can request access."),
        CardFooter().content(
            Button().variant("ghost").content("Cancel"),
            Button().content("Send invites"),
        ),
    )


def every_part() -> Card:
    return Card().content(
        CardMedia().content(html.div().class_("size-full bg-accent-subtle")),
        CardHeader()
        .title("Q3 revenue report")
        .description("Published 14 September")
        .content(Badge().content("New")),
        CardBody().content("Revenue grew 12.4% against a flat quarter last year."),
        CardFooter().content(
            Button().variant("ghost").content("Dismiss"),
            Button().content("Open report"),
        ),
    )


# Interactive


def as_a_link() -> Card:
    return (
        Card()
        .href("#inv-2050")
        .content(
            CardHeader().title("INV-2050").description("Contoso Ltd, $2,190.00"),
        )
    )


def as_a_button() -> Card:
    return (
        Card()
        .interactive()
        .content(
            CardHeader().title("Starter plan").description("Up to 3 seats"),
        )
    )


def with_its_own_action() -> Card:
    return (
        Card()
        .href("#q3-report")
        .content(
            CardHeader()
            .title("Q3 revenue report")
            .description("Published 14 September"),
            CardFooter().content(Button().variant("ghost").content("Archive")),
        )
    )


# Layout


def a_grid_of_cards() -> ComponentType:
    return html.div(
        Card().content(
            CardHeader().title("Revenue").description("Last 30 days"),
            CardBody().content("$48,290"),
        ),
        Card().content(
            CardHeader().title("New customers").description("Last 30 days"),
            CardBody().content("214"),
        ),
    ).class_("grid gap-4 md:grid-cols-2")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Card is a container you assemble from four parts: CardMedia, "
            "CardHeader, CardBody and CardFooter. Each part is optional, and a "
            "Card renders them in the order you pass them. variant() sets the "
            "edge: bordered by default, raised for a shadow in place of the "
            "border, and flat for a sunken fill with no border."
        ),
        pr.code(
            "Card().content(\n"
            '    CardHeader().title("Invite teammates").description("By email"),\n'
            '    CardBody().content("Anyone with the link can request access."),\n'
            "    CardFooter().content(\n"
            '        Button().variant("ghost").content("Cancel"),\n'
            '        Button().content("Send invites"),\n'
            "    ),\n"
            ")"
        ),
        pr.h3("The parts of a Card"),
        pr.p(
            "CardHeader shows a title and a description, and renders its own "
            "children on the trailing side, opposite the title, which is where "
            "a Badge or a small action goes. CardBody pads itself on top only "
            "when it is the first part, so it sits right under a header. "
            "CardFooter is a tinted strip along the bottom with its children "
            "aligned to the end. CardMedia is a 16:9 band across the top that "
            "an img inside it fills, cropped to cover."
        ),
        pr.h2("A Card that links or acts"),
        pr.p(
            "href() makes the header's title a link, and interactive() makes it "
            "a button. Either way the title is stretched over the whole Card, "
            "so a click anywhere on it lands, while the title alone is the tab "
            "stop and the accessible name. Other buttons and links inside the "
            "Card are lifted above that overlay and keep working. href() wins "
            "when both are set."
        ),
        pr.code(
            'Card().href("/invoices/2050/").content(\n'
            '    CardHeader().title("INV-2050").description("Contoso Ltd"),\n'
            '    CardFooter().content(Button().variant("ghost").content("Archive")),\n'
            ")"
        ),
        pr.p(
            "A linked Card needs a CardHeader with a title as one of its own "
            "children, and raises a ValueError without one. Only the first "
            "titled CardHeader directly inside the Card becomes the control."
        ),
        pr.h3("Where the Card's attributes go"),
        pr.p(
            "On a linked Card, what names or activates the control moves onto "
            "the title: aria_label and the other ARIA naming attributes, "
            "on_click and other click and key handlers, and the wiring a "
            "Dialog or an Alpine AJAX request puts on its trigger. Everything "
            "else, such as id() and class_(), stays on the Card itself."
        ),
        pr.h2("Cards in a grid"),
        pr.p(
            "A Card fills the width it is given and sets no width of its own, "
            "so the columns come from the element around it. A grid with "
            "md:grid-cols-2 puts two Cards side by side from 768px and stacks "
            "them below that."
        ),
        pr.code('html.div(card_one, card_two).class_("grid gap-4 md:grid-cols-2")'),
    )


PAGE = ComponentPage(
    Card,
    lede=(
        "A card groups content about one thing, such as a metric, a record or "
        "a report, into a framed block built from a header, body, footer and "
        "media band. With href() or interactive() the whole card becomes one "
        "control."
    ),
    usage=_usage,
    panels=[
        panel("Variants", bordered, raised, flat),
        panel(
            "Anatomy",
            header_and_body,
            body_alone,
            with_footer,
            every_part,
            layout="stack",
        ),
        panel(
            "Interactive",
            as_a_link,
            as_a_button,
            with_its_own_action,
            hint="Hover, then tab to the title",
        ),
        panel(
            "Layout",
            a_grid_of_cards,
            layout="stack",
            hint="Two columns at md and wider, one below md",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "A linked Card puts a real a or button element around the title, so "
            "the title is the accessible name and middle-click and open in new "
            "tab work on a link.",
        ),
        Note(
            "a11y",
            "The focus ring is drawn on the whole Card, and only when its title "
            "has keyboard focus. Focusing a footer button does not light it.",
        ),
        Note(
            "note",
            "Buttons and links inside a linked Card stay clickable and keep "
            "their own tab stops, because the Card lifts them above the title's "
            "overlay.",
        ),
        Note(
            "warn",
            "href() and interactive() raise a ValueError unless the Card has a "
            "CardHeader with a title among its direct children. A header wrapped "
            "in another element does not count.",
        ),
    ],
    parts=[CardHeader, CardBody, CardFooter, CardMedia],
    related=[Panel],
)
