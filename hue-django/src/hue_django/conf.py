from functools import cache
from typing import Callable

from django.conf import settings as django_settings
from django.utils.module_loading import import_string
from hue.formats import Formats
from hue.shortcuts import ShortcutRegistry


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
        The date fields refuse a format they cannot read back; Formats says
        which they read.
        """
        return getattr(django_settings, "HUE_DATE_FORMAT", Formats().date)

    @property
    def HUE_DATETIME_FORMAT(self) -> str:
        """
        The strftime format components write a date with a time in.
        The date and time field refuses a format it cannot read back; Formats
        says which it reads.
        """
        return getattr(django_settings, "HUE_DATETIME_FORMAT", Formats().datetime)

    @property
    def HUE_TIME_FORMAT(self) -> str:
        """
        The strftime format components write a time of day in.
        The time field refuses a format it cannot read back; Formats says
        which it reads.
        """
        return getattr(django_settings, "HUE_TIME_FORMAT", Formats().time)

    @property
    def HUE_SHORTCUTS(self) -> type[ShortcutRegistry] | None:
        """
        The app's ShortcutRegistry, as a dotted path or the class itself.
        Every page binds it, and palettes and menus can show its shortcuts.
        """
        value = getattr(django_settings, "HUE_SHORTCUTS", None)
        return _registry(value) if isinstance(value, str) else value


# Imported once per path rather than on every request.
@cache
def _registry(path: str) -> type[ShortcutRegistry]:
    registry = import_string(path)
    if not (isinstance(registry, type) and issubclass(registry, ShortcutRegistry)):
        raise TypeError(
            f"HUE_SHORTCUTS points at {path}, which is not a ShortcutRegistry."
        )
    return registry


settings = Settings()
