import pytest
from fastapi import Depends
from hue import html
from hue.context import HueContext
from pydantic import BaseModel
from starlette.requests import Request

from hue_fastapi import HueView, Page, Router
from tests.conftest import AJAX_HEADERS, make_app


class Body(BaseModel):
    name: str
    age: int


class MyView(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Home", body=html.div("Home page"))

    @router.fragment_get("comments/")
    async def comments(self, request: Request, context: HueContext[Request]):
        return html.div("Comments")

    @router.fragment_post("comments/")
    async def add_comment(self, request: Request, context: HueContext[Request]):
        return html.div("Comment added")


async def test_index_renders_a_full_page(client_for):
    """
    The index route returns a whole document, not a fragment, and does not
    require an AJAX header.
    """
    async with client_for(make_app(("/myview", MyView))) as client:
        response = await client.get("/myview/")

    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Home page" in response.text


async def test_fragment_returns_a_fragment(client_for):
    """
    Fragment routes render only their own markup.
    """
    async with client_for(make_app(("/myview", MyView))) as client:
        response = await client.get("/myview/comments/", headers=AJAX_HEADERS)

    assert response.status_code == 200
    assert "<!DOCTYPE html>" not in response.text
    assert "Comments" in response.text


async def test_fragment_requires_ajax(client_for):
    """
    A fragment fetched by a plain browser navigation is a bug, not a page.
    """
    async with client_for(make_app(("/myview", MyView))) as client:
        response = await client.get("/myview/comments/")

    assert response.status_code == 400
    assert "AJAX request required" in response.text


async def test_unsupported_method_lists_what_is_allowed(client_for):
    """
    405 advertises every method the path really supports, which Starlette alone
    does not do when several routes share a path.
    """
    async with client_for(make_app(("/myview", MyView))) as client:
        response = await client.put("/myview/comments/", headers=AJAX_HEADERS)

    assert response.status_code == 405
    assert response.headers["allow"] == "GET, HEAD, POST"


async def test_head_on_the_index(client_for):
    """
    GET routes answer HEAD too.
    """
    async with client_for(make_app(("/myview", MyView))) as client:
        response = await client.head("/myview/")

    assert response.status_code == 200


async def test_path_parameters_are_typed(client_for):
    """
    Path parameters reach the handler converted, and a value of the wrong type
    is rejected by FastAPI before the handler runs.
    """

    class PathView(HueView):
        router = Router[Request]()

        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Home", body=html.div("Home"))

        @router.fragment_get("comments/{comment_id}/")
        async def comment(
            self, request: Request, context: HueContext[Request], comment_id: int
        ):
            return html.div(f"Comment {comment_id + 1}")

    async with client_for(make_app(("/p", PathView))) as client:
        ok = await client.get("/p/comments/41/", headers=AJAX_HEADERS)
        bad = await client.get("/p/comments/abc/", headers=AJAX_HEADERS)

    assert ok.status_code == 200
    assert "Comment 42" in ok.text
    assert bad.status_code == 422


async def test_dependencies_and_query_parameters_are_passed_through(client_for):
    """
    hue owns request, context and body. Everything else on the handler is
    FastAPI's, so Depends and query parameters work as they do anywhere else.
    """

    async def get_actor() -> str:
        return "ada"

    class DepView(HueView):
        router = Router[Request]()

        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Home", body=html.div("Home"))

        @router.fragment_get("who/")
        async def who(
            self,
            request: Request,
            context: HueContext[Request],
            actor: str = Depends(get_actor),
            greeting: str = "hi",
        ):
            return html.div(f"{greeting} {actor}")

    async with client_for(make_app(("/d", DepView))) as client:
        response = await client.get(
            "/d/who/", params={"greeting": "hello"}, headers=AJAX_HEADERS
        )

    assert response.status_code == 200
    assert "hello ada" in response.text


@pytest.mark.parametrize(
    "send",
    [
        pytest.param({"data": {"name": "Ada", "age": "36"}}, id="form"),
        pytest.param({"json": {"name": "Ada", "age": 36}}, id="json"),
    ],
)
async def test_body_is_parsed(client_for, send):
    """
    Bodies arrive validated, whether the form posted them or a script sent JSON.
    """

    class BodyView(HueView):
        router = Router[Request]()

        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Home", body=html.div("Home"))

        @router.fragment_post("save/")
        async def save(
            self, request: Request, context: HueContext[Request], body: Body
        ):
            return html.div(f"{body.name} is {body.age}")

    async with client_for(make_app(("/b", BodyView))) as client:
        response = await client.post("/b/save/", headers=AJAX_HEADERS, **send)

    assert response.status_code == 200
    assert "Ada is 36" in response.text


async def test_invalid_body_is_unprocessable(client_for):
    """
    A body that fails validation is a 422, and the handler never runs.
    """

    class BodyView(HueView):
        router = Router[Request]()

        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Home", body=html.div("Home"))

        @router.fragment_post("save/")
        async def save(
            self, request: Request, context: HueContext[Request], body: Body
        ):
            raise AssertionError("the handler should not have been reached")

    async with client_for(make_app(("/b", BodyView))) as client:
        response = await client.post(
            "/b/save/", data={"name": "Ada", "age": "old"}, headers=AJAX_HEADERS
        )

    assert response.status_code == 422


async def test_sync_handlers_are_supported(client_for):
    """
    A synchronous handler runs in a worker thread rather than blocking the loop.
    """

    class SyncView(HueView):
        router = Router[Request]()

        def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Sync", body=html.div("Sync page"))

        @router.fragment_get("bit/")
        def bit(self, request: Request, context: HueContext[Request]):
            return html.div("Sync fragment")

    async with client_for(make_app(("/s", SyncView))) as client:
        page = await client.get("/s/")
        fragment = await client.get("/s/bit/", headers=AJAX_HEADERS)

    assert "Sync page" in page.text
    assert "Sync fragment" in fragment.text


def test_router_is_built_once_and_not_mutated():
    """
    Building the FastAPI router must not add the index to the user's own router,
    which is a class attribute shared with subclasses.
    """
    before = len(MyView.router.routes)
    first = MyView.api_router
    second = MyView.api_router

    assert first is second
    assert len(MyView.router.routes) == before


async def test_subclasses_serve_their_own_index(client_for):
    """
    A subclass overriding index gets its own, rather than the parent's.
    """

    class Parent(HueView):
        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Parent", body=html.div("Parent page"))

    class Child(Parent):
        async def index(self, request: Request, context: HueContext[Request]) -> Page:
            return Page(title="Child", body=html.div("Child page"))

    async with client_for(make_app(("/parent", Parent), ("/child", Child))) as client:
        parent = await client.get("/parent/")
        child = await client.get("/child/")

    assert "Parent page" in parent.text
    assert "Child page" in child.text


def test_a_view_without_an_index_is_rejected():
    """
    The failure shows up when the router is built, not on the first request.
    """

    class NoIndex(HueView):
        router = Router[Request]()

    with pytest.raises(ValueError, match="must define an 'index' method"):
        _ = NoIndex.api_router


async def test_page_reads_configuration_at_render_time(client_for):
    """
    Stylesheet URLs and the title format come from the app being served, so one
    process can serve differently themed apps.
    """
    app = make_app(
        ("/myview", MyView),
        css_url="/static/app.css",
        extra_css_urls=["/extra.css"],
        html_title_factory=lambda title: f"{title} | Test",
    )
    async with client_for(app) as client:
        response = await client.get("/myview/")

    assert "Home | Test</title>" in response.text
    assert 'href="/static/app.css"' in response.text
    assert 'href="/extra.css"' in response.text
