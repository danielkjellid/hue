"""
The colours that tell categories apart: a chart's series and slices, a
calendar's layers and events.

A colour reaches the page as a value, through the --hue-mark property, rather
than as a class, so an app can bring colours of its own and is not held to
the ones hue's stylesheet was built with. The six presets name hue's tokens
and follow the theme, and an app restyles them by redefining those tokens.

    from hue import palette

    BRAND = palette.Color("#e11d48", dark="#fb7185")
    Layer("eng", "Engineering", color=palette.teal)
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

# A colour is written into a style attribute, a chart's JSON and a theme's
# style element, so it is held to the characters a CSS colour is spelled
# with. A semicolon, colon, quote or brace could otherwise add a declaration
# of its own.
_SPELLING = re.compile(r"[#\w\s(),.%/+-]+")


def css_colour(value: str) -> str:
    """
    The value, once it is known to be spelled like a CSS colour.
    """
    if not _SPELLING.fullmatch(value):
        raise ValueError(f"{value!r} is not a CSS colour.")
    return value


@dataclass(frozen=True, slots=True)
class Color:
    """
    A colour for light mode, and optionally another for dark mode, each any
    CSS colour: a hex, an oklch(), a var() of the app's own token.
    """

    light: str
    dark: str | None = None

    def __post_init__(self) -> None:
        for value in (self.light, self.dark):
            if value is not None:
                css_colour(value)

    @property
    def css(self) -> str:
        # light-dark() picks by color-scheme, which the stylesheet sets with
        # the theme, so one inline value covers both.
        if self.dark is None:
            return self.light
        return f"light-dark({self.light}, {self.dark})"

    @property
    def style(self) -> str:
        """
        The inline style that hands it to the classes reading --hue-mark.
        """
        return f"--hue-mark: {self.css}"


accent = Color("var(--color-category-accent)")
teal = Color("var(--color-category-teal)")
orange = Color("var(--color-category-orange)")
purple = Color("var(--color-category-purple)")
yellow = Color("var(--color-category-yellow)")
gray = Color("var(--color-category-gray)")

# The order colours are handed out in when none is chosen. The steps vary in
# lightness as well as hue, so neighbours stay apart under colour-vision
# deficiencies, and the grey comes last because it reads as muted.
ORDER = (accent, teal, orange, purple, yellow, gray)


def assign(chosen: Sequence[Color | None], what: str) -> list[Color]:
    """
    Each chosen colour, with the ones left out filled in by position from
    ORDER. Past its six, a colour has to be chosen.
    """
    for unchosen in [i for i, color in enumerate(chosen) if color is None]:
        if unchosen >= len(ORDER):
            raise ValueError(
                f"{what}: hue picks the first {len(ORDER)} colours by position; "
                f"give the rest a color of their own."
            )
    return [color or ORDER[i] for i, color in enumerate(chosen)]
