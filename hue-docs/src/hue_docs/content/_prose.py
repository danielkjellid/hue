"""Small helpers for authoring prose pages with hue's html components."""

from __future__ import annotations

from hue import html
from hue.types.core import ComponentType

from hue_docs.layout.code import code_block


def page(*children: ComponentType) -> ComponentType:
    return html.div(*children).class_("max-w-3xl space-y-5")


def section(*children: ComponentType) -> ComponentType:
    return html.div(*children).class_("space-y-3")


def h1(text: str) -> ComponentType:
    return html.h1(text).class_("text-3xl font-bold text-surface-900")


def h2(text: str) -> ComponentType:
    return html.h2(text).class_("pt-6 text-xl font-semibold text-surface-900")


def lead(text: str) -> ComponentType:
    return html.p(text).class_("max-w-prose text-lg leading-8 text-surface-600")


def p(*content: ComponentType) -> ComponentType:
    return html.p(*content).class_("max-w-prose leading-7 text-surface-600")


def code(source: str, *, language: str = "python") -> ComponentType:
    return code_block(source, language=language)


def link(text: str, href: str) -> ComponentType:
    return (
        html.a(text)
        .href(href)
        .class_("font-medium text-primary underline underline-offset-2")
    )


def bullets(items: list[ComponentType]) -> ComponentType:
    return html.ul(*[html.li(item).class_("leading-7") for item in items]).class_(
        "max-w-prose list-disc space-y-1 pl-5 text-surface-600"
    )
