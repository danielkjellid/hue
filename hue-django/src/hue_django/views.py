import inspect
from functools import cached_property
from typing import Callable

from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, path
from django.views import View

from hue_django.conf import settings


class HueViewMeta(type):
    """Metaclass to make urls accessible as a class attribute."""

    def __getattr__(cls, name: str):
        if name == "urls":
            return cls._get_urls()
        raise AttributeError(f"{cls.__name__} has no attribute {name}")


class HueView(View, metaclass=HueViewMeta):
    """
    Django-specific base view that provides framework defaults.

    Supports routing via Router for both full page and AJAX fragment routes.

    Example:
        class MyView(HueView):
            title = "My Page"
            router = Router[HttpRequest]()

            @router.get("/")
            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Index")

            @router.ajax_get("comments/<int:comment_id>/")
            async def comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                comment_id: int,
            ):
                return html.div(f"Comment {comment_id}")
    """

    @cached_property
    def css_url(self) -> str:
        """Get the CSS URL using Django's static files storage."""
        return staticfiles_storage.url(settings.HUE_CSS_STATIC_PATH)

    @cached_property
    def js_url(self) -> str:
        """Get the Alpine.js bundle URL using Django's static files storage."""
        return staticfiles_storage.url("hue/js/alpine-bundle.js")

    @cached_property
    def html_title_factory(self) -> Callable[[str], str]:
        return settings.HUE_HTML_TITLE_FACTORY

    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        """
        Generate Django URL patterns from the router.

        Returns a tuple of (urlpatterns, app_name) compatible
        with Django's include() function.

        Usage:
            urlpatterns = [path("myview/", include(MyView.urls))]
            # With namespace:
            urlpatterns = [path("myview/", include(MyView.urls, namespace="myview"))]
            # or
            urlpatterns = MyView.urls[0]  # Just get the patterns
        """
        router = getattr(cls, "router", None)
        if not router:
            # No router, return empty tuple
            return ([], "")

        url_patterns = []
        routes = router.routes

        for route in routes:
            # Create a view method name based on the handler
            handler_name = route.handler.__name__

            # Create URL pattern that dispatches to this route
            # Capture route in closure properly
            async def view_func(request, route=route, **kwargs):
                # Create view instance and set it up properly
                view_instance = cls()
                view_instance.setup(request, **kwargs)
                # Call the async handler
                return await view_instance._handle_route(request, route, **kwargs)

            url_patterns.append(
                path(
                    route.path,
                    view_func,
                    name=handler_name,
                )
            )

        # Return tuple compatible with Django's include()
        # Django expects (urlpatterns, app_name)
        app_name = getattr(cls, "app_name", cls.__name__.lower())
        return (url_patterns, app_name)

    async def _handle_route(
        self, request: HttpRequest, route, **kwargs
    ) -> HttpResponse:
        """
        Handle a route request.

        The router wraps handlers to automatically render Components to HTML,
        so we just call the wrapped handler and return the HTML string.
        """
        # Check method matches
        if route.method != request.method.upper():
            return HttpResponse("Method not allowed", status=405)

        # Extract only path parameters for the handler
        handler_kwargs = {k: v for k, v in kwargs.items() if k in route.path_params}

        # Call the wrapped handler (which returns HTML string, not Component)
        handler_result = route.handler(self, request, **handler_kwargs)

        # Await if it's a coroutine (wrapped handler is async)
        while inspect.iscoroutine(handler_result):
            handler_result = await handler_result

        # Handler now returns HTML string (thanks to router wrapping)
        return HttpResponse(handler_result)
