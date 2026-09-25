import hashlib
from collections.abc import Callable
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.utils.cache import get_conditional_response
from django.utils.http import quote_etag
from hue.assets import read_css, read_js
from hue.toast import ToastMessage, toast

# URL prefix for hue's built-in asset endpoints.
HUE_ASSETS_PREFIX = "/__hue__/"
CSS_URL = f"{HUE_ASSETS_PREFIX}styles.css"
JS_URL = f"{HUE_ASSETS_PREFIX}js/alpine.js"

# Asset path -> (content reader, content type)
_ASSET_ROUTES: dict[str, tuple[Callable[[], str], str]] = {
    CSS_URL: (read_css, "text/css; charset=utf-8"),
    JS_URL: (read_js, "text/javascript; charset=utf-8"),
}

# In-memory cache: asset path -> (encoded content, content hash)
_cache: dict[str, tuple[bytes, str]] = {}

# For a URL that names the content it wants: it can never change, so a
# browser need not ask again.
_IMMUTABLE = "public, max-age=31536000, immutable"


def _get_cached_asset(path: str) -> tuple[bytes, str]:
    """
    Content and hash for an asset, read from the hue package on first access.

    With DEBUG on it is read every time. The bundle is rebuilt while the
    development server runs, and the autoreloader restarts it for Python
    and nothing else.
    """
    if path not in _cache or settings.DEBUG:
        reader, _ = _ASSET_ROUTES[path]
        content = reader().encode("utf-8")
        digest = hashlib.md5(content, usedforsecurity=False).hexdigest()
        _cache[path] = (content, digest)
    return _cache[path]


def versioned_url(path: str) -> str:
    """
    An asset's URL with the hash of its content in it, which is the URL a
    page links. A change to the asset is a new URL, so no browser holds on
    to the old one after a deploy.
    """
    return f"{path}?v={_get_cached_asset(path)[1]}"


def _asset_response(request: HttpRequest) -> HttpResponseBase | None:
    """
    The response for a hue asset request, or None when the request is not one.
    """
    if request.path not in _ASSET_ROUTES or request.method not in ("GET", "HEAD"):
        return None

    content, digest = _get_cached_asset(request.path)
    etag = quote_etag(digest)
    _, content_type = _ASSET_ROUTES[request.path]

    response = HttpResponse(content, content_type=content_type)
    response["ETag"] = etag
    # Cached for good when the URL names this content. Anything else, such
    # as a link written without the hash, asks again each time and gets a
    # 304 while the ETag still matches.
    response["Cache-Control"] = (
        _IMMUTABLE if request.GET.get("v") == digest else "public, no-cache"
    )
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


# Where the toasts raised before a redirect wait for the page after it.
SESSION_KEY = "hue_toasts"


def _load(request: HttpRequest) -> None:
    """
    Hand back whatever the last request left behind, oldest first.
    """
    session = getattr(request, "session", None)
    if session is None:
        return
    stored = session.pop(SESSION_KEY, None)
    if stored:
        toast.restore(ToastMessage.from_dict(data) for data in stored)


def _save(request: HttpRequest) -> None:
    """
    Keep what nothing rendered, for the next request to show.

    A page empties the queue through its region and a fragment through the
    router, so what is left here was raised by something that returned no
    markup at all - a redirect, most often.
    """
    pending = toast.drain()
    session = getattr(request, "session", None)
    if not pending or session is None:
        return
    session[SESSION_KEY] = [message.as_dict() for message in pending]


class HueToastMiddleware:
    """
    Carry toasts across a redirect.

    Without it, toast.success() works for anything that renders - a page or a
    fragment carries its own. With it, one raised by a view that redirects
    waits in the session and arrives with the page after it.

    It also opens the queue for the whole request, so toast.success() works in
    a plain Django view, not only inside a hue router.

        MIDDLEWARE = [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "hue_django.middleware.HueToastMiddleware",
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
        token = toast.open()
        try:
            _load(request)
            response = self.get_response(request)
        finally:
            _save(request)
            toast.close(token)
        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        token = toast.open()
        try:
            _load(request)
            response = await self.get_response(request)
        finally:
            _save(request)
            toast.close(token)
        return response
