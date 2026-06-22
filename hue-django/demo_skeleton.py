"""
Runnable demo of deferred skeleton loading.

    cd hue-django && uv run python demo_skeleton.py
    # then open http://localhost:8000/

The page paints a skeleton instantly; the real content arrives after an
artificial delay in the fragment handler and merges over the skeleton. Bump
DELAY_SECONDS (or throttle the network in devtools) to watch it longer.
"""

from __future__ import annotations

import asyncio
import os
import sys

# This package uses a src/ layout and isn't installed on the path, so a loose
# script can't import hue_django without help (pytest gets this from its config).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import django  # noqa: E402
from django.conf import settings  # noqa: E402

DELAY_SECONDS = 2.0

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="demo-only",
        ROOT_URLCONF="__main__",
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=["django.contrib.staticfiles", "hue_django"],
        STATIC_URL="/static/",
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        MIDDLEWARE=[
            "hue_django.middleware.HueAssetsMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.middleware.common.CommonMiddleware",
        ],
        USE_TZ=True,
        HUE_HTML_TITLE_FACTORY=lambda title: f"{title} · Hue demo",
    )
    django.setup()

from django.http import HttpRequest  # noqa: E402
from django.urls import include, path  # noqa: E402
from hue import html  # noqa: E402
from hue.context import HueContext  # noqa: E402
from hue.router import HueResponse  # noqa: E402
from hue.ui import Button, Callout, Stack, Text  # noqa: E402

from hue_django.pages import Page  # noqa: E402
from hue_django.router import Router  # noqa: E402
from hue_django.skeletonize import defer  # noqa: E402
from hue_django.views import HueView  # noqa: E402

TARGET = "dashboard-body"
CONTENT_URL = "/content/"


def dashboard_content() -> Stack:
    """The real content — and, skeletonised, the shape of the placeholder."""
    return (
        Stack()
        .direction("vertical")
        .spacing("md")
        .content(
            Text("Quarterly dashboard").variant("title-1"),
            Text(
                "Here is a paragraph of body copy that stands in for the kind of "
                "text-heavy content a real dashboard would load from the database."
            ).variant("body"),
            Callout()
            .variant("success")
            .title("All systems go")
            .content("Revenue is up 12% over last quarter."),
            Stack()
            .direction("horizontal")
            .spacing("sm")
            .content(
                Button().variant("primary").fluid(False).content("Export"),
                Button().variant("outline").fluid(False).content("Share"),
            ),
        )
    )


class DashboardView(HueView):
    router = Router[HttpRequest]()

    async def index(self, request: HttpRequest, context: HueContext[HttpRequest]):
        return Page(
            title="Dashboard",
            body=html.div(
                defer(layout=dashboard_content, url=CONTENT_URL, target=TARGET)
            ).class_("mx-auto max-w-2xl p-10"),
        )

    @router.fragment_get("content/")
    async def content(self, request: HttpRequest, context: HueContext[HttpRequest]):
        await asyncio.sleep(DELAY_SECONDS)  # stand-in for slow DB / API I/O
        return HueResponse(component=dashboard_content(), target=TARGET)


urlpatterns = [path("", include(DashboardView.urls))]


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(["demo_skeleton.py", "runserver", "8000"])
