from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type SkeletonShape = Literal["line", "circle", "rect"]

# The pulse is purely decorative motion; motion-reduce drops it for users who
# ask for reduced motion, leaving a static placeholder.
_PULSE = "animate-pulse bg-surface-200 motion-reduce:animate-none"

# Per-shape (height, width, rounded) defaults; width/height/rounded modifiers
# override any piece. Circle leaves width empty so a single size-* class sizes it.
_SHAPE_DEFAULTS: dict[SkeletonShape, tuple[str, str, str]] = {
    "line": ("h-4", "w-full", "rounded-md"),
    "circle": ("size-10", "", "rounded-full"),
    "rect": ("h-24", "w-full", "rounded-lg"),
}


class Skeleton(ChainableComponent):
    """
    A pulsing placeholder shape shown in place of content that hasn't loaded.

    Pick a shape — a text line, a circle for avatars, or a rect for images and
    cards — and optionally override its width, height, or corner rounding with
    Tailwind utility classes. Calling lines() renders a stacked paragraph of
    text lines with the last one shortened, so it reads as prose.

        Skeleton().shape("line").lines(3)

    The shape is decorative and always marked aria-hidden; the surrounding
    loading region (see the defer helper) is what announces busy state to
    assistive tech.

    One nuance on the dimension overrides: hue ships a prebuilt stylesheet, so
    only utilities hue itself uses are guaranteed to have CSS behind them. A
    class outside that set needs the app's own Tailwind build (see the Django
    CSS guide) or it renders unstyled.
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        """A representative instance, used by the docs site for previews."""
        return cls().shape("line").lines(3)

    def shape(self, value: SkeletonShape) -> Self:
        self._props["shape"] = value
        return self

    def width(self, value: str) -> Self:
        """Tailwind width class, e.g. w-32 or w-3/4."""
        self._props["width"] = value
        return self

    def height(self, value: str) -> Self:
        """Tailwind height class, e.g. h-8."""
        self._props["height"] = value
        return self

    def rounded(self, value: str) -> Self:
        """Tailwind corner class, e.g. rounded-lg or rounded-full."""
        self._props["rounded"] = value
        return self

    def lines(self, value: int) -> Self:
        """Render this many stacked text lines (only meaningful for line shape)."""
        self._props["lines"] = value
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, context: HueContext) -> Component:
        shape: SkeletonShape = self._get_prop("shape", "line")
        lines: int = self._get_prop("lines", 1)
        width: str | None = self._get_prop("width")
        height: str | None = self._get_prop("height")
        rounded: str | None = self._get_prop("rounded")

        attrs = self._get_base_html_attrs()
        attrs.setdefault("aria_hidden", "true")

        # A paragraph of lines: stack them and taper the last to read as text.
        if lines > 1:
            line_height = height or "h-4"
            # width sizes the paragraph block; the bars fill it, except the last.
            bars = [
                html.div(
                    class_=classnames(
                        _PULSE,
                        rounded or "rounded-md",
                        line_height,
                        "w-3/4" if is_last else "w-full",
                    )
                )
                for is_last in (i == lines - 1 for i in range(lines))
            ]
            return html.div(
                *bars,
                class_=classnames(
                    "flex flex-col gap-2",
                    width or "w-full",
                    self._get_prop("class_"),
                ),
                **attrs,
            )

        # .get rather than [shape]: shape is a typed Literal, but an untyped
        # call site shouldn't get a KeyError instead of a placeholder.
        default_height, default_width, default_rounded = _SHAPE_DEFAULTS.get(
            shape, _SHAPE_DEFAULTS["line"]
        )
        classes = classnames(
            _PULSE,
            rounded if rounded is not None else default_rounded,
            height if height is not None else default_height,
            width if width is not None else default_width,
            self._get_prop("class_"),
        )
        return html.div(class_=classes, **attrs)
