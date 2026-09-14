from dataclasses import dataclass

import pytest
from django.http import HttpRequest, HttpResponseRedirect
from django.test import Client, override_settings
from django.urls import URLPattern, include, path
from htmy import html
from hue.context import HueContext

from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView

HTTP_OK = 200
HTTP_METHOD_NOT_ALLOWED = 405

# AJAX headers
AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
ALPINE_AJAX_HEADERS = {"HTTP_X_ALPINE_REQUEST": "true"}


def test_hue_view_requires_index_method():
    """
    HueView must define an index method.
    """
    with pytest.raises(ValueError, match="must define an 'index' method"):

        class InvalidView(HueView):
            pass

        _ = InvalidView.urls


def test_hue_view_index_must_be_callable():
    """
    HueView.index must be callable.
    """
    with pytest.raises(ValueError, match="must be a callable method"):

        class InvalidView(HueView):
            index = "not a method"

        _ = InvalidView.urls


def test_hue_view_generates_urls_for_index(urlpatterns_: list[URLPattern]):
    """
    HueView generates URL patterns for index route.
    """

    class MyView(HueView):
        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    assert len(urlpatterns_) == 1
    included = urlpatterns_[0]
    assert included.pattern._route == "myview/"
    # The included patterns tuple contains (urlpatterns, app_name)
    urlpatterns_tuple = MyView.urls
    assert len(urlpatterns_tuple) == 2
    included_patterns = urlpatterns_tuple[0]
    assert len(included_patterns) == 1
    assert included_patterns[0].pattern._route == ""  # index route


def test_hue_view_index_with_router_fragments(urlpatterns_: list[URLPattern]):
    """
    HueView can have both index and fragment routes.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_get("comments/")
        async def comments(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ):
            return html.div("Comments List")

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


def test_hue_view_fragment_requires_ajax(urlpatterns_: list[URLPattern]):
    """
    Fragment routes require AJAX headers.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_get("comments/")
        async def comments(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ):
            return html.div("Comments")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()

    response = client.get("/myview/comments/")
    assert response.status_code == 400


def test_hue_view_fragment_with_path_parameters(urlpatterns_: list[URLPattern]):
    """
    Fragment routes can have path parameters.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_get("comments/<int:comment_id>/")
        async def comment(
            self,
            request: HttpRequest,
            context: HueContext[HttpRequest],
            comment_id: int,
        ):
            return html.div(f"Comment {comment_id}")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()
    response = client.get("/myview/comments/42/", **AJAX_HEADERS)

    assert response.status_code == HTTP_OK
    assert b"Comment 42" in response.content


def test_hue_view_fragment_method_validation(urlpatterns_: list[URLPattern]):
    """
    Fragment routes validate HTTP method.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_post("comments/")
        async def create_comment(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ):
            return html.div("Created")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()

    # GET to POST route should fail
    response = client.get("/myview/comments/", **AJAX_HEADERS)
    assert response.status_code == HTTP_METHOD_NOT_ALLOWED

    # POST to POST route should succeed
    response = client.post("/myview/comments/", **AJAX_HEADERS)
    assert response.status_code == HTTP_OK
    assert b"Created" in response.content


