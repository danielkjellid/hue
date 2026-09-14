from django.urls import URLPattern
import pytest
import django
from django.conf import settings

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
