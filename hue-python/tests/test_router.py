from dataclasses import dataclass as stdlib_dataclass
from typing import Annotated, NotRequired, TypedDict
from unittest.mock import Mock

import pytest
from htmy import html
from pydantic import BaseModel, ConfigDict, Field, Json, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass

from hue.exceptions import AJAXRequiredError, BodyValidationError, DuplicateRouteError
from hue.router import (
    HueResponse,
    RawResponse,
    Route,
    _sequence_fields,
    check_unique_routes,
)
from hue.types.core import Component
from tests.conftest import MockRequest, MockRouter

AJAX = {"X-Requested-With": "XMLHttpRequest"}
FORM = "application/x-www-form-urlencoded"


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


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get", "post", "put", "delete", "patch"])
async def test_a_fragment_route_registers_its_method_path_and_params(
    router: MockRouter, mock_request: type[MockRequest], method: str
):
    seen = {}

    async def show(view_instance, request, context, user_id: str) -> Component:
        seen["context"] = context
        return html.div(f"User {user_id}")

    decorated = getattr(router, f"fragment_{method}")("users/{user_id}")(show)
    # The class body keeps the method it declared.
    assert decorated is show

    (route,) = router.routes
    assert (route.method, route.path, route.path_params) == (
        method.upper(),
        "users/<user_id>",
        ["user_id"],
    )

    request = mock_request(headers=AJAX)
    html_result, status_code = await route.view_func(Mock(), request, user_id="42")
    assert "User 42" in html_result
    assert status_code == 200
    assert seen["context"].request is request
    assert seen["context"].csrf_token == "test-csrf-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, require_ajax, allowed",
    [
        ({}, True, False),
        ({}, False, True),
        ({"X-Requested-With": "XMLHttpRequest"}, True, True),
        ({"X-Alpine-Request": "true"}, True, True),
    ],
    ids=["plain fragment", "plain page", "xmlhttprequest", "alpine ajax"],
)
async def test_a_fragment_needs_an_ajax_request(
    router: MockRouter,
    mock_request: type[MockRequest],
    headers,
    require_ajax,
    allowed,
):
    async def view_func(view_instance, request, context) -> Component:
        return html.div("Test")

    wrapped = router._wrap_view(view_func, require_ajax=require_ajax)
    if not allowed:
        with pytest.raises(AJAXRequiredError):
            await wrapped(Mock(), mock_request(headers=headers))
        return
    html_result, status_code = await wrapped(Mock(), mock_request(headers=headers))
    assert "Test" in html_result
    assert status_code == 200


@pytest.mark.asyncio
async def test_a_sync_handler_runs_through_run_sync(
    router: MockRouter, mock_request: type[MockRequest]
):
    # That is where an integration keeps blocking work off the event loop,
    # so it has one method to override rather than two.
    ran: list[object] = []
    original = router._run_sync

    async def spy(func, /, *args):
        ran.append(func)
        return await original(func, *args)

    router._run_sync = spy  # type: ignore[method-assign]

    def view_func(view_instance, request, context) -> Component:
        return html.div("Sync")

    wrapped = router._wrap_view(view_func, require_ajax=False)
    html_result, _ = await wrapped(Mock(), mock_request())
    assert "Sync" in html_result
    assert len(ran) == 1


@pytest.mark.asyncio
async def test_an_async_handler_behind_a_sync_decorator_is_awaited(
    router: MockRouter, mock_request: type[MockRequest]
):
    # It looks sync until it is called, and then hands back a coroutine.
    async def view_func(view_instance, request, context) -> Component:
        return html.div("Wrapped")

    def plain(*args):
        return view_func(*args)

    wrapped = router._wrap_view(plain, require_ajax=False)
    html_result, _ = await wrapped(Mock(), mock_request())
    assert "Wrapped" in html_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response, wrapper, status",
    [
        (
            HueResponse(html.span("Failed"), target="form-errors", status_code=422),
            'id="form-errors"',
            422,
        ),
        (HueResponse(html.span("Failed")), None, 200),
    ],
    ids=["with target", "defaults"],
)
async def test_a_hue_response_sets_the_status_and_wraps_its_target(
    router: MockRouter, mock_request: type[MockRequest], response, wrapper, status
):
    async def view_func(view_instance, request, context):
        return response

    wrapped = router._wrap_view(view_func, require_ajax=True)
    html_result, status_code = await wrapped(Mock(), mock_request(headers=AJAX))

    assert "Failed" in html_result
    assert status_code == status
    if wrapper:
        assert wrapper in html_result
    else:
        assert html_result.lstrip().startswith("<span")


