import inspect
import json
from collections.abc import Awaitable, Callable, Iterable
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from functools import partial, partialmethod
from http import HTTPStatus
from typing import Any, cast, get_type_hints

from htmy import html
from pydantic import TypeAdapter, ValidationError
from pydantic.json_schema import (
    GenerateJsonSchema,
    JsonSchemaValue,
    JsonSchemaWarningKind,
)

from hue.context import HueContext, HueContextArgs
from hue.exceptions import AJAXRequiredError, BodyValidationError, DuplicateRouteError
from hue.renderer import render_tree
from hue.toast import toast
from hue.types.core import Component, ComponentType
from hue.ui.molecules.datatable import resolve_value
from hue.ui.molecules.toast import region_fragment

DEFAULT_STATUS_CODE = HTTPStatus.OK

# The name a view's page is registered under, so that something drawn on the
# page, such as a declared table, can reverse the page it is on.
PAGE_ROUTE = "index"


@dataclass(slots=True, frozen=True)
class HueResponse:
    """
    A fragment response with an explicit status code and merge target.

    The component is rendered inside a div carrying the target id, which is what
    Alpine AJAX needs to merge the content into the matching element on the page.

        return HueResponse(
            target="login-form",
            component=LoginError(message="Invalid credentials"),
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    """

    component: ComponentType
    target: str | None = None
    status_code: int = DEFAULT_STATUS_CODE

    def htmy(self, context: Any) -> Component:
        if self.target:
            return html.div(self.component, id=self.target)
        return self.component


@dataclass(slots=True)
class RawResponse:
    """
    A framework response (an HttpResponse, a redirect) returned from a handler,
    passed through untouched so the framework integration can return it as-is.
    """

    response: Any


@dataclass
class PathParseResult:
    path: str
    param_names: list[str]


# Handlers return a component, a HueResponse, or a framework response object,
# optionally awaited. The framework response case makes this effectively Any.
type ViewResult = Component | HueResponse | Any
type AwaitableViewResult = ViewResult | Awaitable[ViewResult]
type ViewFunc = Callable[..., AwaitableViewResult]

# A wrapped handler resolves to (html, status_code) or a passthrough RawResponse.
type WrappedViewResult = tuple[str, int] | RawResponse
type WrappedViewFunc = Callable[..., Awaitable[WrappedViewResult]]


@dataclass
class Route:
    """
    A registered route: its HTTP method, path, name and wrapped handler.
    """

    method: str
    path: str
    name: str
    view_func: WrappedViewFunc
    # Names of the parameters captured from the path, populated by the
    # framework-specific path parser.
    path_params: list[str] = field(default_factory=list)


def check_unique_routes(routes: Iterable[Route]) -> None:
    """
    Refuse two routes on one path and method.

    Called by a framework integration on every route it is about to serve,
    the index included: a fragment on the index's own path and method would
    otherwise take the page's place.
    """
    seen: dict[tuple[str, str], Route] = {}
    for route in routes:
        if earlier := seen.get((route.path, route.method)):
            raise DuplicateRouteError(
                f"Two {route.method} routes on {'/' + route.path!r}: "
                f"{earlier.name} and {route.name}. Give one of them its own "
                "path or method."
            )
        seen[(route.path, route.method)] = route


def _resolve_body_type(view_func: ViewFunc) -> type | None:
    """
    The annotation of a handler's body parameter, or None when it has none.

    A body parameter that cannot be resolved is an error at registration time
    rather than a silent fallthrough that would only surface as a confusing
    missing-argument TypeError when the route is first hit.
    """
    if "body" not in inspect.signature(view_func).parameters:
        return None
    try:
        body_type = get_type_hints(view_func).get("body")
    except (NameError, TypeError) as e:
        raise TypeError(
            f"Cannot resolve the type annotation of the 'body' parameter on "
            f"{view_func.__qualname__}: {e}"
        ) from e
    if body_type is None:
        raise TypeError(
            f"The 'body' parameter on {view_func.__qualname__} must be annotated "
            "with the type to parse the request body into."
        )
    return body_type


class _FormSchema(GenerateJsonSchema):
    """
    A JSON schema generator that never fails or warns over a field a form
    cannot post anyway.

    The schema is only read for which fields are lists, so an arbitrary class
    with no JSON form, or a default that cannot be serialized, should not stop
    a route from registering or print a warning when it does.
    """

    def handle_invalid_for_json_schema(
        self, schema: Any, error_info: str
    ) -> JsonSchemaValue:
        return {}

    def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        pass


def _resolve(
    node: JsonSchemaValue, defs: dict[str, JsonSchemaValue]
) -> JsonSchemaValue:
    # A recursive model, a nested one or a type alias sits in $defs.
    while "$ref" in node:
        node = defs[node["$ref"].rsplit("/", 1)[-1]]
    return node


def _is_array(node: JsonSchemaValue, defs: dict[str, JsonSchemaValue]) -> bool:
    node = _resolve(node, defs)
    arms = node.get("anyOf", []) + node.get("oneOf", [])
    return node.get("type") == "array" or any(_is_array(arm, defs) for arm in arms)


