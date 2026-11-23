"""
What every floating panel shares, whichever widget it belongs to.
"""

from __future__ import annotations


def anchor(placement: str, reference: str, *, flip: bool = True) -> dict[str, str]:
    """
    Pin a floating panel 6px off the element it belongs to: the gap is wide
    enough for the panel to read as its own surface and narrow enough for a
    pointer to cross it.

    The panel is fixed rather than absolute. An absolute panel inside a
    dialog is cut off by the scrolling body and the panel around it, while a
    fixed one is placed against the scrim instead, which clips nothing. The
    plugin places it again on every scroll of an ancestor, so it still moves
    with the page. flip=False keeps the panel on the side it was given, for a
    panel whose arrow points one way only.
    """
    modifiers = "fixed" if flip else "fixed.noflip"
    return {f"x-anchor.{modifiers}.{placement}.offset.6": reference}
