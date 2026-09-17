from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _overlay
from hue.utils import classnames, render_if

type DrawerSide = Literal["end", "start", "bottom"]
type DrawerSize = Literal["sm", "md", "lg"]

# Which edge the panel is pinned to, from md up. Below that every drawer is
# the bottom sheet the panel already is: a 420px panel on a 375px screen is a
# dialog with a worse animation.
_SIDES: dict[DrawerSide, str] = {
    "end": "md:items-stretch md:justify-end",
    "start": "md:items-stretch md:justify-start",
    "bottom": "",
}

# The corners that face the page are rounded; the ones against the edge of
# the screen are not, since there is nothing behind them to round away from.
_PANELS: dict[DrawerSide, str] = {
    "end": "md:h-full md:max-h-full md:rounded-s-xl md:rounded-e-none "
    "md:border-t-0 md:border-s md:animate-drawer-end",
    "start": "md:h-full md:max-h-full md:rounded-e-xl md:rounded-s-none "
    "md:border-t-0 md:border-e md:animate-drawer-start",
    "bottom": "",
}

# How wide a side drawer is. A bottom sheet is the width of the screen.
_SIZES: dict[DrawerSize, str] = {
    "sm": "md:w-[min(320px,100vw)]",
    "md": "md:w-[min(420px,100vw)]",
    "lg": "md:w-[min(560px,100vw)]",
}


class Drawer(ChainableComponent):
    """
    A dialog that slides in from an edge, for a list or a form long enough
    that a centred box would be cramped.

    side() is logical - end and start land on the right edge and the left one
    in a left-to-right page, and swap in a right-to-left one. Below md every
    drawer is a bottom sheet. Focus is trapped inside while it is up and
    returns to the trigger when it closes.
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .title("Filters")
            .description("3 filters applied, 148 of 2,481 records")
            .trigger(Button().variant("outline").content("Open filters"))
            .footer(
                Button().variant("ghost").content("Reset all"),
                Button().content("Show 148 records"),
            )
        )

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def side(self, value: DrawerSide) -> Self:
        """
        The edge it arrives from, from md up. Below that it is always the
        bottom sheet, which is the native idiom on a phone.
        """
        self._props["side"] = value
        return self

    def size(self, value: DrawerSize) -> Self:
        """
        How wide a side drawer is. A bottom sheet is the width of the screen.
        """
        self._props["size"] = value
        return self

    def trigger(self, value: ChainableComponent) -> Self:
        """
        The control that opens it.

        A hue component rather than any markup, because the drawer wires the
        click and the expanded state onto the control itself.
        """
        self._props["trigger"] = value
        return self

    def footer(self, *values: ComponentType) -> Self:
        """
        The actions, on a tinted strip along the bottom.

        They are the way out of a drawer that cannot be dismissed, so each
        one needs something to do: x_on("click", "close()") closes it.
        """
        self._props["footer"] = values
        return self

    def dismissible(self, value: bool = True) -> Self:
        """
        Whether it can be closed without answering.

        Off also takes away the close button and the click-outside. Escape
        still works: a modal with no way out is a trap.
        """
        self._props["dismissible"] = value
        return self

    def open(self, value: bool = True) -> Self:
        """
        Start it open, for a drawer the server decided to show.
        """
        self._props["open"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        side: DrawerSide = self._get_prop("side", "end")
        size: DrawerSize = self._get_prop("size", "md")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        footer: tuple[ComponentType, ...] = self._get_prop("footer", ())
        trigger: ChainableComponent | None = self._get_prop("trigger")
        dismissible: bool = self._get_prop("dismissible", True)
        starts_open: bool = self._get_prop("open", False)

        if trigger is not None:
            _overlay.open_on_click(trigger)

        panel = html.aside(
            # The grabber belongs to the sheet, so a side drawer loses it at
            # the width where it stops being one.
            _overlay.grabber("md:hidden" if side != "bottom" else ""),
            _overlay.header(title, description, dismissible=dismissible),
            _overlay.body(self._children),
            _overlay.footer(footer),
            class_=classnames(
                "relative flex w-full max-h-[85vh] flex-col overflow-hidden",
                "rounded-t-xl border-t border-border bg-surface-raised",
                "shadow-overlay animate-sheet-in",
                _PANELS[side],
                _SIZES[size] if side != "bottom" else "",
            ),
            **{
                "role": "dialog",
                "aria_modal": "true",
                ":aria-labelledby": _overlay.TITLE_ID if title is not None else None,
                # inert takes the page behind out of the tab order, noscroll
                # stops it scrolling under the scrim, and the trap returns
                # focus to whatever opened it.
                "x-trap.inert.noscroll": "open",
            },
        )

        return html.div(
            render_if(trigger, lambda control: control),
            html.div(
                panel,
                class_=classnames(_overlay.SCRIM, "items-end", _SIDES[side]),
                **{
                    "x-show": "open",
                    "x-cloak": True,
                    "x-transition.opacity": "",
                    **({"x-on:click.self": "close()"} if dismissible else {}),
                },
            ),
            class_=self._get_prop("class_"),
            **{
                "x-data": _overlay.overlay_state(starts_open),
                "x-id": _overlay.OVERLAY_IDS,
                # Escape always closes, dismissible or not: a modal with no
                # way out is a trap, whatever the question was.
                "x-on:keydown.escape.window": "close()",
                **self._get_base_html_attrs(),
            },
        )
