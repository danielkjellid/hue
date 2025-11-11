from typing import Callable

from django.conf import settings as django_settings


class Settings:
    @property
    def HUE_CSS_STATIC_PATH(self) -> str:
        """
        Make the path to the CSS file configurable. Default to the prebuilt css file.
        """
        return getattr(
            django_settings,
            "HUE_CSS_STATIC_PATH",
            "hue/styles/tailwind.css",
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
