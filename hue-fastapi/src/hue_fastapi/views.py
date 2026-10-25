from collections import defaultdict
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from inspect import Parameter, Signature, signature
from typing import Any, Final, get_type_hints

from fastapi import APIRouter, Depends
from hue.exceptions import AJAXRequiredError, BodyValidationError
from hue.router import PAGE_ROUTE, RawResponse, Route, check_unique_routes
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from hue_fastapi.config import get_config
from hue_fastapi.csrf import SAFE_METHODS, csrf_protect
from hue_fastapi.router import HANDLER_ATTR, MOUNT_STATE, Mount, Router, preload_body

_ALL_METHODS: Final = frozenset(
    {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
)

# A handler takes the view, the request and the context first, whatever it
# calls them, and hue fills those and body in itself. Everything else is handed
# to FastAPI, so path parameters, query parameters and Depends all work.
_HUE_POSITIONAL: Final = 3
_HUE_BODY: Final = "body"


class classproperty[T]:
    """
    A property that reads from the class rather than an instance.
    """

    def __init__(self, fget: Callable[[Any], T]) -> None:
        self.fget = fget

    def __get__(self, instance: object, owner: type | None = None) -> T:
        return self.fget(owner)


def _method_not_allowed(allowed: list[str]) -> Callable[[Request], Awaitable[Response]]:
    async def endpoint(request: Request) -> Response:
        return Response(
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
            headers={"Allow": ", ".join(allowed)},
        )

    return endpoint


class _BaseView:
    @classproperty
    def app_name(cls: Any) -> str:
        return cls.__name__.lower()

    @classproperty
    def api_router(cls: Any) -> APIRouter:
        """
        A FastAPI router for this view, ready for app.include_router. Built
        once per class.
        """
        # Cached on the class itself, not inherited, so a subclass gets its own.
        if "_api_router" not in cls.__dict__:
            cls._api_router = cls._build_api_router()
        return cls._api_router

    @classmethod
    def _build_api_router(cls) -> APIRouter:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    def _routes_to_api_router(cls, routes: list[Route]) -> APIRouter:
        check_unique_routes(routes)
        paths = {route.name: route.path for route in routes}
        api_router = APIRouter()

        by_path: dict[str, list[Route]] = defaultdict(list)
        for route in routes:
            by_path[route.path].append(route)

        for path, path_routes in by_path.items():
            # Starlette paths are absolute; hue normalises the leading slash off.
            starlette_path = "/" + path
            supported: set[str] = set()

            for route in path_routes:
                methods = [route.method]
                if route.method == "GET":
                    methods.append("HEAD")
                supported.update(methods)

                api_router.add_api_route(
                    starlette_path,
                    cls._make_endpoint(route, paths),
                    methods=methods,
                    name=f"{cls.app_name}:{route.name}",
                    dependencies=(
                        [] if route.method in SAFE_METHODS else [Depends(csrf_protect)]
                    ),
                    include_in_schema=False,
                    response_class=HTMLResponse,
                )

            # Starlette reports only the first partially matching route when it
            # answers 405, which would advertise an incomplete Allow header. A
            # catch-all for the remaining methods answers with the full set.
            remaining = sorted(_ALL_METHODS - supported)
            if remaining:
                api_router.add_api_route(
                    starlette_path,
                    _method_not_allowed(sorted(supported)),
                    methods=remaining,
                    include_in_schema=False,
                )

        return api_router

    @classmethod
    def _make_endpoint(
        cls, route: Route, paths: dict[str, str]
    ) -> Callable[..., Awaitable[Response]]:
        handler = getattr(route.view_func, HANDLER_ATTR, None)
        parameters = [Parameter("request", Parameter.KEYWORD_ONLY, annotation=Request)]

        if handler is not None:
            hints = get_type_hints(handler)
            handler_params = list(signature(handler).parameters.items())
            for name, parameter in handler_params[_HUE_POSITIONAL:]:
                if name == _HUE_BODY:
                    continue
                parameters.append(
                    Parameter(
                        name,
                        Parameter.KEYWORD_ONLY,
                        default=parameter.default,
                        annotation=hints.get(name, parameter.annotation),
                    )
                )

        async def endpoint(**kwargs: Any) -> Response:
            request: Request = kwargs.pop("request")
            # Every unsafe method, not only a handler with a body parameter:
            # a table's actions read the posted ids through the router.
            if request.method not in SAFE_METHODS:
                await preload_body(request)
            setattr(request.state, MOUNT_STATE, Mount.of(request, route.path, paths))
            return await cls()._handle_route(request, route, **kwargs)

        endpoint.__signature__ = Signature(parameters)  # type: ignore[attr-defined]
        endpoint.__name__ = route.name
        return endpoint

    async def _handle_route(
        self, request: Request, route: Route, **kwargs: Any
    ) -> Response:
        try:
            result = await route.view_func(self, request, **kwargs)
        except AJAXRequiredError:
            response: Response = PlainTextResponse(
                "AJAX request required", status_code=HTTPStatus.BAD_REQUEST
            )
        except BodyValidationError as exc:
            response = await self.handle_body_validation_error(request, exc)
        else:
            if isinstance(result, RawResponse):
                response = result.response
            else:
                html, status_code = result
                response = HTMLResponse(html, status_code=status_code)

        config = get_config(request.app)
        if config.csrf is not None:
            config.csrf.apply(request, response)
        return response

    async def handle_body_validation_error(
        self, request: Request, exc: BodyValidationError
    ) -> Response:
        """
        The response when a handler's body fails validation. Override to render
        the errors back into the form; exc.errors holds Pydantic's details.
        """
        return PlainTextResponse(str(exc), status_code=HTTPStatus.UNPROCESSABLE_ENTITY)


class HueFragmentsView(_BaseView):
    """
    A view for fragment-only routes, with no index page.

    Groups related fragments behind one router; every route is AJAX-only.

        class CommentsFragments(HueFragmentsView):
            router = Router[Request]()

            @router.fragment_get("comments/")
            async def list_comments(
                self, request: Request, context: HueContext[Request]
            ) -> html.div:
                return html.div("Comments list")

        app.include_router(CommentsFragments.api_router, prefix="/comments")
    """

    @classmethod
    def _build_api_router(cls) -> APIRouter:
        router: Router[Request] | None = getattr(cls, "router", None)
        if router is None:
            raise ValueError(
                f"{cls.__name__} must define a 'router' attribute. "
                "HueFragmentsView requires a router to handle fragment routes."
            )
        return cls._routes_to_api_router(router.routes)


class HueView(_BaseView):
    """
    A full page view with optional fragment routes.

    index (sync or async) handles the initial GET and returns a Page. It may
    take anything else FastAPI can supply as well, such as path parameters,
    query parameters or a Depends, which is why no protocol pins its signature.
    Fragment routes are added with the router and are AJAX-only.

        class LoginView(HueView):
            router = Router[Request]()

            async def index(
                self, request: Request, context: HueContext[Request]
            ) -> Page:
                return Page(title="Login", body=...)

            @router.fragment_post("login/")
            async def login(
                self, request: Request, context: HueContext[Request], body: LoginForm
            ) -> html.div:
                return html.div("Welcome")

        app.include_router(LoginView.api_router, prefix="/login")
    """

    @classmethod
    def _build_api_router(cls) -> APIRouter:
        index = getattr(cls, "index", None)
        if index is None:
            raise ValueError(
                f"{cls.__name__} must define an 'index' method. "
                "HueView requires an index method to handle the initial page load."
            )
        if not callable(index):
            raise ValueError(f"{cls.__name__}.index must be a callable method.")

        # Registered on a private router so the user's router, a class
        # attribute shared with subclasses, is never mutated and each subclass
        # gets its own index.
        index_router = Router[Request]()
        index_router.page("/", name=PAGE_ROUTE)(index)

        router: Router[Request] | None = getattr(cls, "router", None)
        routes = index_router.routes + (router.routes if router else [])
        return cls._routes_to_api_router(routes)
