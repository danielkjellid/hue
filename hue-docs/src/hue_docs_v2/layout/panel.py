"""
A specimen panel, and the page its frame loads.

The canvas is an iframe, not a div: Tailwind's sm: and md: are viewport media
queries, so only a document of its own changes layout when the canvas is made
narrower. It also gives each panel its own data-theme, and keeps an overlay
that opens inside it from covering the docs around it.
"""

from __future__ import annotations

import json

from htmy import html as h
from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import Button, SegmentedControl, SegmentedOption, ToastRegion
from hue.utils import render_when
from hue_fastapi import Page

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout.code import code_block
from hue_docs_v2.model import ComponentPage, Panel, caption
from hue_docs_v2.render import preview
from hue_docs_v2.site import url
from hue_docs_v2.snippets import imports, snippet

# Tailwind's breakpoints, which are what a width is chosen to cross.
VIEWPORTS = {"sm": 640, "md": 768, "lg": 1024, "xl": 1280}


def frame_href(page: ComponentPage, panel: Panel) -> str:
    return f"/_frame/{page.slug}/{panel.slug}/"


def panel_code(panel: Panel) -> str:
    snippets = [snippet(example) for example in panel.examples]
    if len(snippets) == 1:
        body = snippets[0]
    else:
        body = "\n\n".join(
            f"# {caption(example)}\n{code}"
            for example, code in zip(panel.examples, snippets, strict=True)
        )
    head = imports(*snippets)
    return f"{head}\n\n{body}" if head else body


def _viewport_control() -> ComponentType:
    def option(name: str, width: int | None) -> ComponentType:
        value = json.dumps(width)
        return (
            SegmentedOption()
            .value(name)
            .content(name)
            .x_on("click", unsafe(f"width = {value}"))
            .x_bind("aria-pressed", unsafe(f"String(width === {value})"))
        )

    return (
        SegmentedControl()
        .label("Preview width")
        .size("sm")
        .class_("max-md:hidden")
        .content(
            option("Fill", None),
            *[option(name, width) for name, width in VIEWPORTS.items()],
        )
    )


def _theme_control() -> ComponentType:
    def option(theme: str, icon: str) -> ComponentType:
        return (
            SegmentedOption()
            .value(theme)
            .icon_only(f"{theme.title()} theme")
            .content(Icon(icon))
            .x_on("click", unsafe(f"theme = '{theme}'"))
            .x_bind("aria-pressed", unsafe(f"String(effectiveTheme === '{theme}')"))
        )

    return (
        SegmentedControl()
        .label("Preview theme")
        .size("sm")
        .content(option("light", "sun"), option("dark", "moon"))
    )


def _code_toggle(code_id: str) -> ComponentType:
    return (
        Button()
        .variant("ghost")
        .size("xs")
        .aria_controls(code_id)
        .x_bind("aria-expanded", unsafe("String(showCode)"))
        .x_on("click", unsafe("showCode = !showCode"))
        .content(Icon("code"), "Code")
    )


def panel_section(page: ComponentPage, panel: Panel) -> ComponentType:
    code_id = f"{panel.slug}-code"
    bar = html.div(
        html.div(
            html.h2(panel.label).class_("docs-panel-label"),
            render_when(
                bool(panel.hint),
                html.span(panel.hint).class_("truncate text-2xs text-fg-subtle"),
            ),
        ).class_("flex min-w-0 items-baseline gap-3"),
        html.div(
            html.span()
            .class_("font-mono text-2xs tabular-nums text-fg-subtle max-md:hidden")
            .x_text(unsafe("readout()")),
            _viewport_control(),
            _theme_control(),
            _code_toggle(code_id),
        ).class_("flex flex-none items-center gap-2"),
    ).class_(
        "flex flex-wrap items-center justify-between gap-3 border-b border-border "
        "bg-surface-sunken px-4 py-[7px]"
    )
    # Plain markup: the one control here that is not a button has to be put
    # in the tab order by hand, which no hue modifier does.
    handle = h.div(
        h.span(class_="h-8 w-1 rounded-full bg-border-strong"),
        role="separator",
        tabindex="0",
        aria_label="Preview width",
        aria_orientation="vertical",
        class_=(
            "absolute inset-y-0 -end-3 flex w-3 cursor-ew-resize touch-none "
            "items-center justify-center rounded-sm outline-none "
            "focus-visible:shadow-ring hover:[&>span]:bg-border-hover"
        ),
        **{
            ":aria-valuenow": "Math.round(shownWidth)",
            ":aria-valuemin": "minWidth",
            ":aria-valuemax": "maxWidth()",
            ":aria-valuetext": "readout()",
            "x-on:pointerdown": "startDrag($event)",
            "x-on:keydown": "nudge($event)",
        },
    )
    canvas = (
        html.div(
            html.div(
                h.iframe(
                    src=url(frame_href(page, panel)),
                    title=f"{page.title}: {panel.label}",
                    loading="lazy",
                    class_="block w-full border-0 bg-canvas",
                    style=f"height: {max(panel.min_height, 96)}px",
                    **{"x-ref": "frame", "x-on:load": "attach()"},
                ),
                handle,
            )
            .class_("relative max-w-full")
            .x_ref("holder")
            .x_bind(
                "style", unsafe("width === null ? 'width: 100%' : `width: ${width}px`")
            ),
        )
        .class_("overflow-x-auto bg-canvas-subtle pe-4")
        .x_ref("canvas")
    )
    code = (
        html.div(code_block(panel_code(panel)))
        .id(code_id)
        .class_(
            "border-t border-border "
            "[&_.docs-code_pre]:rounded-none [&_.docs-code_pre]:border-0"
        )
        .x_show(unsafe("showCode"))
        .x_cloak()
    )
    return (
        html.section(bar, canvas, code)
        .id(panel.slug)
        .class_(
            "scroll-mt-20 overflow-hidden rounded-lg border border-border bg-surface"
        )
        .x_data(f"docsPanel({json.dumps({'minHeight': panel.min_height})})")
    )


_LAYOUTS = {
    "grid": "grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-x-3 gap-y-4",
    "stack": "flex flex-col gap-6",
    "center": "flex min-h-[180px] flex-wrap items-center justify-center gap-4",
}


async def frame_page(page: ComponentPage, panel: Panel, request: object) -> Page:
    captioned = panel.captions and len(panel.examples) > 1 and panel.layout != "center"
    cells = [
        html.div(
            render_when(captioned, html.span(caption(example)).class_("docs-caption")),
            await preview(example, request),
        ).class_("flex min-w-0 flex-col items-start gap-[7px]")
        for example in panel.examples
    ]
    body = (
        html.div(
            html.div(*cells).class_(_LAYOUTS[panel.layout]),
            # A toast raised in the frame lands in the frame, beside what raised it.
            ToastRegion(),
        )
        .id("frame")
        .class_("p-6")
    )
    return Page(title=f"{page.title}: {panel.label}", body=body)