@stdlib_dataclass
class LoginCredentialsDataclass:
    email: str
    password: str


class LoginCredentialsPydantic(BaseModel):
    email: str
    password: str


@stdlib_dataclass
class OptionalBody:
    email: str = "default"


@stdlib_dataclass
class UserAge:
    age: int


_LOGIN = {"email": "ada@example.com", "password": "secret"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body_type, request_kwargs, expected",
    [
        (
            LoginCredentialsDataclass,
            {"body": '{"email": "ada@example.com", "password": "secret"}'},
            "ada@example.com",
        ),
        (
            LoginCredentialsPydantic,
            {"body": '{"email": "ada@example.com", "password": "secret"}'},
            "ada@example.com",
        ),
        (
            LoginCredentialsDataclass,
            {"content_type": FORM, "form_data": _LOGIN},
            "ada@example.com",
        ),
        (
            LoginCredentialsPydantic,
            {"content_type": FORM, "form_data": _LOGIN},
            "ada@example.com",
        ),
        (OptionalBody, {"body": ""}, "default"),
    ],
    ids=["json dataclass", "json model", "form dataclass", "form model", "empty"],
)
async def test_the_body_is_parsed_into_its_annotation(
    router: MockRouter,
    mock_request: type[MockRequest],
    body_type,
    request_kwargs,
    expected,
):
    async def view_func(view_instance, request, context, body):
        return html.div(f"Email: {body.email}")

    view_func.__annotations__["body"] = body_type
    wrapped = router._wrap_view(view_func, require_ajax=True)
    request = mock_request(headers=AJAX, **request_kwargs)
    html_result, status_code = await wrapped(Mock(), request)

    assert f"Email: {expected}" in html_result
    assert status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body_type, request_kwargs, error_type",
    [
        (LoginCredentialsDataclass, {"body": '{"email": "a@b.c"}'}, "missing"),
        (LoginCredentialsDataclass, {"body": "not valid json"}, "json_invalid"),
        # A body that does not decode is as invalid as one that does not parse.
        (LoginCredentialsDataclass, {"body": b'{"email": "\xff"}'}, "json_invalid"),
        (UserAge, {"body": '{"age": "not a number"}'}, "int_parsing"),
        (
            LoginCredentialsDataclass,
            {"content_type": FORM, "form_data": {"email": "a@b.c"}},
            "missing",
        ),
    ],
    ids=["missing field", "invalid json", "not utf-8", "wrong type", "form missing"],
)
async def test_a_body_that_does_not_validate_raises(
    router: MockRouter,
    mock_request: type[MockRequest],
    body_type,
    request_kwargs,
    error_type,
):
    async def view_func(view_instance, request, context, body):
        return html.div("Should not reach here")

    view_func.__annotations__["body"] = body_type
    wrapped = router._wrap_view(view_func, require_ajax=True)

    with pytest.raises(BodyValidationError) as exc_info:
        await wrapped(Mock(), mock_request(headers=AJAX, **request_kwargs))

    assert exc_info.value.errors[0]["type"] == error_type


@stdlib_dataclass
class Tagged:
    tags: list[str]
    title: str


@pytest.mark.asyncio
async def test_form_data_repeated_name_fills_a_list_field_and_keeps_the_last_otherwise(
    router: MockRouter, mock_request: type[MockRequest]
):
    """
    A list field gets every value posted under its name, as a multiple Combobox
    or a set of checkboxes posts them; any other field gets the last one.
    """

    async def view_func(view_instance, request, context, body: Tagged):
        return html.div(f"{','.join(body.tags)}|{body.title}")

    wrapped = router._wrap_view(view_func, require_ajax=True)
    request = mock_request(
        headers=AJAX,
        content_type=FORM,
        form_data={"tags": ["a", "b"], "title": ["first", "second"]},
    )
    html_result, _ = await wrapped(Mock(), request)

    assert "a,b|second" in html_result


