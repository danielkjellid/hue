"""
A component's page: what it is, how to use it, its panels, its API.
"""

from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import (
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
)
from hue.ui.base import ChainableComponent
from hue.utils import render_if, render_when

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.layout.code import code_block
from hue_docs_v2.layout.panel import panel_section
from hue_docs_v2.model import ComponentPage, Note
from hue_docs_v2.props import props_of

# Each kind of note: its tag and the tag's colour.
_NOTES = {
    "a11y": ("A11y", "text-success-text"),
    "note": ("Note", "text-fg-subtle"),
    "warn": ("Watch", "text-warning-text"),
}


def props_table(cls: type[ChainableComponent]) -> ComponentType:
    props = props_of(cls)
    if not props:
        return pr.p(f"{cls.__name__} has no modifiers of its own.")
    rows = [
        TableRow().content(
            TableCell()
            .class_("align-top")
            .content(
                html.code(prop.signature).class_(
                    "font-mono text-xs text-fg [overflow-wrap:anywhere]"
                )
            ),
            TableCell()
            .class_("align-top")
            .content(pr.inline(prop.default) if prop.default else "-"),
            TableCell().class_("align-top text-fg-muted").content(prop.doc or "-"),
        )
        for prop in props
    ]
    return (
        Table()
        .compact()
        .aria_label(f"{cls.__name__} modifiers")
        .content(
            TableHeader().content(
                TableRow().content(
                    TableHead().content("Modifier"),
                    TableHead().content("Default"),
                    TableHead().content("Description"),
                )
            ),
            TableBody().content(*rows),
        )
    )


def _note(note: Note) -> ComponentType:
    tag, colour = _NOTES[note.kind]
    return html.div(
        html.span(tag).class_(
            f"w-[62px] flex-none pt-[3px] font-ui text-2xs font-bold uppercase "
            f"tracking-[0.04em] {colour}"
        ),
        html.p(pr.rich(note.text)).class_("text-sm leading-relaxed text-fg-muted"),
    ).class_("flex gap-3")


def component_main(page: ComponentPage, pages: list[ComponentPage]) -> ComponentType:
    # Only the related components that have a page yet, so no link 404s.
    by_class = {other.component: other for other in pages}
    related = [by_class[cls] for cls in page.related if cls in by_class]
    api = [
        pr.h2("API"),
        props_table(page.component),
        *[
            html.div(pr.h3(part.__name__), props_table(part)).class_("space-y-3")
            for part in page.parts
        ],
    ]
    names = ", ".join([page.title, *[part.__name__ for part in page.parts]])
    return html.div(
        html.header(
            # Kept out of the index, or every excerpt starts with it.
            html.p(f"Hue · {page.category}")
            .class_(
                "mb-2 font-ui text-2xs font-bold uppercase tracking-[0.08em] "
                "text-accent-text"
            )
            .data("pagefind-ignore", ""),
            pr.h1(page.title),
            pr.lead(page.lede).class_("mt-3"),
        ).class_("mb-10"),
        code_block(f"from hue.ui import {names}"),
        html.div(*[panel_section(page, panel) for panel in page.panels]).class_(
            "mt-10 flex flex-col gap-6"
        ),
        render_if(page.usage, lambda usage: html.div(usage()).class_("mt-8")),
        html.div(*api).class_("mt-4 space-y-4"),
        render_when(
            bool(page.notes),
            html.div(
                pr.h2("Notes"),
                html.div(*[_note(note) for note in page.notes]).class_(
                    "flex flex-col gap-2"
                ),
            ).class_("mt-4 space-y-4"),
        ),
        render_when(
            bool(related),
            html.div(
                pr.h2("Related"),
                html.ul(
                    *[html.li(pr.link(other.title, other.href)) for other in related]
                ).class_("flex flex-wrap gap-x-4 gap-y-1"),
            ).class_("mt-4 space-y-3"),
        ),
    )
