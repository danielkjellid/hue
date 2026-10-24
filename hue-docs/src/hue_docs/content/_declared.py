"""
Stand-ins for a request and a router, so a docs page can render a real
declaration without a view to hang it on.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Request:
    """
    Just enough of a request to carry a query string.
    """

    def __init__(self, **params: str) -> None:
        self.params = params


class Router:
    """
    A real declaration is handed the view's own Router and registers its
    action route on it; here it is registered on nothing and never called.
    URLs are spelled out under prefix, since there is no URLconf to reverse
    them against.
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def fragment_post(self, path: str) -> Any:
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {name: [value] for name, value in request.params.items()}

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        # Nothing is ever posted to a docs page.
        return {}

    def _refusal(self, error: Exception) -> None:
        return None

    def _csrf_field(self) -> None:
        return None

    def _narrow_to(self, rows: Any, key: str, values: list[str]) -> Any:
        return [row for row in rows if str(row[key]) in values]

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        action = params.get("action")
        return f"/{self.prefix}/{action}/" if action else f"/{self.prefix}/"

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        # A list has no event loop to keep off.
        return func(*args)
