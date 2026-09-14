from __future__ import annotations

import math
from typing import Literal

from htmy import SafeStr, html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type ProgressVariant = Literal["accent", "success", "warning", "danger"]
type ProgressSize = Literal["sm", "md", "lg"]

_VARIANT_CLASSES: dict[ProgressVariant, str] = {
    "accent": "bg-accent",
    "success": "bg-success",
    "warning": "bg-warning",
    "danger": "bg-danger",
}

_TRACK_CLASSES: dict[ProgressSize, str] = {"sm": "h-1", "md": "h-1.5", "lg": "h-2.5"}

# Spelled out rather than derived from the fill classes: Tailwind scans source
# text, so a class name built at runtime is one it never sees and never emits.
_RING_CLASSES: dict[ProgressVariant, str] = {
    "accent": "stroke-accent",
    "success": "stroke-success",
    "warning": "stroke-warning",
    "danger": "stroke-danger",
}

# Ring geometry. 52px box, 21px radius, 5px stroke.
_RING_SIZE = 52
_RING_RADIUS = 21
_RING_CIRCUMFERENCE = 2 * math.pi * _RING_RADIUS


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


class Progress(ChainableComponent):
    """
    How far along something is, as a horizontal bar.

    Leave value() unset for an indeterminate bar, which omits aria-valuenow
    rather than reporting zero. label() shows above the bar and names it.

        Progress().value(64).label("Uploading archive.zip")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().value(64).label("Uploading archive.zip")

    def value(self, value: float) -> Self:
        """
        Percent complete. Left unset, the bar is indeterminate.
        """
        self._props["value"] = value
        return self

    def variant(self, value: ProgressVariant) -> Self:
        self._props["variant"] = value
        return self

    def size(self, value: ProgressSize) -> Self:
        self._props["size"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What is in progress. Shown above the bar and used as its name.
        """
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ProgressVariant = self._get_prop("variant", "accent")
        size: ProgressSize = self._get_prop("size", "md")
        label: str | None = self._get_prop("label")
        raw: float | None = self._get_prop("value")
        value = None if raw is None else _clamp(raw)

        fill = html.div(
            class_=classnames(
                "h-full rounded-[inherit]",
                _VARIANT_CLASSES[variant],
                # Indeterminate: a short bar sweeping the track, since there is
                # no width to animate to.
                "w-[40%] animate-progress"
                if value is None
                else "transition-[width] duration-260 ease-out",
            ),
            style=None if value is None else f"width:{value:g}%",
        )

        track = html.div(
            fill,
            class_=classnames(
                "relative w-full overflow-hidden rounded-full bg-border",
                _TRACK_CLASSES[size],
            ),
            **{
                "role": "progressbar",
                "aria_valuemin": "0",
                "aria_valuemax": "100",
                # Omitted entirely when indeterminate: aria-valuenow="0" would
                # announce "0 percent", which reads as stalled rather than
                # unknown.
                "aria_valuenow": None if value is None else f"{value:g}",
                "aria_label": label,
                **self._get_base_html_attrs(),
            },
        )

        if label is None:
            return track

        return html.div(
            html.div(
                html.span(label),
                render_if(
                    None if value is None else f"{value:g}%",
                    lambda text: html.span(text, class_="tabular-nums text-fg-muted"),
                ),
                class_="flex items-baseline justify-between gap-3 text-sm",
            ),
            track,
            class_=classnames("flex flex-col gap-1.5", self._get_prop("class_")),
        )


class ProgressRing(ChainableComponent):
    """
    The same as Progress, drawn as a circle.

    Announced as an image stating the percentage, because a bare circle tells a
    screen reader nothing.

        ProgressRing().value(64).label("Storage used")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().value(64).label("Storage used")

    def value(self, value: float) -> Self:
        self._props["value"] = value
        return self

    def variant(self, value: ProgressVariant) -> Self:
        self._props["variant"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ProgressVariant = self._get_prop("variant", "accent")
        label: str | None = self._get_prop("label")
        value = _clamp(self._get_prop("value", 0))

        described = f"{value:g} percent complete"
        if label is not None:
            described = f"{label}, {described}"

        offset = _RING_CIRCUMFERENCE * (1 - value / 100)
        centre = _RING_SIZE / 2
        fill_classes = classnames(
            "transition-[stroke-dashoffset] duration-260 ease-out",
            _RING_CLASSES[variant],
        )

        # htmy models no SVG children, so the two circles are built as markup.
        # Every value here is computed from numbers, never from caller text.
        circles = (
            f'<circle cx="{centre:g}" cy="{centre:g}" r="{_RING_RADIUS}" '
            f'fill="none" stroke-width="5" class="stroke-border"></circle>'
            f'<circle cx="{centre:g}" cy="{centre:g}" r="{_RING_RADIUS}" '
            f'fill="none" stroke-width="5" stroke-linecap="round" '
            f'stroke-dasharray="{_RING_CIRCUMFERENCE:.2f}" '
            f'stroke-dashoffset="{offset:.2f}" class="{fill_classes}"></circle>'
        )

        return html.svg(
            SafeStr(circles),
            width=_RING_SIZE,
            height=_RING_SIZE,
            # Drawn from twelve o'clock rather than three.
            class_=classnames("-rotate-90", self._get_prop("class_")),
            **{
                "role": "img",
                "aria_label": described,
                **self._get_base_html_attrs(),
            },
        )
