"""
Drawing a shortcut's keys, for the rows that show one: a palette item and a
menu item. What the keys are and how they are bound lives in hue.shortcuts.
"""

from __future__ import annotations

from htmy import html

from hue.shortcuts import Steps
from hue.types.core import ComponentType
from hue.ui.atoms.kbd import Kbd


def keys(steps: Steps) -> ComponentType:
    """
    The steps as Kbd, one per key press. A screen reader hears "then"
    between the presses of a sequence, which the gap only shows.
    """
    pressed: list[ComponentType] = []
    for index, step in enumerate(steps):
        if index:
            pressed.append(html.span(" then ", class_="sr-only"))
        pressed.append(Kbd(*(key.upper() if len(key) == 1 else key for key in step)))
    return html.span(*pressed, class_="ms-auto inline-flex items-center gap-1.5")
