"""
A theme: the parts of hue's design tokens an app redefines, from Python.

Each tone (accent, success, warning, danger, info) is built on a ramp of
ten steps, and replacing the ramp recolours every token of that tone in both
modes. Any single token can be set as well, a colour with an optional dark
value, a font stack or a radius. What a theme leaves out keeps hue's value.

    Theme(
        accent=Ramp(["#F5F3FF", "#EDE9FE", ..., "#4C1D95"]),
        colors={"surface": Color("#FFFFFF", dark="#18181B")},
        fonts={"ui": '"Geist", sans-serif'},
    )

The page writes it as a style element after hue's stylesheet, so a stylesheet
the app adds after that still has the last word.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, get_args

from hue.palette import Color, css_colour

type ColorToken = Literal[
    "canvas",
    "canvas-subtle",
    "surface",
    "surface-raised",
    "surface-hover",
    "surface-active",
    "surface-sunken",
    "surface-inverse",
    "surface-inverse-fg",
    "scrim",
    "fg",
    "fg-strong",
    "fg-muted",
    "fg-subtle",
    "fg-disabled",
    "border",
    "border-strong",
    "border-input",
    "border-hover",
    "accent",
    "accent-hover",
    "accent-active",
    "accent-fg",
    "accent-subtle",
    "accent-subtle-hover",
    "accent-border",
    "accent-text",
    "accent-vivid",
    "success",
    "success-text",
    "success-subtle",
    "success-border",
    "success-vivid",
    "warning",
    "warning-text",
    "warning-subtle",
    "warning-border",
    "warning-vivid",
    "danger",
    "danger-hover",
    "danger-fg",
    "danger-text",
    "danger-subtle",
    "danger-border",
    "danger-vivid",
    "info",
    "info-text",
    "info-subtle",
    "info-border",
    "info-vivid",
    "category-accent",
    "category-teal",
    "category-orange",
    "category-purple",
    "category-yellow",
    "category-gray",
]
type FontToken = Literal["ui", "body", "mono"]
type RadiusToken = Literal["xs", "sm", "md", "lg", "xl"]

TONES = ("accent", "success", "warning", "danger", "info")
STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900)

# Written into a style element, so held to what a font stack and a length are
# spelled with: no semicolon, brace or angle bracket to end the declaration,
# the rule or the element early.
_FONT = re.compile(r"[\w\s,'\"-]+")
_LENGTH = re.compile(r"[\w\s.%()+*/-]+")


@dataclass(frozen=True, slots=True)
class Ramp:
    """
    One colour in ten steps, from 50, the lightest, to 900, the darkest. A
    tone's tokens read fixed steps of it: the accent is 700 in light mode and
    500 in dark, so the steps should get darker as hue's own do.
    """

    steps: Sequence[str]

    def __post_init__(self) -> None:
        if len(self.steps) != len(STEPS):
            raise ValueError(
                f"A Ramp has {len(STEPS)} steps, 50 to 900; this has {len(self.steps)}."
            )
        object.__setattr__(self, "steps", tuple(map(css_colour, self.steps)))


@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    """
    What an app changes about hue's look. accent, success, warning, danger
    and info each replace that tone's ramp. colors, fonts and radii set single
    tokens by name, and a colour without a dark value is used in both modes.
    """

    accent: Ramp | None = None
    success: Ramp | None = None
    warning: Ramp | None = None
    danger: Ramp | None = None
    info: Ramp | None = None
    colors: Mapping[ColorToken, Color] = field(default_factory=dict)
    fonts: Mapping[FontToken, str] = field(default_factory=dict)
    radii: Mapping[RadiusToken, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # The types name every token, and these say the same at runtime for
        # a caller that is not type-checked: a misspelt name would otherwise
        # set a property nothing reads.
        for given, token, what in (
            (self.colors, ColorToken, "colour"),
            (self.fonts, FontToken, "font"),
            (self.radii, RadiusToken, "radius"),
        ):
            known = get_args(token.__value__)
            for name in given:
                if name not in known:
                    raise ValueError(f"{name!r} is not a {what} token of hue's.")
        for value in self.fonts.values():
            if not _FONT.fullmatch(value):
                raise ValueError(f"{value!r} is not a font stack.")
        for value in self.radii.values():
            if not _LENGTH.fullmatch(value):
                raise ValueError(f"{value!r} is not a length.")

    @property
    def css(self) -> str:
        """
        The theme as rules. :root[data-theme] outranks the stylesheet's dark
        block, so a value given once holds in both modes, and the dark rule
        after it, of the same weight, wins in dark mode.
        """
        both: list[tuple[str, str]] = []
        for tone in TONES:
            ramp: Ramp | None = getattr(self, tone)
            if ramp is not None:
                both += [
                    (f"--hue-{tone}-{step}", value)
                    for step, value in zip(STEPS, ramp.steps, strict=True)
                ]
        both += [(f"--color-{name}", c.light) for name, c in self.colors.items()]
        both += [(f"--font-{name}", value) for name, value in self.fonts.items()]
        both += [(f"--radius-{name}", value) for name, value in self.radii.items()]
        dark = [
            (f"--color-{name}", color.dark)
            for name, color in self.colors.items()
            if color.dark is not None
        ]
        rules = [_rule(":root, :root[data-theme]", both)]
        if dark:
            rules.append(_rule(':root[data-theme="dark"]', dark))
        return "\n".join(rules)


def _rule(selector: str, declarations: list[tuple[str, str]]) -> str:
    body = "".join(f"\n  {name}: {value};" for name, value in declarations)
    return f"{selector} {{{body}\n}}"
