import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import partialmethod
from http import HTTPStatus
from typing import Any, cast, get_type_hints

from htmy import html
from pydantic import TypeAdapter, ValidationError

from hue.context import HueContext, HueContextArgs
from hue.exceptions import AJAXRequiredError, BodyValidationError
from hue.renderer import render_tree
from hue.types.core import Component, ComponentType

# Default HTTP status code for successful responses
DEFAULT_STATUS_CODE = HTTPStatus.OK


@dataclass(slots=True, frozen=True)
class HueResponse:
    """
    A structured response for fragment handlers.

    Wraps a component with a target ID and status code. The component is rendered
    inside a div with the target ID, which is necessary for Alpine AJAX to properly
    merge the content using innerHTML.

    Example:
        @router.fragment_post("login/")
        async def login(self, request, context):
            if not valid:
                # Returns 422 with error fragment wrapped in <div id="login-form">
                return HueResponse(
                    target="login-form",
                    component=LoginError(message="Invalid credentials"),
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            return SuccessFragment()
    """

    component: ComponentType
    target: str | None = None
    status_code: int = DEFAULT_STATUS_CODE

    def htmy(self, context: Any) -> Component:
        """Wrap the component in a div with the target ID for Alpine AJAX merging."""
        if self.target:
            return html.div(self.component, id=self.target)
        return self.component


@dataclass(slots=True)
class RawResponse:
    """
    Wrapper for passing through raw framework responses (e.g., HttpResponse, redirects).

    When a view function returns something that looks like a framework response
    (has status_code attribute), the router wraps it in RawResponse so the
    framework-specific handler can pass it through directly.

    This allows returning Django's redirect(), HttpResponse, etc. from handlers.

    Example:
        from django.shortcuts import redirect

        @router.fragment_post("login/")
        async def login(self, request, context, body: LoginForm):
            user = await sync_to_async(authenticate)(request, **body.dict())
            if user:
                await sync_to_async(django_login)(request, user)
                return redirect("/dashboard/")  # Passed through directly
            return LoginError()
    """

    response: Any


@dataclass
class PathParseResult:
    path: str
    param_names: list[str]


# Type alias for view function results
# Can be: Component, HueResponse, or any framework response (e.g., HttpResponse)
type ViewResult = Component | HueResponse | Any
type AwaitableViewResult = ViewResult | Awaitable[ViewResult]

# Type alias for wrapped view function results
# Returns either (html_string, status_code) or RawResponse for passthrough
type WrappedViewResult = tuple[str, int] | RawResponse

# Type alias for wrapped view functions
# Signature: (view_instance, request, **kwargs) -> Awaitable[WrappedViewResult]
type WrappedViewFunc = Callable[..., Awaitable[WrappedViewResult]]

# Type alias for original view functions (return Component or HueResponse)
# Signature: (view_instance, request: T_Request, context: HueContext[T_Request],
#             **kwargs) -> ViewResult | Awaitable[ViewResult]
type ViewFunc = Callable[..., AwaitableViewResult]


@dataclass
class Route:
    """Represents a single route with its view function and metadata."""

    method: str
    path: str
    name: str
    view_func: WrappedViewFunc
    # List of parameter names extracted from path
    # Framework-specific routers can populate this based on their path syntax
    path_params: list[str] = field(default_factory=list)


