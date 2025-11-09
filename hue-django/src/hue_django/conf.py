from django.conf import settings as django_settings


class Settings:
    @property
    def HUE_ENABLE_HMR(self) -> bool:
        return getattr(django_settings, "HUE_ENABLE_HMR", False)


settings = Settings()
