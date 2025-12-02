"""
Tests for HueView and HueFragmentsView.
"""

import pytest
from django.http import HttpRequest
from django.test import Client
from django.urls import URLPattern, include, path
from htmy import html
from hue.context import HueContext

from src.hue_django.pages import Page
from src.hue_django.router import Router
from src.hue_django.views import HueFragmentsView, HueView

# HTTP status codes
HTTP_OK = 200
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

# AJAX headers
AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
ALPINE_AJAX_HEADERS = {"HTTP_X_ALPINE_REQUEST": "true"}


class TestHueView:
    """Tests for HueView (full page with optional fragments)."""

    def test_hue_view_requires_index_method(self):
        """HueView must define an index method."""
        with pytest.raises(ValueError, match="must define an 'index' method"):

            class InvalidView(HueView):
                pass

            _ = InvalidView.urls

    def test_hue_view_index_must_be_callable(self):
        """HueView.index must be callable."""
        with pytest.raises(ValueError, match="must be a callable method"):

            class InvalidView(HueView):
                index = "not a method"

            _ = InvalidView.urls

    def test_hue_view_generates_urls_for_index(self, urlpatterns_: list[URLPattern]):
        """HueView generates URL patterns for index route."""

        class MyView(HueView):
            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        assert len(urlpatterns_) == 1
        included = urlpatterns_[0]
        assert included.pattern._route == "myview/"
        # The included patterns tuple contains (urlpatterns, app_name)
        urlpatterns_tuple = MyView.urls
        assert len(urlpatterns_tuple) == 2
        included_patterns = urlpatterns_tuple[0]
        assert len(included_patterns) == 1
        assert included_patterns[0].pattern._route == ""

    def test_hue_view_index_returns_full_page(self, urlpatterns_: list[URLPattern]):
        """HueView index route returns full HTML page."""

        class MyView(HueView):
            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Test Page"))

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()
        response = client.get("/myview/")

        assert response.status_code == HTTP_OK
        assert b"Test Page" in response.content
        assert b"<!DOCTYPE html>" in response.content
        assert b"<html" in response.content

    def test_hue_view_index_with_router_fragments(self, urlpatterns_: list[URLPattern]):
        """HueView can have both index and fragment routes."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_get("comments/")
            async def comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments List")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()

        # Test index (full page)
        response = client.get("/myview/")
        assert response.status_code == HTTP_OK
        assert b"Index" in response.content

        # Test fragment route (AJAX)
        response = client.get("/myview/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Comments List" in response.content
        # Fragment should not be full HTML page
        assert b"<!DOCTYPE html>" not in response.content

    def test_hue_view_fragment_requires_ajax(self, urlpatterns_: list[URLPattern]):
        """Fragment routes require AJAX headers."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_get("comments/")
            async def comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()

        # Non-AJAX request to fragment route should fail
        # The AssertionError from router gets converted to 400
        response = client.get("/myview/comments/")
        assert response.status_code == 400

    def test_hue_view_fragment_with_path_parameters(
        self, urlpatterns_: list[URLPattern]
    ):
        """Fragment routes can have path parameters."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_get("comments/<int:comment_id>/")
            async def comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                comment_id: int,
            ):
                return html.div(f"Comment {comment_id}")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()
        response = client.get("/myview/comments/42/", **AJAX_HEADERS)

        assert response.status_code == HTTP_OK
        assert b"Comment 42" in response.content

    def test_hue_view_fragment_method_validation(self, urlpatterns_: list[URLPattern]):
        """Fragment routes validate HTTP method."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_post("comments/")
            async def create_comment(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Created")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()

        # GET to POST route should fail
        response = client.get("/myview/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_METHOD_NOT_ALLOWED

        # POST to POST route should succeed
        response = client.post("/myview/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Created" in response.content

    def test_hue_view_all_http_methods(self, urlpatterns_: list[URLPattern]):
        """HueView supports all HTTP methods for fragments."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_get("test/")
            async def get_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("GET")

            @router.fragment_post("test/")
            async def post_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("POST")

            @router.fragment_put("test/")
            async def put_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("PUT")

            @router.fragment_patch("test/")
            async def patch_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("PATCH")

            @router.fragment_delete("test/")
            async def delete_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("DELETE")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()

        # Test all methods (normalize HTML whitespace)
        assert b"GET" in client.get("/myview/test/", **AJAX_HEADERS).content
        assert b"POST" in client.post("/myview/test/", **AJAX_HEADERS).content
        assert b"PUT" in client.put("/myview/test/", **AJAX_HEADERS).content
        assert b"PATCH" in client.patch("/myview/test/", **AJAX_HEADERS).content
        assert b"DELETE" in client.delete("/myview/test/", **AJAX_HEADERS).content

    def test_hue_view_alpine_ajax_header(self, urlpatterns_: list[URLPattern]):
        """Fragment routes accept Alpine AJAX header."""

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

            @router.fragment_get("test/")
            async def test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Test")

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()
        response = client.get("/myview/test/", **ALPINE_AJAX_HEADERS)

        assert response.status_code == HTTP_OK
        assert b"Test" in response.content

    def test_hue_view_creates_router_if_missing(self, urlpatterns_: list[URLPattern]):
        """HueView creates router if not provided."""

        class MyView(HueView):
            # No router defined

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(body=html.div("Index"))

        urlpatterns_.clear()
        urlpatterns_.append(path("myview/", include(MyView.urls)))

        client = Client()
        response = client.get("/myview/")

        assert response.status_code == HTTP_OK
        assert b"Index" in response.content


class TestHueFragmentsView:
    """Tests for HueFragmentsView (fragments only)."""

    def test_hue_fragments_view_requires_router(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView must define a router."""
        with pytest.raises(ValueError, match="must define a 'router' attribute"):

            class InvalidView(HueFragmentsView):
                pass

            _ = InvalidView.urls

    def test_hue_fragments_view_handles_fragments(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView handles fragment routes."""

        class CommentsView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments List")

            @router.fragment_post("comments/")
            async def create_comment(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comment Created")

        urlpatterns_.clear()
        urlpatterns_.append(path("comments/", include(CommentsView.urls)))

        client = Client()

        # GET fragment
        response = client.get("/comments/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Comments List" in response.content
        assert b"<!DOCTYPE html>" not in response.content

        # POST fragment
        response = client.post("/comments/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Comment Created" in response.content

    def test_hue_fragments_view_with_path_parameters(
        self, urlpatterns_: list[URLPattern]
    ):
        """HueFragmentsView handles path parameters."""

        class CommentsView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/<int:comment_id>/")
            async def get_comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                comment_id: int,
            ):
                return html.div(f"Comment {comment_id}")

            @router.fragment_get(
                "users/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>/"
            )
            async def get_nested_comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                user_id: int,
                post_id: int,
                comment_id: int,
            ):
                return html.div(f"User {user_id}, Post {post_id}, Comment {comment_id}")

        urlpatterns_.clear()
        urlpatterns_.append(path("api/", include(CommentsView.urls)))

        client = Client()

        # Single parameter
        response = client.get("/api/comments/123/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Comment 123" in response.content

        # Multiple parameters
        response = client.get("/api/users/1/posts/2/comments/3/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"User 1, Post 2, Comment 3" in response.content

    def test_hue_fragments_view_requires_ajax(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView routes require AJAX."""

        class CommentsView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments")

        urlpatterns_.clear()
        urlpatterns_.append(path("comments/", include(CommentsView.urls)))

        client = Client()

        # Non-AJAX request should fail
        response = client.get("/comments/comments/")
        assert response.status_code == 400  # Bad Request for missing AJAX headers

    def test_hue_fragments_view_method_validation(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView validates HTTP methods."""

        class CommentsView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_post("comments/")
            async def create_comment(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Created")

        urlpatterns_.clear()
        urlpatterns_.append(path("comments/", include(CommentsView.urls)))

        client = Client()

        # Wrong method
        response = client.get("/comments/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_METHOD_NOT_ALLOWED

        # Correct method
        response = client.post("/comments/comments/", **AJAX_HEADERS)
        assert response.status_code == HTTP_OK
        assert b"Created" in response.content

    def test_hue_fragments_view_all_methods(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView supports all HTTP methods."""

        class TestView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("test/")
            async def get_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("GET")

            @router.fragment_post("test/")
            async def post_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("POST")

            @router.fragment_put("test/")
            async def put_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("PUT")

            @router.fragment_patch("test/")
            async def patch_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("PATCH")

            @router.fragment_delete("test/")
            async def delete_test(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("DELETE")

        urlpatterns_.clear()
        urlpatterns_.append(path("api/", include(TestView.urls)))

        client = Client()

        # Test all methods (normalize HTML whitespace)
        assert b"GET" in client.get("/api/test/", **AJAX_HEADERS).content
        assert b"POST" in client.post("/api/test/", **AJAX_HEADERS).content
        assert b"PUT" in client.put("/api/test/", **AJAX_HEADERS).content
        assert b"PATCH" in client.patch("/api/test/", **AJAX_HEADERS).content
        assert b"DELETE" in client.delete("/api/test/", **AJAX_HEADERS).content

    def test_hue_fragments_view_no_index_route(self, urlpatterns_: list[URLPattern]):
        """HueFragmentsView does not have an index route."""

        class CommentsView(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments")

        urlpatterns_.clear()
        urlpatterns_.append(path("api/", include(CommentsView.urls)))

        client = Client()

        # Root path should 404 (no index route)
        response = client.get("/api/")
        assert response.status_code == HTTP_NOT_FOUND
