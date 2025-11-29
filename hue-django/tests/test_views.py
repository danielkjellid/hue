from typing import Any

from django.urls import include, path
import pytest
from django.http import HttpRequest
from htmy import html

from src.hue.context import HueContext
from src.hue_django.router import Router
from src.hue_django.views import HueView


def test_hue_view__index():
    class MyView(HueView):
        title = "Test view"
        router = Router[HttpRequest]()

        @router.get("/")
        async def index(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ) -> html.p:
            return html.p("Index")

        @router.ajax_get("comments/")
        async def comments(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ) -> html.p:
            return html.p("Comments")

        @router.ajax_get("comments/<int:comment_id>/")
        async def comment(
            self,
            request: HttpRequest,
            context: HueContext[HttpRequest],
            comment_id: int,
        ) -> html.p:
            return html.p(f"Comment {comment_id}")

        @router.ajax_post("comments/")
        async def create_comment(
            self,
            request: HttpRequest,
            context: HueContext[HttpRequest],
            body: dict[str, Any],
        ) -> html.p:
            return html.p(f"Create comment {body}")

    print(MyView.urls)

    urlpatterns = [path("myview/", include(MyView.urls))]

    assert False
