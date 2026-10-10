"""
Keyboard shortcuts, declared once for an app.

An app lists its shortcuts as attributes of a ShortcutRegistry subclass and
hands the class to create_page_base. Every page made from that base binds
them, so a shortcut works on every page, and the command palette and the
menus that show one refer to the attribute rather than repeating its keys.
The whole set is checked when the class is defined, so two shortcuts on the
same keys fail at startup and not in somebody's browser.

A shortcut that only makes sense on some pages is declared scoped, and a
handler switches it on for its own response with shortcuts.use(), the way
toast.success() queues a toast: no context to pass, because the request's
list lives in a ContextVar the router opens and closes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from contextvars import ContextVar, Token
from dataclasses import dataclass
from itertools import combinations
from typing import Any, ClassVar, Final

from htmy import Component, Context, html

from hue.context import HueContext
from hue.js import Expression, expect
from hue.types.core import ComponentType

_MODIFIERS = frozenset({"mod", "ctrl", "alt", "shift"})

#: Where a shortcut goes: a URL, or a function of the request that returns
#: one, for a URL that has to be reversed per request.
type Href = str | Callable[[Any], str]

type Steps = tuple[tuple[str, ...], ...]


def parse_keys(steps: Iterable[str]) -> Steps:
    """
    Each key press as its keys, lower-cased, refusing what the browser could
    never match: no steps, an unknown modifier, or a modifier on its own.

    A step is one key press, with the keys of a chord joined by plus signs:
    ("mod+k",) is Command-K, or Control-K away from Apple platforms, and
    ("g", "b") is G followed by B.
    """
    parsed = []
    for step in steps:
        keys = tuple(key.strip().lower() for key in step.split("+"))
        *modifiers, key = keys
        if not key or key in _MODIFIERS:
            raise ValueError(f"{step!r} has no key to press, only modifiers.")
        unknown = set(modifiers) - _MODIFIERS
        if unknown:
            raise ValueError(
                f"{step!r} uses {', '.join(sorted(unknown))} as a modifier; "
                "the modifiers are mod, ctrl, alt and shift."
            )
        parsed.append(keys)
    if not parsed:
        raise ValueError("A shortcut needs at least one key, such as 'mod+k'.")
    return tuple(parsed)


def binding(steps: Steps, *, describe: bool = False) -> dict[str, str]:
    """
    The x-shortcut attribute for steps. describe only announces them, for a
    visible row whose keys are bound somewhere else.
    """
    name = "x-shortcut.describe" if describe else "x-shortcut"
    return {name: json.dumps(["+".join(step) for step in steps])}


class Shortcut:
    """
    One thing an app does from the keyboard: what it is called, the keys
    that do it, and where it goes or what it runs.

    Declared as an attribute of a ShortcutRegistry. href is a URL or a
    function of the request; action is an Alpine expression. group, icon,
    description and keywords are for the palette that lists it. A scoped
    shortcut is off until a handler calls shortcuts.use() for it, and may
    leave its href or action to that call.
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


def _check(shortcuts: tuple[Shortcut, ...]) -> None:
    """
    Refuse two shortcuts that would fight over a key press on either kind of
    platform: the same keys, or one whose keys start the other's, which would
    run before the other could finish.
    """
    for first, second in combinations(shortcuts, 2):
        for apple in (True, False):
            a = _as_pressed(first.steps, apple=apple)
            b = _as_pressed(second.steps, apple=apple)
            if a == b:
                raise ValueError(f"{first!r} and {second!r} use the same keys.")
            shorter, longer = sorted(((first, a), (second, b)), key=lambda x: len(x[1]))
            if longer[1][: len(shorter[1])] == shorter[1]:
                raise ValueError(
                    f"{shorter[0]!r} runs as soon as it is pressed, so "
                    f"{longer[0]!r}, which starts with the same keys, never could."
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
        cls.shortcuts = tuple(found.values())
        _check(cls.shortcuts)

    @classmethod
    def check(cls, shortcut: Shortcut) -> None:
        """
        Refuse a shortcut declared somewhere else, such as a palette's hotkey,
        whose keys would fight with one of these.
        """
        _check((*cls.shortcuts, shortcut))

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
                    f"{cls.__name__}, the registry this page binds."
                )
        return [
            used.get(shortcut) or Active(shortcut, shortcut.href, shortcut.action)
            for shortcut in cls.shortcuts
            if not shortcut.scoped or shortcut in used
        ]

    @classmethod
    def from_context(cls, context: Context) -> type[ShortcutRegistry] | None:
        """
        The registry the page being rendered binds, if it has one.
        """
        found = context.get(ShortcutRegistry)
        return found if isinstance(found, type) else None


_USED: ContextVar[list[Active]] = ContextVar("hue_shortcuts_used")


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
            _USED.get().append(Active(shortcut, href, action))
        except LookupError:
            raise RuntimeError(
                "shortcuts.use() was called with no request to carry it. The "
                "router opens the list for the length of a request."
            ) from None

    def used(self) -> list[Active]:
        """
        The scoped shortcuts switched on so far in this request.
        """
        try:
            return list(_USED.get())
        except LookupError:
            return []

    def open(self) -> Token[list[Active]] | None:
        """
        Start a request's list, unless one is already open; None means the
        list somebody else opened, and theirs to close.
        """
        try:
            _USED.get()
        except LookupError:
            return _USED.set([])
        return None

    def close(self, token: Token[list[Active]] | None) -> None:
        if token is not None:
            _USED.reset(token)


shortcuts: Final = _Shortcuts()


class ShortcutHost:
    """
    The elements a page's shortcuts are bound to: a hidden link or button for
    each one that is on, which the shortcut clicks.

    BasePage renders it for a page made with a registry; nothing else needs
    to. Hidden, and out of the accessibility tree, because the rows that show
    a shortcut are where it is announced.
    """

    def __init__(self, registry: type[ShortcutRegistry]) -> None:
        self.registry = registry

    def htmy(self, context: Context) -> Component:
        request = HueContext.from_context(context).request
        return html.div(
            *(self._element(item, request) for item in self.registry.active()),
            hidden="",
            aria_hidden="true",
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
