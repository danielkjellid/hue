from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Views and Router"),
        pr.lead(
            "hue-django wires Hue's AJAX-first router into Django. Two view "
            "classes cover the common cases: HueView for full pages that also "
            "serve fragments, and HueFragmentsView for fragment-only endpoints."
        ),
        pr.h2("Router"),
        pr.p(
            "The Django router (hue_django.router.Router) extends Hue's base "
            "router with the Django-specific pieces: it speaks Django's "
            "<type:name> URL syntax, extracts the CSRF token from the request, "
            "and detects AJAX requests via request.META."
        ),
        pr.code(
            "from hue_django.router import Router\n"
            "from django.http import HttpRequest\n\n"
            "class MyView(HueView):\n"
            "    router = Router[HttpRequest]()"
        ),
        pr.p(
            "HueView creates a router automatically if you don't declare one; "
            "HueFragmentsView always requires an explicit router."
        ),
        pr.h2("Path parameters"),
        pr.p(
            "Routes use Django's URL pattern syntax. Captured parameters are "
            "passed to the handler as keyword arguments after the request and "
            "context:"
        ),
        pr.code(
            "from hue import html\n"
            "from hue.context import HueContext\n"
            "from django.http import HttpRequest\n\n"
            '@router.fragment_get("comments/<int:comment_id>/")\n'
            "async def get_comment(\n"
            "    self,\n"
            "    request: HttpRequest,\n"
            "    context: HueContext[HttpRequest],\n"
            "    comment_id: int,\n"
            ") -> html.div:\n"
            '    return html.div(f"Comment {comment_id}")'
        ),
        pr.p(
            "The standard Django converters are supported — int, str, slug, "
            "uuid, and path — and a single route may capture several "
            "parameters."
        ),
        pr.h2("HueView"),
        pr.p(
            "HueView is for full page views that can also handle AJAX fragment "
            "updates. It must define an index method (sync or async) that "
            "handles the initial GET and returns a Page; fragment routes are "
            "added with the router and are AJAX-only."
        ),
        pr.code(
            "from hue import html\n"
            "from hue.context import HueContext\n"
            "from hue_django.views import HueView\n"
            "from hue_django.pages import Page\n"
            "from hue_django.router import Router\n"
            "from django.http import HttpRequest\n\n"
            "class LoginView(HueView):\n"
            "    router = Router[HttpRequest]()\n\n"
            "    async def index(\n"
            "        self, request: HttpRequest, context: HueContext[HttpRequest]\n"
            "    ) -> Page:\n"
            '        return Page(body=html.div("Login page"))\n\n'
            '    @router.fragment_post("login/")\n'
            "    async def login(\n"
            "        self, request: HttpRequest, context: HueContext[HttpRequest]\n"
            "    ) -> html.div:\n"
            '        return html.div("Login successful")'
        ),
        pr.h2("HueFragmentsView"),
        pr.p(
            "HueFragmentsView is for fragment-only collections — API-like "
            "endpoints that return HTML fragments with no full page. It "
            "requires an explicit router and has no index route; every route "
            "is AJAX-only."
        ),
        pr.code(
            "from hue import html\n"
            "from hue.context import HueContext\n"
            "from hue_django.views import HueFragmentsView\n"
            "from hue_django.router import Router\n"
            "from django.http import HttpRequest\n\n"
            "class CommentsFragments(HueFragmentsView):\n"
            "    router = Router[HttpRequest]()\n\n"
            '    @router.fragment_get("comments/")\n'
            "    async def list_comments(\n"
            "        self, request: HttpRequest, context: HueContext[HttpRequest]\n"
            "    ) -> html.div:\n"
            '        return html.div("Comments list")\n\n'
            '    @router.fragment_post("comments/")\n'
            "    async def create_comment(\n"
            "        self, request: HttpRequest, context: HueContext[HttpRequest]\n"
            "    ) -> html.div:\n"
            '        return html.div("Comment created")'
        ),
        pr.p(
            "Reach for HueView when the initial load needs a full page, and "
            "HueFragmentsView when you only need fragment endpoints."
        ),
        pr.h2("URL configuration"),
        pr.p(
            "Both classes expose a urls attribute — a (urlpatterns, app_name) "
            "tuple ready for Django's include(). The app name defaults to the "
            "lowercased class name."
        ),
        pr.code(
            "# urls.py\n"
            "from django.urls import include, path\n"
            "from myapp.views import CommentsFragments, MyView\n\n"
            "urlpatterns = [\n"
            '    path("myview/", include(MyView.urls)),\n'
            '    path("api/comments/", include(CommentsFragments.urls)),\n'
            "]"
        ),
        pr.h2("HTTP methods and AJAX"),
        pr.p(
            "Fragment routes exist for every standard verb — fragment_get, "
            "fragment_post, fragment_put, fragment_patch, and fragment_delete "
            "— and several methods can share a path. Because fragments are "
            "AJAX-only, the router checks for an X-Requested-With: "
            "XMLHttpRequest or X-Alpine-Request: true header and returns 400 "
            "without one, and 405 for an unsupported method."
        ),
        pr.p(
            "When testing fragment routes with Django's test client, send one "
            "of those headers so the request is recognised as AJAX:"
        ),
        pr.code(
            "from django.test import Client\n\n"
            "client = Client()\n"
            "response = client.get(\n"
            '    "/myview/comments/",\n'
            '    HTTP_X_REQUESTED_WITH="XMLHttpRequest",\n'
            ")"
        ),
    )


PAGE = ProsePage(
    slug="django/views",
    title="Views and Router",
    nav_label="Views and Router",
    group="Django",
    order=0,
    build=_build,
)
