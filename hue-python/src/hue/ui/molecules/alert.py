from __future__ import annotations

from typing import Literal

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
_ACTIONS = (
    "mt-3 flex gap-2 [&_button]:text-current "
    "[&_button:hover]:bg-black/6 [&_button:active]:bg-black/10 "
    "dark:[&_button:hover]:bg-black/24 dark:[&_button:active]:bg-black/36"
)


class Alert(ChainableComponent):
    """
    A message about the thing it sits next to.

    variant() sets the tone, picks the icon, and decides how loudly it is
    announced when it arrives: danger interrupts, the rest wait for a gap.

        Alert().variant("danger").title("Payment failed")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("info")
            .title("Scheduled maintenance")
            .description("The API is read-only on Sunday between 02:00 and 04:00 UTC.")
        )

    def variant(self, value: AlertVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
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

    def banner(self, value: bool = True) -> Self:
        """
        Square it off and run it edge to edge, for a message about the whole
        page rather than about one thing on it.
        """
        self._props["banner"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: AlertVariant = self._get_prop("variant", "neutral")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        actions: tuple[ComponentType, ...] = self._get_prop("actions", ())
        dismissible: bool = self._get_prop("dismissible", False)
        banner: bool = self._get_prop("banner", False)

        body = html.div(
            render_if(
                title,
                lambda text: html.div(
                    text, class_="font-ui text-base font-bold leading-[1.4]"
                ),
            ),
            render_if(
                description,
                lambda text: html.div(
                    text,
                    class_=classnames(
                        "max-w-[68ch] text-sm leading-[1.5]",
                        # Neutral has no tone of its own to inherit.
                        "text-fg-muted" if variant == "neutral" else None,
                    ),
                ),
            ),
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
                    icon, aria_hidden="true", class_="mt-px flex-none [&_svg]:size-4"
                ),
            ),
            body,
            close if dismissible else UNDEFINED,
            class_=classnames(
                "flex items-start gap-3 border px-4 py-3 text-base",
                "rounded-none border-x-0" if banner else "rounded-md",
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
