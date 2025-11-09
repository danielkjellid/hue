from django.conf import settings as django_settings
from pathlib import Path


class Settings:
    @property
    def HUE_PROJECT_ROOT(self) -> Path | None:
        return getattr(django_settings, "HUE_PROJECT_ROOT", None)

    @property
    def HUE_CSS_OUTPUT_PATH(self) -> Path | None:
        return getattr(django_settings, "HUE_CSS_OUTPUT_PATH", None)

    @property
    def HUE_CSS_INPUT_PATH(self) -> Path | None:
        return getattr(django_settings, "HUE_CSS_INPUT_PATH", None)

    @property
    def HUE_CONTENT_PATHS(self) -> list[Path]:
        return getattr(django_settings, "HUE_CONTENT_PATHS", [])

    @property
    def HUE_COMPONENT_MODULES(self) -> list[str]:
        return getattr(django_settings, "HUE_COMPONENT_MODULES", [])


settings = Settings()