def test_hue_view_all_http_methods(urlpatterns_: list[URLPattern]):
    """
    HueView supports all HTTP methods for fragments.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

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

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()

    # Test all methods (normalize HTML whitespace)
    assert b"GET" in client.get("/myview/test/", **AJAX_HEADERS).content
    assert b"POST" in client.post("/myview/test/", **AJAX_HEADERS).content
    assert b"PUT" in client.put("/myview/test/", **AJAX_HEADERS).content
    assert b"PATCH" in client.patch("/myview/test/", **AJAX_HEADERS).content
    assert b"DELETE" in client.delete("/myview/test/", **AJAX_HEADERS).content


def test_hue_view_alpine_ajax_header(urlpatterns_: list[URLPattern]):
    """
    Fragment routes accept Alpine AJAX header.
    """

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_get("test/")
        async def test(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return html.div("Test")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()
    response = client.get("/myview/test/", **ALPINE_AJAX_HEADERS)

    assert response.status_code == HTTP_OK
    assert b"Test" in response.content


def test_hue_view_creates_router_if_missing(urlpatterns_: list[URLPattern]):
    """
    HueView creates router if not provided.
    """

    class MyView(HueView):
        # No router defined

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    client = Client()
    response = client.get("/myview/")

    assert response.status_code == HTTP_OK
    assert b"Index" in response.content


def test_hue_view_urls_are_built_once_and_do_not_mutate_the_router():
    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

    first = MyView.urls
    second = MyView.urls

    assert first is second
    assert MyView.router.routes == []


def test_hue_view_subclass_serves_its_own_index(urlpatterns_: list[URLPattern]):
    class Parent(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("PARENT"))

    class Child(Parent):
        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("CHILD"))

    urlpatterns_.append(path("p/", include(Parent.urls)))
    urlpatterns_.append(path("c/", include(Child.urls)))
    client = Client()

    assert b"PARENT" in client.get("/p/").content
    assert b"CHILD" in client.get("/c/").content


def test_hue_view_bare_path_parameter(urlpatterns_: list[URLPattern]):
    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_get("items/<slug>/")
        async def item(
            self, request: HttpRequest, context: HueContext[HttpRequest], slug: str
        ):
            return html.div(f"Item {slug}")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    response = Client().get("/myview/items/abc/", **AJAX_HEADERS)
    assert response.status_code == HTTP_OK
    assert b"Item abc" in response.content


def test_hue_view_head_and_allow_header(urlpatterns_: list[URLPattern]):
    class MyView(HueView):
        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

    urlpatterns_.append(path("myview/", include(MyView.urls)))
    client = Client()

    assert client.head("/myview/").status_code == HTTP_OK
    response = client.post("/myview/")
    assert response.status_code == HTTP_METHOD_NOT_ALLOWED
    assert response["Allow"] == "GET, HEAD"


def test_hue_view_sync_handlers(urlpatterns_: list[URLPattern]):
    class MyView(HueView):
        router = Router[HttpRequest]()

        def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Sync index"))

        @router.fragment_get("frag/")
        def frag(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return html.div("Sync fragment")

    urlpatterns_.append(path("myview/", include(MyView.urls)))
    client = Client()

    assert b"Sync index" in client.get("/myview/").content
    assert b"Sync fragment" in client.get("/myview/frag/", **AJAX_HEADERS).content


def test_hue_view_passes_framework_responses_through(urlpatterns_: list[URLPattern]):
    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_post("go/")
        async def go(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return HttpResponseRedirect("/elsewhere/")

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    response = Client().post("/myview/go/", **AJAX_HEADERS)
    assert response.status_code == 302
    assert response["Location"] == "/elsewhere/"


def test_hue_view_body_validation(urlpatterns_: list[URLPattern]):
    @dataclass
    class Form:
        name: str
        age: int

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_post("save/")
        async def save(
            self, request: HttpRequest, context: HueContext[HttpRequest], body: Form
        ):
            return html.div(f"{body.name} is {body.age}")

    urlpatterns_.append(path("myview/", include(MyView.urls)))
    client = Client()

    ok = client.post("/myview/save/", {"name": "Ada", "age": "36"}, **AJAX_HEADERS)
    assert ok.status_code == HTTP_OK
    assert b"Ada is 36" in ok.content

    bad = client.post("/myview/save/", {"name": "Ada", "age": "x"}, **AJAX_HEADERS)
    assert bad.status_code == 422


def test_hue_view_csrf_header_accepted_on_ajax_post(urlpatterns_: list[URLPattern]):
    """The Alpine bundle sends X-CSRFToken, the header name Django reads."""

    class MyView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="", body=html.div("Index"))

        @router.fragment_post("save/")
        async def save(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return html.div("Saved")

    urlpatterns_.append(path("myview/", include(MyView.urls)))
    client = Client(enforce_csrf_checks=True)

    client.get("/myview/")
    token = client.cookies["csrftoken"].value

    assert client.post("/myview/save/", **AJAX_HEADERS).status_code == 403
    response = client.post("/myview/save/", HTTP_X_CSRFTOKEN=token, **AJAX_HEADERS)
    assert response.status_code == HTTP_OK


def test_page_reads_settings_at_render_time(urlpatterns_: list[URLPattern]):
    class MyView(HueView):
        async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
            return Page(title="Home", body=html.div("Index"))

    urlpatterns_.append(path("myview/", include(MyView.urls)))

    with override_settings(
        HUE_EXTRA_CSS_URLS=["/extra.css"],
        HUE_HTML_TITLE_FACTORY=lambda title: f"{title} | Test",
    ):
        content = Client().get("/myview/").content

    assert b'href="/extra.css"' in content
    assert b"Home | Test</title>" in content
