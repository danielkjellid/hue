"""
Keyboard shortcuts, declared once for an app.

An app lists its shortcuts as attributes of a ShortcutRegistry subclass and
puts the class in the render context, the way it gives its date formats:
hue-django reads it from the HUE_SHORTCUTS setting. Every page binds them,
so a shortcut works on every page, and the command palette and the menus
that show one refer to the attribute rather than repeating its keys. The
whole set is checked when the class is defined, so two shortcuts on the same
keys fail at startup and not in somebody's browser.

A shortcut that only makes sense on some pages is declared scoped, and a
handler switches it on for its own response with shortcuts.use(), the way
toast.success() queues a toast: no context to pass, because the request's
list lives in a ContextVar that request_scope opens around each request.
The latest response decides: a fragment whose handler does not switch it on
turns it off.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from contextvars import ContextVar, Token
from dataclasses import dataclass
from itertools import combinations
from typing import Any, ClassVar, Final, NamedTuple

from htmy import Component, Context, html

from hue.js import Expression, expect
from hue.types.core import ComponentType

_MODIFIERS = frozenset({"mod", "ctrl", "alt", "shift"})


class Key(NamedTuple):
    """
    A key with a name: what Kbd draws for it, and what the browser calls it.
    """

    glyph: str
    #: Announced in place of the glyph, which a screen reader would otherwise
    #: read by its Unicode name. None when the glyph is already a word.
    spoken: str | None
    #: How KeyboardEvent.key spells it, which aria-keyshortcuts uses too. None
    #: for a modifier, which is held rather than pressed.
    event: str | None = None


#: Every key with a name, as a shortcut writes it. The one place they are
#: listed: Kbd draws from it, and binding() writes the browser's spelling
#: from it, so the script that matches the keys needs no table of its own.
KEYS: dict[str, Key] = {
    "shift": Key("⇧", "Shift"),
    "alt": Key("⌥", "Alt"),
    "ctrl": Key("⌃", "Control"),
    "esc": Key("Esc", None, "Escape"),
    "enter": Key("↵", "Enter", "Enter"),
    "tab": Key("Tab", None, "Tab"),
    "space": Key("Space", None, " "),
    "backspace": Key("⌫", "Backspace", "Backspace"),
    "delete": Key("⌦", "Delete", "Delete"),
    "up": Key("↑", "Arrow up", "ArrowUp"),
    "down": Key("↓", "Arrow down", "ArrowDown"),
    "left": Key("←", "Arrow left", "ArrowLeft"),
    "right": Key("→", "Arrow right", "ArrowRight"),
    "home": Key("Home", None, "Home"),
    "end": Key("End", None, "End"),
    "pageup": Key("PgUp", "Page up", "PageUp"),
    "pagedown": Key("PgDn", "Page down", "PageDown"),
}

#: The keys with names a shortcut can press, the modifiers being held instead.
NAMED_KEYS = frozenset(name for name, key in KEYS.items() if key.event is not None)

# Other names people reach for, each the same key as one of the above. Written
# down so "escape" and "esc" cannot be declared as two shortcuts that the
# browser would then see as one.
_ALIASES = {
    "escape": "esc",
    "return": "enter",
    "del": "delete",
    "arrowup": "up",
    "arrowdown": "down",
    "arrowleft": "left",
    "arrowright": "right",
}

#: A function key, f1 to f12.
FUNCTION_KEY = re.compile(r"f([1-9]|1[0-2])")

# Keys that move focus, press the focused control, scroll or close an
# overlay. Taken on their own they would stop doing that on every page, so
# they need mod, ctrl or alt.
_NEEDS_A_MODIFIER = frozenset(
    {"tab", "enter", "space", "esc", "up", "down", "left", "right"}
    | {"home", "end", "pageup", "pagedown"}
)

#: Where a shortcut goes: a URL, or a function of the request that returns
#: one, for a URL that has to be reversed per request.
type Href = str | Callable[[Any], str]

type Steps = tuple[tuple[str, ...], ...]


def _key(name: str, step: str) -> str:
    key = _ALIASES.get(name, name)
    # ASCII only: a character outside it sits on a different key on every
    # layout that has it, and on the rest cannot be typed.
    if len(key) == 1 and key.isascii() and key.isprintable() and key != " ":
        return key
    if key in NAMED_KEYS or FUNCTION_KEY.fullmatch(key):
        return key
    raise ValueError(
        f"{step!r} presses {name!r}, which is not a key. Use a single ASCII "
        "character, a function key, or one of "
        f"{', '.join(sorted(NAMED_KEYS))}."
    )


def _is_letter(key: str) -> bool:
    # ASCII only: the browser's shift rules for other letters vary by layout.
    return key.isascii() and key.isalpha()


def parse_keys(steps: Iterable[str]) -> Steps:
    """
    Each key press as its keys, lower-cased and with one name per key,
    refusing what the browser could never match.

    A step is one key press, with the keys of a chord joined by plus signs:
    ("mod+k",) is Command-K, or Control-K away from Apple platforms, and
    ("g", "b") is G followed by B.
    """
    parsed = []
    for step in steps:
        if step.endswith("+"):
            raise ValueError(
                f"{step!r} ends in a plus sign, which joins keys and cannot be "
                "one: the plus key cannot be bound."
            )
        *modifiers, name = (part.strip().lower() for part in step.split("+"))
        if not name or name in _MODIFIERS:
            raise ValueError(f"{step!r} has no key to press, only modifiers.")
        unknown = set(modifiers) - _MODIFIERS
        if unknown:
            raise ValueError(
                f"{step!r} uses {', '.join(sorted(unknown))} as a modifier; "
                "the modifiers are mod, ctrl, alt and shift."
            )
        key = _key(name, step)
        # Shift turns a digit or a symbol into another character, and the
        # browser reports the character: shift+1 arrives as "!".
        if "shift" in modifiers and len(key) == 1 and not _is_letter(key):
            raise ValueError(
                f"{step!r} adds shift to {key!r}. Write the character shift "
                "types instead, such as '?' rather than 'shift+/'."
            )
        if key in _NEEDS_A_MODIFIER and not {"mod", "ctrl", "alt"} & set(modifiers):
            raise ValueError(
                f"{step!r} would take {key} from every page, where it moves "
                "focus, presses a control, scrolls or closes something. Add "
                "mod, ctrl or alt."
            )
        # Option on a Mac types a character of its own, and only a letter or
        # a digit can be told apart by the key it was typed on.
        if "alt" in modifiers and len(key) == 1 and not key.isalnum():
            raise ValueError(
                f"{step!r} adds alt to {key!r}, which Option on a Mac turns into "
                "another character. Use alt with a letter, a digit or a named key."
            )
        # In the order written, which is the order Kbd draws them in.
        parsed.append((*dict.fromkeys(modifiers), key))
    if not parsed:
        raise ValueError("A shortcut needs at least one key, such as 'mod+k'.")
    return tuple(parsed)


def binding(steps: Steps, *, describe: bool = False) -> dict[str, str]:
    """
    The x-shortcut attribute for steps. describe only announces them, for a
    visible row whose keys are bound somewhere else.

    Each key is written the way KeyboardEvent.key spells it, ArrowUp for up
    and F5 for f5, which is also how aria-keyshortcuts spells it, so the
    browser matches and announces what it is given as it is.
    """
    name = "x-shortcut.describe" if describe else "x-shortcut"
    return {name: json.dumps(["+".join(map(_spelled, step)) for step in steps])}


def _spelled(key: str) -> str:
    if key in NAMED_KEYS:
        return str(KEYS[key].event)
    return key.upper() if FUNCTION_KEY.fullmatch(key) else key


class Shortcut:
    """
    One thing an app does from the keyboard: what it is called, the keys
    that do it, and where it goes or what it runs.

    Declared as an attribute of a ShortcutRegistry. href is a URL or a
    function of the request; action is an Alpine expression, which runs in
    the page's scope when the keys are pressed. icon is drawn by the rows
    that show it, and group, description and keywords are for the palette. A
    scoped shortcut is off until a handler calls shortcuts.use() for it, and
    may leave its href or action to that call.
    """

    def __init__(
        self,
        label: str,
        *keys: str,
        href: Href | None = None,
        action: Expression | None = None,
        group: str | None = None,
        icon: ComponentType | None = None,
        description: str | None = None,
        keywords: tuple[str, ...] = (),
        scoped: bool = False,
    ) -> None:
        self.label = label
        self.steps = parse_keys(keys)
        if href is not None and action is not None:
            raise ValueError(f"{label!r} has both an href and an action; pick one.")
        if not scoped and href is None and action is None:
            raise ValueError(
                f"{label!r} has nothing to do. Give it an href or an action, or "
                "make it scoped and give it one in shortcuts.use()."
            )
        self.href = href
        self.action = (
            expect(action, modifier="Shortcut(action=...)") if action else None
        )
        self.group = group
        self.icon = icon
        self.description = description
        self.keywords = keywords
        self.scoped = scoped
        # Set when the registry class is defined, so a shortcut can say which
        # one it is in an error.
        self.name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        keys = " then ".join("+".join(step) for step in self.steps)
        return f"<Shortcut {self.name or self.label!r}: {keys}>"


@dataclass(frozen=True, slots=True)
class Active:
    """
    A shortcut as one request has it: on, and with what it does settled.
    """

    shortcut: Shortcut
    href: Href | None
    action: Expression | None

    def url(self, request: Any) -> str | None:
        return self.href(request) if callable(self.href) else self.href


def _as_pressed(steps: Steps, *, apple: bool) -> tuple[frozenset[str], ...]:
    """
    The keys as one platform reads them, since mod is ctrl away from Apple
    platforms and "mod+k" and "ctrl+k" are then the same press.
    """
    meaning = "meta" if apple else "ctrl"
    return tuple(
        frozenset(meaning if key == "mod" else key for key in step) for step in steps
    )


def _clash(first: tuple[str, Steps], second: tuple[str, Steps]) -> None:
    """
    Refuse two shortcuts that would fight over a key press on either kind of
    platform, given as what to call each in an error and its steps.

    The same keys clash, and so does a shorter one found anywhere in the
    longer one's sequence but at its end: it runs as soon as it is pressed,
    and the longer one never gets the rest. One that ends the other's is
    fine, because the browser prefers the longer of two that both match what
    was just pressed, so B on its own and G then B both stay reachable.
    """
    for apple in (True, False):
        a = _as_pressed(first[1], apple=apple)
        b = _as_pressed(second[1], apple=apple)
        if a == b:
            raise ValueError(f"{first[0]} and {second[0]} use the same keys.")
        (short, short_keys), (long, long_keys) = sorted(
            ((first[0], a), (second[0], b)), key=lambda pair: len(pair[1])
        )
        width = len(short_keys)
        # Every place the shorter one could sit, the end excepted.
        for start in range(len(long_keys) - width):
            if long_keys[start : start + width] == short_keys:
                raise ValueError(
                    f"{short} runs as soon as it is pressed, so {long}, which "
                    "has the same keys partway through, never could finish."
                )


class ShortcutRegistry:
    """
    Every shortcut an app has, as class attributes.

    Attributes rather than names in a list, so a menu item or a handler
    refers to Shortcuts.create_invoice and a type checker knows whether there
    is one. Defining the class checks the whole set for keys that collide.

        class Shortcuts(ShortcutRegistry):
            billing = Shortcut("Go to Billing", "g", "b", href="/billing/")
    """

    shortcuts: ClassVar[tuple[Shortcut, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Inherited ones too, so an app can split its set across classes.
        found: dict[str, Shortcut] = {}
        for klass in reversed(cls.__mro__):
            for name, value in vars(klass).items():
                if isinstance(value, Shortcut):
                    found[name] = value
                else:
                    # A subclass that sets an inherited one to anything else,
                    # None say, has taken it out.
                    found.pop(name, None)
        taken = set(found) & set(vars(ShortcutRegistry))
        if taken:
            raise ValueError(
                f"{cls.__name__} names a shortcut {', '.join(sorted(taken))}, "
                "which the registry uses itself. Call it something else."
            )
        cls.shortcuts = tuple(found.values())
        for first, second in combinations(cls.shortcuts, 2):
            _clash((repr(first), first.steps), (repr(second), second.steps))

    @classmethod
    def check(cls, what: str, steps: Steps) -> None:
        """
        Refuse keys declared somewhere else, such as a palette's hotkey, that
        would fight with one of these. what names them in the error.
        """
        for existing in cls.shortcuts:
            _clash((repr(existing), existing.steps), (what, steps))

    @classmethod
    def active(cls) -> list[Active]:
        """
        The shortcuts that are on for the request being handled: every
        unscoped one, and the scoped ones a handler switched on.
        """
        used = {item.shortcut: item for item in shortcuts.used()}
        for item in used.values():
            if item.shortcut not in cls.shortcuts:
                raise ValueError(
                    f"{item.shortcut!r} was switched on, but it is not in "
                    f"{cls.__name__}, the registry this app binds."
                )
        return [
            used.get(shortcut) or Active(shortcut, shortcut.href, shortcut.action)
            for shortcut in cls.shortcuts
            if not shortcut.scoped or shortcut in used
        ]


@dataclass(slots=True)
class _Request:
    """
    What one request has done with its shortcuts: the scoped ones it switched
    on, and whether anything rendered their bindings yet.
    """

    used: list[Active]
    bound: bool = False


_REQUEST: ContextVar[_Request] = ContextVar("hue_shortcuts_request")


class _Shortcuts:
    """
    Switching on the scoped shortcuts for one response.
    """

    def use(
        self,
        shortcut: Shortcut,
        *,
        href: Href | None = None,
        action: Expression | None = None,
    ) -> None:
        """
        Switch a scoped shortcut on for the response being built, with what it
        does here when that depends on the page: the invoice it archives, say.
        """
        if not shortcut.scoped:
            raise ValueError(
                f"{shortcut!r} is on every page already; only a scoped shortcut "
                "is switched on with use()."
            )
        if href is not None and action is not None:
            raise ValueError(f"{shortcut!r} was given both an href and an action.")
        if action is not None:
            action = expect(action, modifier="shortcuts.use(action=...)")
        if href is None and action is None:
            href, action = shortcut.href, shortcut.action
        if href is None and action is None:
            raise ValueError(
                f"{shortcut!r} has nothing to do here. Give use() an href or an "
                "action, or give the Shortcut one."
            )
        try:
            _REQUEST.get().used.append(Active(shortcut, href, action))
        except LookupError:
            raise RuntimeError(
                "shortcuts.use() was called with no request to carry it. The "
                "router opens the list for the length of a request, and "
                "HueRequestMiddleware for a plain Django view."
            ) from None

    def used(self) -> list[Active]:
        """
        The scoped shortcuts switched on so far in this request.
        """
        request = _REQUEST.get(None)
        return list(request.used) if request is not None else []

    def bound(self) -> bool:
        """
        Whether this request has rendered its shortcut bindings, which a page
        does and a fragment does not.
        """
        request = _REQUEST.get(None)
        return request is not None and request.bound

    def _bind(self) -> None:
        if (request := _REQUEST.get(None)) is not None:
            request.bound = True

    def open(self) -> Token[_Request] | None:
        """
        Start a request's list, unless one is already open; None means the
        list somebody else opened, and theirs to close.
        """
        if _REQUEST.get(None) is not None:
            return None
        return _REQUEST.set(_Request(used=[]))

    def close(self, token: Token[_Request] | None) -> None:
        if token is not None:
            _REQUEST.reset(token)


shortcuts: Final = _Shortcuts()


class ShortcutHost:
    """
    The elements an app's shortcuts are bound to: a hidden link or button for
    each one that is on, which the shortcut clicks.

    BasePage renders it when the render context has a registry. For an app
    with scoped shortcuts the router appends it to every fragment as well:
    it is synced, so that copy replaces the page's, and the scoped shortcuts
    on are the ones the latest handler switched on.

    Hidden, and out of the accessibility tree, because the rows that show a
    shortcut are where it is announced.
    """

    def __init__(self, registry: type[ShortcutRegistry]) -> None:
        self.registry = registry

    def htmy(self, context: Context) -> Component:
        # Imported here: hue.context imports this module for the registry type.
        from hue.context import HueContext  # noqa: PLC0415

        request = HueContext.from_context(context).request
        shortcuts._bind()
        return html.div(
            *(self._element(item, request) for item in self.registry.active()),
            id="hue-shortcuts",
            hidden="",
            aria_hidden="true",
            **{"x-sync": ""},
        )

    def _element(self, item: Active, request: Any) -> ComponentType:
        bound = binding(item.shortcut.steps)
        url = item.url(request)
        if url is not None:
            return html.a(href=url, tabindex="-1", **bound)
        return html.button(
            type="button",
            tabindex="-1",
            **{**bound, "x-on:click": item.action},
        )
