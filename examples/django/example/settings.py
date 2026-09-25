"""
Settings for the example app: SQLite, hue's assets served by its own
middleware, and nothing a real deployment would need.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
SECRET_KEY = "hue-example-not-a-secret"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "hue_django",
    "example.invoices",
]

MIDDLEWARE = [
    "hue_django.middleware.HueAssetsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "example.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "example" / "static"]

# hue styles its own components. The page around them is the app's, so its
# few rules come from a stylesheet of its own, loaded after hue's.
HUE_EXTRA_CSS_URLS = ["/static/example.css"]
HUE_HTML_TITLE_FACTORY = lambda title: f"{title} - hue example"  # noqa: E731

# How the table writes the dates it is handed, instead of ISO 8601.
HUE_DATE_FORMAT = "%d %b %Y"
