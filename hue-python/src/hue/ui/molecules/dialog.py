from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

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
    "w-full max-h-[85vh] rounded-t-xl border-t animate-sheet-in "
    "sm:max-h-[calc(100vh-4rem)] sm:rounded-xl sm:border sm:animate-dialog-in"
)


class Dialog(ChainableComponent):
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

    def _render(self, context: HueContext) -> Component:
        size: DialogSize = self._get_prop("size", "md")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        footer: tuple[ComponentType, ...] = self._get_prop("footer", ())
        trigger: ChainableComponent | None = self._get_prop("trigger")
        dismissible: bool = self._get_prop("dismissible", True)
        destructive: bool = self._get_prop("destructive", False)
        starts_open: bool = self._get_prop("open", False)

        if trigger is not None:
            trigger.x_on("click", "open = true").x_bind("aria-expanded", "open")
            trigger._attrs.setdefault("aria_haspopup", "dialog")

        title_id = "$id('hue-dialog-title')"
        description_id = "$id('hue-dialog-description')"

        heading = html.div(
            render_if(
                title,
                lambda text: html.h2(
                    text,
                    class_="font-ui text-lg font-bold leading-[1.3] "
                    "tracking-[-0.015em] text-fg",
                    **{":id": title_id},
                ),
            ),
            render_if(
                description,
                lambda text: html.p(
                    text,
                    class_="mt-1 text-sm leading-[1.55] text-fg-muted",
                    **{":id": description_id},
                ),
            ),
            class_="min-w-0 flex-1",
        )

        close = html.button(
            HueIcon("x").class_("size-4"),
            type="button",
            aria_label="Close",
            class_=classnames(
                "grid size-7 flex-none place-content-center rounded-sm",
                "cursor-pointer text-fg-subtle hover:bg-surface-hover hover:text-fg",
                FOCUS_RING,
            ),
            **{"x-on:click": "close()"},
        )

        panel = html.div(
            html.div(
                aria_hidden="true",
                class_="mx-auto mt-3 mb-1 h-1 w-9 flex-none rounded-full "
                "bg-border-strong sm:hidden",
            ),
            # The header is there when there is anything to put in it.
            render_when(
                bool(title or description or dismissible),
                html.div(
                    heading,
                    render_when(dismissible, close),
                    class_="flex items-start gap-4 px-5 pt-5 pb-3",
                ),
            ),
            render_when(
                bool(self._children),
                # min-h-0 is what lets this scroll rather than pushing the
                # footer out of the clipped panel.
                html.div(
                    *self._children,
                    class_="min-h-0 flex-1 overflow-y-auto px-5 pb-5 text-base",
                ),
            ),
            render_when(
                bool(footer),
                html.div(
                    *footer,
                    # On a phone the strip is the bottom edge of the screen,
                    # so its buttons clear the home indicator. The max() is
                    # py-4 everywhere the inset is zero.
                    class_="flex items-center justify-end gap-2 border-t "
                    "border-border bg-surface-sunken px-5 pt-4 "
                    "pb-[max(1rem,env(safe-area-inset-bottom))]",
                ),
            ),
            class_=classnames(
                "relative flex flex-col overflow-hidden",
                "border-border bg-surface-raised shadow-overlay",
                _SHEET,
                _SIZES[size],
            ),
            **{
                "role": "alertdialog" if destructive else "dialog",
                "aria_modal": "true",
                ":aria-labelledby": title_id if title is not None else None,
                # Announced with the title only where the wrong answer cannot
                # be undone; elsewhere it is read in order like any other text.
                ":aria-describedby": (
                    description_id if destructive and description else None
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
                class_="fixed inset-0 z-80 flex items-end justify-center "
                "bg-scrim backdrop-blur-[2px] sm:items-center sm:p-4",
                **{
                    "x-show": "open",
                    "x-cloak": True,
                    "x-transition.opacity": "",
                    **({"x-on:click.self": "close()"} if dismissible else {}),
                },
            ),
            class_=self._get_prop("class_"),
            **{
                # close() rather than a bare assignment, so the actions in the
                # footer have a way out to call that is not the state's shape.
                "x-data": f"{{ open: {str(starts_open).lower()}, "
                "close() { this.open = false } }",
                "x-id": "['hue-dialog-title', 'hue-dialog-description']",
                # Escape always closes, dismissible or not: a modal with no
                # way out is a trap, whatever the question was.
                "x-on:keydown.escape.window": "close()",
                **self._get_base_html_attrs(),
            },
        )
