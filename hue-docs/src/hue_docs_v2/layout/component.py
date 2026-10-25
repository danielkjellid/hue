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
from hue_docs_v2.model import ComponentPage, Note, kebab
from hue_docs_v2.props import props_of

_NOTE_TAGS = {"a11y": "A11y", "note": "Note", "warn": "Watch"}
_NOTE_COLOURS = {
    "a11y": "text-success-text",
    "note": "text-fg-subtle",
    "warn": "text-warning-text",
}


def pagehead(eyebrow: str, title: str, lede: str) -> ComponentType:
    return html.header(
        html.p(eyebrow).class_("docs-eyebrow"),
        html.h1(title).class_("font-ui text-3xl font-bold tracking-tight text-fg"),
        html.p(lede).class_("mt-3 max-w-[66ch] text-md leading-relaxed text-fg-muted"),
    ).class_("mb-10")


def props_table(cls: type[ChainableComponent]) -> ComponentType:
    props = props_of(cls)
    if not props:
        return pr.p(f"{cls.__name__} has no modifiers of its own.")
    rows = [
        TableRow().content(
            TableCell()
            .class_("align-top")
            .content(html.code(prop.signature).class_("docs-signature")),
            TableCell()
            .class_("align-top")
            .content(
                html.code(prop.default).class_("docs-inline-code")
                if prop.default
                else "-"
            ),
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
    return html.div(
        html.span(_NOTE_TAGS[note.kind]).class_(
            f"w-[62px] flex-none pt-[3px] font-ui text-2xs font-bold uppercase "
            f"tracking-[0.04em] {_NOTE_COLOURS[note.kind]}"
        ),
        html.p(note.text).class_("text-sm leading-relaxed text-fg-muted"),
    ).class_("flex gap-3")


def component_main(page: ComponentPage) -> ComponentType:
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
        pagehead(f"Hue · {page.category}", page.title, page.lede),
        code_block(f"from hue.ui import {names}"),
        html.div(*[panel_section(page, panel) for panel in page.panels]).class_(
            "mt-10 flex flex-col gap-6"
        ),
        render_if(page.usage, lambda usage: html.div(usage()).class_("mt-8")),
        html.div(*api).class_("mt-4 space-y-4"),
        render_when(
            bool(page.notes),
            html.div(
                pr.h2("Accessibility"),
                html.div(*[_note(note) for note in page.notes]).class_(
                    "flex flex-col gap-2"
                ),
            ).class_("mt-4 space-y-4"),
        ),
        render_when(
            bool(page.related),
            html.div(
                pr.h2("Related"),
                html.ul(
                    *[
                        html.li(
                            pr.link(cls.__name__, f"/components/{kebab(cls.__name__)}/")
                        )
                        for cls in page.related
                    ]
                ).class_("flex flex-wrap gap-x-4 gap-y-1"),
            ).class_("mt-4 space-y-3"),
        ),
    )
