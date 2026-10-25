import hashlib
from collections.abc import Callable
from typing import Final

from hue.assets import chart_bundle_path, read_chart_js, read_css, read_js
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

HUE_ASSETS_PREFIX: Final = "/__hue__/"
CSS_URL: Final = f"{HUE_ASSETS_PREFIX}styles.css"
JS_URL: Final = f"{HUE_ASSETS_PREFIX}js/alpine.js"
# Beside the bundle, which fetches it by this name when a chart appears.
CHART_JS_URL: Final = f"{HUE_ASSETS_PREFIX}js/{chart_bundle_path().name}"

# Reader and content type per served path. Tests replace this mapping.
_ASSET_ROUTES: dict[str, tuple[Callable[[], str], str]] = {
    CSS_URL: (read_css, "text/css; charset=utf-8"),
    JS_URL: (read_js, "text/javascript; charset=utf-8"),
    CHART_JS_URL: (read_chart_js, "text/javascript; charset=utf-8"),
}

# path -> (body, content hash)
_cache: dict[str, tuple[bytes, str]] = {}

# For a URL that names the content it wants: it can never change, so a
# browser need not ask again.
_IMMUTABLE: Final = "public, max-age=31536000, immutable"


def _get_cached_asset(path: str, debug: bool = False) -> tuple[bytes, str]:
    """
    Content and hash for an asset, read from the hue package on first access.

    In debug it is read every time: the bundle is rebuilt while the
    development server runs, and the reloader restarts it for Python only.
    """
    if path not in _cache or debug:
        reader, _ = _ASSET_ROUTES[path]
        body = reader().encode("utf-8")
        digest = hashlib.md5(body, usedforsecurity=False).hexdigest()
        _cache[path] = (body, digest)
    return _cache[path]


def versioned_url(path: str, debug: bool = False) -> str:
    """
    An asset's URL with the hash of its content in it, which is the URL a
    page links. A change to the asset is a new URL, so no browser holds on
    to the old one after a deploy.
    """
    return f"{path}?v={_get_cached_asset(path, debug)[1]}"


def _etag_matches(if_none_match: str, etag: str) -> bool:
    """
    RFC 7232 If-None-Match, which may be a comma separated list, may use weak
    validators, and may be a bare star.
    """
    for candidate in (part.strip() for part in if_none_match.split(",")):
        if candidate == "*" or candidate.removeprefix("W/") == etag:
            return True
    return False


def _asset_endpoint(path: str) -> Callable[[Request], Response]:
    def endpoint(request: Request) -> Response:
        body, digest = _get_cached_asset(path, request.app.debug)
        _, content_type = _ASSET_ROUTES[path]
        etag = f'"{digest}"'
        headers = {
            "ETag": etag,
            # Cached for good when the URL names this content. Anything else,
            # such as a link written without the hash, asks again each time
            # and gets a 304 while the ETag still matches.
            "Cache-Control": (
                _IMMUTABLE
                if request.query_params.get("v") == digest
                else "public, no-cache"
            ),
        }

        if_none_match = request.headers.get("if-none-match")
        if if_none_match and _etag_matches(if_none_match, etag):
            return Response(status_code=304, headers=headers)
        return Response(content=body, media_type=content_type, headers=headers)

    return endpoint


def add_asset_routes(app: Starlette) -> None:
    """
    Serve hue's stylesheet and scripts straight out of the installed package,
    with no static files step and no CDN.
    """
    for path in _ASSET_ROUTES:
        app.add_route(
            path,
            _asset_endpoint(path),
            methods=["GET", "HEAD"],
            include_in_schema=False,
        )
