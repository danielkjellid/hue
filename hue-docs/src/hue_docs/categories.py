"""Sidebar grouping for components.

Each component declares its own section via a ``category`` class attribute (in
``hue-python``), so there's no central component→section map to maintain — a new
component lands in the right place automatically. The only thing that lives here
is the *order* in which sections appear, which is a cross-component presentation
choice the docs own.
"""

from __future__ import annotations

from collections.abc import Iterable

from hue_docs.discovery import ComponentDoc

# Preferred order of sidebar sections. Categories not listed here appear after
# these, alphabetically.
CATEGORY_ORDER = ["Layout", "Typography", "Actions", "Inputs", "Feedback", "Media"]

DEFAULT_CATEGORY = "Components"


def category_for(doc: ComponentDoc) -> str:
    return getattr(doc.cls, "category", DEFAULT_CATEGORY) or DEFAULT_CATEGORY


def ordered_categories(docs: Iterable[ComponentDoc]) -> list[str]:
    """Categories present among *docs*, in display order (unknown ones last)."""
    present = {category_for(doc) for doc in docs}

    def rank(category: str) -> tuple[int, object]:
        try:
            return (0, CATEGORY_ORDER.index(category))
        except ValueError:
            return (1, category)

    return sorted(present, key=rank)
