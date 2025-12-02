import pytest
from django.http import HttpRequest
from django.test import Client
from django.urls import URLPattern, include, path
from htmy import html
from hue.context import HueContext

from hue_django.router import Router
from hue_django.views import HueFragmentsView

# HTTP status codes
HTTP_OK = 200
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

# AJAX headers
AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
ALPINE_AJAX_HEADERS = {"HTTP_X_ALPINE_REQUEST": "true"}


def test_hue_fragments_view_requires_router(urlpatterns_: list[URLPattern]):
    """HueFragmentsView must define a router."""
    with pytest.raises(ValueError, match="must define a 'router' attribute"):

        class InvalidView(HueFragmentsView):
            pass

        _ = InvalidView.urls


def test_hue_fragments_view_handles_fragments(urlpatterns_: list[URLPattern]):
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


def test_hue_fragments_view_with_path_parameters(urlpatterns_: list[URLPattern]):
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


def test_hue_fragments_view_requires_ajax(urlpatterns_: list[URLPattern]):
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


def test_hue_fragments_view_method_validation(urlpatterns_: list[URLPattern]):
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


def test_hue_fragments_view_all_methods(urlpatterns_: list[URLPattern]):
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


def test_hue_fragments_view_no_index_route(urlpatterns_: list[URLPattern]):
    """HueFragmentsView does not have an index route."""

    class CommentsView(HueFragmentsView):
        router = Router[HttpRequest]()

        @router.fragment_get("comments/")
        async def list_comments(request: HttpRequest, context: HueContext[HttpRequest]):
            return html.div("Comments")

    urlpatterns_.clear()
    urlpatterns_.append(path("api/", include(CommentsView.urls)))

    client = Client()

    # Root path should 404 (no index route)
    response = client.get("/api/")
    assert response.status_code == HTTP_NOT_FOUND
