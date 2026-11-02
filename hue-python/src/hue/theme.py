"""
A theme: what an app changes about hue's look, written in Python.

A Theme is made of groups that follow the design tokens: the accent, each
status tone, the surfaces, the text, the borders, the category colours, the
fonts and the corners. Every field names what it styles and is optional, and
whatever a theme leaves out keeps hue's value.

    Theme(
        accent=Accent(fill=Color("#6D28D9", dark="#8B5CF6")),
        surfaces=Surfaces(canvas=Color("#FFFFFF", dark="#09090B")),
        fonts=Fonts(ui='"Geist", sans-serif'),
        corners=Corners(control="6px"),
    )

The page writes it as a style element after hue's stylesheet, so a stylesheet
the app adds after that still has the last word.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, fields
from typing import ClassVar

from typing_extensions import Self

from hue.palette import Color

# Written into a style element, so held to what a font stack and a length are
# spelled with: no semicolon, brace or angle bracket to end the declaration,
# the rule or the element early.
_FONT = re.compile(r"[\w\s,'\"-]+")
_LENGTH = re.compile(r"[\w\s.%()+*/-]+")


@dataclass(frozen=True, slots=True, kw_only=True)
class _Group:
    """
    A group of tokens, one per field. _TOKENS names the custom property each
    field sets.
    """

    _TOKENS: ClassVar[dict[str, str]]

    def _set(self) -> Iterator[tuple[str, str | Color]]:
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                yield self._TOKENS[field.name], value


_STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900)


def _scale(steps: Sequence[str]) -> dict[int, str]:
    if len(steps) != len(_STEPS):
        raise ValueError(f"A scale has ten steps, 50 to 900; this has {len(steps)}.")
    return dict(zip(_STEPS, steps, strict=True))


def _tint(color: str, percent: int) -> str:
    # How hue's own dark mode tints a tone: its colour over transparency.
    return f"color-mix(in srgb, {color} {percent}%, transparent)"


@dataclass(frozen=True, slots=True, kw_only=True)
class Accent(_Group):
    """
    The brand colour. fill is a primary button and anything selected, with fg
    the text on it. subtle is a tinted background, border the edge around
    one, text a link or an accented word, and vivid a decorative mark such as
    a chart's fill.
    """

    fill: Color | None = None
    hover: Color | None = None
    active: Color | None = None
    fg: Color | None = None
    subtle: Color | None = None
    subtle_hover: Color | None = None
    border: Color | None = None
    text: Color | None = None
    vivid: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "fill": "--color-accent",
        "hover": "--color-accent-hover",
        "active": "--color-accent-active",
        "fg": "--color-accent-fg",
        "subtle": "--color-accent-subtle",
        "subtle_hover": "--color-accent-subtle-hover",
        "border": "--color-accent-border",
        "text": "--color-accent-text",
        "vivid": "--color-accent-vivid",
    }

    @classmethod
    def from_scale(cls, steps: Sequence[str]) -> Self:
        """
        Every colour but fg from a scale of ten steps, 50 to 900, lightest
        first, read the way hue reads its blue. In light mode fill is 700,
        hover 800, active 900, subtle 50, subtle_hover 100, border 200, text
        700 and vivid 500. Dark mode fills with 500, lightens hover and active
        to 400 and 300, writes text in 400, and tints with 500 at 14%, 22%
        and 38%. fg keeps hue's value; set it to whatever reads on the fill.
        """
        s = _scale(steps)
        return cls(
            fill=Color(s[700], dark=s[500]),
            hover=Color(s[800], dark=s[400]),
            active=Color(s[900], dark=s[300]),
            subtle=Color(s[50], dark=_tint(s[500], 14)),
            subtle_hover=Color(s[100], dark=_tint(s[500], 22)),
            border=Color(s[200], dark=_tint(s[500], 38)),
            text=Color(s[700], dark=s[400]),
            vivid=Color(s[500]),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Status(_Group):
    """
    One status tone: success, warning or info. fill is the solid colour, such
    as an icon or a progress bar, and text the tone written on its subtle
    background, which border edges. vivid is a decorative mark.
    """

    fill: Color | None = None
    text: Color | None = None
    subtle: Color | None = None
    border: Color | None = None
    vivid: Color | None = None

    # The tone's name, filled in by the Theme field it sits in.
    _TOKENS: ClassVar[dict[str, str]] = {
        "fill": "--color-{tone}",
        "text": "--color-{tone}-text",
        "subtle": "--color-{tone}-subtle",
        "border": "--color-{tone}-border",
        "vivid": "--color-{tone}-vivid",
    }

    @classmethod
    def from_scale(cls, steps: Sequence[str]) -> Self:
        """
        Every colour from a scale of ten steps, 50 to 900, lightest first. In
        light mode fill is 700, text 800, subtle 50, border 200 and vivid
        500. Dark mode fills with 400, writes text in 300, makes vivid 400,
        and tints with 500 at 14% and 36%.
        """
        return cls(**_status(_scale(steps)))


@dataclass(frozen=True, slots=True, kw_only=True)
class Danger(Status):
    """
    The danger tone, which is also a button: Status's colours, plus hover for
    the button under the pointer and fg for the text on its fill.
    """

    hover: Color | None = None
    fg: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        **Status._TOKENS,
        "hover": "--color-{tone}-hover",
        "fg": "--color-{tone}-fg",
    }

    @classmethod
    def from_scale(cls, steps: Sequence[str]) -> Self:
        """
        Status's colours from the scale, and hover from 800, or 300 in dark
        mode. fg keeps hue's value; set it to whatever reads on the fill.
        """
        s = _scale(steps)
        return cls(**_status(s), hover=Color(s[800], dark=s[300]))


def _status(s: dict[int, str]) -> dict[str, Color]:
    return {
        "fill": Color(s[700], dark=s[400]),
        "text": Color(s[800], dark=s[300]),
        "subtle": Color(s[50], dark=_tint(s[500], 14)),
        "border": Color(s[200], dark=_tint(s[500], 36)),
        "vivid": Color(s[500], dark=s[400]),
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Surfaces(_Group):
    """
    What things sit on. canvas is the page and canvas_subtle a band across
    it. base is a card or a panel, raised a popover or a menu, and sunken a
    well such as a track. hover and active are a row or an item under the
    pointer and pressed. inverse is a tooltip's bubble, with inverse_fg its
    text, and scrim the shade behind a dialog.
    """

    canvas: Color | None = None
    canvas_subtle: Color | None = None
    base: Color | None = None
    raised: Color | None = None
    sunken: Color | None = None
    hover: Color | None = None
    active: Color | None = None
    inverse: Color | None = None
    inverse_fg: Color | None = None
    scrim: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "canvas": "--color-canvas",
        "canvas_subtle": "--color-canvas-subtle",
        "base": "--color-surface",
        "raised": "--color-surface-raised",
        "sunken": "--color-surface-sunken",
        "hover": "--color-surface-hover",
        "active": "--color-surface-active",
        "inverse": "--color-surface-inverse",
        "inverse_fg": "--color-surface-inverse-fg",
        "scrim": "--color-scrim",
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Text(_Group):
    """
    The colours text is written in. default is most of it; strong is for
    headings that stand out, muted for secondary text, subtle for hints and
    placeholders, and disabled for controls that are.
    """

    default: Color | None = None
    strong: Color | None = None
    muted: Color | None = None
    subtle: Color | None = None
    disabled: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "default": "--color-fg",
        "strong": "--color-fg-strong",
        "muted": "--color-fg-muted",
        "subtle": "--color-fg-subtle",
        "disabled": "--color-fg-disabled",
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Borders(_Group):
    """
    Edges. default divides and frames, strong is an edge that has to show,
    input is around a form control, and hover is that edge under the pointer.
    """

    default: Color | None = None
    strong: Color | None = None
    input: Color | None = None
    hover: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "default": "--color-border",
        "strong": "--color-border-strong",
        "input": "--color-border-input",
        "hover": "--color-border-hover",
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Categories(_Group):
    """
    The six presets hue.palette names, which charts and calendars draw their
    series, slices and layers in. gray is the muted one.
    """

    accent: Color | None = None
    teal: Color | None = None
    orange: Color | None = None
    purple: Color | None = None
    yellow: Color | None = None
    gray: Color | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "accent": "--color-category-accent",
        "teal": "--color-category-teal",
        "orange": "--color-category-orange",
        "purple": "--color-category-purple",
        "yellow": "--color-category-yellow",
        "gray": "--color-category-gray",
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Fonts(_Group):
    """
    Font stacks. ui is controls and headings, body is running text, and mono
    is code and keys. Hue loads no webfonts, so load the faces you name.
    """

    ui: str | None = None
    body: str | None = None
    mono: str | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "ui": "--font-ui",
        "body": "--font-body",
        "mono": "--font-mono",
    }

    def __post_init__(self) -> None:
        for _, value in self._set():
            if not _FONT.fullmatch(str(value)):
                raise ValueError(f"{value!r} is not a font stack.")


@dataclass(frozen=True, slots=True, kw_only=True)
class Corners(_Group):
    """
    How round corners are, by what they are on. small is a checkbox, a
    swatch or an inline link; item is a row in a menu or a list, a badge or
    a tooltip; control is a button or a field; container is a card, a panel
    or a popover; overlay is a dialog or a drawer.
    """

    small: str | None = None
    item: str | None = None
    control: str | None = None
    container: str | None = None
    overlay: str | None = None

    _TOKENS: ClassVar[dict[str, str]] = {
        "small": "--radius-xs",
        "item": "--radius-sm",
        "control": "--radius-md",
        "container": "--radius-lg",
        "overlay": "--radius-xl",
    }

    def __post_init__(self) -> None:
        for _, value in self._set():
            if not _LENGTH.fullmatch(str(value)):
                raise ValueError(f"{value!r} is not a length.")


@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    """
    What an app changes about hue's look, a group at a time. A colour without
    a dark value holds in both modes.
    """

    accent: Accent | None = None
    success: Status | None = None
    warning: Status | None = None
    danger: Danger | None = None
    info: Status | None = None
    surfaces: Surfaces | None = None
    text: Text | None = None
    borders: Borders | None = None
    categories: Categories | None = None
    fonts: Fonts | None = None
    corners: Corners | None = None

    def tokens(self) -> Iterator[tuple[str, str | Color]]:
        """
        Each custom property the theme sets, with its value.
        """
        for field in fields(self):
            group: _Group | None = getattr(self, field.name)
            if group is not None:
                for token, value in group._set():
                    yield token.format(tone=field.name), value

    @property
    def css(self) -> str:
        """
        The theme as rules. :root[data-theme] outranks the stylesheet's dark
        block, so a value given once holds in both modes, and the dark rule
        after it, of the same weight, wins in dark mode.
        """
        both: list[tuple[str, str]] = []
        dark: list[tuple[str, str]] = []
        for token, value in self.tokens():
            if isinstance(value, Color):
                both.append((token, value.light))
                if value.dark is not None:
                    dark.append((token, value.dark))
            else:
                both.append((token, value))
        rules = [_rule(":root, :root[data-theme]", both)]
        if dark:
            rules.append(_rule(':root[data-theme="dark"]', dark))
        return "\n".join(rules)


def _rule(selector: str, declarations: list[tuple[str, str]]) -> str:
    body = "".join(f"\n  {name}: {value};" for name, value in declarations)
    return f"{selector} {{{body}\n}}"