def _sequence_fields(adapter: TypeAdapter[Any]) -> frozenset[str]:
    """
    The names in a form that a body read by this adapter takes as a list.

    A form is only names and strings, and a name posted twice means a list
    to one field and a mistake to another, so the body's own type decides.
    The adapter's validation schema is asked rather than the type hints,
    because it already knows the names pydantic validates from, Optional and
    NotRequired unwrapped, and that a Json field is one string on the wire.
    Attribute names are included alongside aliases, for a model that is
    populated by name.
    """
    names: set[str] = set()
    for by_alias in (True, False):
        schema = adapter.json_schema(
            by_alias=by_alias, mode="validation", schema_generator=_FormSchema
        )
        defs = schema.get("$defs", {})
        properties = _resolve(schema, defs).get("properties", {})
        names.update(name for name, node in properties.items() if _is_array(node, defs))
    return frozenset(names)


class Router[T_Request]:
    """
    Framework-agnostic base router for defining routes on a view.

    Fragment routes return HTML fragments and require AJAX requests. The page
    route returns a full page and does not. Framework integrations subclass this
    and implement the request accessors.
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []

    @property
    def routes(self) -> list[Route]:
        return self._routes.copy()

    def _normalize_path(self, path: str) -> str:
        # The root path "/" becomes "".
        return path.lstrip("/")

    def _parse_path_params(self, path: str) -> PathParseResult:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    async def render(self, component: ComponentType, request: T_Request) -> str:
        """
        Render a component to an HTML string with this request's context.
        """
        return await render_tree(
            component, context_args=self._get_context_args(request)
        )

    async def _render_pending_toasts(self, request: T_Request) -> str:
        """
        The toasts nothing has rendered yet, under the region's id.

        A page renders its own in the region it already has, which empties the
        queue; a fragment has no region, so they ride along behind whatever it
        returned and Alpine AJAX merges them into the one on the page.
        """
        pending = toast.drain()
        if not pending:
            return ""
        return await self.render(region_fragment(pending), request)

    def _is_ajax_request(self, request: T_Request) -> bool:
        """
        True when the request carries an X-Requested-With: XMLHttpRequest or an
        X-Alpine-Request: true header.

        Assumes request.headers is a case-insensitive mapping, which holds for
        Django, Starlette and most frameworks. Override otherwise.
        """
        headers = getattr(request, "headers", None)
        if headers is None:
            return False
        return (
            headers.get("X-Requested-With") == "XMLHttpRequest"
            or headers.get("X-Alpine-Request") == "true"
        )

    def _get_request_body(self, request: T_Request) -> str:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_request_content_type(self, request: T_Request) -> str:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_form_values(self, request: T_Request) -> dict[str, list[str]]:
        """
        The submitted form with every value kept, not just the last.

        A column of checkboxes, or a multiple Combobox, is several values
        under one name, so flattening the form here would lose all but one.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_query_values(self, request: T_Request) -> dict[str, list[str]]:
        """
        The query string with every value kept, not just the last.

        A set of checkboxes sharing a name is how a browser submits a
        list, and flattening that to a dict keeps one of them - which is
        exactly the case a multiple-choice filter is.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _url_for(self, request: T_Request, name: str, **params: Any) -> str:
        """
        Where one of this router's own routes lives, for this request.

        A route's path is written relative to wherever the view ends up
        mounted, so nothing here can spell the whole URL - only the
        framework knows what the view was included under. The request is
        passed because the answer depends on it: the same view mounted
        twice has two URLs, and the one you want is the one the reader is
        already browsing.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _form_fields(self) -> AbstractSet[str]:
        """
        The fields a framework adds to a form that belong to no one's state,
        such as its CSRF token, so they are not echoed back into links.
        """
        return frozenset()

    def _passes_through(self, error: Exception) -> bool:
        """
        Whether an exception from a handler is an answer to send rather than a
        failure to report, such as a framework's permission-denied or not-found.
        The base router knows none.
        """
        return False

    def _narrow_to(self, rows: Any, key: str, values: list[str]) -> Any:
        """
        The rows whose value at key is one of values.

        This is how an action is kept to rows the reader could see: the ids
        a browser posts are narrowed to the rows the table would show. Here
        the rows are walked, which is what a list is for. An integration
        whose rows are a query overrides it to filter in the database.
        """
        wanted = set(values)
        return [row for row in rows if str(resolve_value(row, key)) in wanted]

    async def _call_view_func(
        self,
        view_func: ViewFunc,
        view_instance: object,
        request: T_Request,
        context: HueContext[T_Request],
        **kwargs: Any,
    ) -> Any:
        """
        Call the handler and return its result.

        A coroutine function is awaited on the loop. Anything else goes
        through _run_sync, which is where an integration keeps blocking work
        off the loop, so a sync handler gets that for free. An async handler
        behind a plain sync decorator looks sync until it is called, so a
        result that turns out to be awaitable is awaited as well.
        """
        if inspect.iscoroutinefunction(view_func):
            return await view_func(view_instance, request, context, **kwargs)
        result = await self._run_sync(
            partial(view_func, view_instance, request, context, **kwargs)
        )
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        """
        Call a blocking function from inside an async route.

        This is for a sync handler, and for work a route does on a handler's
        behalf, such as fetching the rows a table needs or running an action.
        The base router calls it directly. An integration whose ORM refuses to
        run on the event loop overrides it to run the call in a thread.
        """
        return func(*args)

    def _parse_body(
        self,
        request: T_Request,
        adapter: TypeAdapter[Any],
        sequence_fields: AbstractSet[str],
    ) -> Any:
        """
        Parse the request body with the given Pydantic adapter.

        JSON bodies are decoded first; anything else is treated as form data,
        where the names in sequence_fields keep every value posted under them
        and the rest keep the last.
        Raises BodyValidationError when decoding or validation fails.
        """
        content_type = self._get_request_content_type(request)

        if "application/json" in content_type:
            try:
                # Read inside the try: an integration decodes the bytes here,
                # and a body that is not UTF-8 is as invalid as bad JSON.
                raw_body = self._get_request_body(request)
                data = json.loads(raw_body) if raw_body else {}
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise BodyValidationError(
                    errors=[{"type": "json_invalid", "msg": str(e)}]
                ) from e
        else:
            data = {
                name: values if name in sequence_fields else values[-1]
                for name, values in self._get_form_values(request).items()
                if values
            }

        try:
            return adapter.validate_python(data)
        except ValidationError as e:
            raise BodyValidationError(errors=e.errors()) from e

    def _wrap_view(
        self, view_func: ViewFunc, require_ajax: bool = True
    ) -> WrappedViewFunc:
        """
        Wrap a handler so it receives a HueContext, gets its body parameter parsed
        (when annotated), and has its component result rendered to HTML.

        The wrapped handler returns (html, status_code), or a RawResponse when
        the handler returned a framework response object.
        """
        body_type = _resolve_body_type(view_func)
        # Built once here: constructing a TypeAdapter per request is roughly two
        # orders of magnitude slower than validating with an existing one.
        body_adapter: TypeAdapter[Any] | None = (
            TypeAdapter(body_type) if body_type is not None else None
        )
        sequence_fields = (
            _sequence_fields(body_adapter) if body_adapter is not None else frozenset()
        )

        async def wrapped_view(
            view_instance: object, request: T_Request, **kwargs: Any
        ) -> WrappedViewResult:
            if require_ajax and not self._is_ajax_request(request):
                raise AJAXRequiredError()

            if body_adapter is not None:
                kwargs["body"] = self._parse_body(
                    request, body_adapter, sequence_fields
                )

            # The queue lives exactly as long as the request, so toast() is a
            # plain call from anywhere in the handler and nothing it raises
            # can reach the next one.
            token = toast.open()
            try:
                context = HueContext(**self._get_context_args(request))
                result = await self._call_view_func(
                    view_func, view_instance, request, context, **kwargs
                )

                if isinstance(result, HueResponse):
                    status_code = result.status_code
                elif hasattr(result, "status_code"):
                    # Anything else with a status code is a framework response,
                    # which renders nothing for a toast to ride along with. When
                    # this router opened the queue, nothing outside will carry
                    # them on either, and dropping one quietly is worse than
                    # saying so.
                    if token is not None and toast.drain():
                        raise RuntimeError(
                            "A toast was raised by a handler that returned a "
                            "response with no markup to carry it, such as a "
                            "redirect. Add a middleware that carries toasts "
                            "across a response like that (HueToastMiddleware "
                            "in hue_django), or return a fragment instead."
                        )
                    return RawResponse(response=result)
                else:
                    status_code = DEFAULT_STATUS_CODE

                rendered_html = await self.render(cast(ComponentType, result), request)
                rendered_html += await self._render_pending_toasts(request)
                return rendered_html, status_code
            finally:
                toast.close(token)

        return wrapped_view

    def _request(
        self,
        method: str,
        path: str,
        require_ajax: bool = True,
        name: str | None = None,
    ) -> Callable[[ViewFunc], ViewFunc]:
        def decorator(view_func: ViewFunc) -> ViewFunc:
            parsed_path = self._parse_path_params(self._normalize_path(path))

            self._routes.append(
                Route(
                    name=name or view_func.__name__.lower(),
                    method=method.upper(),
                    path=parsed_path.path,
                    view_func=self._wrap_view(view_func, require_ajax=require_ajax),
                    path_params=parsed_path.param_names,
                )
            )
            # Return the original so the method stays callable on the view.
            return view_func

        return decorator

    # A full-page GET route that is not AJAX-gated. Framework views use this to
    # register the index; fragments use the decorators below.
    page = partialmethod(_request, "GET", require_ajax=False)

    fragment_get = partialmethod(_request, "GET", require_ajax=True)
    fragment_post = partialmethod(_request, "POST", require_ajax=True)
    fragment_put = partialmethod(_request, "PUT", require_ajax=True)
    fragment_delete = partialmethod(_request, "DELETE", require_ajax=True)
    fragment_patch = partialmethod(_request, "PATCH", require_ajax=True)
