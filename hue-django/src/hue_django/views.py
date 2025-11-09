from functools import cached_property
from typing import ClassVar

from hue.base import BaseView, ViewValidationMixin
from django.contrib.staticfiles.storage import staticfiles_storage


class HueView(BaseView, ViewValidationMixin):
    """
    Django-specific base view that provides framework defaults.

    Subclasses can override any attribute as needed - you don't need to
    redefine all attributes, only the ones you want to change.

    Example:
        class MyView(HueView):
            title = "My Page"  # Only override what you need

        class AnotherView(HueView):
            title = "Another Page"
            x_data = {"custom": "value"}  # Can also override x_data
    """

    @cached_property
    def css_url(self) -> str:
        """Get the CSS URL using Django's static files storage."""
        return staticfiles_storage.url("styles/tailwind.css")
