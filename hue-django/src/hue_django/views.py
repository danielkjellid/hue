import inspect
from functools import cached_property
from typing import Callable

from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.urls import URLPattern, path
from django.views import View
from htmy import Renderer

from hue.context import HueContext, HueContextArgs

from hue_django.conf import settings
from hue_django.router import Router  # noqa: F401


class HueViewMeta(type):
    """Metaclass to make urls accessible as a class attribute."""

    def __getattr__(cls, name: str):
        if name == "urls":
            return cls._get_urls()
        raise AttributeError(f"{cls.__name__} has no attribute {name}")


class HueFragmentsView(View, metaclass=HueViewMeta):
    """
    Django-specific base view for fragment-only routes.

    This view is meant as a collective view for fragments with similar attributes.
    It must have a router defined, and only handles decorated routes (fragments).

    Example:
        class CommentsFragments(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.ajax_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comments list")

            @router.ajax_post("comments/")
            async def create_comment(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Comment created")
    """

    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        """
        Generate Django URL patterns from the router.

        Returns a tuple of (urlpatterns, app_name) compatible
        with Django's include() function.

        Raises:
            ValueError: If no router is defined on the class.
        """
        router = getattr(cls, "router", None)
        if not router:
            raise ValueError(
                f"{cls.__name__} must define a 'router' attribute. "
                "HueFragmentsView requires a router to handle fragment routes."
            )

        url_patterns = []
        routes = router.routes

        for route in routes:
            # Create a view method name based on the view function
            view_func_name = route.view_func.__name__

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
                    name=view_func_name,
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

        The router wraps view functions to automatically render Components to HTML,
        so we just call the wrapped handler and return the HTML string.
        """
        # Check method matches
        if route.method != request.method.upper():
            return HttpResponse("Method not allowed", status=405)

        # Extract only path parameters for the handler
        handler_kwargs = {k: v for k, v in kwargs.items() if k in route.path_params}

        # Call the wrapped handler (which returns HTML string, not Component)
        view_func_result = route.view_func(self, request, **handler_kwargs)

        # Await if it's a coroutine (wrapped handler is async)
        while inspect.iscoroutine(view_func_result):
            view_func_result = await view_func_result

        # Handler now returns HTML string (thanks to router wrapping)
        return HttpResponse(view_func_result)


class HueView(HueFragmentsView):
    """
    Django-specific base view for full page views with optional fragment routes.

    This view must have an `async def index` method that handles the initial
    page load (GET "/"). It can optionally define a router for additional
    AJAX fragment routes.

    Example:
        class LoginView(HueView):
            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return Page(...)  # Full page on initial load

            router = Router[HttpRequest]()

            @router.ajax_post("login/")
            async def login(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Login successful")  # Fragment
    """

    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        """
        Generate Django URL patterns from the index method and optional router.

        Returns a tuple of (urlpatterns, app_name) compatible
        with Django's include() function.

        Raises:
            ValueError: If no index method is defined on the class.
        """
        # Check for index method
        if not hasattr(cls, "index"):
            raise ValueError(
                f"{cls.__name__} must define an 'async def index' method. "
                "HueView requires an index method to handle the initial page load."
            )

        if not callable(cls.index):
            raise ValueError(f"{cls.__name__}.index must be a callable method.")

        # Check if it's async (should be, but we'll handle both)
        is_async = inspect.iscoroutinefunction(cls.index)

        url_patterns = []

        # Get router if it exists (for context creation)
        router = getattr(cls, "router", None)

        # Create index route (GET "/") - always full page
        async def index_view_func(request, **kwargs):
            view_instance = cls()
            view_instance.setup(request, **kwargs)

            # Create context
            if router:
                context_args = router._get_context_args(request)
            else:
                # Fallback if no router - create minimal context
                context_args = HueContextArgs[HttpRequest](
                    request=request,
                    csrf_token=get_token(request),
                )

            context = HueContext(**context_args)

            # Call index method
            if is_async:
                component = await cls.index(view_instance, request, context, **kwargs)
            else:
                component = cls.index(view_instance, request, context, **kwargs)

            # Render as full page (not fragment)
            # Since this is the index route, it should always render as full page
            # We need to ensure it's not treated as an AJAX request
            if router:
                # Use router's render method for full page
                # The router's _wrap_handler checks for AJAX headers, but we're
                # calling _render directly, so it will render as full page
                html_string = await router._render(component, view_instance, request)
            else:
                # No router, use basic rendering
                renderer = Renderer()
                html_string = await renderer.render(
                    HueContext(component, **context_args)
                )

            return HttpResponse(html_string)

        url_patterns.append(path("", index_view_func, name="index"))

        # Add router routes if router exists (all fragments)
        if router:
            routes = router.routes

            for route in routes:
                # Create a view method name based on the handler
                view_func_name = route.view_func.__name__

                # Create URL pattern that dispatches to this route
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
                        name=view_func_name,
                    )
                )

        # Return tuple compatible with Django's include()
        # Django expects (urlpatterns, app_name)
        app_name = getattr(cls, "app_name", cls.__name__.lower())
        return (url_patterns, app_name)
