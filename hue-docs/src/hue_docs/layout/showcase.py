"""Render a component's docs page: header + a card per showcased variant."""

from __future__ import annotations

from htmy import SafeStr
from hue import html
from hue.types.core import ComponentType

from hue_docs.discovery import ComponentDoc
from hue_docs.layout.code import code_block
from hue_docs.registry import Showcase, Variant, example_code
from hue_docs.render import render_html_sync

_CONTAINER = {
    "row": "flex flex-wrap gap-4",
    "grid": "grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3",
    "stack": "flex flex-col gap-4",
}

_CARD_WIDTH = {
    "row": "min-w-64 flex-1",
    "grid": "",
    "stack": "w-full",
}


def _preview(variant: Variant) -> ComponentType:
    try:
        rendered = render_html_sync(variant.build())
    except Exception as exc:  # defensive: keep one bad variant from failing the build
        return html.p(f"Could not render: {exc}").class_("text-sm text-destructive")
    # Already-rendered HTML; embed verbatim without re-escaping.
    return SafeStr(rendered)


def _card(variant: Variant, layout: str) -> ComponentType:
    return html.div(
        html.div(
            html.span(variant.label).class_(
                "absolute left-2 top-2 rounded bg-surface px-1.5 py-0.5 "
                "text-[10px] uppercase tracking-wide text-surface-400"
            ),
            _preview(variant),
        ).class_(
            "relative flex min-h-28 flex-wrap items-center justify-center gap-3 "
            "rounded-lg border border-surface-200 bg-background px-6 pb-6 pt-8"
        ),
        code_block(variant.code),
    ).class_(f"space-y-2 {_CARD_WIDTH[layout]}")


def _showcase_block(showcase: Showcase) -> ComponentType:
    children: list[ComponentType] = [
        html.h2(showcase.title).class_("text-xl font-semibold text-surface-900"),
    ]
    if showcase.description:
        children.append(
            html.p(showcase.description).class_("max-w-prose text-sm text-surface-600")
        )
    children.append(
        html.div(
            *[_card(variant, showcase.layout) for variant in showcase.variants]
        ).class_(_CONTAINER[showcase.layout])
    )
    return html.section(*children).class_("space-y-4")


def _header(doc: ComponentDoc) -> ComponentType:
    children: list[ComponentType] = [
        html.h1(doc.name).class_("text-3xl font-bold text-surface-900"),
    ]
    children.extend(
        html.p(text).class_("max-w-prose leading-7 text-surface-600")
        for text in doc.paragraphs
    )
    usage = example_code(doc)
    if usage:
        children.append(code_block(usage))
    return html.div(*children).class_("space-y-3")


def component_main(
    doc: ComponentDoc,
    showcases: list[Showcase],
    playground: ComponentType | None = None,
) -> ComponentType:
    sections: list[ComponentType] = [_header(doc)]
    if playground is not None:
        sections.append(playground)
    if not showcases:
        sections.append(
            html.p("No showcase available for this component yet.").class_(
                "text-surface-500"
            )
        )
    sections.extend(_showcase_block(showcase) for showcase in showcases)
    return html.div(*sections).class_("space-y-12")
