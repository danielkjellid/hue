from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _overlay
from hue.utils import classnames, render_if

type DialogSize = Literal["sm", "md", "lg"]

# A width is something only the centred dialog has: below sm the panel is a
# sheet the width of the screen. Capped against the viewport as well as set,
# so it keeps a margin rather than running under the edges.
_SIZES: dict[DialogSize, str] = {
    "sm": "sm:w-[min(380px,calc(100vw-2rem))]",
    "md": "sm:w-[min(480px,calc(100vw-2rem))]",
    "lg": "sm:w-[min(640px,calc(100vw-2rem))]",
}

# On a phone a box floating in the middle of the screen is a worse drawer -
# the thumb is at the bottom edge and the box is not. Below sm the panel is
# the drawer's bottom sheet: docked to that edge, full width, its top corners
# rounded and only its top edge drawn, coming up from the edge it sits on.
_SHEET = (
    "w-full max-h-[85vh] rounded-t-xl border-t "
    "animate-sheet-in group-[.leaving]:animate-sheet-out "
    "sm:max-h-[calc(100vh-4rem)] sm:rounded-xl sm:border "
    "sm:animate-dialog-in sm:group-[.leaving]:animate-dialog-out"
)


class Dialog(_overlay.WrapsTrigger):
    """
    A window over the page that has to be dealt with before anything else.

    trigger() opens it and open() starts it open. Focus is trapped inside
    while it is up and returns to the trigger when it closes; the page behind
    cannot be scrolled or tabbed into. destructive() makes it an alertdialog,
    for a question whose wrong answer cannot be undone. Below sm it docks to
    the bottom edge as a sheet.

        Dialog().title("Delete project").trigger(Button().content("Delete"))
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .title("Invite teammates")
            .description("They will get an email with a join link.")
            .trigger(Button().content("Invite"))
            .footer(
                Button().variant("ghost").content("Cancel"),
                Button().content("Send invites"),
            )
        )

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def label(self, value: str) -> Self:
        """
        The panel's accessible name, for a dialog with no title to be named by.
        """
        self._props["label"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def size(self, value: DialogSize) -> Self:
        self._props["size"] = value
        return self

    def trigger(self, value: ChainableComponent) -> Self:
        """
        The control that opens it.

        A hue component rather than any markup, because the dialog wires the
        click and the expanded state onto the control itself.
        """
        self._props["trigger"] = value
        return self

    def footer(self, *values: ComponentType) -> Self:
        """
        The actions, on a tinted strip along the bottom.

        They are the way out of a dialog that cannot be dismissed, so each
        one needs something to do: x_on("click", "close()") closes it.
        """
        self._props["footer"] = values
        return self

    def dismissible(self, value: bool = True) -> Self:
        """
        Whether it can be closed without answering.

        Off also takes away the close button and the click-outside, for a
        dialog that has to be resolved one way or the other. Escape still
        works: a modal with no way out is a trap.
        """
        self._props["dismissible"] = value
        return self

    def destructive(self, value: bool = True) -> Self:
        """
        Make it an alertdialog, for a question whose wrong answer cannot be
        undone. The description is announced with the title rather than left
        for the reader to find.
        """
        self._props["destructive"] = value
        return self

    def open(self, value: bool = True) -> Self:
        """
        Start it open, for a dialog the server decided to show.
        """
        self._props["open"] = value
        return self

    def _render(self, context: Context) -> Component:
        size: DialogSize = self._get_prop("size", "md")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        footer: tuple[ComponentType, ...] = self._get_prop("footer", ())
        trigger: ChainableComponent | None = self._get_prop("trigger")
        dismissible: bool = self._get_prop("dismissible", True)
        destructive: bool = self._get_prop("destructive", False)
        starts_open: bool = self._get_prop("open", False)

        find_trigger = _overlay.wire_trigger(
            trigger, popup="dialog", on={"click": "open = true"}
        )

        panel = html.div(
            _overlay.grabber("sm:hidden"),
            _overlay.header(title, description, dismissible=dismissible),
            _overlay.body(self._children),
            _overlay.footer(footer),
            class_=classnames(
                "relative flex flex-col overflow-hidden",
                "border-border bg-surface-raised shadow-overlay",
                _SHEET,
                _SIZES[size],
            ),
            **{
                "role": "alertdialog" if destructive else "dialog",
                "aria_modal": "true",
                **_overlay.accessible_name("Dialog", title, self._get_prop("label")),
                # Announced with the title only where the wrong answer cannot
                # be undone; elsewhere it is read in order like any other text.
                ":aria-describedby": (
                    _overlay.DESCRIPTION_ID if destructive and description else None
                ),
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
                class_=classnames(
                    _overlay.SCRIM,
                    "items-end justify-center sm:items-center sm:p-4",
                ),
                **{
                    "x-show": "open",
                    "x-cloak": True,
                    "x-transition:enter": "transition-opacity duration-[180ms]",
                    "x-transition:enter-start": "opacity-0",
                    # The panel's own way out runs while this class is on,
                    # which is the only thing timing the pair.
                    "x-transition:leave": _overlay.LEAVING,
                    "x-transition:leave-end": "opacity-0",
                    **(_overlay.DISMISS_ON_SCRIM if dismissible else {}),
                    **_overlay.HOLDS_FOCUS,
                },
            ),
            class_=self._get_prop("class_"),
            **{
                # Escape always closes, dismissible or not: a modal with no
                # way out is a trap, whatever the question was.
                # Opened by its trigger, the focus trap hands focus back on
                # close. Started open by the server, there was nothing to hand
                # back, so close() sends it to the trigger instead.
                **_overlay.overlay_root(
                    _overlay.overlay_state(
                        starts_open, return_to=find_trigger if starts_open else None
                    )
                ),
                "x-id": _overlay.OVERLAY_IDS,
                **self._get_base_html_attrs(),
            },
        )
