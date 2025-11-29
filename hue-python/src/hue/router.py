from collections.abc import Callable
from dataclasses import dataclass
from functools import partialmethod


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

        # Create route
        route = Route(
            method=method.upper(),
            path=final_path,
            handler=handler,
            is_ajax=is_ajax,
            path_params=param_names,
        )

        self._routes.append(route)
        return handler

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
