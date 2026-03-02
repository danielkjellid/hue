import hashlib

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from hue_django.middleware import HUE_ASSETS_PREFIX, HueAssetsMiddleware, _cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the asset cache before each test."""
    _cache.clear()
    yield
    _cache.clear()


@pytest.fixture
def middleware():
    """Create a middleware instance with a simple passthrough get_response."""

    def get_response(request):
        return HttpResponse("fallthrough", status=404)

    return HueAssetsMiddleware(get_response)


@pytest.fixture
def rf():
    return RequestFactory()


class TestMiddlewareServesAssets:
    def test_serves_css(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css")
        response = middleware(request)

        assert response.status_code == 200
        assert "text/css" in response["Content-Type"]
        assert len(response.content) > 0

    def test_serves_js(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}js/alpine.js")
        response = middleware(request)

        assert response.status_code == 200
        assert "javascript" in response["Content-Type"]
        assert len(response.content) > 0

    def test_falls_through_for_unknown_asset(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}unknown.txt")
        response = middleware(request)

        assert response.status_code == 404
        assert response.content == b"fallthrough"

    def test_falls_through_for_non_hue_path(self, middleware, rf) -> None:
        request = rf.get("/some/other/path/")
        response = middleware(request)

        assert response.status_code == 404
        assert response.content == b"fallthrough"


class TestMiddlewareCaching:
    def test_sets_etag_header(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css")
        response = middleware(request)

        assert "ETag" in response
        assert len(response["ETag"]) > 0

    def test_returns_304_on_matching_etag(self, middleware, rf) -> None:
        # First request to get the ETag
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css")
        response = middleware(request)
        etag = response["ETag"]

        # Second request with If-None-Match
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css", HTTP_IF_NONE_MATCH=etag)
        response = middleware(request)

        assert response.status_code == 304

    def test_returns_200_on_non_matching_etag(self, middleware, rf) -> None:
        request = rf.get(
            f"{HUE_ASSETS_PREFIX}styles.css", HTTP_IF_NONE_MATCH="wrong-etag"
        )
        response = middleware(request)

        assert response.status_code == 200

    def test_sets_cache_control_header(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css")
        response = middleware(request)

        assert "Cache-Control" in response
        assert "public" in response["Cache-Control"]

    def test_caches_content_in_memory(self, middleware, rf) -> None:
        request = rf.get(f"{HUE_ASSETS_PREFIX}styles.css")
        middleware(request)

        assert "styles.css" in _cache
        content, etag = _cache["styles.css"]
        assert len(content) > 0
        assert etag == hashlib.md5(content.encode()).hexdigest()
