"""
The frame every docs page sits in: navigation, top bar, content, contents.
"""

from __future__ import annotations

from htmy import html as h
from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Kbd,
    Sidebar,
    SidebarBody,
    SidebarHeader,
    SidebarHeading,
    SidebarItem,
    SidebarSection,
    TableOfContents,
    ThemeSwitcher,
    ToastRegion,
)
from hue.utils import render_when
from hue_fastapi import Page

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout.search import search_dialog
from hue_docs_v2.model import NavGroup
from hue_docs_v2.site import url


def _brand() -> ComponentType:
    return (
        html.a(
            html.span("H").class_(
                "grid size-[30px] flex-none place-content-center rounded-md "
                "bg-accent font-ui text-[15px] font-bold text-accent-fg"
            ),
            html.span(
                html.span("Hue").class_(
                    "block font-ui text-md font-bold leading-tight tracking-tight"
                ),
                html.span("Component library").class_(
                    "block text-2xs tracking-wide text-fg-subtle"
                ),
            ),
        )
        .href(url("/"))
        .class_("flex items-center gap-3 rounded-md text-fg focus-visible:shadow-ring")
    )


def _sidebar(nav: list[NavGroup], current: str) -> ComponentType:
    sections = [
        SidebarSection().content(
            SidebarHeading().content(group.title),
            *[
                # The home page is "/", which every path starts with.
                SidebarItem()
                .href(url(item.href))
                .exact(item.href == "/")
                .content(item.label)
                for item in group.items
            ],
        )
        for group in nav
    ]
    return (
        html.aside(
            Sidebar()
            .current(url(current))
            .label("Documentation")
            .class_("h-full")
            .content(
                SidebarHeader().class_("border-b-0 px-5 pt-5").content(_brand()),
                SidebarBody().label("Documentation").class_("gap-5").content(*sections),
            )
        )
        .id("docs-nav")
        .class_(
            "z-30 w-[252px] flex-none border-e border-border bg-canvas-subtle "
            "lg:sticky lg:top-0 lg:h-screen max-lg:fixed max-lg:inset-y-0 "
            "max-lg:start-0 max-lg:shadow-overlay"
        )
        # Off-canvas below lg, shown by the menu button.
        .x_bind("class", unsafe("navOpen ? '' : 'max-lg:hidden'"))
        .x_on("keydown.escape", unsafe("navOpen = false; $refs.menu.focus()"))
    )


def _search_trigger() -> ComponentType:
    return (
        Button()
        .variant("outline")
        .size("sm")
        .aria_keyshortcuts("Meta+K Control+K")
        .content(
            Icon("search"),
            html.span("Search").class_("text-fg-muted"),
            Kbd("mod", "k").class_("ms-4 max-sm:hidden"),
        )
        .x_on("click", unsafe("$dispatch('docs-search')"))
    )


def _topbar(title: str) -> ComponentType:
    return html.header(
        html.div(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Menu")
            .class_("lg:hidden")
            .aria_controls("docs-nav")
            .x_ref("menu")
            .x_bind("aria-expanded", unsafe("navOpen"))
            .x_on("click", unsafe("navOpen = !navOpen"))
            .content(Icon("menu")),
            html.p(title).class_("truncate font-ui text-base font-semibold"),
        ).class_("flex min-w-0 items-center gap-2"),
        html.div(_search_trigger(), ThemeSwitcher()).class_("flex items-center gap-3"),
    ).class_(
        "sticky top-0 z-20 flex h-14 items-center justify-between gap-4 "
        "border-b border-border bg-canvas/[0.88] px-5 backdrop-blur-[10px] lg:px-8"
    )


def shell(
    *,
    title: str,
    nav: list[NavGroup],
    current: str,
    main: ComponentType,
    contents: bool = True,
) -> Page:
    skip = (
        html.a("Skip to content")
        .href("#content")
        .class_(
            "fixed start-3 top-3 z-50 -translate-y-[200%] rounded-sm bg-fg px-3 py-2 "
            "font-ui text-sm font-semibold text-canvas focus-visible:translate-y-0"
        )
    )
    toc = render_when(
        contents,
        html.aside(TableOfContents().of("#content")).class_(
            "sticky top-14 hidden max-h-[calc(100vh-3.5rem)] w-56 flex-none "
            "self-start overflow-y-auto py-10 xl:block"
        ),
    )
    body = html.div(
        skip,
        html.div(
            # Behind the off-canvas navigation, so a tap beside it closes it.
            html.div()
            .class_("fixed inset-0 z-20 bg-scrim lg:hidden")
            .x_show(unsafe("navOpen"))
            .x_cloak()
            .x_on("click", unsafe("navOpen = false")),
            _sidebar(nav, current),
            html.div(
                _topbar(title),
                html.div(
                    html.main(main)
                    .id("content")
                    .data("pagefind-body", "")
                    .class_("min-w-0 max-w-[1120px] flex-1 px-5 pb-20 pt-10 lg:px-8"),
                    toc,
                ).class_("flex gap-8 xl:pe-6"),
            ).class_("min-w-0 flex-1"),
        ).class_("flex min-h-screen"),
        ToastRegion(),
        search_dialog(),
        # A classic script, so it runs before the bundle's module and its
        # Alpine components are registered by the time Alpine starts.
        h.script(src=url("/static/docs.js")),
    ).x_data("{ navOpen: false }")
    return Page(title=title, body=body)
