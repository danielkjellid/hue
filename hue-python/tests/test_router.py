from dataclasses import dataclass as stdlib_dataclass
from unittest.mock import Mock

import pytest
from htmy import html
from pydantic import BaseModel

from hue.context import HueContext
from hue.exceptions import AJAXRequiredError, BodyValidationError
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


# Tests for body parsing


@stdlib_dataclass
class LoginCredentialsDataclass:
    email: str
    password: str


class LoginCredentialsPydantic(BaseModel):
    email: str
    password: str


@pytest.mark.asyncio
async def test_body_parsing_with_dataclass(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that request body is automatically parsed into a dataclass."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsDataclass,
    ):
        return html.div(f"Email: {body.email}, Password: {body.password}")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body='{"email": "test@example.com", "password": "secret123"}',
    )
    html_result, status_code = await wrapped(view_instance, request)

    assert "Email: test@example.com" in html_result
    assert "Password: secret123" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_body_parsing_with_pydantic_model(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that request body is automatically parsed into a Pydantic model."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsPydantic,
    ):
        return html.div(f"Email: {body.email}")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body='{"email": "pydantic@example.com", "password": "secret"}',
    )
    html_result, status_code = await wrapped(view_instance, request)

    assert "Email: pydantic@example.com" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_body_parsing_missing_field_raises_error(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that missing required fields raise BodyValidationError."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsDataclass,
    ):
        return html.div("Should not reach here")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body='{"email": "test@example.com"}',  # Missing password
    )

    with pytest.raises(BodyValidationError) as exc_info:
        await wrapped(view_instance, request)

    assert len(exc_info.value.errors) > 0


@pytest.mark.asyncio
async def test_body_parsing_invalid_json_raises_error(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that invalid JSON raises BodyValidationError."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsDataclass,
    ):
        return html.div("Should not reach here")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body="not valid json",
    )

    with pytest.raises(BodyValidationError) as exc_info:
        await wrapped(view_instance, request)

    assert exc_info.value.errors[0]["type"] == "json_invalid"


@pytest.mark.asyncio
async def test_body_parsing_wrong_type_raises_error(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that wrong field types raise BodyValidationError."""
    view_instance = Mock()

    @stdlib_dataclass
    class UserAge:
        age: int

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: UserAge,
    ):
        return html.div("Should not reach here")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body='{"age": "not a number"}',
    )

    with pytest.raises(BodyValidationError):
        await wrapped(view_instance, request)


@pytest.mark.asyncio
async def test_body_parsing_empty_body_uses_defaults(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that empty body uses default values."""
    view_instance = Mock()

    @stdlib_dataclass
    class OptionalBody:
        name: str = "default"

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: OptionalBody,
    ):
        return html.div(f"Name: {body.name}")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body="",
    )
    html_result, status_code = await wrapped(view_instance, request)

    assert "Name: default" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_body_parsing_in_route_decorator(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test body parsing works with route decorators."""
    view_instance = Mock()

    @router.fragment_post("login/")
    async def login(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsPydantic,
    ):
        return html.div(f"Logged in as {body.email}")

    route = router.routes[0]
    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        body='{"email": "user@test.com", "password": "pass"}',
    )
    html_result, status_code = await route.view_func(view_instance, request)

    assert "Logged in as user@test.com" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_handler_without_body_param_works(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that handlers without body parameter still work."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ):
        return html.div("No body needed")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
    html_result, status_code = await wrapped(view_instance, request)

    assert "No body needed" in html_result
    assert status_code == 200


# Tests for form data parsing
@pytest.mark.asyncio
async def test_body_parsing_with_form_data(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that form data is automatically parsed."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsDataclass,
    ):
        return html.div(f"Email: {body.email}, Password: {body.password}")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        content_type="application/x-www-form-urlencoded",
        form_data={"email": "form@example.com", "password": "formpass"},
    )
    html_result, status_code = await wrapped(view_instance, request)

    assert "Email: form@example.com" in html_result
    assert "Password: formpass" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_body_parsing_form_data_with_pydantic(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that form data works with Pydantic models."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsPydantic,
    ):
        return html.div(f"Email: {body.email}")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        content_type="application/x-www-form-urlencoded",
        form_data={"email": "pydantic@form.com", "password": "secret"},
    )
    html_result, status_code = await wrapped(view_instance, request)

    assert "Email: pydantic@form.com" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_body_parsing_form_data_missing_field(
    router: MockRouter, mock_request: type[MockRequest]
):
    """Test that missing fields in form data raise BodyValidationError."""
    view_instance = Mock()

    async def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
        body: LoginCredentialsDataclass,
    ):
        return html.div("Should not reach here")

    wrapped = router._wrap_view(view_func, require_ajax=True)

    request = mock_request(
        headers={"X-Requested-With": "XMLHttpRequest"},
        content_type="application/x-www-form-urlencoded",
        form_data={"email": "test@example.com"},  # Missing password
    )

    with pytest.raises(BodyValidationError):
        await wrapped(view_instance, request)
