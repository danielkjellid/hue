import inspect
from http import HTTPStatus
from typing import TYPE_CHECKING, Awaitable, Protocol

from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, path
from django.views import View
from hue.context import HueContext
from hue.exceptions import AJAXRequiredError
from hue.pages import BasePage
from hue.router import HueResponse

from hue_django.router import Router


class IndexMethod(Protocol):
    """
    Protocol defining the signature for the index method in HueView subclasses.

    The index method can be either synchronous or asynchronous, returning
    a BasePage instance or an Awaitable[BasePage] respectively.
    """

    def __call__(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
    ) -> BasePage | Awaitable[BasePage]: ...


class _BaseViewMeta(type):
    """Metaclass to make urls accessible as a class attribute."""

    def __getattr__(cls, name: str):
        if name == "urls":
            return cls._get_urls()
        if name == "app_name":
            return cls.get_app_name()
        raise AttributeError(f"{cls.__name__} has no attribute {name}")


class _BaseView(View, metaclass=_BaseViewMeta):
    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def get_app_name(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def _create_url_patterns_from_router(
        cls, router: Router[HttpRequest] | None
    ) -> list[URLPattern]:
        if not router:
            return []

        url_patterns: list[URLPattern] = []
        routes = router.routes

        # Group routes by path to handle multiple methods on same path
        routes_by_path: dict[str, list] = {}
        for route in routes:
            if route.path not in routes_by_path:
                routes_by_path[route.path] = []
            routes_by_path[route.path].append(route)

        # Create one URL pattern per unique path
        for path_str, path_routes in routes_by_path.items():
            # Create a dispatcher that checks all routes for this path
            async def view_func(request, routes=path_routes, **kwargs):
                # Create view instance and set it up properly
                view_instance = cls()
                view_instance.setup(request, **kwargs)
                # Find the route that matches the HTTP method
                matching_route = None
                for route in routes:
                    if route.method == request.method.upper():
                        matching_route = route
                        break
                # If no matching route, return 405
                if not matching_route:
                    return HttpResponse("Method not allowed", status=405)
                # Call the async handler with the matching route
                # Catch AssertionError from AJAX validation and return 400
                try:
                    return await view_instance._handle_route(
                        request, matching_route, **kwargs
                    )
                except AJAXRequiredError:
                    return HttpResponse("Bad Request", status=400)

            # Use the first route's function name for the URL pattern name
            view_func_name = path_routes[0].name

            url_patterns.append(
                path(
                    path_str,
                    view_func,
                    name=view_func_name,
                )
            )

        return url_patterns

    async def _handle_route(
        self, request: HttpRequest, route, **kwargs
    ) -> HttpResponse:
        """
        Handle a route request.

        The router wraps view functions to automatically render Components to HTML,
        so we just call the wrapped handler and return the tuple (html, status_code).
        """
        # Extract only path parameters for the handler
        handler_kwargs = {k: v for k, v in kwargs.items() if k in route.path_params}

        # Call the wrapped handler (which returns (html_string, status_code))
        # Catch AJAXRequiredError from AJAX validation
        try:
            view_func_result = route.view_func(self, request, **handler_kwargs)

            # Await if it's a coroutine (wrapped handler is async)
            while inspect.iscoroutine(view_func_result):
                view_func_result = await view_func_result

            # Handler returns tuple of (html_string, status_code)
            html, status_code = view_func_result
            return HttpResponse(html, status=status_code)
        except AJAXRequiredError:
            return HttpResponse("Bad Request", status=400)


class HueFragmentsView(_BaseView):
    """
    Django-specific base view for fragment-only routes.

    This view is meant as a collective view for fragments with similar attributes.
    It must have a router defined, and only handles decorated routes (fragments).

    Example:
        class CommentsFragments(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Component:
                return CommentsList(comments=comments)

            @router.fragment_post("comments/")
            async def create_comment(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Component | HueResponse:
                form = CommentForm(request.POST)
                if not form.is_valid():
                    # Return 422 with error fragment wrapped in target div
                    return HueResponse(
                        component=FormErrors(errors=form.errors),
                        target="comment-form",
                        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                return CommentCreated(comment=form.save())
    """

    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        """
        Generate Django URL patterns from the router.

        Returns a tuple of (urlpatterns, app_name) compatible with Django's include()
        function.
        """
        router = getattr(cls, "router", None)

        if not router:
            raise ValueError(
                f"{cls.__name__} must define a 'router' attribute. "
                "HueFragmentsView requires a router to handle fragment routes."
            )

        url_patterns = cls._create_url_patterns_from_router(router)

        # Return tuple compatible with Django's include()
        # Django expects (urlpatterns, app_name)
        return (url_patterns, cls.app_name)


class HueView(_BaseView):
    """
    Django-specific base view for full page views with optional fragment routes.

    This view must have an `index` method (sync or async) that handles the initial
    page load (GET "/"). It can optionally define a router for additional
    AJAX fragment routes.

    Example:
        class LoginView(HueView):
            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Page:
                return Page(...)  # Full page on initial load

            router = Router[HttpRequest]()

            @router.fragment_post("authenticate/")
            async def authenticate(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Component | HueResponse:
                form = LoginForm(request.POST)
                if not form.is_valid():
                    return HueResponse(
                        component=LoginError(errors=form.errors),
                        target="login-form",
                        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                user = authenticate(**form.cleaned_data)
                if not user:
                    return HueResponse(
                        component=LoginError(message="Invalid credentials"),
                        target="login-form",
                        status_code=HTTPStatus.UNAUTHORIZED,
                    )
                return LoginSuccess()
    """

    if TYPE_CHECKING:
        # Type hint for subclasses - index method must match IndexMethod protocol
        index: IndexMethod

    @classmethod
    def _get_urls(cls) -> tuple[list[URLPattern], str]:
        """
        Generate Django URL patterns from the index method and optional router.
        """
        # Check for index method
        if not hasattr(cls, "index"):
            raise ValueError(
                f"{cls.__name__} must define an 'index' method. "
                "HueView requires an index method to handle the initial page load."
            )

        if not callable(cls.index):
            raise ValueError(f"{cls.__name__}.index must be a callable method.")

        if (router := getattr(cls, "router", None)) is None:
            router = Router[HttpRequest]()

        # Register index route with the router. Uses _page decorator to
        # mark it as a non-AJAX route.
        router._page("/")(cls.index)
        url_patterns = cls._create_url_patterns_from_router(router)

        # Return tuple compatible with Django's include()
        # Django expects (urlpatterns, app_name)
        return (url_patterns, cls.app_name)
