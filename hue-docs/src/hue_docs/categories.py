"""Sidebar grouping for components.

Components are clustered into named subsections (e.g. the inputs live together
under "Inputs") instead of one flat alphabetical list. Unmapped components fall
back to a generic "Components" group, so a newly added component still shows up
automatically — just drop it in the map below to give it a home.
"""

from __future__ import annotations

from collections.abc import Iterable

# Order in which subsections appear in the sidebar.
CATEGORY_ORDER = ["Layout", "Typography", "Actions", "Inputs", "Feedback", "Media"]

DEFAULT_CATEGORY = "Components"

_COMPONENT_CATEGORY = {
    "Stack": "Layout",
    "Spacer": "Layout",
    "Text": "Typography",
    "Label": "Typography",
    "Button": "Actions",
    "TextInput": "Inputs",
    "EmailInput": "Inputs",
    "PasswordInput": "Inputs",
    "NumberInput": "Inputs",
    "Callout": "Feedback",
    "Icon": "Media",
}


def category_for(name: str) -> str:
    return _COMPONENT_CATEGORY.get(name, DEFAULT_CATEGORY)


def ordered_categories(names: Iterable[str]) -> list[str]:
    """Categories present among *names*, in display order (unmapped last)."""
    present = {category_for(name) for name in names}
    ordered = [category for category in CATEGORY_ORDER if category in present]
    if DEFAULT_CATEGORY in present:
        ordered.append(DEFAULT_CATEGORY)
    return ordered
