from collections.abc import Callable
from functools import partialmethod
from typing import Any, Literal

from django.http import HttpRequest
from hue.types.core import ComponentType


class ViewRouter:
    """
    Router for defining child routes within a HueView.

    Routes are matched against the relative path after the view's base URL.
    Supports all HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS.

    Example:
        class AlbumView(HueView):
            router = ViewRouter()

            @router.get("comments/")
            async def get_comments(self, request: HttpRequest) -> ComponentType:
                comments = await get_comments_from_db()
                return [html.p(comment.text) for comment in comments]
    """

    def __init__(self):
        # Store routes as: (method, path) -> handler
        self._routes: dict[tuple[str, str], Callable] = {}

    def _cleaned_path(self, path: str) -> str:
        """
        Clean the path by removing leading/trailing slashes and adding a trailing slash.
        """
        if normalized_path := path.strip("/"):
            normalized_path = f"{normalized_path}/"
        else:
            normalized_path = "/"

        return normalized_path

    def _register(
        self,
        method: str,
        path: str,
        handler: Callable[[Any, HttpRequest], ComponentType],
    ) -> Callable[[Any, HttpRequest], ComponentType]:
        """Register a route handler."""
        # Normalize path: remove leading/trailing slashes, then add trailing slash
        normalized_path = self._cleaned_path(path)
        self._routes[(method.upper(), normalized_path)] = handler
        return handler

    def find_route(self, method: str, path: str) -> Callable | None:
        """
        Find a route handler for the given method and path.

        Args:
            method: HTTP method (e.g., "GET", "POST")
            path: Relative path (e.g., "comments/")

        Returns:
            The route handler if found, None otherwise.
        """
        # Normalize the path the same way as registration
        normalized_path = self._cleaned_path(path)
        return self._routes.get((method.upper(), normalized_path))

    def _request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        path: str,
    ) -> Callable[[Any, HttpRequest], ComponentType]:
        return self._register(method, path)

    get = partialmethod(_request, "GET")
    post = partialmethod(_request, "POST")
    put = partialmethod(_request, "PUT")
    delete = partialmethod(_request, "DELETE")
    patch = partialmethod(_request, "PATCH")
    head = partialmethod(_request, "HEAD")
    options = partialmethod(_request, "OPTIONS")
