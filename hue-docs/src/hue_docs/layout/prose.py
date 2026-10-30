"""
Helpers for writing a guide page out of hue's own html.
"""

from __future__ import annotations

from htmy import Fragment
from hue import html
from hue.html import Element
from hue.types.core import ComponentType

from hue_docs.layout.code import code_block
from hue_docs.model import slugify
from hue_docs.site import url


def page(*children: ComponentType) -> ComponentType:
    return html.div(*children).class_("space-y-5")


def section(*children: ComponentType) -> ComponentType:
    return html.div(*children).class_("space-y-3")


def h1(text: str) -> ComponentType:
    return html.h1(text).class_("font-ui text-3xl font-bold tracking-tight text-fg")


def h2(text: str) -> ComponentType:
    # An id of its own, so the table of contents and search can land on it.
    return (
        html.h2(text)
        .id(slugify(text))
        .class_("scroll-mt-20 pt-6 font-ui text-xl font-semibold text-fg")
    )


def h3(text: str) -> ComponentType:
    return (
        html.h3(text)
        .id(slugify(text))
        .class_("scroll-mt-20 pt-2 font-ui text-md font-semibold text-fg")
    )


def rich(text: str) -> ComponentType:
    """
    Text with each `backticked` run set as inline code, which is how prose
    names a class, a function, a parameter or anything else typed in code.
    """
    parts = text.split("`")
    if len(parts) % 2 == 0:
        raise ValueError(f"An unpaired backtick in {text!r}.")
    return Fragment(
        *[inline(part) if index % 2 else part for index, part in enumerate(parts)]
    )


def _rich_all(content: tuple[ComponentType, ...]) -> list[ComponentType]:
    return [rich(each) if isinstance(each, str) else each for each in content]


def lead(text: str) -> Element:
    return html.p(rich(text)).class_(
        "max-w-[66ch] text-md leading-relaxed text-fg-muted"
    )


def p(*content: ComponentType) -> ComponentType:
    return html.p(*_rich_all(content)).class_("leading-relaxed text-fg-muted")


def code(source: str, *, language: str = "python") -> ComponentType:
    return code_block(source, language=language)


def inline(text: str) -> ComponentType:
    return html.code(text).class_("docs-inline-code")


def link(text: str, href: str) -> ComponentType:
    return (
        html.a(text)
        .href(url(href))
        .class_("font-medium text-accent-text underline underline-offset-2")
    )


def bullets(items: list[ComponentType]) -> ComponentType:
    return html.ul(
        *[html.li(*_rich_all((item,))).class_("leading-relaxed") for item in items]
    ).class_("list-disc space-y-1 ps-5 text-fg-muted")
