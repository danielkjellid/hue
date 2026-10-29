from __future__ import annotations

from htmy import Context, html
from typing_extensions import Self

from hue import html as hue_html
from hue.js import unsafe
from hue.shortcuts import FUNCTION_KEY, KEYS, Key
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

# Which key "mod" means, and whether the modifiers are drawn as Apple's glyphs
# or as words, is only knowable in the browser. The server renders the
# Apple glyph and Alpine corrects it, so the markup is right either way and
# nothing flashes for the majority of a given app's users. The answer comes
# from the store the shortcuts are matched by, so the key drawn is the key
# that works; without hue's bundle there is no store, and the glyph stays.
_IS_APPLE = "($store.shortcuts?.apple ?? true)"

_COMMAND = Key("⌘", "Command")

# How each modifier is printed away from Apple platforms, whose keyboards
# spell them out rather than drawing the glyphs.
_OFF_APPLE = {
    "mod": Key("Ctrl", "Control"),
    "ctrl": Key("Ctrl", "Control"),
    "alt": Key("Alt", "Alt"),
    "shift": Key("Shift", "Shift"),
}


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
    and the other modifiers are drawn as words away from Apple platforms,
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

    def _modifier(self, name: str) -> ComponentType:
        apple = _COMMAND if name == "mod" else KEYS[name]
        other = _OFF_APPLE[name]
        return (
            hue_html.kbd()
            .class_(_KEY_CLASSES)
            # A scope of its own, so it resolves wherever Alpine runs and not
            # only under a page that declares one.
            .x_data({})
            .content(
                hue_html.span(apple.glyph)
                .aria_hidden("true")
                .x_text(unsafe(f"{_IS_APPLE} ? '{apple.glyph}' : '{other.glyph}'")),
                hue_html.span(apple.spoken)
                .class_("sr-only")
                .x_text(unsafe(f"{_IS_APPLE} ? '{apple.spoken}' : '{other.spoken}'")),
            )
        )

    def _key(self, key: str) -> ComponentType:
        if key.lower() in _OFF_APPLE:
            return self._modifier(key.lower())

        named = KEYS.get(key.lower())
        if named is None:
            return html.kbd(self._printed(key), class_=_KEY_CLASSES)
        if named.spoken is None:
            return html.kbd(named.glyph, class_=_KEY_CLASSES)
        return html.kbd(
            html.span(named.glyph, aria_hidden="true"),
            html.span(named.spoken, class_="sr-only"),
            class_=_KEY_CLASSES,
        )

    def _printed(self, key: str) -> str:
        """
        The key as it should read on its cap: what to type.

        A letter on its own is drawn as written, so a shortcut's plain "g"
        shows g, and nobody holds Shift for a capital G that never matches.
        In a chord a letter is a capital, the way ⌘K and ⇧G are written,
        since the modifier beside it already says what to hold. A function
        key is a capital either way.
        """
        if FUNCTION_KEY.fullmatch(key.lower()):
            return key.upper()
        if len(key) == 1 and len(self._keys) > 1:
            return key.upper()
        return key

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
