from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Accordion, AccordionItem, Tabs

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def billing_questions() -> Accordion:
    return Accordion().content(
        AccordionItem()
        .title("How is usage calculated?")
        .open()
        .content("Metered per API call, aggregated hourly and billed monthly."),
        AccordionItem()
        .title("Can I change plans mid-cycle?")
        .content("Upgrades take effect at once and are prorated."),
        AccordionItem()
        .title("What happens if a payment fails?")
        .content("We retry three times over eight days."),
    )


# Variants


def ruled() -> Accordion:
    return Accordion().content(
        AccordionItem().title("Request headers").content("Authorization is required."),
        AccordionItem().title("Rate limits").content("600 requests per minute."),
    )


def boxed() -> Accordion:
    return (
        Accordion()
        .boxed()
        .content(
            AccordionItem()
            .title("Request headers")
            .content("Authorization is required."),
            AccordionItem().title("Rate limits").content("600 requests per minute."),
        )
    )


# States


def all_closed() -> Accordion:
    return Accordion().content(
        AccordionItem().title("Shipping").content("Ships in two working days."),
        AccordionItem().title("Returns").content("Free within 30 days."),
    )


def one_open() -> Accordion:
    return Accordion().content(
        AccordionItem().title("Shipping").open().content("Ships in two working days."),
        AccordionItem().title("Returns").content("Free within 30 days."),
    )


def multiple_open() -> Accordion:
    return (
        Accordion()
        .multiple()
        .content(
            AccordionItem()
            .title("Shipping")
            .open()
            .content("Ships in two working days."),
            AccordionItem().title("Returns").open().content("Free within 30 days."),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Building an Accordion"),
        pr.p(
            "An Accordion holds AccordionItem children. Each item takes its "
            "heading text from title() and its panel from content(). open() "
            "starts an item open."
        ),
        pr.code(
            "Accordion().content(\n"
            "    AccordionItem()\n"
            '    .title("How is usage calculated?")\n'
            "    .open()\n"
            '    .content("Metered per API call."),\n'
            '    AccordionItem().title("Can I change plans?").content("Yes."),\n'
            ")"
        ),
        pr.h2("One open item or several in an Accordion"),
        pr.p(
            "By default an Accordion keeps one item open: opening one closes "
            "the one that was open. multiple() lets any number stay open. In "
            "the default mode, when more than one item is set with open(), "
            "only the first of them starts open."
        ),
        pr.h2("Heading levels in an Accordion"),
        pr.p(
            "Every trigger sits inside a heading, which is how a screen reader "
            "lists and jumps between the sections. The level is h3 by default. "
            'Set heading() to one of "h2", "h3", "h4", "h5" or "h6" so it fits '
            "the headings around the Accordion. The level changes the markup "
            "and not the look."
        ),
        pr.code(
            'AccordionItem().heading("h2").title("Rate limits").content(...)',
        ),
        pr.h2("Accordion width"),
        pr.p(
            "An Accordion fills the width of its container, so it does not "
            "change width as items open and close. The text in a panel stops "
            "at 72 characters a line."
        ),
    )


PAGE = ComponentPage(
    Accordion,
    lede=(
        "An accordion is a list of sections that open and close under their "
        "headings. By default one section is open at a time. It suits "
        "content that a reader needs only a part of, such as a list of "
        "questions and answers."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            billing_questions,
            layout="stack",
            hint="Click a heading, or Tab to it and press Enter or Space",
        ),
        panel("Variants", ruled, boxed, layout="stack"),
        panel("States", all_closed, one_open, multiple_open, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "Each trigger is a native button inside a heading, with "
            "aria-expanded for its state and aria-controls pointing at its "
            "panel. It is in the tab order, and Enter or Space toggles it.",
        ),
        Note(
            "a11y",
            "Each panel has role=region and is labelled by its trigger, so a "
            "screen reader that lands in a panel announces which section it "
            "is in.",
        ),
        Note(
            "note",
            "The ids that join a trigger to its panel are generated per item "
            "with Alpine's $id, so two accordions on one page cannot point at "
            "each other's panels.",
        ),
        Note(
            "note",
            "The chevron is drawn from aria-expanded, so it turns with the "
            "state a screen reader hears.",
        ),
        Note(
            "warn",
            "Panels carry x-cloak, so every panel stays hidden until Alpine "
            "has loaded. A page without hue's script shows only the headings, "
            "with no way to open them.",
        ),
    ],
    parts=[AccordionItem],
    related=[Tabs],
)
