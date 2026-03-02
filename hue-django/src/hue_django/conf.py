from typing import Callable

from django.conf import settings as django_settings


class Settings:
    @property
    def HUE_EXTRA_CSS_URLS(self) -> list[str]:
        """
        List of additional CSS URLs to include in <head> after Hue's base CSS.

        Users build and serve their own CSS however they like, then add the URL
        here. Hue includes it in the page after its own CSS.
        """
        return getattr(
            django_settings,
            "HUE_EXTRA_CSS_URLS",
            [],
        )

    @property
    def HUE_HTML_TITLE_FACTORY(self) -> Callable[[str], str]:
        """
        Callback function to make the HTML title.
        """
        return getattr(
            django_settings,
            "HUE_HTML_TITLE_FACTORY",
            lambda title: f"{title} - Hue",
        )


settings = Settings()
