"""The auto-generated navigation sidebar."""

from __future__ import annotations

from hue import html
from hue.types.core import ComponentType

from hue_docs.models import NavGroup


def _nav_link(label: str, href: str, *, active: bool) -> ComponentType:
    base = "block rounded-md px-3 py-1.5 text-sm transition-colors"
    if active:
        style = "bg-surface text-surface-900 font-medium"
    else:
        style = "text-surface-600 hover:bg-surface hover:text-surface-900"
    return html.a(label).href(href).class_(f"{base} {style}")


def _nav_group(group: NavGroup, active_href: str) -> ComponentType:
    return (
        html.div()
        .class_("mb-6")
        .content(
            html.p(group.title).class_(
                "mb-2 px-3 text-xs font-semibold uppercase tracking-wide "
                "text-surface-400"
            ),
            html.nav(
                *[
                    _nav_link(item.label, item.href, active=item.href == active_href)
                    for item in group.items
                ]
            ).class_("space-y-0.5"),
        )
    )


def sidebar(groups: list[NavGroup], active_href: str) -> ComponentType:
    return (
        html.aside(
            *[_nav_group(group, active_href) for group in groups],
        )
        .class_(
            "w-60 shrink-0 border-r border-surface-200 px-4 py-8 "
            "lg:sticky lg:top-14 lg:h-[calc(100vh-3.5rem)] lg:overflow-y-auto"
        )
        # Hidden on small screens unless the mobile menu is open (navOpen lives
        # on the page wrapper's x-data scope).
        .x_bind("class", "navOpen ? '' : 'max-lg:hidden'")
    )
