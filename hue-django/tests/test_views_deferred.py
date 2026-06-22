"""
End-to-end check of the deferred-content pattern on a real HueView.

The index renders a skeleton instantly and wires an Alpine AJAX fetch; a
fragment route returns the real content wrapped in the matching target so the
client can merge it in. This proves the full loop using only existing routing.
"""

from django.http import HttpRequest
from django.test import Client
from django.urls import URLPattern, include, path
from htmy import html
from hue.context import HueContext
from hue.router import HueResponse

from hue_django.pages import Page
from hue_django.router import Router
from hue_django.skeletonize import defer
from hue_django.views import HueView

HTTP_OK = 200
AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

TARGET = "dashboard-body"
CONTENT_URL = "/dash/content/"


def _real_content() -> html.div:
    return html.div("Real dashboard content")


class DashboardView(HueView):
    router = Router[HttpRequest]()

    async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
        # The skeleton is derived from the same components the fragment returns,
        # so it can never drift from the real layout. Passing the factory lets
        # the no-query guard bracket construction too.
        return Page(
            title="Dashboard",
            body=defer(layout=_real_content, url=CONTENT_URL, target=TARGET),
        )

    @router.fragment_get("content/")
    async def content(self, request: HttpRequest, context: HueContext[HttpRequest]):
        return HueResponse(component=_real_content(), target=TARGET)


def test_index_renders_skeleton_and_defer_wiring(urlpatterns_: list[URLPattern]):
    urlpatterns_.clear()
    urlpatterns_.append(path("dash/", include(DashboardView.urls)))

    response = Client().get("/dash/")
    body = response.content.decode()

    assert response.status_code == HTTP_OK
    # Full page with the deferred region, but NOT the real content yet.
    assert "<!DOCTYPE html>" in body
    assert f'id="{TARGET}"' in body
    assert "animate-pulse" in body
    assert f"$ajax('{CONTENT_URL}'" in body
    assert "Real dashboard content" not in body


def test_fragment_returns_real_content_in_matching_target(
    urlpatterns_: list[URLPattern],
):
    urlpatterns_.clear()
    urlpatterns_.append(path("dash/", include(DashboardView.urls)))

    response = Client().get("/dash/content/", **AJAX_HEADERS)
    body = response.content.decode()

    assert response.status_code == HTTP_OK
    # The fragment is the real content wrapped in the merge target id.
    assert "Real dashboard content" in body
    assert f'id="{TARGET}"' in body
    assert "<!DOCTYPE html>" not in body
