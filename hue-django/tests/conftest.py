import django
import pytest
from django.conf import settings
from django.urls import URLPattern
from hue import assets
from hue_django import middleware

urlpatterns = []

# Configure Django settings for testing
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-testing-only",
        INSTALLED_APPS=["hue_django"],
        ROOT_URLCONF="tests.conftest",
        MIDDLEWARE=[
            "hue_django.middleware.HueAssetsMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
        ],
        USE_TZ=True,
        ALLOWED_HOSTS=["*"],
    )
    django.setup()


@pytest.fixture
def urlpatterns_() -> list[URLPattern]:
    """
    The urlpatterns list Django's ROOT_URLCONF uses, emptied before each test so
    tests can register their own views in isolation.
    """
    urlpatterns.clear()
    return urlpatterns


@pytest.fixture(autouse=True)
def _stub_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Serve stand-in assets to the middleware.

    The middleware's job is caching, ETags and content types, none of which care
    what the bytes are - and hue's stylesheet is generated, so depending on it
    here would tie these tests to another package's build. hue-python covers
    that the real assets exist and are readable.
    """
    monkeypatch.setitem(
        assets.ASSET_ROUTES,
        assets.CSS_URL,
        (lambda: ".stub{color:red}", "text/css; charset=utf-8"),
    )
    monkeypatch.setitem(
        assets.ASSET_ROUTES,
        assets.JS_URL,
        (lambda: "export const stub = 1;", "text/javascript; charset=utf-8"),
    )
