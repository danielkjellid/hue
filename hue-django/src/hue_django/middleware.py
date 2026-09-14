import hashlib
from collections.abc import Callable
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.utils.cache import get_conditional_response
from django.utils.http import quote_etag
from hue.assets import read_css, read_js

# URL prefix for hue's built-in asset endpoints.
HUE_ASSETS_PREFIX = "/__hue__/"
CSS_URL = f"{HUE_ASSETS_PREFIX}styles.css"
JS_URL = f"{HUE_ASSETS_PREFIX}js/alpine.js"

# Asset path -> (content reader, content type)
_ASSET_ROUTES: dict[str, tuple[Callable[[], str], str]] = {
    CSS_URL: (read_css, "text/css; charset=utf-8"),
    JS_URL: (read_js, "text/javascript; charset=utf-8"),
}

# In-memory cache: asset path -> (encoded content, quoted etag)
_cache: dict[str, tuple[bytes, str]] = {}


def _get_cached_asset(path: str) -> tuple[bytes, str]:
    """
    Content and ETag for an asset, read from the hue package on first access.
    """
    if path not in _cache:
        reader, _ = _ASSET_ROUTES[path]
        content = reader().encode("utf-8")
        digest = hashlib.md5(content, usedforsecurity=False).hexdigest()
        _cache[path] = (content, quote_etag(digest))
    return _cache[path]


def _asset_response(request: HttpRequest) -> HttpResponseBase | None:
    """
    The response for a hue asset request, or None when the request is not one.
    """
    if request.path not in _ASSET_ROUTES or request.method not in ("GET", "HEAD"):
        return None

    content, etag = _get_cached_asset(request.path)
    _, content_type = _ASSET_ROUTES[request.path]

    response = HttpResponse(content, content_type=content_type)
    response["ETag"] = etag
    response["Cache-Control"] = "public, max-age=3600"
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
