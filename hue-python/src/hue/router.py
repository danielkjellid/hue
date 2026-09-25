import inspect
import json
from collections.abc import Awaitable, Callable
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from functools import partialmethod
from http import HTTPStatus
from typing import Any, cast, get_type_hints

from htmy import html
from pydantic import TypeAdapter, ValidationError

from hue.context import HueContext, HueContextArgs
from hue.exceptions import AJAXRequiredError, BodyValidationError
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

    def _get_form_data(self, request: T_Request) -> dict[str, Any]:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_form_values(self, request: T_Request) -> dict[str, list[str]]:
        """
        The submitted form with every value kept, not just the last.

        Separate from _get_form_data because the flat dict that returns keeps
        only the last value under each name, and a column of checkboxes is
        several values under one.
        """
        return {
            name: [str(value)] for name, value in self._get_form_data(request).items()
        }

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
        Call the handler and return its result, awaiting it if needed.

        Framework integrations override this when sync handlers need special
        treatment, for example Django's sync_to_async so ORM access works.
        """
        result = view_func(view_instance, request, context, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        """
        Call a blocking function from inside an async route.

        This is for work a route does on a handler's behalf, such as fetching
        the rows a table needs or running an action. The base router calls it
        directly. An integration whose ORM refuses to run on the event loop
        overrides it to run the call in a thread, as _call_view_func does for a
        sync handler.
        """
        return func(*args)

    def _parse_body(self, request: T_Request, adapter: TypeAdapter[Any]) -> Any:
        """
        Parse the request body with the given Pydantic adapter.

        JSON bodies are decoded first; anything else is treated as form data.
        Raises BodyValidationError when decoding or validation fails.
        """
        content_type = self._get_request_content_type(request)

        if "application/json" in content_type:
            raw_body = self._get_request_body(request)
            try:
                data = json.loads(raw_body) if raw_body else {}
            except json.JSONDecodeError as e:
                raise BodyValidationError(
                    errors=[{"type": "json_invalid", "msg": str(e)}]
                ) from e
        else:
            data = self._get_form_data(request)

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

        async def wrapped_view(
            view_instance: object, request: T_Request, **kwargs: Any
        ) -> WrappedViewResult:
            if require_ajax and not self._is_ajax_request(request):
                raise AJAXRequiredError()

            if body_adapter is not None:
                kwargs["body"] = self._parse_body(request, body_adapter)

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
                    # Anything else with a status code is a framework response.
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
