from collections.abc import Callable
from functools import cached_property

from hue.pages import BasePage

from hue_django.conf import settings
from hue_django.middleware import CSS_URL, JS_URL, versioned_url


class Page(BasePage):
    """
    The Django page shell, wired to the asset middleware URLs.

    Settings are read when a page renders rather than at import, so
    override_settings works and importing this module never needs configured
    settings.
    """

    @cached_property
    def css_url(self) -> str:
        return versioned_url(CSS_URL)

    @cached_property
    def js_url(self) -> str:
        return versioned_url(JS_URL)

    @cached_property
    def extra_css_urls(self) -> list[str]:
        return settings.HUE_EXTRA_CSS_URLS

    def html_title_factory(self) -> Callable[[str], str]:
        return settings.HUE_HTML_TITLE_FACTORY
