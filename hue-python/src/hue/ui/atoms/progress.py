from __future__ import annotations

import math
from typing import Literal

from htmy import Context, SafeStr, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

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
# The round caps reach half the 5px stroke past each end of the arc, which
# closes a small gap. Short of 100 the arc is scaled into what is left after
# both caps and a 3px gap, so 99% still looks unfinished.
_RING_OPEN_ARC = _RING_CIRCUMFERENCE - 5 - 3


def _whole(value: float) -> str:
    # Rounded down, so nothing short of done reads as 100, and short enough
    # to fit inside a ring.
    return f"{math.floor(value)}"


def _clamp(value: float) -> float:
    # min(100, nan) is 100, so a NaN would otherwise report itself complete.
    if math.isnan(value):
        raise ValueError("A progress value must be a number, not NaN.")
    return max(0.0, min(100.0, value))


class Progress(ChainableComponent):
    """
    How far along something is, as a horizontal bar.

    indeterminate() is for work whose length is unknown: the bar sweeps and
    omits aria-valuenow rather than reporting zero. label() names the bar and
    is required, since a progressbar with no name is announced as nothing more
    than a percentage; hidden_label() keeps the name off the screen.

        Progress().value(64).label("Uploading archive.zip")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().value(64).label("Uploading archive.zip")

    def value(self, value: float) -> Self:
        """
        Percent complete.
        """
        self._props["value"] = value
        return self

    def indeterminate(self, value: bool = True) -> Self:
        """
        Sweep the bar instead of filling it, for work whose length is unknown.

        Wins over value(), so a bar can be handed a stale percentage and still
        say it no longer knows one.
        """
        self._props["indeterminate"] = value
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

    def hidden_label(self, value: bool = True) -> Self:
        """
        Keep the label as the bar's name but take it, and the percentage
        beside it, off the screen, for a bar whose purpose is obvious from
        where it sits.
        """
        self._props["hidden_label"] = value
        return self

    def _render(self, context: Context) -> Component:
        variant: ProgressVariant = self._get_prop("variant", "accent")
        size: ProgressSize = self._get_prop("size", "md")
        label: str | None = (self._get_prop("label") or "").strip() or None
        hidden_label: bool = self._get_prop("hidden_label", False)
        raw: float | None = self._get_prop("value")
        indeterminate: bool = self._get_prop("indeterminate", False)
        value = None if indeterminate or raw is None else _clamp(raw)

        if label is None:
            raise ValueError(
                "Progress needs a label() to name it; add hidden_label() to "
                "keep it off the screen."
            )

        fill = html.div(
            class_=classnames(
                "h-full rounded-[inherit]",
                _VARIANT_CLASSES[variant],
                # Indeterminate: a short bar sweeping the track, since there is
                # no width to animate to. With motion reduced the sweep stops,
                # and a still 40% bar would read as 40% done, so it fills the
                # track faintly instead.
                "w-[40%] animate-progress motion-reduce:w-full "
                "motion-reduce:animate-none motion-reduce:opacity-40"
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
                # A bare bar has no wrapper, so the caller's classes land here.
                self._get_prop("class_") if hidden_label else None,
            ),
            **{
                "role": "progressbar",
                "aria_valuemin": "0",
                "aria_valuemax": "100",
                # Omitted entirely when indeterminate: aria-valuenow="0" would
                # announce "0 percent", which reads as stalled rather than
                # unknown.
                "aria_valuenow": None if value is None else f"{value:.15g}",
                # A screen reader rounds valuenow to the nearest percent, so
                # it is given the readout, which never says 100 short of done.
                "aria_valuetext": None if value is None else f"{_whole(value)}%",
                "aria_label": label,
                **self._get_base_html_attrs(),
            },
        )

        if hidden_label:
            return track

        return html.div(
            html.div(
                html.span(label),
                render_if(
                    None if value is None else f"{_whole(value)}%",
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

    show_value() prints the percentage in the middle, for a ring that stands on
    its own. It is announced as an image stating the percentage either way,
    because a bare circle tells a screen reader nothing.

        ProgressRing().value(64).label("Storage used")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().value(64).show_value().label("Storage used")

    def value(self, value: float) -> Self:
        self._props["value"] = value
        return self

    def variant(self, value: ProgressVariant) -> Self:
        self._props["variant"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def show_value(self, value: bool = True) -> Self:
        """
        Print the percentage in the middle of the ring.

        Worth it wherever the ring is the only thing there; a ring already sat
        beside the figure it stands for would just say it twice.
        """
        self._props["show_value"] = value
        return self

    def _render(self, context: Context) -> Component:
        variant: ProgressVariant = self._get_prop("variant", "accent")
        label: str | None = (self._get_prop("label") or "").strip() or None
        show_value: bool = self._get_prop("show_value", False)
        value = _clamp(self._get_prop("value", 0))

        described = f"{_whole(value)} percent complete"
        if label is not None:
            described = f"{label}, {described}"

        arc = _RING_CIRCUMFERENCE if value == 100 else _RING_OPEN_ARC * value / 100
        offset = _RING_CIRCUMFERENCE - arc
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

        ring = html.svg(
            SafeStr(circles),
            width=_RING_SIZE,
            height=_RING_SIZE,
            # Drawn from twelve o'clock rather than three.
            class_="-rotate-90",
            role="img",
            aria_label=described,
        )

        # The readout sits over the ring rather than inside the svg, which is
        # rotated a quarter turn and would lay the figure on its side. It is
        # hidden from assistive tech because the svg above already says it.
        return html.span(
            ring,
            render_when(
                show_value,
                html.span(
                    f"{_whole(value)}%",
                    class_=classnames(
                        "absolute inset-0 flex items-center justify-center",
                        "font-ui text-2xs font-semibold tabular-nums text-fg",
                    ),
                    aria_hidden="true",
                ),
            ),
            class_=classnames("relative inline-flex", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )
