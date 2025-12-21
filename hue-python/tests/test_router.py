from unittest.mock import Mock

import pytest
from htmy import html

from hue.context import HueContext
from hue.exceptions import AJAXRequiredError
from hue.router import HueResponse, PathParseResult
from hue.types.core import Component
from tests.conftest import MockRequest, MockRouter


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/test", "test"),
        ("/test/path", "test/path"),
        ("/", ""),
        ("///test", "test"),
        ("/test/", "test/"),
    ],
)
def test_normalize_path(router: MockRouter, path: str, expected: str):
    assert router._normalize_path(path) == expected


@pytest.mark.parametrize(
    "path, parsed_path, expected",
    [
        (
            "users/{user_id}/posts/{post_id}",
            "users/<user_id>/posts/<post_id>",
            ["user_id", "post_id"],
        ),
        ("users/posts", "users/posts", []),
        ("{id}", "<id>", ["id"]),
    ],
)
def test_parse_path_params(
    router: MockRouter, path: str, parsed_path: str, expected: PathParseResult
):
    result = router._parse_path_params(path)
    assert result.path == parsed_path
    assert result.param_names == expected


def test_fragment_get_registers_route(router: MockRouter):
    @router.fragment_get("users/")
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


def test_fragment_post_registers_route(router: MockRouter):
    @router.fragment_post("users/")
    async def create_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Create user")

    assert len(router.routes) == 1
    route = router.routes[0]
    assert route.method == "POST"


def test_multiple_routes_registered(router: MockRouter):
    @router.fragment_get("users/")
    async def get_users(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Users")

    @router.fragment_get("posts/")
    async def get_posts(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Posts")

    assert len(router.routes) == 2
    assert router.routes[0].path == "users/"
    assert router.routes[1].path == "posts/"


def test_route_with_path_parameters(router: MockRouter):
    @router.fragment_get("users/{user_id}")
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


def test_route_method_uppercased(router: MockRouter):
    @router.fragment_get("test/")
    async def handler(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    assert router.routes[0].method == "GET"


def test_decorator_returns_original_function(router: MockRouter):
    @router.fragment_get("test/")
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
async def test_wrapped_view_validates_ajax_request(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    # Non-AJAX request should raise error
    request = mock_request(headers={})
    with pytest.raises(AJAXRequiredError):
        await wrapped(view_instance, request)


@pytest.mark.asyncio
async def test_wrapped_view_allows_non_ajax_request(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    # Non-AJAX routes (like index/page routes) don't require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=False)

    # Non-AJAX request should work
    request = mock_request(headers={})
    html_result, status_code = await wrapped(view_instance, request)
    assert isinstance(html_result, str)
    assert "Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_accepts_xmlhttprequest(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    # XMLHttpRequest header should work
    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)
    assert isinstance(html_result, str)
    assert "Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_accepts_alpine_ajax(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Test")

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    # Alpine AJAX header should work
    request = mock_request(headers={"X-Alpine-Request": "true"})
    html_result, status_code = await wrapped(view_instance, request)
    assert isinstance(html_result, str)
    assert "Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_handles_sync_function(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Sync Test")

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)
    assert isinstance(html_result, str)
    assert "Sync Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_handles_async_function(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("Async Test")

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)
    assert isinstance(html_result, str)
    assert "Async Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_passes_path_parameters(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        user_id: str,
    ) -> Component:
        return html.div(f"User {user_id}")

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request, user_id="123")
    assert isinstance(html_result, str)
    assert "User 123" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_wrapped_view_passes_context(
    router: MockRouter, mock_request: type[MockRequest]
):
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

    # Fragment routes require AJAX
    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    await wrapped(view_instance, request)

    assert captured_context is not None
    # Check that it's a HueContext instance (generic type checking)
    assert type(captured_context).__name__ == "HueContext"
    assert captured_context.request == request
    assert captured_context.csrf_token == "test-csrf-token"


@pytest.mark.asyncio
async def test_render_converts_component_to_html(
    router: MockRouter, mock_request: type[MockRequest]
):
    component = html.div("Hello World")
    request = mock_request()

    result = await router.render(component, request)

    assert isinstance(result, str)
    assert "Hello World" in result
    assert "<div" in result


@pytest.mark.asyncio
async def test_render_handles_nested_components(
    router: MockRouter, mock_request: type[MockRequest]
):
    component = html.div(html.span("Nested"), html.p("Content"))
    request = mock_request()

    result = await router.render(component, request)

    assert isinstance(result, str)
    assert "Nested" in result
    assert "Content" in result


@pytest.mark.asyncio
async def test_full_route_execution(
    router: MockRouter, mock_request: type[MockRequest]
):
    view_instance = Mock()

    @router.fragment_get("users/{user_id}")
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
    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await route.view_func(
        view_instance, request, user_id="42"
    )

    assert isinstance(html_result, str)
    assert "User 42" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_multiple_http_methods(router: MockRouter):
    @router.fragment_get("users/")
    async def get_users(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("GET")

    @router.fragment_post("users/")
    async def create_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        return html.div("POST")

    @router.fragment_put("users/{id}")
    async def update_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("PUT")

    @router.fragment_delete("users/{id}")
    async def delete_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("DELETE")

    @router.fragment_patch("users/{id}")
    async def patch_user(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        id: str,
    ) -> Component:
        return html.div("PATCH")

    assert len(router.routes) == 5
    methods = {route.method for route in router.routes}
    assert methods == {"GET", "POST", "PUT", "DELETE", "PATCH"}


@pytest.mark.asyncio
async def test_routes_property_returns_copy(router: MockRouter):
    @router.fragment_get("test/")
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


# Tests for HueResponse
@pytest.mark.asyncio
async def test_hue_response_with_target(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test HueResponse wraps component in div with target ID."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return HueResponse(
            component=html.span("Error message"),
            target="error-container",
            status_code=422,
        )

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)

    # Should be wrapped in div with target ID
    assert 'id="error-container"' in html_result
    assert "Error message" in html_result
    assert status_code == 422


@pytest.mark.asyncio
async def test_hue_response_without_target(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test HueResponse without target returns component directly."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return HueResponse(
            component=html.span("Success"),
            status_code=200,
        )

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)

    # Should not be wrapped in extra div
    assert "<span" in html_result
    assert "Success" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_hue_response_default_status_code(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test HueResponse uses 200 as default status code."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return HueResponse(component=html.div("Content"))

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    _, status_code = await wrapped(view_instance, request)

    assert status_code == 200


@pytest.mark.asyncio
async def test_hue_response_401_unauthorized(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test HueResponse for authentication failure."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return HueResponse(
            component=html.div("Invalid credentials"),
            target="login-form",
            status_code=401,
        )

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)

    assert 'id="login-form"' in html_result
    assert "Invalid credentials" in html_result
    assert status_code == 401


@pytest.mark.asyncio
async def test_hue_response_in_route_decorator(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test HueResponse works with route decorators."""
    view_instance = Mock()

    @router.fragment_post("submit/")
    async def submit_form(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return HueResponse(
            component=html.div("Validation failed"),
            target="form-errors",
            status_code=422,
        )

    route = router.routes[0]
    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await route.view_func(view_instance, request)

    assert 'id="form-errors"' in html_result
    assert "Validation failed" in html_result
    assert status_code == 422
