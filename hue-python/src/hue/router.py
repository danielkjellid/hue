import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import partialmethod
from typing import Any, cast

from htmy import Renderer

from hue.context import HueContext, HueContextArgs
from hue.types.core import Component, ComponentType

# Type alias for wrapped view functions (return HTML string)
# Signature: (view_instance, request: T_Request, **kwargs) -> Awaitable[str]
type WrappedViewFunc = Callable[..., Awaitable[str]]

# Type alias for original view functions (return Component)
# Signature: (view_instance, request: T_Request, context: HueContext[T_Request],
#             **kwargs) -> Component | Awaitable[Component]
type ViewFunc = Callable[..., Component | Awaitable[Component]]


@dataclass
class PathParseResult:
    path: str
    param_names: list[str]


@dataclass
class Route:
    """Represents a single route with its view function and metadata."""

    method: str
    path: str
    view_func: WrappedViewFunc
    # List of parameter names extracted from path
    # Framework-specific routers can populate this based on their path syntax
    path_params: list[str] = field(default_factory=list)


class Router[T_Request]:
    """
    Framework-agnostic base router for defining routes in HueView.

    Routes should be AJAX requests and return fragments (Component).
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

    def _build_context(
        self,
        component: ComponentType,
        request: T_Request,
    ) -> HueContext[T_Request]:
        """
        Build the hue context for the component and request.
        """
        context_args = self._get_context_args(request)
        return HueContext(component, **context_args)

    async def _render(
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
        context = self._build_context(component, request)
        renderer = Renderer()
        result: str = await renderer.render(context)
        return result

    def _wrap_view(self, view_func: ViewFunc) -> WrappedViewFunc:
        """
        Wrap a view function to automatically render Components and pass the hue
        context.
        """

        async def wrapped_view(
            view_instance: object, request: T_Request, **kwargs: Any
        ) -> str:
            is_ajax_req = False
            is_alpine_ajax_req = False
            headers = getattr(request, "headers", {})
            if hasattr(headers, "get"):
                is_ajax_req = headers.get("X-Requested-With") == "XMLHttpRequest"
                is_alpine_ajax_req = headers.get("X-Alpine-Request") == "true"

            if not is_ajax_req and not is_alpine_ajax_req:
                raise ValueError("Not an AJAX request")

            # Build context for the handler (without component yet)
            context_args: HueContextArgs[T_Request] = self._get_context_args(request)
            context: HueContext[T_Request] = HueContext(**context_args)

            # Call the original view function with self, request, context, and path
            # params
            view_func_result = view_func(view_instance, request, context, **kwargs)

            # Await if it's a coroutine
            while inspect.iscoroutine(view_func_result):
                view_func_result = await view_func_result

            # After awaiting, result is Component, not Awaitable[Component]
            # Type checker needs help understanding this
            component = cast(ComponentType, view_func_result)

            return await self._render(component, request)

        # Always return async wrapper (view functions should be async for rendering)
        return wrapped_view

    def _request(self, method: str, path: str) -> Callable[[ViewFunc], ViewFunc]:
        """
        Internal method to register a route.

        Used with partialmethod to create the route decorator methods.
        """

        def decorator(view_func: ViewFunc) -> ViewFunc:
            normalized_path = self._normalize_path(path)

            parsed_path = self._parse_path_params(normalized_path)
            wrapped_view = self._wrap_view(view_func)

            route = Route(
                method=method.upper(),
                path=parsed_path.path,
                view_func=wrapped_view,
                path_params=parsed_path.param_names,
            )

            self._routes.append(route)

            # Return the original view function for decorator chain.
            return view_func

        return decorator

    ajax_get = partialmethod(_request, "GET")
    ajax_post = partialmethod(_request, "POST")
    ajax_put = partialmethod(_request, "PUT")
    ajax_delete = partialmethod(_request, "DELETE")
    ajax_patch = partialmethod(_request, "PATCH")
