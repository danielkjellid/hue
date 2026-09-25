import pytest
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.test import AsyncRequestFactory, RequestFactory, override_settings

from hue_django.middleware import (
    _ASSET_ROUTES,
    CSS_URL,
    JS_URL,
    HueAssetsMiddleware,
    _cache,
    versioned_url,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    _cache.clear()
    yield
    _cache.clear()


@pytest.fixture
def middleware():
    def get_response(request):
        return HttpResponse("fallthrough", status=404)

    return HueAssetsMiddleware(get_response)


@pytest.fixture
def rf():
    return RequestFactory()


class TestMiddlewareServesAssets:
    def test_serves_css(self, middleware, rf) -> None:
        response = middleware(rf.get(CSS_URL))

        assert response.status_code == 200
        assert "text/css" in response["Content-Type"]
        assert len(response.content) > 0

    def test_serves_js(self, middleware, rf) -> None:
        response = middleware(rf.get(JS_URL))

        assert response.status_code == 200
        assert "javascript" in response["Content-Type"]
        assert len(response.content) > 0

    def test_head_request(self, middleware, rf) -> None:
        response = middleware(rf.head(CSS_URL))

        assert response.status_code == 200
        assert "ETag" in response

    @pytest.mark.parametrize("path", ["/__hue__/unknown.txt", "/some/other/path/"])
    def test_falls_through_for_other_paths(self, middleware, rf, path) -> None:
        response = middleware(rf.get(path))

        assert response.status_code == 404
        assert response.content == b"fallthrough"

    def test_falls_through_for_non_safe_methods(self, middleware, rf) -> None:
        response = middleware(rf.post(CSS_URL))

        assert response.status_code == 404
        assert response.content == b"fallthrough"

    def test_async_chain(self) -> None:
        async def get_response(request):
            return HttpResponse("fallthrough", status=404)

        middleware = HueAssetsMiddleware(get_response)
        arf = AsyncRequestFactory()

        asset = async_to_sync(middleware)(arf.get(CSS_URL))
        other = async_to_sync(middleware)(arf.get("/other/"))

        assert asset.status_code == 200
        assert other.content == b"fallthrough"


class TestMiddlewareCaching:
    def test_sets_quoted_etag_and_cache_control(self, middleware, rf) -> None:
        response = middleware(rf.get(CSS_URL))

        assert response["ETag"].startswith('"') and response["ETag"].endswith('"')
        assert "public" in response["Cache-Control"]

    @pytest.mark.parametrize(
        "if_none_match",
        [
            "{etag}",
            "W/{etag}",
            '"other", {etag}',
            "*",
        ],
    )
    def test_returns_304_on_matching_etag(self, middleware, rf, if_none_match) -> None:
        etag = middleware(rf.get(CSS_URL))["ETag"]

        response = middleware(
            rf.get(CSS_URL, HTTP_IF_NONE_MATCH=if_none_match.format(etag=etag))
        )

        assert response.status_code == 304
        assert response["ETag"] == etag

    def test_returns_200_on_non_matching_etag(self, middleware, rf) -> None:
        response = middleware(rf.get(CSS_URL, HTTP_IF_NONE_MATCH='"wrong-etag"'))

        assert response.status_code == 200

    @override_settings(DEBUG=False)
    def test_reads_asset_once(self, middleware, rf, monkeypatch) -> None:
        reads: list[int] = []
        monkeypatch.setitem(
            _ASSET_ROUTES,
            CSS_URL,
            (lambda: reads.append(1) or ".a{}", "text/css; charset=utf-8"),
        )
        middleware(rf.get(CSS_URL))
        middleware(rf.get(CSS_URL))

        assert len(reads) == 1

    @override_settings(DEBUG=True)
    def test_rereads_asset_while_debugging(self, middleware, rf, monkeypatch) -> None:
        # A bundle rebuilt while the development server runs is served
        # without a restart, which the autoreloader does not do for it.
        content = iter([".a{}", ".b{}"])
        monkeypatch.setitem(
            _ASSET_ROUTES, CSS_URL, (lambda: next(content), "text/css; charset=utf-8")
        )
        assert middleware(rf.get(CSS_URL)).content == b".a{}"
        assert middleware(rf.get(CSS_URL)).content == b".b{}"

    def test_a_url_naming_the_content_is_cached_for_good(self, middleware, rf) -> None:
        url = versioned_url(CSS_URL)
        version = url.split("?v=")[1]

        response = middleware(rf.get(CSS_URL, {"v": version}))

        assert "immutable" in response["Cache-Control"]

    @pytest.mark.parametrize("query", [{}, {"v": "stale"}])
    def test_any_other_url_asks_again(self, middleware, rf, query) -> None:
        # After a deploy, a page cached with the old hash still gets the
        # new content, confirmed by ETag rather than assumed for an hour.
        response = middleware(rf.get(CSS_URL, query))

        assert response["Cache-Control"] == "public, no-cache"

    def test_the_versioned_url_changes_with_the_content(self, monkeypatch) -> None:
        with override_settings(DEBUG=True):
            content = iter([".a{}", ".b{}"])
            monkeypatch.setitem(
                _ASSET_ROUTES,
                CSS_URL,
                (lambda: next(content), "text/css; charset=utf-8"),
            )
            assert versioned_url(CSS_URL) != versioned_url(CSS_URL)
