from functools import cached_property
from typing import Callable

from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.views import View
from hue.base import BaseView, ViewValidationMixin
from hue.context import HueContextArgs

from hue_django.conf import settings


class HueView(BaseView, ViewValidationMixin, View):
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
        return staticfiles_storage.url(settings.HUE_CSS_STATIC_PATH)

    @cached_property
    def html_title_factory(self) -> Callable[[str], str]:
        return settings.HUE_HTML_TITLE_FACTORY

    async def get(self, request: HttpRequest) -> HttpResponse:
        context = HueContextArgs[HttpRequest](
            request=request,
            csrf_token=get_token(request),
        )
        page_content = await self.render(context)
        return HttpResponse(page_content)
