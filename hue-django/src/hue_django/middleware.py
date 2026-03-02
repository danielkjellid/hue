import hashlib
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from hue.assets import read_css, read_js

# URL prefix for Hue's built-in asset endpoints.
HUE_ASSETS_PREFIX = "/__hue__/"

# Asset routes: path suffix -> (content reader, content type)
_ASSET_ROUTES: dict[str, tuple[Callable[[], str], str]] = {
    "styles.css": (read_css, "text/css; charset=utf-8"),
    "js/alpine.js": (read_js, "application/javascript; charset=utf-8"),
}

# In-memory cache: path suffix -> (content, etag)
_cache: dict[str, tuple[str, str]] = {}


def _get_cached_asset(path: str) -> tuple[str, str]:
    """Get asset content and ETag, reading from disk on first access."""
    if path not in _cache:
        reader, _ = _ASSET_ROUTES[path]
        content = reader()
        etag = hashlib.md5(content.encode()).hexdigest()
        _cache[path] = (content, etag)
    return _cache[path]


class HueAssetsMiddleware:
    """Django middleware that serves Hue's built-in CSS and JS assets.

    Intercepts requests to /__hue__/ and serves assets directly from
    the hue Python package. No collectstatic or static file configuration
    needed.

    Add to MIDDLEWARE in settings.py:
        MIDDLEWARE = [
            "hue_django.middleware.HueAssetsMiddleware",
            ...
        ]
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.path.startswith(HUE_ASSETS_PREFIX):
            return self.get_response(request)

        asset_path = request.path[len(HUE_ASSETS_PREFIX) :]

        if asset_path not in _ASSET_ROUTES:
            return self.get_response(request)

        content, etag = _get_cached_asset(asset_path)
        _, content_type = _ASSET_ROUTES[asset_path]

        # Handle conditional requests (304 Not Modified)
        if_none_match = request.META.get("HTTP_IF_NONE_MATCH", "")
        if if_none_match == etag:
            return HttpResponse(status=304)

        response = HttpResponse(content, content_type=content_type)
        response["ETag"] = etag
        response["Cache-Control"] = "public, max-age=3600"
        return response
