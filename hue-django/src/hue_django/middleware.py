from collections.abc import Callable
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.utils.cache import get_conditional_response
from django.utils.http import quote_etag
from hue import assets
from hue.assets import CHART_JS_URL, CSS_URL, JS_URL
from hue.scope import request_scope
from hue.toast import keep_in_session, restore_from_session

__all__ = [
    "CHART_JS_URL",
    "CSS_URL",
    "JS_URL",
    "HueAssetsMiddleware",
    "HueRequestMiddleware",
    "versioned_url",
]


def versioned_url(path: str) -> str:
    """
    An asset's URL with the hash of its content in it, re-read on every call
    while DEBUG is on, since the bundle is rebuilt as the server runs.
    """
    return assets.versioned_url(path, reload=settings.DEBUG)


def _asset_response(request: HttpRequest) -> HttpResponseBase | None:
    """
    The response for a hue asset request, or None when the request is not one.
    """
    if request.path not in assets.ASSET_ROUTES or request.method not in (
        "GET",
        "HEAD",
    ):
        return None

    content, digest = assets.served_asset(request.path, reload=settings.DEBUG)
    etag = quote_etag(digest)
    _, content_type = assets.ASSET_ROUTES[request.path]

    response = HttpResponse(content, content_type=content_type)
    response["ETag"] = etag
    response["Cache-Control"] = assets.cache_control(digest, request.GET.get("v"))
    # Turns the response into a 304 when If-None-Match matches, handling weak
    # validators, lists and "*" per RFC 7232.
    return get_conditional_response(request, etag=etag, response=response)


class HueAssetsMiddleware:
    """
    Serve hue's built-in CSS and JS straight from the hue package.

    No collectstatic or static file configuration is needed. Works under both
    WSGI and ASGI without forcing the rest of the chain through a thread.

        MIDDLEWARE = [
            "hue_django.middleware.HueAssetsMiddleware",
            ...
        ]
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: Callable[[HttpRequest], Any]) -> None:
        self.get_response = get_response
        if iscoroutinefunction(get_response):
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> Any:
        if iscoroutinefunction(self):
            return self.__acall__(request)
        return _asset_response(request) or self.get_response(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        return _asset_response(request) or await self.get_response(request)


class HueRequestMiddleware:
    """
    Open hue's request-scoped state for the whole request, and carry toasts
    across a redirect.

    The toast queue and the list shortcuts.use() writes to are opened here
    as well as in the router, so toast.success() and shortcuts.use() work in a
    plain Django view and not only inside a hue route. Without it, a toast
    still works for anything that renders, since a page or a fragment carries
    its own, and a hue route that redirects after raising one is an error.
    With it, that toast waits in the session and arrives with the page after
    it.

        MIDDLEWARE = [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "hue_django.middleware.HueRequestMiddleware",
            ...
        ]
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: Callable[[HttpRequest], Any]) -> None:
        self.get_response = get_response
        if iscoroutinefunction(get_response):
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> Any:
        if iscoroutinefunction(self):
            return self.__acall__(request)
        with request_scope():
            try:
                restore_from_session(getattr(request, "session", None))
                response = self.get_response(request)
            finally:
                keep_in_session(getattr(request, "session", None))
        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        with request_scope():
            try:
                restore_from_session(getattr(request, "session", None))
                response = await self.get_response(request)
            finally:
                keep_in_session(getattr(request, "session", None))
        return response
