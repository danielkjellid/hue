from __future__ import annotations

from typing import NamedTuple

from htmy import Context, html
from typing_extensions import Self

from hue import html as hue_html
from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames


class _Key(NamedTuple):
    glyph: str
    #: Announced in place of the glyph. None when the glyph is already a word.
    name: str | None


# Glyphs a screen reader would otherwise read as its Unicode name - "place of
# interest sign" for the command key - get a spoken name instead.
_NAMED_KEYS: dict[str, _Key] = {
    "shift": _Key("⇧", "Shift"),
    "alt": _Key("⌥", "Alt"),
    "ctrl": _Key("⌃", "Control"),
    "enter": _Key("↵", "Enter"),
    "backspace": _Key("⌫", "Backspace"),
    "delete": _Key("⌦", "Delete"),
    "up": _Key("↑", "Arrow up"),
    "down": _Key("↓", "Arrow down"),
    "left": _Key("←", "Arrow left"),
    "right": _Key("→", "Arrow right"),
    "esc": _Key("Esc", None),
    "tab": _Key("Tab", None),
}

# Which key "mod" means is only knowable in the browser. The server renders the
# Apple glyph and Alpine corrects it, so the markup is right either way and
# nothing flashes for the majority of a given app's users.
_IS_APPLE = "/Mac|iPhone|iPad|iPod/.test(navigator.platform)"

_KEY_CLASSES = (
    "inline-flex items-center justify-center min-w-5 h-5 px-[5px] "
    "border border-border-strong border-b-2 rounded-sm bg-surface "
    "text-fg-muted font-mono text-2xs font-semibold leading-none"
)


class Kbd(ChainableComponent):
    """
    Keyboard keys, rendered as real kbd elements.

    Modifier names become their glyphs and carry a spoken name alongside, so a
    screen reader announces "Command" rather than the glyph's Unicode name.
    "mod" is the command key on Apple platforms and control everywhere else,
    which only the browser can decide.

        Kbd("mod", "K")
    """

    category = "Typography"

    def __init__(self, *keys: str) -> None:
        super().__init__()
        self._keys: tuple[str, ...] = keys

    @classmethod
    def example(cls) -> Self:
        return cls("mod", "K")

    def keys(self, *values: str) -> Self:
        self._keys = values
        return self

    def _mod_key(self) -> ComponentType:
        return (
            hue_html.kbd()
            .class_(_KEY_CLASSES)
            .x_data(f"{{ apple: {_IS_APPLE} }}")
            .content(
                hue_html.span("⌘")
                .aria_hidden("true")
                .x_text(unsafe("apple ? '⌘' : 'Ctrl'")),
                hue_html.span("Command")
                .class_("sr-only")
                .x_text(unsafe("apple ? 'Command' : 'Control'")),
            )
        )

    def _key(self, key: str) -> ComponentType:
        if key == "mod":
            return self._mod_key()

        named = _NAMED_KEYS.get(key.lower())
        if named is None:
            return html.kbd(key, class_=_KEY_CLASSES)
        if named.name is None:
            return html.kbd(named.glyph, class_=_KEY_CLASSES)
        return html.kbd(
            html.span(named.glyph, aria_hidden="true"),
            html.span(named.name, class_="sr-only"),
            class_=_KEY_CLASSES,
        )

    def _render(self, context: Context) -> Component:
        # Always wrapped, even for one key, so the caller's class_ and
        # attributes have a single predictable home.
        return html.span(
            *(self._key(key) for key in self._keys),
            class_=classnames(
                "inline-flex items-center gap-[3px]",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
