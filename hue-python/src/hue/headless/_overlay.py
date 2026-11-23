"""
The behaviour every overlay shares, whichever widget it belongs to: where a
floating panel sits, how an overlay closes, how its panel is named and how
its trigger is wired.
"""

from __future__ import annotations

from hue.base import ChainableComponent


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


# Alpine mints the ids, so two overlays on a page cannot share one.
TITLE_ID = "$id('hue-overlay-title')"
DESCRIPTION_ID = "$id('hue-overlay-description')"
OVERLAY_IDS = "['hue-overlay-title', 'hue-overlay-description']"

#: How every overlay, the popover and the menu included, closes on Escape.
#: The listener sits on the overlay and not on the window: window listeners
#: run outermost first, so an inner overlay could never stop an outer one. It
#: stops the key, so one press closes only the innermost open overlay and a
#: page-wide Escape behind it (the one that clears a table's selection, say)
#: never fires.
CLOSE_ON_ESCAPE = {
    "x-on:keydown.escape": "if (open) { $event.stopPropagation(); close() }"
}

#: The listener above only hears keys pressed inside the overlay. A click on
#: anything that cannot take focus leaves focus on the body, where the
#: listener cannot hear it. A popover or a menu puts this on its panel. A
#: modal puts it on the scrim, which takes the focus from a click on the
#: panel's text or beside the panel; the focus trap then moves it back in.
HOLDS_FOCUS = {"tabindex": "-1"}


#: Close on a click on the scrim itself, but only one that also began there.
#: A click lands on the element that holds both ends of the press, so a drag
#: that selects text in the panel and lets go over the scrim is a click on
#: the scrim too, and closing would throw away whatever was being selected.
#: The press is kept on the element rather than in an x-data of its own,
#: which would become the scope the panel's x-refs register on.
DISMISS_ON_SCRIM = {
    "x-on:pointerdown": "$el.huePressed = $event.target === $el",
    "x-on:click.self": "if ($el.huePressed) close()",
}


def overlay_state(starts_open: bool = False, *, return_to: str | None = None) -> str:
    """
    The x-data an overlay carries.

    close() rather than a bare assignment, so the actions inside have a way
    out to call that is not the state's shape. return_to is the expression
    wire_trigger returned, for an overlay whose focus close() has to put back
    by hand. A modal's focus trap does that on its own, except for one the
    server started open, which had nothing to return to. The focus waits a
    tick, so a trap still holding the page has let go and the trigger is no
    longer inert.
    """
    refocus = f"; setTimeout(() => {return_to}?.focus())" if return_to else ""
    return (
        f"{{ open: {str(starts_open).lower()}, "
        f"close() {{ this.open = false{refocus} }} }}"
    )


def accessible_name(
    kind: str,
    title: str | None,
    label: str | None,
    *,
    title_id: str = TITLE_ID,
) -> dict[str, str]:
    """
    The attribute that names the panel: its title where it has one, the
    label otherwise. A Popover mints its own title id, so it passes that.

    A modal that announces itself as "dialog" and nothing else leaves a
    screen reader user inside something they cannot identify, so having
    neither is an error rather than a panel rendered without a name.
    """
    if title is not None:
        return {":aria-labelledby": title_id}
    if label is None:
        raise ValueError(
            f"A {kind} needs an accessible name; give it a title(), or a "
            "label() when it has no visible heading."
        )
    return {"aria-label": label}


def overlay_root(state: str) -> dict[str, str]:
    """
    The attributes every overlay's root carries: its state, and Escape
    closing it. state is overlay_state(), or a bundled component's own for
    an overlay with more to it.
    """
    return {"x-data": state, **CLOSE_ON_ESCAPE}


#: What wire_trigger hands back for a control it has marked.
TRIGGER = "$root.querySelector('[data-hue-trigger]')"


def wire_trigger(
    trigger: ChainableComponent | None,
    *,
    popup: str,
    on: dict[str, str],
    bind: dict[str, str] | None = None,
) -> str:
    """
    Put an overlay's listeners and state on the control that opens it, and
    return the expression that finds that control again from inside.

    Listeners go on as x-on rather than @, and bindings as x-bind rather
    than :, so a handler or a binding the control already has through
    on_click or x_bind stays beside them instead of being overwritten under
    the same key. The control is the trigger's own, which for a Tooltip is
    the control it labels rather than the span it wraps it in.

    The way back is a query rather than x-ref, because a ref registers on the
    nearest x-data, and a control wrapped in a Tooltip sits inside the
    tooltip's. The control renders before the panel, so the first mark under
    the overlay's root is its own. With no control there is no mark of its
    own, and the first one would belong to an overlay nested in the content,
    so the expression is null instead.
    """
    control = trigger._trigger_control() if trigger is not None else None
    if control is None:
        return "null"

    for event, expression in on.items():
        control._attrs[f"x-on:{event}"] = expression
    for attr, expression in {"aria-expanded": "open", **(bind or {})}.items():
        control._attrs[f"x-bind:{attr}"] = expression
    control._attrs.setdefault("aria_haspopup", popup)
    control._attrs["data-hue-trigger"] = ""
    return TRIGGER