@stdlib_dataclass
class AliasedTags:
    tags: Annotated[list[str], Field(alias="tag")]


class AliasedTagsTypedDict(TypedDict):
    tags: Annotated[list[str], Field(alias="tag")]


@pytest.mark.asyncio
@pytest.mark.parametrize("body_type", [AliasedTags, AliasedTagsTypedDict])
async def test_form_data_repeated_name_fills_an_aliased_list_field(
    router: MockRouter, mock_request: type[MockRequest], body_type
):
    """
    Pydantic reads an alias out of Annotated on a stdlib dataclass or TypedDict
    too, so the list is posted under the alias rather than the attribute name.
    """

    async def view_func(view_instance, request, context, body):
        tags = body["tags"] if isinstance(body, dict) else body.tags
        return html.div(",".join(tags))

    view_func.__annotations__["body"] = body_type
    wrapped = router._wrap_view(view_func, require_ajax=True)
    request = mock_request(
        headers=AJAX, content_type=FORM, form_data={"tag": ["a", "b"]}
    )
    html_result, _ = await wrapped(Mock(), request)

    assert "a,b" in html_result


class TaggedTypedDict(TypedDict):
    tags: NotRequired[Annotated[tuple[str, ...], "doc"]]
    ids: Json[list[int]]
    title: str


class TaggedModel(BaseModel):
    tags: set[str] | None = Field(default=None, alias="tag")
    ids: Json[list[int]]
    title: str


class Opaque:
    pass


type Labels = list[str]


class Node(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    children: list["Node"] = []
    parent: "Node | None" = None
    labels: Labels = []
    handle: Opaque | None = None


@pydantic_dataclass
class Owned:
    tags: list[str] | None = None
    owner: Node | None = None


@pytest.mark.parametrize(
    "body_type, expected",
    [
        (Tagged, {"tags"}),
        (TaggedTypedDict, {"tags"}),
        (TaggedModel, {"tags", "tag"}),
        (AliasedTags, {"tags", "tag"}),
        (AliasedTagsTypedDict, {"tags", "tag"}),
        # A nested model's own lists are not the form's, a recursive model
        # still answers, and a field with no JSON form is simply not a list.
        (Owned, {"tags"}),
        (Node, {"children", "labels"}),
        (int, set()),
    ],
)
def test_sequence_fields_are_read_from_the_body_type(body_type, expected):
    # A Json field is one string on the wire, which is how ajax() sends a list.
    assert _sequence_fields(TypeAdapter(body_type)) == expected


@pytest.mark.asyncio
async def test_framework_response_is_passed_through(router, mock_request):
    class FakeRedirect:
        status_code = 302

    async def view(self, request, context):
        return FakeRedirect()

    wrapped = router._wrap_view(view, require_ajax=False)
    result = await wrapped(object(), mock_request())

    assert isinstance(result, RawResponse)
    assert isinstance(result.response, FakeRedirect)


def test_unannotated_body_parameter_is_rejected_at_registration(router):
    with pytest.raises(TypeError, match="must be annotated"):

        @router.fragment_post("save/")
        async def view(self, request, context, body):
            return html.div()


def _route(method: str, path: str, name: str) -> Route:
    return Route(method=method, path=path, name=name, view_func=Mock())


def test_two_routes_on_one_path_and_method_are_refused():
    # Dispatch is by path and then method, so the second would replace the
    # first without a word.
    with pytest.raises(DuplicateRouteError, match="index and listing"):
        check_unique_routes([_route("GET", "", "index"), _route("GET", "", "listing")])


def test_one_path_takes_one_route_per_method():
    check_unique_routes([_route("GET", "x/", "show"), _route("POST", "x/", "save")])
