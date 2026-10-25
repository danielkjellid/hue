"""
Raising a toast.

Two halves of the same thing under one name.

toast.success("Invoice sent") queues one on the server. It is a plain call
from anywhere - no context to thread through, because the queue is
request-scoped in a ContextVar that request_scope opens around each
request. Whatever the handler returns carries the toast with it: a page
renders it into its region, and a fragment gets the region appended to the
response.

toast.js.success("Copied") is the browser half, an expression to hand to
on_click for the things the server never hears about. Its values are quoted
by json.dumps rather than by hand, so an apostrophe in a description is a
word rather than a syntax error in someone's page.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, MutableMapping
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Final, Literal

from hue.js import Expression, expect

type ToastVariant = Literal["success", "danger", "warning", "info", "loading"]

# A label and the expression the button runs, e.g.
# ("Retry", ajax("/invoices/2048/send/", method="post", target="invoice")).
type ToastAction = tuple[str, Expression]


class Inherit(Enum):
    """
    Nothing was said about how long, so the region's own duration stands.

    An enum rather than a bare object, because that is the sentinel a type
    checker can narrow: duration is not INHERIT leaves int | None behind.
    """

    TOKEN = auto()


INHERIT: Final = Inherit.TOKEN

type Duration = int | None | Inherit


def _expression(
    variant: str,
    title: str,
    description: str | None,
    duration: Duration,
    action: ToastAction | None,
) -> Expression:
    options: list[str] = []
    if description is not None:
        options.append(f"description: {json.dumps(description)}")
    if duration is not INHERIT:
        options.append(f"duration: {json.dumps(duration)}")
    if action is not None:
        label, expression = action
        expect(expression, modifier="A toast's action")
        # The label is text and is quoted; the expression is code and is not.
        # A block body rather than a bare one, because what on_click takes may
        # hold statements, and those are no arrow function's value.
        options.append(
            f"action: {{ label: {json.dumps(label)}, "
            f"onClick: () => {{ {expression} }} }}"
        )
    arguments = json.dumps(title)
    if options:
        arguments += ", { " + ", ".join(options) + " }"
    return Expression(f"$toast.{variant}({arguments})")


@dataclass(frozen=True, slots=True)
class ToastMessage:
    """
    One toast a handler asked for, waiting for something to render it.
    """

    variant: ToastVariant
    title: str
    description: str | None = None
    duration: Duration = field(default=INHERIT)
    dismissible: bool = True
    action: Any = None

    def as_dict(self) -> dict[str, Any]:
        """
        The message as plain data, for a store that has to outlive the
        request - a session, between a redirect and the page after it.

        An action is a component, which is not data, so one cannot be stored.
        Saying so beats a toast that quietly loses its button on the way.
        """
        if self.action is not None:
            raise TypeError(
                "A toast with an action cannot be stored between requests: "
                "its action is a component. Raise this one from the handler "
                "that renders the page, or leave the action off."
            )
        return {
            "variant": self.variant,
            "title": self.title,
            "description": self.description,
            "duration": None if self.duration is INHERIT else self.duration,
            "inherit": self.duration is INHERIT,
            "dismissible": self.dismissible,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToastMessage:
        """
        A message read back out of a store.
        """
        return cls(
            variant=data["variant"],
            title=data["title"],
            description=data.get("description"),
            duration=INHERIT if data.get("inherit") else data.get("duration"),
            dismissible=data.get("dismissible", True),
        )


# One list per request. A ContextVar rather than something handed around, so
# toast.success() is a plain call from wherever the work happens - and one per
# request rather than one per process, so a toast cannot surface in somebody
# else's response.
_QUEUE: ContextVar[list[ToastMessage]] = ContextVar("hue_toasts")


class _Js:
    """
    The browser half of toast: one method per variant, each returning the
    Expression that raises it, which on_click and x_on take as they are.

        Button().content("Copy").x_on("click", toast.js.success("Copied"))

    duration is milliseconds, None is a toast that stays, and leaving it out
    takes the region's own. action is a label and the expression its button
    runs.
    """

    def success(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("success", title, description, duration, action)

    def danger(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("danger", title, description, duration, action)

    def warning(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("warning", title, description, duration, action)

    def info(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("info", title, description, duration, action)

    def loading(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("loading", title, description, duration, action)


class _Toast:
    """
    Where a toast is raised from, either side of the wire.

    The methods here queue one on the server; toast.js raises one in the
    browser. duration is milliseconds, None is a toast that stays, and
    leaving it out takes the region's own.
    """

    js: Final = _Js()

    def success(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        dismissible: bool = True,
        action: Any = None,
    ) -> None:
        self._queue("success", title, description, duration, dismissible, action)

    def danger(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        dismissible: bool = True,
        action: Any = None,
    ) -> None:
        self._queue("danger", title, description, duration, dismissible, action)

    def warning(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        dismissible: bool = True,
        action: Any = None,
    ) -> None:
        self._queue("warning", title, description, duration, dismissible, action)

    def info(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        dismissible: bool = True,
        action: Any = None,
    ) -> None:
        self._queue("info", title, description, duration, dismissible, action)

    def loading(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: Duration = INHERIT,
        dismissible: bool = True,
        action: Any = None,
    ) -> None:
        self._queue("loading", title, description, duration, dismissible, action)

    def _queue(
        self,
        variant: ToastVariant,
        title: str,
        description: str | None,
        duration: Duration,
        dismissible: bool,
        action: Any,
    ) -> None:
        message = ToastMessage(
            variant=variant,
            title=title,
            description=description,
            duration=duration,
            dismissible=dismissible,
            action=action,
        )
        # Outside a request there is nowhere for it to go, and dropping it
        # quietly would be worse than the AttributeError of never having one.
        try:
            _QUEUE.get().append(message)
        except LookupError:
            raise RuntimeError(
                "toast.{}() was called with no request to carry it. The queue "
                "is open for the length of a request; outside one, "
                "render a Toast yourself.".format(variant)
            ) from None

    def open(self) -> Token[list[ToastMessage]] | None:
        """
        Start a request's queue, unless one is already open.

        None means somebody outside already opened it - a middleware that
        carries toasts across a redirect, say - and it is theirs to close.
        request_scope calls this either way and hands whatever it gets to
        close().
        """
        try:
            _QUEUE.get()
        except LookupError:
            return _QUEUE.set([])
        return None

    def close(self, token: Token[list[ToastMessage]] | None) -> None:
        """
        End a request's queue, whatever happened in it. A None token is one
        somebody else opened, so it is left alone.
        """
        if token is not None:
            _QUEUE.reset(token)

    def restore(self, messages: Iterable[ToastMessage]) -> None:
        """
        Put messages back at the front of the queue, for a store handing back
        what was raised before a redirect.
        """
        try:
            queued = _QUEUE.get()
        except LookupError:
            raise RuntimeError(
                "Toasts can only be restored inside a request. Open the queue first."
            ) from None
        queued[:0] = messages

    def drain(self) -> list[ToastMessage]:
        """
        Take everything queued so far, leaving the queue empty.

        Whatever renders the toasts calls this - the region when a page has
        one, the router otherwise - so a toast is rendered once and only once.
        """
        try:
            queued = _QUEUE.get()
        except LookupError:
            return []
        taken = list(queued)
        queued.clear()
        return taken


toast: Final = _Toast()


# Where the toasts raised before a redirect wait for the page after it.
SESSION_KEY = "hue_toasts"


def restore_from_session(session: MutableMapping[str, Any] | None) -> None:
    """
    Hand back what the last request left in the session, oldest first, and
    take it out, so it is shown once.

    For an integration's request middleware; a None session, where the app
    has none, restores nothing.
    """
    stored = session.pop(SESSION_KEY, None) if session is not None else None
    if stored:
        toast.restore(ToastMessage.from_dict(data) for data in stored)


def keep_in_session(session: MutableMapping[str, Any] | None) -> None:
    """
    Keep what nothing rendered for the next request to show.

    A page empties the queue through its region and a fragment through the
    router, so what is left was raised by something that returned no markup,
    a redirect most often.
    """
    pending = toast.drain()
    if pending and session is not None:
        session[SESSION_KEY] = [message.as_dict() for message in pending]
