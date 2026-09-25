from collections import defaultdict
from collections.abc import Awaitable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseNotAllowed,
)
from django.urls import URLPattern, path
from django.utils.functional import classproperty
from django.views import View
from hue.context import HueContext
from hue.exceptions import AJAXRequiredError, BodyValidationError
from hue.pages import BasePage
from hue.router import RawResponse, Route

from hue_django.router import Router

type UrlPatterns = tuple[list[URLPattern], str]


class _BaseView(View):
    @classproperty
    def app_name(cls: Any) -> str:
        return cls.__name__.lower()

    @classproperty
    def urls(cls: Any) -> UrlPatterns:
        """
        (urlpatterns, app_name), ready for Django's include(). Built once per
        class.
        """
        # Cached on the class itself, not inherited, so a subclass gets its own.
        if "_urls" not in cls.__dict__:
            cls._urls = cls._build_urls()
        return cls._urls

    @classmethod
    def _build_urls(cls) -> UrlPatterns:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def _url_patterns(cls, routes: list[Route]) -> list[URLPattern]:
        # One Django URL pattern per path; the dispatcher picks the route by
        # method. The pattern takes the name of the first route on that path.
        by_path: dict[str, list[Route]] = defaultdict(list)
        for route in routes:
            by_path[route.path].append(route)

        return [
            path(path_str, cls._dispatcher(path_routes), name=path_routes[0].name)
            for path_str, path_routes in by_path.items()
        ]

    @classmethod
    def _dispatcher(cls, routes: list[Route]) -> Any:
        by_method = {route.method: route for route in routes}
        # HEAD falls back to GET; Django strips the body.
        if "GET" in by_method:
            by_method.setdefault("HEAD", by_method["GET"])

        async def view(request: HttpRequest, **kwargs: Any) -> HttpResponseBase:
            route = by_method.get(request.method or "")
            if route is None:
                return HttpResponseNotAllowed(sorted(by_method))

            instance = cls()
            instance.setup(request, **kwargs)
            return await instance._handle_route(request, route, **kwargs)

        return view

    async def _handle_route(
        self, request: HttpRequest, route: Route, **kwargs: Any
    ) -> HttpResponseBase:
        try:
            result = await route.view_func(self, request, **kwargs)
        except AJAXRequiredError:
            return HttpResponseBadRequest("AJAX request required")
        except BodyValidationError as exc:
            return self.handle_body_validation_error(request, exc)

        if isinstance(result, RawResponse):
            return result.response

        html, status_code = result
        return HttpResponse(html, status=status_code)

    def handle_body_validation_error(
        self, request: HttpRequest, exc: BodyValidationError
    ) -> HttpResponseBase:
        """
        The response when a handler's body fails validation. Override to render
        the errors back into the form; exc.errors holds Pydantic's details.
        """
        return HttpResponse(str(exc), status=HTTPStatus.UNPROCESSABLE_ENTITY)


class HueFragmentsView(_BaseView):
    """
    A view for fragment-only routes, with no index page.

    Groups related fragments behind one router; every route is AJAX-only.

        class CommentsFragments(HueFragmentsView):
            router = Router[HttpRequest]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> html.div:
                return html.div("Comments list")
    """

    @classmethod
    def _build_urls(cls) -> UrlPatterns:
        router: Router[HttpRequest] | None = getattr(cls, "router", None)
        if router is None:
            raise ValueError(
                f"{cls.__name__} must define a 'router' attribute. "
                "HueFragmentsView requires a router to handle fragment routes."
            )
        return cls._url_patterns(router.routes), cls.app_name


class HueView(_BaseView):
    """
    A full page view with optional fragment routes.

    index (sync or async) handles the initial GET and returns a Page. Fragment
    routes are added with the router and are AJAX-only.

        class LoginView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Page:
                return Page(title="Login", body=...)

            @router.fragment_post("login/")
            async def login(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> html.div:
                return html.div("Login successful")
    """

    if TYPE_CHECKING:
        # A method rather than an attribute of a callable type, so that the
        # def a subclass writes, self and all, is an override mypy accepts.
        # Declared for the type checker only: at runtime a view without one
        # is refused by name below.
        def index(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ) -> BasePage | Awaitable[BasePage]: ...

    @classmethod
    def _build_urls(cls) -> UrlPatterns:
        index = getattr(cls, "index", None)
        if index is None:
            raise ValueError(
                f"{cls.__name__} must define an 'index' method. "
                "HueView requires an index method to handle the initial page load."
            )
        if not callable(index):
            raise ValueError(f"{cls.__name__}.index must be a callable method.")

        # The index is registered on a private router so the user's router (a
        # class attribute, shared with subclasses) is never mutated, and each
        # subclass gets its own index.
        index_router = Router[HttpRequest]()
        index_router.page("/")(index)

        router: Router[HttpRequest] | None = getattr(cls, "router", None)
        routes = index_router.routes + (router.routes if router else [])
        return cls._url_patterns(routes), cls.app_name
