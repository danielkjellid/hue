from __future__ import annotations

from htmy import Context, html
from typing_extensions import Self

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
# spell them out rather than drawing the glyphs, in the order they are
# conventionally written there: Ctrl+Alt+Shift.
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


def _glyph(glyph: str, **attrs: str) -> ComponentType:
    """
    A glyph that only shows, beside the spoken name that is read.

    Drawn as generated content rather than text, because aria-hidden does
    not hold inside something hidden: a tooltip's bubble describes its
    control while hidden, and a text glyph would be read there along with
    the name, every modifier twice.
    """
    return html.span(
        aria_hidden="true",
        data_glyph=glyph,
        class_="before:content-[attr(data-glyph)]",
        **attrs,
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

    def keys(self, *values: str) -> Self:
        self._keys = values
        return self

    def _modifier(self, name: str, off_apple: str) -> ComponentType:
        apple = _COMMAND if name == "mod" else KEYS[name]
        other = _OFF_APPLE[off_apple]
        return html.kbd(
            _glyph(
                apple.glyph,
                **{":data-glyph": f"{_IS_APPLE} ? '{apple.glyph}' : '{other.glyph}'"},
            ),
            html.span(
                apple.spoken or "",
                class_="sr-only",
                **{"x-text": f"{_IS_APPLE} ? '{apple.spoken}' : '{other.spoken}'"},
            ),
            class_=_KEY_CLASSES,
            # A scope of its own, so it resolves wherever Alpine runs and not
            # only under a page that declares one.
            **{"x-data": "{}"},
        )

    def _key(self, key: str) -> ComponentType:
        named = KEYS.get(key.lower())
        if named is None:
            return html.kbd(self._printed(key), class_=_KEY_CLASSES)
        if named.spoken is None:
            return html.kbd(named.glyph, class_=_KEY_CLASSES)
        return html.kbd(
            _glyph(named.glyph),
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
        # Apple writes the modifiers in the order given and everyone else as
        # Ctrl+Alt+Shift. Each modifier's place shows, off Apple, the one
        # sorted into it, so the order is right in the markup a screen reader
        # walks and not only on screen.
        names = [key.lower() for key in self._keys]
        off_apple = iter(
            sorted((n for n in names if n in _OFF_APPLE), key=list(_OFF_APPLE).index)
        )
        # Always wrapped, even for one key, so the caller's class_ and
        # attributes have a single predictable home.
        return html.span(
            *(
                self._modifier(name, next(off_apple))
                if name in _OFF_APPLE
                else self._key(key)
                for key, name in zip(self._keys, names, strict=True)
            ),
            class_=classnames(
                "inline-flex items-center gap-[3px]",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
