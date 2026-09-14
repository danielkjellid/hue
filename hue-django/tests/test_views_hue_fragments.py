import pytest
from django.http import HttpRequest
from django.test import Client
from django.urls import URLPattern, include, path
from htmy import html
from hue.context import HueContext

from hue_django.router import Router
from hue_django.views import HueFragmentsView

AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

# The dispatcher shared with HueView (methods, path params, AJAX gating) is
# covered in test_views_hue_view.py; these tests cover what differs.


def test_hue_fragments_view_requires_router():
    with pytest.raises(ValueError, match="must define a 'router' attribute"):

        class InvalidView(HueFragmentsView):
            pass

        _ = InvalidView.urls


def test_hue_fragments_view_handles_fragments(urlpatterns_: list[URLPattern]):
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

    urlpatterns_.append(path("api/", include(CommentsView.urls)))
    client = Client()

    response = client.get("/api/comments/", **AJAX_HEADERS)
    assert response.status_code == 200
    assert b"Comments List" in response.content
    assert b"<!DOCTYPE html>" not in response.content

    response = client.post("/api/comments/", **AJAX_HEADERS)
    assert response.status_code == 200
    assert b"Comment Created" in response.content


def test_hue_fragments_view_has_no_index_route(urlpatterns_: list[URLPattern]):
    class CommentsView(HueFragmentsView):
        router = Router[HttpRequest]()

        @router.fragment_get("comments/")
        async def list_comments(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ):
            return html.div("Comments")

    urlpatterns_.append(path("api/", include(CommentsView.urls)))

    assert Client().get("/api/").status_code == 404
