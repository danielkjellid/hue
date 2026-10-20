"""
What a declared DataTable and a declared Calendar have in common.

Both keep their state in the page's URL under their key, carry the rest of
the query through every link and form, register one POST route for their
actions, and answer a handler that failed or refused on the page itself.
This is that part, written once.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Collection, Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Protocol
from urllib.parse import urlencode

from htmy import Context, html

from hue import toast
from hue.router import PAGE_ROUTE, HueResponse
from hue.types.core import ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import TextInput
from hue.utils import render_if

type Pairs = tuple[tuple[str, str], ...]


class Routes(Protocol):
    """
    What a declaration needs from the router it is handed: somewhere to
    register its action route, and the framework's answers to the questions
    only the framework can answer.
    """

    def fragment_post(self, path: str) -> Callable[[Any], Any]: ...
    def _get_query_values(self, request: Any) -> dict[str, list[str]]: ...
    def _get_form_values(self, request: Any) -> dict[str, list[str]]: ...
    def _url_for(self, request: Any, name: str, **params: Any) -> str: ...
    def _refusal(self, error: Exception) -> HTTPStatus | None: ...
    def _csrf_field(self) -> str | None: ...
    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R: ...


def one(asked: Mapping[str, list[str]], name: str) -> str | None:
    """
    The one value a parameter holds, or the last of several.
    """
    values = asked.get(name)
    return values[-1] if values else None


def many(asked: Mapping[str, list[str]], name: str) -> tuple[str, ...]:
    """
    Every value a parameter holds, however it was spelled.

    A browser repeats the name once per checkbox, while the links a
    declaration builds join the values with commas, since that is what
    someone editing a query string by hand would write. Both read the same.
    """
    return tuple(
        part for value in asked.get(name, ()) for part in value.split(",") if part
    )


def bound_from[B](context: Context, kind: type[B], component: object, by: str) -> B:
    """
    The binding a component is rendered inside, or an error saying what is
    missing. Every part reads the same binding, so none of them is handed
    the request.
    """
    found = context.get(kind)
    if isinstance(found, kind):
        return found
    raise ValueError(
        f"{type(component).__name__} draws part of a {by.lower()} bound to a "
        f"request, and there is none here. It is drawn by {by}.from_state()."
    )


@dataclass(frozen=True, slots=True)
class Urls:
    """
    Where a declaration lives, for one request: the page it is drawn on,
    which every link and form points at, and the route of each action.
    Reversed once per binding rather than once per link, and never written
    by hand, so include() can move the view under a prefix.
    """

    read: str
    act: Mapping[str, str]


class Bound:
    """
    The part of a binding that writes links: its own state under its key,
    and everything else the URL held, such as another table's state on the
    same page, sent back unchanged.
    """

    __slots__ = ()

    declaration: Declaration[Any]
    urls: Urls
    others: Pairs

    @property
    def key(self) -> str:
        return self.declaration.key

    def _params(self, state: Any) -> Mapping[str, str]:
        """
        The parts of state that differ from the defaults, by their short
        names.
        """
        raise NotImplementedError

    def query(
        self, state: Any, *, without: AbstractSet[str] = frozenset()
    ) -> list[tuple[str, str]]:
        """
        The query string for state, as pairs: this one's own part under its
        key, apart from without, and everything else as it was.
        """
        own = [
            (self.declaration.param(name), value)
            for name, value in self._params(state).items()
            if name not in without
        ]
        return [*self.others, *own]

    def _link(self, state: Any) -> str:
        asked = self.query(state)
        return self.urls.read + (f"?{urlencode(asked)}" if asked else "")


def search_id(key: str) -> str:
    """
    The id of the search box's form, which the fields it carries name.
    """
    return f"{key}-search"


def csrf(
    declared: Declaration[Any], token: str, *, form: str | None = None
) -> ComponentType:
    """
    The framework's CSRF token as a hidden field, for a form that has to
    post without the script, or nothing for a framework without one.
    """
    return render_if(
        declared._router._csrf_field(),
        lambda name: html.input_(type="hidden", name=name, value=token, form=form),
    )


def carried(
    pairs: Iterable[tuple[str, str]], *, form: str | None = None
) -> tuple[ComponentType, ...]:
    """
    A query as hidden fields, tied to form when they sit outside it.
    """
    return tuple(
        html.input_(type="hidden", name=name, value=value, form=form)
        for name, value in pairs
    )


class Declaration[R: Routes]:
    """
    A table or a calendar declared once, at class scope, and the one route
    its actions post to, {key}/<action>/.
    """

    def __init__(self, router: R, key: str) -> None:
        self.key = key
        self._router = router
        # One spelling of the route's name, used to register it and to find
        # it again. Two declarations on one view would otherwise both call
        # theirs "act", since the router takes a route's name off the
        # handler's __name__ as it decorates.
        self._act_route = f"{key}_act"

    def param(self, name: str) -> str:
        """
        What one part of the state is called in the URL. Under the key,
        because a page can hold two and a URL holds both their states.
        """
        return f"{self.key}-{name}"

    def _split(
        self,
        values: Mapping[str, list[str]],
        names: Iterable[str],
        skipped: AbstractSet[str] = frozenset(),
    ) -> tuple[dict[str, list[str]], Pairs]:
        """
        A query or a posted form, split into the parts named, by their
        short names, and everything else, which goes back out as it came.

        Exact names rather than everything under the key's prefix, because
        a key can start another: a table called a would otherwise take the
        state of a table called a-b for its own. The framework's own field,
        its CSRF token, is nobody's and goes nowhere, and neither does
        anything skipped.
        """
        own_names = {self.param(name): name for name in names}
        dropped = {*skipped, self._router._csrf_field()}
        own: dict[str, list[str]] = {}
        others: list[tuple[str, str]] = []
        for name, found in values.items():
            if name in own_names:
                own[own_names[name]] = found
            elif name not in dropped:
                others.extend((name, value) for value in found)
        return own, tuple(others)

    def _urls_for(self, request: Any, actions: Iterable[str]) -> Urls:
        return Urls(
            read=self._router._url_for(request, PAGE_ROUTE),
            act={
                name: self._router._url_for(request, self._act_route, action=name)
                for name in actions
            },
        )

    def _register_route(
        self,
        actions: Collection[str],
        serve: Callable[[Any, Any, str], Awaitable[Any]],
    ) -> None:
        """
        The route the actions post to, which hands serve the request, the
        context and the action, and answers anything else with a 404.
        Reading needs no route of its own: the page reads the query string.
        """

        async def act(view: Any, request: Any, context: Any, action: str) -> Any:
            if action not in actions:
                return HueResponse(
                    component=html.p(f"{self.key} has no action called {action!r}."),
                    status_code=HTTPStatus.NOT_FOUND,
                )
            return await serve(request, context, action)

        # Named before it is registered, not after: the router takes a
        # route's name off __name__ as it decorates.
        act.__name__ = self._act_route
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)

    async def _run(
        self,
        request: Any,
        handler: Callable[..., Any],
        given: Any,
        *,
        label: str,
        description: str,
    ) -> HTTPStatus:
        """
        A handler, run off the event loop, and the status to answer with.

        Whatever it raises is answered on the page with a toast, and the
        caller draws the state as it now is. A refusal, a not found or a
        permission denied, keeps the framework's status, because the
        framework's own page has no element in it for the browser to swap,
        and the form would be submitted again as a plain request, landing
        the reader on that page. Anything else is logged with its
        traceback, since nothing is raised for an error tracker to catch.
        It is logged under the module that declares the table or calendar,
        where an app's log config already points.
        """
        try:
            await self._router._run_sync(handler, request, given)
        except Exception as error:
            refused = self._router._refusal(error)
            if refused is None:
                logging.getLogger(type(self).__module__).exception(
                    "%s: the %r action failed", self.key, label
                )
            toast.danger(f"{label} failed", description=description)
            return refused or HTTPStatus.INTERNAL_SERVER_ERROR
        return HTTPStatus.OK


class SearchInput(TextInput):
    """
    A text input with the search type, which gives it the search role and a
    search key on a phone's keyboard. Not exported: a search box is a GET
    form around one of these, which search_form builds.
    """

    _input_type = "search"


# How long a search box waits after the last keystroke before it submits.
# Long enough that a word typed at speed is one request rather than five,
# short enough that the rows have moved by the time you look at them.
SEARCH_DELAY = "300ms"


def search_form(
    declared: Declaration[Any],
    *,
    param: str,
    label: str,
    value: str,
    read: str,
    target: str,
) -> ComponentType:
    """
    The search box's own GET form, under search_id. A form because Enter
    already submits one and x-target only turns that into a swap, so search
    works with Alpine off; typing submits it after a pause, and Escape
    empties it.
    """
    key = declared.key
    field = (
        SearchInput()
        .name(declared.param(param))
        .id(f"{key}-{param}")
        .size("sm")
        .label(label)
        .hidden_label()
        .placeholder(label)
        .value(value)
        .leading_icon(HueIcon("search"))
    )
    # Stopped, so an escape that empties the box is not also an escape that
    # closes whatever the box is inside. An empty box lets it through.
    field._attrs["x-on:keydown.escape"] = (
        "if ($el.value) { $event.stopPropagation(); $el.value = ''; "
        "$el.form.requestSubmit() }"
    )
    return html.form(
        field,
        id=search_id(key),
        method="get",
        action=read,
        # The free space in the band up to a readable cap: a field as wide
        # as the band reads as a search of the page.
        class_="min-w-0 flex-1 basis-64 sm:max-w-80",
        **{
            # replace rather than push: a word typed at speed would
            # otherwise be a history entry per pause in it.
            "x-target.replace": target,
            f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )
