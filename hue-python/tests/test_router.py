import re
from unittest.mock import Mock

import pytest
from htmy import html

from src.hue.context import HueContext, HueContextArgs
from src.hue.router import PathParseResult, Router
from src.hue.types.core import Component


# Mock request object
class MockRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


# Test router implementation
class MockRouter(Router[MockRequest]):
    """Concrete router implementation for testing."""

    def _parse_path_params(self, path: str) -> PathParseResult:
        """Simple path parser that extracts {param} patterns."""

        # Find all {param} patterns
        param_pattern = r"\{(\w+)\}"
        matches = re.findall(param_pattern, path)
        param_names = list(matches)

        # Convert to simple path format (remove braces for testing)
        final_path = re.sub(r"\{(\w+)\}", r"<\1>", path)

        return PathParseResult(path=final_path, param_names=param_names)

    def _get_context_args(self, request: MockRequest) -> HueContextArgs[MockRequest]:
        """Return mock context args."""
        return HueContextArgs[MockRequest](
            request=request,
            csrf_token="test-csrf-token",
        )


def test_normalize_path_strips_leading_slash():
    router = MockRouter()
    assert router._normalize_path("/test") == "test"
    assert router._normalize_path("/test/path") == "test/path"


def test_normalize_path_handles_root_path():
    router = MockRouter()
    assert router._normalize_path("/") == ""


def test_normalize_path_handles_multiple_leading_slashes():
    router = MockRouter()
    assert router._normalize_path("///test") == "test"


def test_normalize_path_preserves_trailing_slash():
    router = MockRouter()
    assert router._normalize_path("/test/") == "test/"


def test_parse_path_params_extracts_parameters():
    router = MockRouter()
    result = router._parse_path_params("users/{user_id}/posts/{post_id}")
    assert result.path == "users/<user_id>/posts/<post_id>"
    assert result.param_names == ["user_id", "post_id"]


def test_parse_path_params_handles_no_parameters():
    router = MockRouter()
    result = router._parse_path_params("users/posts")
    assert result.path == "users/posts"
    assert result.param_names == []


def test_parse_path_params_handles_single_parameter():
    router = MockRouter()
    result = router._parse_path_params("{id}")
    assert result.path == "<id>"
    assert result.param_names == ["id"]


def test_ajax_get_registers_route():
    router = MockRouter()

    @router.ajax_get("users/")
    async def get_users(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Users")

    assert len(router.routes) == 1
    route = router.routes[0]
    assert route.method == "GET"
    assert route.path == "users/"
    assert route.path_params == []


def test_ajax_post_registers_route():
    router = MockRouter()

    @router.ajax_post("users/")
    async def create_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Create user")

    assert len(router.routes) == 1
    route = router.routes[0]
    assert route.method == "POST"


def test_multiple_routes_registered():
    router = MockRouter()

    @router.ajax_get("users/")
    async def get_users(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Users")

    @router.ajax_get("posts/")
    async def get_posts(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Posts")

    EXPECTED_ROUTES = 2
    assert len(router.routes) == EXPECTED_ROUTES
    assert router.routes[0].path == "users/"
    assert router.routes[1].path == "posts/"


def test_route_with_path_parameters():
    router = MockRouter()

    @router.ajax_get("users/{user_id}")
    async def get_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        user_id: str,
    ) -> Component:
        return html.div(f"User {user_id}")

    assert len(router.routes) == 1
    route = router.routes[0]
    assert route.path == "users/<user_id>"
    assert route.path_params == ["user_id"]


def test_route_method_uppercased():
    router = MockRouter()

    @router.ajax_get("test/")
    async def handler(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    assert router.routes[0].method == "GET"


def test_decorator_returns_original_function():
    router = MockRouter()

    @router.ajax_get("test/")
    async def handler(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    # Decorator should return the original function
    assert callable(handler)
    assert handler.__name__ == "handler"


@pytest.mark.asyncio
async def test_wrapped_view_validates_ajax_request():
    router = MockRouter()
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    wrapped = router._wrap_view(view_func)

    # Non-AJAX request should raise error
    request = MockRequest(headers={})
    with pytest.raises(AssertionError, match="Not an AJAX request"):
        await wrapped(view_instance, request)


@pytest.mark.asyncio
async def test_wrapped_view_accepts_xmlhttprequest():
    router = MockRouter()
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    wrapped = router._wrap_view(view_func)

    # XMLHttpRequest header should work
    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    result = await wrapped(view_instance, request)
    assert isinstance(result, str)
    assert "Test" in result


@pytest.mark.asyncio
async def test_wrapped_view_accepts_alpine_ajax():
    router = MockRouter()
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    wrapped = router._wrap_view(view_func)

    # Alpine AJAX header should work
    request = MockRequest(headers={"X-Alpine-Request": "true"})
    result = await wrapped(view_instance, request)
    assert isinstance(result, str)
    assert "Test" in result


@pytest.mark.asyncio
async def test_wrapped_view_handles_sync_function():
    router = MockRouter()
    view_instance = Mock()

    def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Sync Test")

    wrapped = router._wrap_view(view_func)

    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    result = await wrapped(view_instance, request)
    assert isinstance(result, str)
    assert "Sync Test" in result


@pytest.mark.asyncio
async def test_wrapped_view_handles_async_function():
    router = MockRouter()
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Async Test")

    wrapped = router._wrap_view(view_func)

    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    result = await wrapped(view_instance, request)
    assert isinstance(result, str)
    assert "Async Test" in result


@pytest.mark.asyncio
async def test_wrapped_view_passes_path_parameters():
    router = MockRouter()
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        user_id: str,
    ) -> Component:
        return html.div(f"User {user_id}")

    wrapped = router._wrap_view(view_func)

    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    result = await wrapped(view_instance, request, user_id="123")
    assert isinstance(result, str)
    assert "User 123" in result


@pytest.mark.asyncio
async def test_wrapped_view_passes_context():
    router = MockRouter()
    view_instance = Mock()
    captured_context = None

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        nonlocal captured_context
        captured_context = context
        return html.div("Test")

    wrapped = router._wrap_view(view_func)

    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    await wrapped(view_instance, request)

    assert captured_context is not None
    # Check that it's a HueContext instance (generic type checking)
    assert type(captured_context).__name__ == "HueContext"
    assert captured_context.request == request
    assert captured_context.csrf_token == "test-csrf-token"


@pytest.mark.asyncio
async def test_render_converts_component_to_html():
    router = MockRouter()
    component = html.div("Hello World")
    request = MockRequest()

    result = await router._render(component, request)

    assert isinstance(result, str)
    assert "Hello World" in result
    assert "<div" in result


@pytest.mark.asyncio
async def test_render_handles_nested_components():
    router = MockRouter()
    component = html.div(html.span("Nested"), html.p("Content"))
    request = MockRequest()

    result = await router._render(component, request)

    assert isinstance(result, str)
    assert "Nested" in result
    assert "Content" in result


@pytest.mark.asyncio
async def test_full_route_execution():
    router = MockRouter()
    view_instance = Mock()

    @router.ajax_get("users/{user_id}")
    async def get_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        user_id: str,
    ) -> Component:
        return html.div(f"User {user_id}")

    # Get the wrapped route
    route = router.routes[0]
    assert route.method == "GET"
    assert route.path == "users/<user_id>"
    assert route.path_params == ["user_id"]

    # Execute the wrapped view
    request = MockRequest(headers={"X-Requested-With": "XMLHttpRequest"})
    result = await route.view_func(view_instance, request, user_id="42")

    assert isinstance(result, str)
    assert "User 42" in result


@pytest.mark.asyncio
async def test_multiple_http_methods():
    router = MockRouter()

    @router.ajax_get("users/")
    async def get_users(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("GET")

    @router.ajax_post("users/")
    async def create_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("POST")

    @router.ajax_put("users/{id}")
    async def update_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("PUT")

    @router.ajax_delete("users/{id}")
    async def delete_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("DELETE")

    @router.ajax_patch("users/{id}")
    async def patch_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("PATCH")

    EXPECTED_ROUTES = 5
    assert len(router.routes) == EXPECTED_ROUTES
    methods = {route.method for route in router.routes}
    assert methods == {"GET", "POST", "PUT", "DELETE", "PATCH"}


@pytest.mark.asyncio
async def test_routes_property_returns_copy():
    router = MockRouter()

    @router.ajax_get("test/")
    async def handler(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    routes1 = router.routes
    routes2 = router.routes

    # Should be different objects (copies)
    assert routes1 is not routes2
    # But should have same content
    assert len(routes1) == len(routes2) == 1
