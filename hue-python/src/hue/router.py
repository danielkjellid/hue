import inspect
from collections.abc import Callable
from dataclasses import dataclass
from functools import partialmethod
from typing import Any

from htmy import Renderer

from hue.context import HueContext, HueContextArgs


@dataclass
class Route:
    """Represents a single route with its handler and metadata."""

    method: str
    path: str
    handler: Callable
    is_ajax: bool = False
    # List of parameter names extracted from path
    # Framework-specific routers can populate this based on their path syntax
    path_params: list[str] = None

    def __post_init__(self):
        if self.path_params is None:
            self.path_params = []


class Router[T_Request]:
    """
    Framework-agnostic base router for defining routes in HueView.

    Routes can be regular (full page) or AJAX (fragments).
    Path parameter parsing is framework-specific and should be handled
    by framework-specific router subclasses.

    Example:
        class MyView(HueView):
            router = Router[HttpRequest]()

            @router.get("/")
            async def index(self, request: HttpRequest):
                return html.div("Index")

            @router.ajax_get("comments/")
            async def comments(self, request: HttpRequest):
                return html.div("Comments")
    """

    def __init__(self):
        # Store routes as: (method, path_pattern) -> Route
        self._routes: list[Route] = []

    def _normalize_path(self, path: str) -> str:
        """
        Normalize the path (e.g., strip leading slashes).

        Can be overridden by framework-specific routers for custom normalization.
        """
        # Default: strip leading slash
        # Root path "/" becomes "" (empty string)
        return path.lstrip("/")

    def _parse_path_params(self, path: str) -> tuple[str, list[str]]:
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _is_ajax_request(self, request: object) -> bool:
        """
        Check if the request is an AJAX request.

        Framework-specific routers can override this to provide
        framework-specific AJAX detection.

        Default implementation checks for X-Requested-With header.

        Args:
            request: The framework request object

        Returns:
            True if the request is an AJAX request
        """
        # Default: check for X-Requested-With header
        # Framework-specific routers can override this
        headers = getattr(request, "headers", {})
        if hasattr(headers, "get"):
            return headers.get("X-Requested-With") == "XMLHttpRequest"
        return False

    def _get_context_args(
        self, view_instance: object, request: object
    ) -> HueContextArgs:
        """
        Get framework-specific context arguments (request, CSRF token, etc.).

        Framework-specific routers must override this to provide
        framework-specific context.

        Args:
            view_instance: The view instance
            request: The framework request object

        Returns:
            HueContextArgs dictionary with request and csrf_token
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    async def _render(
        self, component_or_view: Any, view_instance: object, request: object
    ) -> str:
        """
        Render a Component or View to HTML string.

        This is framework-agnostic - it uses Renderer to convert Components to HTML.
        The renderer calls .htmy() on all components, so both fragments and full
        pages are rendered the same way.

        For full pages, pass the view_instance itself (which has htmy() that creates
        the full page structure). For fragments, pass the component directly.

        Args:
            component_or_view: The Component to render (fragment) or View instance
                (full page)
            view_instance: The view instance (for context)
            request: The framework request object

        Returns:
            HTML string of the rendered component
        """
        context_args = self._get_context_args(view_instance, request)
        # Wrap in a HueContext and render it
        # The renderer will call .htmy() on component_or_view
        context = HueContext(component_or_view, **context_args)
        renderer = Renderer()
        return await renderer.render(context)

    def _wrap_handler(self, handler: Callable, is_ajax: bool) -> Callable:
        """
        Wrap a handler to automatically render Components.

        This is core logic - handlers return Components, and this wrapper
        automatically renders them to HTML (fragment or full page).

        Args:
            handler: The original handler function
            is_ajax: Whether this is an AJAX route (fragment) or full page

        Returns:
            Wrapped handler that returns HTML string instead of Component
        """

        async def wrapped_handler(view_instance, request, **kwargs):
            # Call the original handler
            handler_result = handler(view_instance, request, **kwargs)

            # Await if it's a coroutine
            while inspect.iscoroutine(handler_result):
                handler_result = await handler_result

            component = handler_result

            # Determine if this should be a full page or fragment:
            # - Explicit AJAX routes always return fragments
            # - Regular routes return fragments if accessed via AJAX,
            #   otherwise full page
            is_ajax_request = self._is_ajax_request(request)

            if is_ajax or is_ajax_request:
                # Fragment: render component directly
                return await self._render(component, view_instance, request)
            else:
                # Full page: store component for view's body() to use,
                # then render the view instance itself
                view_instance._router_component = component
                try:
                    return await self._render(view_instance, view_instance, request)
                finally:
                    delattr(view_instance, "_router_component")

        # Always return async wrapper (handlers should be async for rendering)
        return wrapped_handler

    def _register(
        self,
        method: str,
        path: str,
        handler: Callable,
        is_ajax: bool = False,
    ) -> Callable:
        """Register a route handler."""
        # Normalize path (framework-specific routers can override)
        normalized_path = self._normalize_path(path)

        # Parse path parameters (framework-specific routers can override)
        final_path, param_names = self._parse_path_params(normalized_path)

        # Wrap handler with rendering logic (framework-specific routers can override)
        wrapped_handler = self._wrap_handler(handler, is_ajax)

        # Create route
        route = Route(
            method=method.upper(),
            path=final_path,
            handler=wrapped_handler,
            is_ajax=is_ajax,
            path_params=param_names,
        )

        self._routes.append(route)
        return handler  # Return original handler for decorator chain

    def _request(
        self, method: str, is_ajax: bool, path: str
    ) -> Callable[[Callable], Callable]:
        """
        Internal method to register a route.

        Used with partialmethod to create the route decorator methods.
        """

        def decorator(handler: Callable) -> Callable:
            return self._register(method, path, handler, is_ajax=is_ajax)

        return decorator

    get = partialmethod(_request, "GET", False)
    ajax_get = partialmethod(_request, "GET", True)
    ajax_post = partialmethod(_request, "POST", True)
    ajax_put = partialmethod(_request, "PUT", True)
    ajax_delete = partialmethod(_request, "DELETE", True)
    ajax_patch = partialmethod(_request, "PATCH", True)

    def get_routes(self) -> list[Route]:
        """Get all registered routes."""
        return self._routes.copy()

    def find_route(
        self,
        method: str,
        path: str,
        is_ajax: bool | None = None,
    ) -> Route | None:
        """
        Find a route by method and path.

        This is a simple implementation - in a real scenario, you'd want
        to match Django URL patterns properly. This is mainly for testing.
        """
        method = method.upper()
        for route in self._routes:
            if route.method == method:
                if is_ajax is not None and route.is_ajax != is_ajax:
                    continue
                # Simple path matching (Django will handle the actual matching)
                if route.path == path or route.path.rstrip("/") == path.rstrip("/"):
                    return route
        return None