class Router[T_Request]:
    """
    Framework-agnostic base router for defining routes in HueView.

    Fragment routes return HTML fragments (Component) and require AJAX requests.
    Page routes return full pages and don't require AJAX.
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []

    @property
    def routes(self) -> list[Route]:
        return self._routes.copy()

    def _normalize_path(self, path: str) -> str:
        """
        Normalize the path (e.g., strip leading slashes).
        """
        # Default: strip leading slash
        # Root path "/" becomes "" (empty string)
        return path.lstrip("/")

    def _parse_path_params(self, path: str) -> PathParseResult:
        """
        Parse the path parameters from the path.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        """
        Get framework-specific context arguments (request, CSRF token, etc.).
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    async def render(
        self,
        component: ComponentType,
        request: T_Request,
    ) -> str:
        """
        Render a Component to HTML string.

        This is framework-agnostic - it uses Renderer to convert Components to HTML.
        The renderer calls .htmy() on all components, so both fragments and full
        pages are rendered the same way.
        """
        return await render_tree(
            component, context_args=self._get_context_args(request)
        )

    def _is_ajax_request(self, request: T_Request) -> bool:
        """
        Check if the request is an AJAX request.

        Framework-specific routers should override this method to handle
        framework-specific header access.

        Returns True if the request has either:
        - X-Requested-With: XMLHttpRequest header, or
        - X-Alpine-Request: true header
        """
        headers = getattr(request, "headers", {})

        if hasattr(headers, "get"):
            is_ajax_req = headers.get("X-Requested-With") == "XMLHttpRequest"
            is_alpine_ajax_req = headers.get("X-Alpine-Request") == "true"
            return is_ajax_req or is_alpine_ajax_req

        return False

    def _get_request_body(self, request: T_Request) -> str:
        """
        Get the raw request body as a string.

        Framework-specific routers should override this method to handle
        framework-specific body access.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_request_content_type(self, request: T_Request) -> str:
        """
        Get the content type of the request.

        Framework-specific routers should override this method.
        Returns empty string if content type is not available.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    def _get_form_data(self, request: T_Request) -> dict[str, Any]:
        """
        Get form data from the request as a dictionary.

        Framework-specific routers should override this method.
        Returns empty dict if no form data is available.
        """
        raise NotImplementedError(
            "This method must be overridden by framework-specific routers"
        )

    async def _call_view_func(
        self,
        view_func: ViewFunc,
        view_instance: object,
        request: T_Request,
        context: HueContext[T_Request],
        **kwargs: Any,
    ) -> Any:
        """
        Call the view function and return its result.

        Framework-specific routers can override this to handle sync/async
        execution differently. For example, Django needs to wrap sync functions
        with sync_to_async for proper ASGI compatibility.

        Default implementation calls the function directly and awaits if needed.
        """
        result = view_func(view_instance, request, context, **kwargs)

        # Await if it's a coroutine
        while inspect.iscoroutine(result):
            result = await result

        return result

    def _parse_body(self, request: T_Request, body_type: type) -> Any:
        """
        Parse the request body into the specified type using Pydantic.

        Supports both JSON and form-encoded data (application/x-www-form-urlencoded).
        Uses Pydantic's TypeAdapter which supports both Pydantic models and
        dataclasses.

        Raises:
            BodyValidationError: If the body cannot be parsed or validated.
        """
        content_type = self._get_request_content_type(request)

        # Determine how to parse based on content type
        if "application/json" in content_type:
            # Parse as JSON
            raw_body = self._get_request_body(request)
            try:
                data = json.loads(raw_body) if raw_body else {}
            except json.JSONDecodeError as e:
                raise BodyValidationError(
                    errors=[{"type": "json_invalid", "msg": str(e)}]
                ) from e
        else:
            # Default to form data (application/x-www-form-urlencoded or multipart)
            data = self._get_form_data(request)

        # Validate and convert to the target type using Pydantic
        try:
            adapter = TypeAdapter(body_type)
            return adapter.validate_python(data)
        except ValidationError as e:
            raise BodyValidationError(errors=e.errors()) from e

    def _wrap_view(
        self, view_func: ViewFunc, require_ajax: bool = True
    ) -> WrappedViewFunc:
        """
        Wrap a view function to automatically render Components and pass the hue
        context.

        The wrapped view returns a tuple of (html_string, status_code).
        View functions can return:
        - Component (uses default 200 status)
        - HueResponse (structured response with target, component, and status_code)

        If the view function has a `body` parameter with a type annotation,
        the request body will be automatically parsed into that type using
        Pydantic's TypeAdapter (supports both Pydantic models and dataclasses).
        """
        # Check if the view function has a 'body' parameter with a type hint
        try:
            type_hints = get_type_hints(view_func)
            body_type = type_hints.get("body")
        except Exception:
            # get_type_hints can fail with forward references, etc.
            body_type = None

        async def wrapped_view(
            view_instance: object, request: T_Request, **kwargs: Any
        ) -> WrappedViewResult:
            if require_ajax and not self._is_ajax_request(request):
                raise AJAXRequiredError()

            # Parse body if the handler expects it
            if body_type is not None:
                parsed_body = self._parse_body(request, body_type)
                kwargs["body"] = parsed_body

            # Build context for the handler (without component yet)
            context_args: HueContextArgs[T_Request] = self._get_context_args(request)
            context: HueContext[T_Request] = HueContext(**context_args)

            # Call the view function via hook (allows framework-specific handling)
            view_func_result = await self._call_view_func(
                view_func, view_instance, request, context, **kwargs
            )

            # Check if the result is a raw framework response (e.g., HttpResponse)
            # These have a status_code attribute and are not our HueResponse type
            if hasattr(view_func_result, "status_code") and not isinstance(
                view_func_result, HueResponse
            ):
                # Pass through raw responses directly
                return RawResponse(response=view_func_result)

            # Extract component and status code based on return type
            if isinstance(view_func_result, HueResponse):
                # HueResponse: use its properties (htmy() wraps in div with target)
                component = cast(ComponentType, view_func_result)
                status_code = view_func_result.status_code
            else:
                # Plain Component: use default status
                component = cast(ComponentType, view_func_result)
                status_code = DEFAULT_STATUS_CODE

            rendered_html = await self.render(component, request)
            return rendered_html, status_code

        # Always return async wrapper (view functions should be async for rendering)
        return wrapped_view

    def _request(
        self, method: str, path: str, require_ajax: bool = True
    ) -> Callable[[ViewFunc], ViewFunc]:
        """
        Internal method to register a route.

        Used with partialmethod to create the route decorator methods.
        """

        def decorator(view_func: ViewFunc) -> ViewFunc:
            normalized_path = self._normalize_path(path)

            parsed_path = self._parse_path_params(normalized_path)
            wrapped_view = self._wrap_view(view_func, require_ajax=require_ajax)

            route = Route(
                name=view_func.__name__.lower(),
                method=method.upper(),
                path=parsed_path.path,
                view_func=wrapped_view,
                path_params=parsed_path.param_names,
            )

            self._routes.append(route)

            # Return the original view function for decorator chain.
            return view_func

        return decorator

    # Non-AJAX route decorator for full page loads (e.g., index routes)
    # Should not be used normally, but is useful for constructing the router manually.
    _page = partialmethod(_request, "GET", require_ajax=False)

    fragment_get = partialmethod(_request, "GET", require_ajax=True)
    fragment_post = partialmethod(_request, "POST", require_ajax=True)
    fragment_put = partialmethod(_request, "PUT", require_ajax=True)
    fragment_delete = partialmethod(_request, "DELETE", require_ajax=True)
    fragment_patch = partialmethod(_request, "PATCH", require_ajax=True)
