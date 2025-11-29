import re
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Route:
    """Represents a single route with its handler and metadata."""

    method: str
    path: str
    handler: Callable
    is_ajax: bool = False
    # List of parameter names from path like <int:comment_id>
    path_params: list[str] = None

    def __post_init__(self):
        if self.path_params is None:
            self.path_params = []


class Router[T_Request]:
    """
    Lightweight router for defining routes in HueView.

    Routes can be regular (full page) or AJAX (fragments).
    Supports Django URL patterns like "comments/<int:comment_id>/".

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

    def _parse_path_params(self, path: str) -> tuple[str, list[str]]:
        """
        Parse Django URL pattern parameters from path.

        Example:
            "comments/<int:comment_id>/" -> (
                "comments/<int:comment_id>/", ["comment_id"]
            )
            "users/<str:username>/posts/" -> (
                "users/<str:username>/posts/", ["username"]
            )

        Returns:
            Tuple of (django_path_pattern, list_of_param_names)
        """
        # Find all <type:name> patterns
        param_pattern = r"<(\w+):(\w+)>"
        matches = re.findall(param_pattern, path)
        param_names = [name for _, name in matches]

        # The path is already in Django URL pattern format, just return it
        return path, param_names

    def _register(
        self,
        method: str,
        path: str,
        handler: Callable,
        is_ajax: bool = False,
    ) -> Callable:
        """Register a route handler."""
        # Strip leading slash - Django URL patterns don't need it
        # Root path "/" becomes "" (empty string)
        normalized_path = path.lstrip("/")

        # Parse path parameters
        django_path, param_names = self._parse_path_params(normalized_path)

        # Create route
        route = Route(
            method=method.upper(),
            path=django_path,
            handler=handler,
            is_ajax=is_ajax,
            path_params=param_names,
        )

        self._routes.append(route)
        return handler

    def get(self, path: str) -> Callable:
        """Register a GET route (full page)."""
        return lambda handler: self._register("GET", path, handler, is_ajax=False)

    def ajax_get(self, path: str) -> Callable:
        """Register an AJAX GET route (fragment)."""
        return lambda handler: self._register("GET", path, handler, is_ajax=True)

    def ajax_post(self, path: str) -> Callable:
        """Register an AJAX POST route (fragment)."""
        return lambda handler: self._register("POST", path, handler, is_ajax=True)

    def ajax_put(self, path: str) -> Callable:
        """Register an AJAX PUT route (fragment)."""
        return lambda handler: self._register("PUT", path, handler, is_ajax=True)

    def ajax_delete(self, path: str) -> Callable:
        """Register an AJAX DELETE route (fragment)."""
        return lambda handler: self._register("DELETE", path, handler, is_ajax=True)

    def ajax_patch(self, path: str) -> Callable:
        """Register an AJAX PATCH route (fragment)."""
        return lambda handler: self._register("PATCH", path, handler, is_ajax=True)

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
