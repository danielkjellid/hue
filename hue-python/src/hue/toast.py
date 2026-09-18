"""
Raising a toast.

Two halves of the same thing under one name. The browser half is here: an
expression to hand to x_on, for the things the server never hears about - a
copy to the clipboard, going offline. The server half, which queues a toast
to ride along with whatever a handler returns, lands with the router work.

Values are quoted by json.dumps rather than by hand, so an apostrophe in a
description is a word rather than a syntax error in someone's page.
"""

from __future__ import annotations

import json
from typing import Final

from hue.js import Expression

# A label and the expression the button runs, e.g. ("Retry", "$ajax('/send/')").
type ToastAction = tuple[str, str]


class _Inherit:
    """
    Nothing was said about how long, so the region's own duration stands.
    """


_INHERIT: Final = _Inherit()

type _Duration = int | None | _Inherit


def _expression(
    variant: str,
    title: str,
    description: str | None,
    duration: _Duration,
    action: ToastAction | None,
) -> Expression:
    options: list[str] = []
    if description is not None:
        options.append(f"description: {json.dumps(description)}")
    if not isinstance(duration, _Inherit):
        options.append(f"duration: {json.dumps(duration)}")
    if action is not None:
        label, expression = action
        # The label is text and is quoted; the expression is code and is not.
        options.append(
            f"action: {{ label: {json.dumps(label)}, onClick: () => {expression} }}"
        )
    arguments = json.dumps(title)
    if options:
        arguments += ", { " + ", ".join(options) + " }"
    return Expression(f"$toast.{variant}({arguments})")


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
        duration: _Duration = _INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("success", title, description, duration, action)

    def danger(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: _Duration = _INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("danger", title, description, duration, action)

    def warning(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: _Duration = _INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("warning", title, description, duration, action)

    def info(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: _Duration = _INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("info", title, description, duration, action)

    def loading(
        self,
        title: str,
        *,
        description: str | None = None,
        duration: _Duration = _INHERIT,
        action: ToastAction | None = None,
    ) -> Expression:
        return _expression("loading", title, description, duration, action)


class _Toast:
    """
    Where a toast is raised from, either side of the wire.
    """

    js: Final = _Js()


toast: Final = _Toast()
