"""
Expressions, and the one way to write an unsafe one.

Everything Alpine evaluates is code: a click handler, a binding, a condition.
There is no escaping that makes code safe, so the modifiers that evaluate
their argument do not take a string at all. They take an Expression, and the
only way to build one out of your own text is to say unsafe() - which is what
makes that decision greppable in a review rather than invisible in an
f-string.

The builders here quote their arguments with json.dumps, so the short way to
write an action is also the safe one.
"""

from __future__ import annotations

import re
from json import dumps
from typing import Any

# A function or a path to one: sendInvoice, $store.cart.add, window.print.
_FUNCTION = re.compile(r"^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*$")


class Expression(str):
    """
    A fragment of JavaScript for Alpine to evaluate.

    A str subclass, so it goes wherever a string goes; the type is the whole
    point of it. Build one with call(), with a helper that returns one such
    as toast.js, or with unsafe().
    """

    __slots__ = ()


def unsafe(source: str) -> Expression:
    """
    Vouch for a fragment of JavaScript.

    Nothing is escaped or checked - the source is handed to Alpine as written,
    so never build one out of anything a user typed. The name is the point:
    every place that decision was made answers to one grep.
    """
    return Expression(source)


def call(function: str, *args: Any) -> Expression:
    """
    A call to a function on the page, with its arguments quoted.

        call("sendInvoice", invoice.id)     # sendInvoice(2048)

    The arguments are JSON, so anything you can put in a dict goes; the
    function has to be a name or a path to one, not an expression, or there
    would be nothing left to quote.
    """
    if not _FUNCTION.match(function):
        raise ValueError(
            f"{function!r} is not a function name or a path to one. "
            "Write the whole thing with unsafe() if that is what you mean."
        )
    return Expression(f"{function}({', '.join(dumps(arg) for arg in args)})")


def close() -> Expression:
    """
    Close the overlay this sits inside.

    Dialog, Drawer, Popover and DropdownMenu all put a close() in scope, so an
    action in one of them says what it does rather than vouching for a string.
    The nearest one wins: in a popover inside a dialog this closes the popover
    and leaves the dialog where it is.
    """
    return Expression("close()")


def expect(value: Expression, *, modifier: str) -> Expression:
    """
    Refuse a plain string where an expression is required, and say what to do
    about it. The type catches this at rest; this catches it at runtime.
    """
    if not isinstance(value, Expression):
        raise TypeError(
            f"{modifier} takes an expression, not a string. Build one with "
            "call() or another helper, or wrap it in unsafe() if it really is "
            "code you wrote."
        )
    return value
