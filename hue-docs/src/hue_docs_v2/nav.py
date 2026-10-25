"""
The sidebar's groups: the guides first, then the components by category.
"""

from __future__ import annotations

from collections import defaultdict

from hue_docs_v2.model import ComponentPage, GuidePage, NavGroup, NavItem

GUIDE_GROUPS = ["Get started", "Guides", "Django"]

# Categories not listed come after these, alphabetically.
CATEGORY_ORDER = [
    "Layout",
    "Typography",
    "Actions",
    "Inputs",
    "Feedback",
    "Navigation",
    "Data",
    "Charts",
    "Media",
]


def _category_rank(category: str) -> tuple[int, int | str]:
    try:
        return (0, CATEGORY_ORDER.index(category))
    except ValueError:
        return (1, category)


def build_nav(
    guides: list[GuidePage], components: list[ComponentPage]
) -> list[NavGroup]:
    unknown = {page.group for page in guides} - set(GUIDE_GROUPS)
    if unknown:
        raise ValueError(
            f"Guides use nav groups not in GUIDE_GROUPS: {sorted(unknown)}"
        )

    nav = []
    for group in GUIDE_GROUPS:
        pages = sorted((p for p in guides if p.group == group), key=lambda p: p.order)
        if pages:
            nav.append(NavGroup(group, [NavItem(p.nav_label, p.href) for p in pages]))

    by_category: dict[str, list[ComponentPage]] = defaultdict(list)
    for page in components:
        by_category[page.category].append(page)
    for category in sorted(by_category, key=_category_rank):
        members = sorted(by_category[category], key=lambda p: p.title)
        nav.append(NavGroup(category, [NavItem(p.title, p.href) for p in members]))
    return nav
