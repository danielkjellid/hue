from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import (
    Accordion,
    Disclosure,
    NumberInput,
    Stack,
    Switch,
    Textarea,
    TextInput,
)

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def a_long_form_folded() -> ComponentType:
    return (
        Stack()
        .align_items("items-stretch")
        .content(
            Disclosure()
            .title("General")
            .content(
                Stack()
                .spacing("md")
                .align_items("items-stretch")
                .content(
                    TextInput().name("product_name").label("Name").required(),
                    Textarea().name("product_description").label("Description"),
                )
            ),
            Disclosure()
            .title("Pricing")
            .closed()
            .content(
                Stack()
                .spacing("md")
                .align_items("items-stretch")
                .content(
                    NumberInput().name("price").label("Price").prefix("$").value("49"),
                    Switch().name("subscription").label("Bill monthly"),
                )
            ),
            Disclosure()
            .title("Search engines")
            .closed()
            .content(
                TextInput()
                .name("slug")
                .label("URL slug")
                .prefix("northwind.com/")
                .value("acoustic-guitar")
            ),
        )
    )


# States


def open_by_default() -> Disclosure:
    return Disclosure().title("General").content("Everything about the product itself.")


def closed() -> Disclosure:
    return (
        Disclosure()
        .title("Advanced")
        .closed()
        .content("Settings most products never change.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Disclosure` is one section of a page that the reader can fold "
            "away. `title()` is the text of the band across the top, and the "
            "children are what the band opens and closes. A `Disclosure` starts "
            "open; `closed()` starts it folded."
        ),
        pr.code(
            'Disclosure().title("Pricing").closed().content(\n'
            '    NumberInput().name("price").label("Price").prefix("$"),\n'
            ")"
        ),
        pr.h3("Several sections on one page"),
        pr.p(
            "Each `Disclosure` keeps its own open state and answers to nothing "
            "else on the page, so any number can be open at once. An `Accordion` "
            "is the component for a set of sections that agree on how many "
            "stay open."
        ),
        pr.h3("Where a Disclosure keeps its state"),
        pr.p(
            "The open state lives in Alpine on the page and is not submitted or "
            "remembered. A form field inside a closed `Disclosure` is hidden with "
            "`display: none` but stays in the form, so it is still submitted."
        ),
    )


PAGE = ComponentPage(
    Disclosure,
    lede=(
        "A disclosure is a section of a page under a heading that folds its "
        "content away and back. Use one to break a long form into sections a "
        "reader can open as they go."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            a_long_form_folded,
            layout="stack",
            captions=False,
            hint="Click a band, or tab to it and press Enter",
        ),
        panel("States", open_by_default, closed, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The title is a button inside an `h3`, so a screen reader finds each "
            "section in its list of headings.",
        ),
        Note(
            "a11y",
            "The button carries `aria-expanded` and `aria-controls`, and the content "
            "is a region labelled by the button, so a reader inside it hears "
            "which section it is in.",
        ),
        Note(
            "note",
            "Enter and Space toggle the section, because the trigger is a native "
            "button.",
        ),
        Note(
            "warn",
            "The title is always an `h3`, whatever the headings around the "
            "`Disclosure`. There is no modifier for the level.",
        ),
    ],
    related=[Accordion],
)
