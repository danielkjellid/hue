"""
Keyboard shortcuts, drawn and bound from one declaration.

A shortcut is written as steps: one string per key press, with the keys of a
chord joined by plus signs. shortcut("mod+k") is Command-K, or Control-K
away from Apple platforms, and shortcut("g", "b") is G followed by B. The
same steps become the Kbd a reader sees and the x-shortcut binding the
browser answers to, so the two cannot disagree.
"""

from __future__ import annotations

import json

from htmy import html

from hue.types.core import ComponentType
from hue.ui.atoms.kbd import Kbd

_MODIFIERS = frozenset({"mod", "ctrl", "alt", "shift"})


def parse(steps: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """
    Each step as its keys, lower-cased, refusing what the browser could
    never match: an empty step, an unknown modifier, or a modifier on its
    own.
    """
    if not steps:
        raise ValueError("A shortcut needs at least one step, such as 'mod+k'.")
    parsed = []
    for step in steps:
        keys = tuple(key.strip().lower() for key in step.split("+"))
        *modifiers, key = keys
        if not key or key in _MODIFIERS:
            raise ValueError(f"{step!r} has no key to press, only modifiers.")
        unknown = set(modifiers) - _MODIFIERS
        if unknown:
            raise ValueError(
                f"{step!r} uses {', '.join(sorted(unknown))} as a modifier; "
                "the modifiers are mod, ctrl, alt and shift."
            )
        parsed.append(keys)
    return tuple(parsed)


def keys(steps: tuple[str, ...]) -> ComponentType:
    """
    The steps as Kbd, one per key press. A screen reader hears "then"
    between the presses of a sequence, which the gap only shows.
    """
    pressed: list[ComponentType] = []
    for index, step in enumerate(parse(steps)):
        if index:
            pressed.append(html.span(" then ", class_="sr-only"))
        pressed.append(Kbd(*(key.upper() if len(key) == 1 else key for key in step)))
    return html.span(*pressed, class_="ms-auto inline-flex items-center gap-1.5")


def binding(steps: tuple[str, ...]) -> dict[str, str]:
    """
    The attribute that binds the steps, for the x-shortcut directive.
    """
    return {"x-shortcut": json.dumps(["+".join(step) for step in parse(steps)])}
