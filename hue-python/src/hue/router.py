import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import partialmethod
from http import HTTPStatus
from typing import Any, cast

from htmy import html

from hue.context import HueContext, HueContextArgs
from hue.exceptions import AJAXRequiredError
from hue.renderer import render_tree
from hue.types.core import Component, ComponentType

# Default HTTP status code for successful responses
DEFAULT_STATUS_CODE = HTTPStatus.OK


@dataclass(slots=True, frozen=True)
class HueResponse:
    """
    A structured response for fragment handlers.

    Wraps a component with a target ID and status code. The component is rendered
    inside a div with the target ID, which is necessary for Alpine AJAX to properly
    merge the content using innerHTML.

    Example:
        @router.fragment_post("login/")
        async def login(self, request, context):
            if not valid:
                # Returns 422 with error fragment wrapped in <div id="login-form">
                return HueResponse(
                    target="login-form",
                    component=LoginError(message="Invalid credentials"),
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            return SuccessFragment()
    """

    component: ComponentType
    target: str | None = None
    status_code: int = DEFAULT_STATUS_CODE

    def htmy(self, context: Any) -> Component:
        """Wrap the component in a div with the target ID for Alpine AJAX merging."""
        if self.target:
            return html.div(self.component, id=self.target)
        return self.component


@dataclass
class PathParseResult:
    path: str
    param_names: list[str]


# Type alias for view function results
# Can be: Component or HueResponse (for custom status codes and targets)
type ViewResult = Component | HueResponse
type AwaitableViewResult = ViewResult | Awaitable[ViewResult]

# Type alias for wrapped view functions (return HTML string + status code)
# Signature: (view_instance, request: T_Request, **kwargs) -> Awaitable[tuple[str, int]]
type WrappedViewFunc = Callable[..., Awaitable[tuple[str, int]]]

# Type alias for original view functions (return Component or HueResponse)
# Signature: (view_instance, request: T_Request, context: HueContext[T_Request],
#             **kwargs) -> ViewResult | Awaitable[ViewResult]
type ViewFunc = Callable[..., AwaitableViewResult]


@dataclass
class Route:
    """Represents a single route with its view function and metadata."""

    method: str
    path: str
    name: str
    view_func: WrappedViewFunc
    # List of parameter names extracted from path
    # Framework-specific routers can populate this based on their path syntax
    path_params: list[str] = field(default_factory=list)


class Router[T_Request]:
    """
    Framework-agnostic base router for defining routes in HueView.

    Fragment routes return HTML fragments (Component) and require AJAX requests.
    Page routes return full pages and don't require AJAX.
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []

    @property
    def routes(self) -> list[Route]:
        return self._routes.copy()

    def _normalize_path(self, path: str) -> str:
        """
        Normalize the path (e.g., strip leading slashes).
        """
        # Default: strip leading slash
        # Root path "/" becomes "" (empty string)
        return path.lstrip("/")

    def _parse_path_params(self, path: str) -> PathParseResult:
        """
        Parse the path parameters from the path.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        """
        Get framework-specific context arguments (request, CSRF token, etc.).
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    async def render(
        self,
        component: ComponentType,
        request: T_Request,
    ) -> str:
        """
        Render a Component to HTML string.

        This is framework-agnostic - it uses Renderer to convert Components to HTML.
        The renderer calls .htmy() on all components, so both fragments and full
        pages are rendered the same way.
        """
        return await render_tree(
            component, context_args=self._get_context_args(request)
        )

    def _is_ajax_request(self, request: T_Request) -> bool:
        """
        Check if the request is an AJAX request.

        Framework-specific routers should override this method to handle
        framework-specific header access.

        Returns True if the request has either:
        - X-Requested-With: XMLHttpRequest header, or
        - X-Alpine-Request: true header
        """
        headers = getattr(request, "headers", {})

        if hasattr(headers, "get"):
            is_ajax_req = headers.get("X-Requested-With") == "XMLHttpRequest"
            is_alpine_ajax_req = headers.get("X-Alpine-Request") == "true"
            return is_ajax_req or is_alpine_ajax_req

        return False

    def _wrap_view(
        self, view_func: ViewFunc, require_ajax: bool = True
    ) -> WrappedViewFunc:
        """
        Wrap a view function to automatically render Components and pass the hue
        context.

        The wrapped view returns a tuple of (html_string, status_code).
        View functions can return:
        - Component (uses default 200 status)
        - HueResponse (structured response with target, component, and status_code)
        """

        async def wrapped_view(
            view_instance: object, request: T_Request, **kwargs: Any
        ) -> tuple[str, int]:
            if require_ajax and not self._is_ajax_request(request):
                raise AJAXRequiredError()

            # Build context for the handler (without component yet)
            context_args: HueContextArgs[T_Request] = self._get_context_args(request)
            context: HueContext[T_Request] = HueContext(**context_args)

            # Call the original view function with self, request, context, and path
            # params
            view_func_result = view_func(view_instance, request, context, **kwargs)

            # Await if it's a coroutine
            while inspect.iscoroutine(view_func_result):
                view_func_result = await view_func_result

            # Extract component and status code based on return type
            if isinstance(view_func_result, HueResponse):
                # HueResponse: use its properties (htmy() wraps in div with target)
                component = cast(ComponentType, view_func_result)
                status_code = view_func_result.status_code
            else:
                # Plain Component: use default status
                component = cast(ComponentType, view_func_result)
                status_code = DEFAULT_STATUS_CODE

            rendered_html = await self.render(component, request)
            return rendered_html, status_code

        # Always return async wrapper (view functions should be async for rendering)
        return wrapped_view

    def _request(
        self, method: str, path: str, require_ajax: bool = True
    ) -> Callable[[ViewFunc], ViewFunc]:
        """
        Internal method to register a route.

        Used with partialmethod to create the route decorator methods.
        """

        def decorator(view_func: ViewFunc) -> ViewFunc:
            normalized_path = self._normalize_path(path)

            parsed_path = self._parse_path_params(normalized_path)
            wrapped_view = self._wrap_view(view_func, require_ajax=require_ajax)

            route = Route(
                name=view_func.__name__.lower(),
                method=method.upper(),
                path=parsed_path.path,
                view_func=wrapped_view,
                path_params=parsed_path.param_names,
            )

            self._routes.append(route)

            # Return the original view function for decorator chain.
            return view_func

        return decorator

    # Non-AJAX route decorator for full page loads (e.g., index routes)
    # Should not be used normally, but is useful for constructing the router manually.
    _page = partialmethod(_request, "GET", require_ajax=False)

    fragment_get = partialmethod(_request, "GET", require_ajax=True)
    fragment_post = partialmethod(_request, "POST", require_ajax=True)
    fragment_put = partialmethod(_request, "PUT", require_ajax=True)
    fragment_delete = partialmethod(_request, "DELETE", require_ajax=True)
    fragment_patch = partialmethod(_request, "PATCH", require_ajax=True)
