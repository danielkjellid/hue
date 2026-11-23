"""
The modal dialog as parts.

    DialogRoot().content(
        DialogTrigger().content(Button().content("Invite")),
        DialogScrim().content(
            DialogPanel().content(
                DialogTitle().content("Invite people"),
                DialogDescription().content("They will get a join link."),
                DialogClose().aria_label("Close").content(HueIcon("x")),
            ),
        ),
    )

The root holds the open state, closes on Escape and scopes the ids the title
and the description take. Every other part reads the root's state from the
context, so the panel knows whether a title names it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from htmy import Context, html
from htmy.core import Tag
from typing_extensions import Self

from hue.base import ChainableComponent
from hue.headless._overlay import (
    DESCRIPTION_ID,
    DISMISS_ON_SCRIM,
    HOLDS_FOCUS,
    OVERLAY_IDS,
    TITLE_ID,
    TRIGGER,
    accessible_name,
    overlay_root,
    overlay_state,
    wire_trigger,
)
from hue.headless.part import Part
from hue.types.core import Component, ComponentType


@dataclass(frozen=True, slots=True)
class DialogState:
    """
    What a dialog's parts need to know about the dialog they are in.
    """

    titled: bool = False
    described: bool = False
    dismissible: bool = True
    destructive: bool = False


class DialogRoot(Part):
    """
    The scope a dialog's parts share: whether it is open, and Escape closing
    it. A hue:open event on it opens it from anywhere on the page.

    destructive() makes the panel an alertdialog, for a question whose wrong
    answer cannot be undone. dismissible(False) leaves the scrim inert to a
    click, and Escape still closes it.
    """

    def open(self, value: bool = True) -> Self:
        """
        Start it open, for a dialog the server decided to show.
        """
        self._props["open"] = value
        return self

    def dismissible(self, value: bool = True) -> Self:
        self._props["dismissible"] = value
        return self

    def destructive(self, value: bool = True) -> Self:
        self._props["destructive"] = value
        return self

    def htmy_context(self) -> Context:
        return {
            DialogState: DialogState(
                titled=_has(self._children, DialogTitle),
                described=_has(self._children, DialogDescription),
                dismissible=self._get_prop("dismissible", True),
                destructive=self._get_prop("destructive", False),
            )
        }

    def _render(self, context: Context) -> Component:
        self._refuse_x_data()
        # Opened by its trigger, the focus trap hands focus back on close.
        # Started open by the server there was nothing to hand back, so
        # close() sends it to the trigger instead.
        starts_open: bool = self._get_prop("open", False)
        refocus = starts_open and _has(self._children, DialogTrigger)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                **overlay_root(
                    overlay_state(starts_open, return_to=TRIGGER if refocus else None)
                ),
                **{
                    "x-id": OVERLAY_IDS,
                    # For a control outside its scope, such as a shortcut.
                    "x-on:hue:open": "open = true",
                },
            ),
        )


class DialogTrigger(Part):
    """
    The control that opens the dialog, given as its one child. It draws no
    element of its own: the dialog's listeners and expanded state go on the
    control, beside whatever handlers it already has.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, DialogState)
        match self._children:
            case (ChainableComponent() as control,):
                wire_trigger(control, popup="dialog", on={"click": "open = true"})
                return control
        raise ValueError(
            "DialogTrigger takes one hue component, the control that opens the "
            "dialog, because the dialog wires its click onto that control."
        )


class DialogScrim(Part):
    """
    The layer over the page that holds the panel, shown while the dialog is
    open. A press that begins and ends on it closes a dismissible dialog.
    """

    def _render(self, context: Context) -> Component:
        state = self._state(context, DialogState)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                **{
                    "x-show": "open",
                    "x-cloak": True,
                    **(DISMISS_ON_SCRIM if state.dismissible else {}),
                    **HOLDS_FOCUS,
                },
            ),
        )


class DialogPanel(Part):
    """
    The modal panel. A DialogTitle inside names it, and label() names a
    panel with no title; having neither raises.
    """

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _render(self, context: Context) -> Component:
        state = self._state(context, DialogState)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                role="alertdialog" if state.destructive else "dialog",
                aria_modal="true",
                **{
                    **accessible_name("Dialog", state.titled, self._get_prop("label")),
                    # Announced with the title only where the wrong answer
                    # cannot be undone; elsewhere it is read in order.
                    "x-bind:aria-describedby": (
                        DESCRIPTION_ID
                        if state.destructive and state.described
                        else None
                    ),
                    # inert takes the page behind out of the tab order,
                    # noscroll stops it scrolling under the scrim, and the
                    # trap returns focus to whatever opened it.
                    "x-trap.inert.noscroll": "open",
                },
            ),
        )


class DialogTitle(Part):
    """
    The heading that names the panel.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, DialogState)
        return html.h2(
            *self._content(), **self._wired(context, **{"x-bind:id": TITLE_ID})
        )


class DialogDescription(Part):
    """
    The sentence under the title. A destructive dialog announces it with the
    title.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, DialogState)
        return html.p(
            *self._content(), **self._wired(context, **{"x-bind:id": DESCRIPTION_ID})
        )


class DialogClose(Part):
    """
    A button that closes the dialog.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, DialogState)
        return html.button(
            *self._content(),
            **self._wired(context, type="button", **{"x-on:click": "close()"}),
        )


def _has(children: Iterable[ComponentType], part: type[Part]) -> bool:
    """
    Whether a part of this kind is among children, however deep in other
    markup, short of a dialog nested inside, whose parts are its own.
    """
    for child in children:
        if isinstance(child, part):
            return True
        if isinstance(child, DialogRoot):
            continue
        if isinstance(child, ChainableComponent) and _has(child._children, part):
            return True
        if isinstance(child, Tag) and _has(child.children, part):
            return True
    return False
