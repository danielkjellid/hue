"""
What a palette item and a menu item share when they run one of the app's
shortcuts: finding what it does in this request, refusing to do anything
else, and drawing its keys. What the keys are and how they are bound lives
in hue.shortcuts.
"""

from __future__ import annotations

from htmy import Context, html

from hue.context import HueContext
from hue.js import Expression
from hue.shortcuts import Shortcut, Steps
from hue.types.core import ComponentType
from hue.ui.atoms.kbd import Kbd

NO_REGISTRY = (
    "this app binds no shortcuts. Put its registry in the render context: "
    "HUE_SHORTCUTS in hue-django, or shortcuts in HueContextArgs"
)


def resolve(
    context: Context, shortcut: Shortcut, *, own: bool, disabled: bool
) -> tuple[str | None, Expression | None]:
    """
    Where the shortcut goes or what it runs in this request, for a row that
    shows it.

    Refuses a row that also does something of its own: the keys only ever
    run the shortcut, so a row with its own href or handler would do one
    thing when clicked and another when its keys were pressed, and a
    disabled one would still run from the keyboard. A shortcut that should
    not run on a page is scoped and not used there. Refuses one this request
    does not bind, too, since the row would show keys that do nothing.
    """
    if own:
        raise ValueError(
            f"A row runs {shortcut!r}, so it cannot also have an href or a "
            "handler of its own: its keys would do something else."
        )
    if disabled:
        raise ValueError(
            f"A row runs {shortcut!r} and is disabled, but its keys would still "
            "run it. Make the shortcut scoped and leave it unused on this page."
        )
    hue = HueContext.from_context(context)
    if hue.shortcuts is None:
        raise ValueError(f"A row shows {shortcut!r}, but {NO_REGISTRY}.")
    for item in hue.shortcuts.active():
        if item.shortcut is shortcut:
            return item.url(hue.request), item.action
    raise ValueError(
        f"A row shows {shortcut!r}, which is not on for this request: it is "
        "scoped and nothing called shortcuts.use() for it, or it belongs to "
        "another registry."
    )


def keys(steps: Steps) -> ComponentType:
    """
    The steps as Kbd, one per key press. A screen reader hears "then"
    between the presses of a sequence, which the gap only shows.
    """
    pressed: list[ComponentType] = []
    for index, step in enumerate(steps):
        if index:
            pressed.append(html.span(" then ", class_="sr-only"))
        pressed.append(Kbd(*step))
    return html.span(*pressed, class_="ms-auto inline-flex items-center gap-1.5")
