"""
FastAPI integration for hue: class-based views that render hue pages and
Alpine AJAX fragments, a router that understands Starlette's path syntax, CSRF
protection, and routes that serve hue's CSS and JS straight from the package.
"""

from hue_fastapi.config import (
    HueConfig,
    HueNotConfiguredError,
    configure_hue,
    get_config,
)
from hue_fastapi.csrf import CsrfConfig, csrf_protect
from hue_fastapi.middleware import HueRequestMiddleware
from hue_fastapi.pages import Page
from hue_fastapi.router import Router
from hue_fastapi.views import HueFragmentsView, HueView

__all__ = [
    "CsrfConfig",
    "HueConfig",
    "HueFragmentsView",
    "HueNotConfiguredError",
    "HueRequestMiddleware",
    "HueView",
    "Page",
    "Router",
    "configure_hue",
    "csrf_protect",
    "get_config",
]
