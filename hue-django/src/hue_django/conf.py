from typing import Callable

from django.conf import settings as django_settings
from hue.formats import Formats


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

    @property
    def HUE_DATE_FORMAT(self) -> str:
        """
        The strftime format components write a date in, ISO 8601 by default.
        """
        return getattr(django_settings, "HUE_DATE_FORMAT", Formats().date)

    @property
    def HUE_DATETIME_FORMAT(self) -> str:
        """
        The strftime format components write a date with a time in.
        """
        return getattr(django_settings, "HUE_DATETIME_FORMAT", Formats().datetime)


settings = Settings()
