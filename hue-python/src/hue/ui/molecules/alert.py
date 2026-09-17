from __future__ import annotations

from typing import ClassVar, Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type AlertVariant = Literal["neutral", "info", "success", "warning", "danger"]

# Fill, edge and the tone everything inside takes. The title and the
# description share that tone: the guide darkens the title a step with
# color-mix, which the -text tokens already are, so weight carries the
# hierarchy instead of a second colour per variant.
_VARIANTS: dict[AlertVariant, str] = {
    "neutral": "bg-surface-sunken border-border text-fg",
    "info": "bg-info-subtle border-info-border text-info-text",
    "success": "bg-success-subtle border-success-border text-success-text",
    "warning": "bg-warning-subtle border-warning-border text-warning-text",
    "danger": "bg-danger-subtle border-danger-border text-danger-text",
}

# What the variant is worth interrupting for. danger is assertive because it
# is the one that stops the user getting what they came for; the rest are
# polite, so they are read when the screen reader reaches a gap rather than
# over the top of whatever it is saying.
#
# Safe to have by default: a live region that exists with its content already
# in it is never announced, so a server-rendered alert is read in document
# order like any other text. The role only does anything when the alert
# arrives after the page - which is exactly when it should.
_ROLES: dict[AlertVariant, str] = {
    "neutral": "status",
    "info": "status",
    "success": "status",
    "warning": "status",
    "danger": "alert",
}

_ICONS: dict[AlertVariant, str] = {
    "neutral": "circle-info",
    "info": "circle-info",
    "success": "circle-check",
    "warning": "triangle-alert",
    "danger": "circle-x",
}

# A ghost button inside an alert takes the alert's tone rather than its own
# near-black, and veils its own background instead of dropping an opaque grey
# patch on a coloured surface. Always black, in both themes: the label is dark
# on light and light on dark, so darkening is the one direction that raises
# contrast either way.
#
# Scoped to the ghosts. Applied to every button it repaints a solid one's
# label in the alert's tone as well - pale pink on a pink fill, which is the
# contrast failure the rule exists to prevent, caused by the rule.
#
# The state goes inside the selector rather than in front of it: a hover
# stacked onto an arbitrary variant emits nothing at all, silently.
# Written out rather than built from a shared prefix: Tailwind finds a class
# by scanning source text, so one assembled from an f-string is one it never
# sees - and emits nothing, with no error to say so.
_ACTIONS = (
    "mt-3 flex flex-wrap items-center gap-2 "
    "[&_[data-variant=ghost]]:text-current "
    "[&_[data-variant=ghost]:hover]:bg-black/6 "
    "[&_[data-variant=ghost]:active]:bg-black/10 "
    "dark:[&_[data-variant=ghost]:hover]:bg-black/24 "
    "dark:[&_[data-variant=ghost]:active]:bg-black/36"
)


class Alert(ChainableComponent):
    """
    A message about the thing it sits next to.

    variant() sets the tone, picks the icon, and decides how loudly it is
    announced when it arrives: danger interrupts, the rest wait for a gap.
    content() is whatever goes under the title - a sentence, or a row with
    something in it - and actions() the buttons under that.

        Alert().variant("danger").title("Payment failed").content("Try again later.")
    """

    category = "Feedback"

    #: Whether the box runs to the edges of whatever holds it. Banner is the
    #: one that does; it is a class attribute rather than a modifier because
    #: it is what the two of them are, not something either can be talked out
    #: of halfway down a chain.
    edge_to_edge: ClassVar[bool] = False

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("info")
            .title("Scheduled maintenance")
            .content("The API is read-only on Sunday between 02:00 and 04:00 UTC.")
        )

    def variant(self, value: AlertVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        """
        An icon of your own, in place of the one the variant picks.
        """
        self._props["icon"] = value
        return self

    def actions(self, *values: ComponentType) -> Self:
        self._props["actions"] = values
        return self

    def dismissible(self, value: bool = True) -> Self:
        """
        Add a close button that removes the alert.
        """
        self._props["dismissible"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: AlertVariant = self._get_prop("variant", "neutral")
        title: str | None = self._get_prop("title")
        actions: tuple[ComponentType, ...] = self._get_prop("actions", ())
        dismissible: bool = self._get_prop("dismissible", False)

        body = html.div(
            render_if(
                title,
                lambda text: html.div(
                    text,
                    # A step louder than the description below it, so the two
                    # are not one block of the same colour.
                    class_="font-ui text-base font-bold leading-[1.4] text-stronger",
                ),
            ),
            html.div(
                *self._children,
                class_=classnames(
                    "max-w-[68ch] text-sm leading-[1.5]",
                    # Neutral has no tone of its own to inherit.
                    "text-fg-muted" if variant == "neutral" else None,
                ),
            )
            if self._children
            else UNDEFINED,
            html.div(*actions, class_=_ACTIONS) if actions else UNDEFINED,
            class_="flex min-w-0 flex-1 flex-col gap-0.5",
        )

        close = html.button(
            HueIcon("x").class_("size-4"),
            type="button",
            aria_label="Dismiss",
            class_=classnames(
                "-mt-0.5 -me-1 grid size-6 flex-none place-content-center",
                "cursor-pointer rounded-sm text-current",
                "hover:bg-black/6 dark:hover:bg-black/24",
                FOCUS_RING,
            ),
            **{"x-on:click": "shown = false"},
        )

        alert = html.div(
            render_if(
                self._get_prop("icon", HueIcon(_ICONS[variant])),
                lambda icon: html.span(
                    icon,
                    aria_hidden="true",
                    # 2px, which is neither what the arithmetic asks for nor
                    # what the guide says. Centring the disc on the title's
                    # cap band puts it at 1px, but a 16px disc beside a 10px
                    # cap height reads heavy there; sitting it on the cap line
                    # at 4px drops it too far. flex, or the svg aligns to the
                    # text baseline of its own span and none of this applies.
                    class_="mt-0.5 flex flex-none [&_svg]:size-4",
                ),
            ),
            body,
            close if dismissible else UNDEFINED,
            class_=classnames(
                "flex items-start gap-3 border px-4 py-3 text-base",
                "rounded-none border-x-0" if self.edge_to_edge else "rounded-md",
                _VARIANTS[variant],
                self._get_prop("class_"),
            ),
            **{
                "role": _ROLES[variant],
                # After, so a caller who knows better can say so.
                **self._get_base_html_attrs(),
            },
        )

        if not dismissible:
            return alert
        return html.div(alert, **{"x-data": "{ shown: true }", "x-show": "shown"})


class Banner(Alert):
    """
    An alert about the whole page, run edge to edge across the top of it.

    Everything an Alert has, in the shape a page-level message takes: squared
    off, with no side borders, so it reads as part of the frame rather than as
    something sitting inside the content.

        Banner().variant("warning").title("Your trial ends on Friday")
    """

    category = "Feedback"

    edge_to_edge: ClassVar[bool] = True

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("info")
            .title("Scheduled maintenance on Sunday")
            .content("The API is read-only between 02:00 and 04:00 UTC.")
        )
