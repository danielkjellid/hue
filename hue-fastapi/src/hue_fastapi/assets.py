from collections.abc import Callable

from hue import assets
from hue.assets import CHART_JS_URL, CSS_URL, JS_URL
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["CHART_JS_URL", "CSS_URL", "JS_URL", "add_asset_routes"]


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
        body, digest = assets.served_asset(path, reload=request.app.debug)
        _, content_type = assets.ASSET_ROUTES[path]
        etag = f'"{digest}"'
        headers = {
            "ETag": etag,
            "Cache-Control": assets.cache_control(
                digest, request.query_params.get("v")
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
    for path in assets.ASSET_ROUTES:
        app.add_route(
            path,
            _asset_endpoint(path),
            methods=["GET", "HEAD"],
            include_in_schema=False,
        )
