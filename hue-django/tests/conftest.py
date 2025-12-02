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
        INSTALLED_APPS=[
            "django.contrib.staticfiles",
            "hue_django",
        ],
        STATIC_URL="/static/",
        STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
        ROOT_URLCONF="tests.conftest",
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
        ],
        USE_TZ=True,
        HUE_CSS_STATIC_PATH="hue/styles/tailwind.css",
        HUE_HTML_TITLE_FACTORY=lambda title: f"{title} - Hue",
        ALLOWED_HOSTS=["*"],
    )
    django.setup()


@pytest.fixture
def urlpatterns_() -> list[URLPattern]:
    """Fixture that returns a reference to tests.urls.urlpatterns.

    This allows tests to modify the URL patterns that Django's ROOT_URLCONF
    will use. The list is cleared before each test to ensure isolation.
    """

    # Clear the list before each test for isolation
    urlpatterns.clear()

    # Return a reference to the actual list Django uses
    return urlpatterns
