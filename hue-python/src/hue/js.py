"""
Expressions, and the one way to write an unsafe one.

Everything Alpine evaluates is code: a click handler, a binding, a condition.
There is no escaping that makes code safe, so the modifiers that evaluate
their argument do not take a string at all. They take an Expression, and the
only way to build one out of your own text is to say unsafe() - which is what
makes that decision greppable in a review rather than invisible in an
f-string.

call() and ajax() quote their arguments with json.dumps, so the short way to
write an action is also the safe one.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from json import dumps
from typing import Any, Literal, get_args

# A function or a path to one: sendInvoice, $store.cart.add, window.print.
_FUNCTION = re.compile(r"^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*$")


class Expression(str):
    """
    A fragment of JavaScript for Alpine to evaluate.

    A str subclass, so it goes wherever a string goes; the type is the whole
    point of it. Build one with call(), ajax() or close(), with a helper that
    returns one such as toast.js, or with unsafe().
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

    An argument that is already an Expression goes in as written, because
    that is the whole of what unsafe() said about it - quoting it back into
    a string would make the one way of passing a variable the one way that
    cannot work. The same holds for one inside a dict or a list:

        call("remove", unsafe("selected"))  # remove(selected)
        call("save", {"ids": unsafe("selected")})  # save({"ids": selected})
    """
    if not _FUNCTION.match(function):
        raise ValueError(
            f"{function!r} is not a function name or a path to one. "
            "Write the whole thing with unsafe() if that is what you mean."
        )
    return Expression(f"{function}({', '.join(_argument(arg) for arg in args)})")


def _argument(value: Any) -> str:
    """
    A value as JavaScript: JSON, except that an Expression goes in as written
    wherever it sits, inside a dict or a list as much as on its own. Quoted
    whole by json.dumps, a nested one would arrive as a string.
    """
    if isinstance(value, Expression):
        return value
    if isinstance(value, Mapping):
        fields = (f"{dumps(name)}: {_argument(item)}" for name, item in value.items())
        return "{" + ", ".join(fields) + "}"
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_argument(item) for item in value) + "]"
    return dumps(value)


type Method = Literal["get", "post", "put", "patch", "delete"]

_METHODS: tuple[str, ...] = get_args(Method.__value__)


def ajax(
    url: str | Expression,
    *,
    target: str | Sequence[str],
    method: Method = "get",
    body: Mapping[str, Any] | None = None,
) -> Expression:
    """
    A request to one of your routes, with the response merged into the page.

        ajax(f"/invoices/{invoice.id}/", method="delete", target="invoices")

    Alpine AJAX's $ajax, written for you. target is the id, or the ids, of the
    elements whose contents the response replaces. It is required because
    $ajax would fall back to the id of the element the expression runs on,
    and fail on one without an id.

    body is sent as form fields, which a route's body model validates. A list
    or a dict in it arrives as one field holding JSON, the way $ajax sends
    them, so the route reads [3, 4] from "[3,4]". A None is left out, so the
    model's default applies rather than the text "null". A GET takes no body.

    Every value is quoted, the URL and the body's included. One that is
    already an Expression goes in as written, for what only the browser
    knows, as with call():

        ajax(url, method="post", target="invoices", body={"ids": unsafe("selected")})
    """
    targets = [target] if isinstance(target, str) else list(target)
    if not targets or not all(targets):
        raise ValueError("ajax() needs the id of at least one element to update.")
    # $ajax reads the ids out of one string split on spaces.
    if any(re.search(r"\s", each) for each in targets):
        raise ValueError(f"{targets!r} has an id with a space in it, which no id has.")
    # For a caller without a type checker: "GET" would slip past the check on
    # a GET's body below, and still be sent as a GET.
    if method not in _METHODS:
        raise ValueError(
            f"{method!r} is not a method; use one of {', '.join(_METHODS)}."
        )
    if body is not None and method == "get":
        raise ValueError(
            "A GET takes no body: $ajax would send it as the query string, which "
            "a route's body model never reads. Put the values in the URL, or "
            "send them with post."
        )
    options: dict[str, Any] = {
        "method": method,
        "target": " ".join(targets),
        # Without it $ajax leaves the page's x-sync elements alone, and a toast
        # the route raised, which arrives in the synced toast region, is
        # dropped. Forms and links sync by default; this matches them.
        "sync": True,
    }
    if body is not None:
        options["body"] = {
            name: value for name, value in body.items() if value is not None
        }
    return call("$ajax", url, options)


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
            "call(), ajax() or another helper, or wrap it in unsafe() if it "
            "really is code you wrote."
        )
    return value
