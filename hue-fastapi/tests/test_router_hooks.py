"""
The request hooks hue's core reads through, which a table, a filter and a
toast all depend on beyond what a single fragment exercises.
"""

from typing import Annotated

from fastapi import File, HTTPException, UploadFile
from hue import html
from hue.context import HueContext
from hue.formats import Formats
from hue.router import PAGE_ROUTE
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.toast import SESSION_KEY, toast
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from hue_fastapi import HueFragmentsView, HueRequestMiddleware, HueView, Page, Router
from tests._annotated_for_typing_only import TypingOnly
from tests.conftest import AJAX_HEADERS, make_app


class Echo(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Echo", body=html.div("Echo"))

    @router.fragment_get("query/")
    async def query(self, request: Request, context: HueContext[Request]):
        values = self.router._get_query_values(request)
        return html.div(repr(sorted(values.items())))

    @router.fragment_post("form/")
    async def form(self, request: Request, context: HueContext[Request]):
        values = self.router._get_form_values(request)
        return html.div(repr(sorted(values.items())))

    @router.fragment_get("links/{item}/")
    async def links(self, request: Request, context: HueContext[Request], item: int):
        page = self.router._url_for(request, PAGE_ROUTE)
        other = self.router._url_for(request, "links", item=item + 1)
        return html.div(f"{page} {other}")


async def test_query_keeps_every_value_under_a_name(client_for):
    async with client_for(make_app(("/echo", Echo))) as client:
        response = await client.get(
            "/echo/query/?status=paid&status=draft&q=x", headers=AJAX_HEADERS
        )

    assert "('status', ['paid', 'draft'])" in response.text
    assert "('q', ['x'])" in response.text


async def test_a_form_keeps_every_value_without_a_body_parameter(client_for):
    """
    A table's actions post their ids to a handler that declares no body, and
    read them through the router.
    """
    async with client_for(make_app(("/echo", Echo))) as client:
        response = await client.post(
            "/echo/form/",
            data={"selected": ["1", "2"]},
            headers=AJAX_HEADERS,
        )

    assert "('selected', ['1', '2'])" in response.text


async def test_url_for_follows_the_mount_the_request_came_through(client_for):
    """
    The same view mounted twice links back into the mount the reader is in.
    """
    app = make_app(("/a", Echo), ("/b", Echo))
    async with client_for(app) as client:
        a = await client.get("/a/links/1/", headers=AJAX_HEADERS)
        b = await client.get("/b/links/1/", headers=AJAX_HEADERS)

    assert "/a/ /a/links/2/" in a.text
    assert "/b/ /b/links/2/" in b.text


def test_starlette_errors_pass_through():
    assert Router()._passes_through(HTTPException(status_code=404))
    assert not Router()._passes_through(ValueError())


class Shortcuts(ShortcutRegistry):
    home = Shortcut("Home", "g", "h", href="/")


async def test_formats_and_shortcuts_reach_the_context(client_for):
    seen = {}

    class Probe(HueFragmentsView):
        router = Router[Request]()

        @router.fragment_get("probe/")
        async def probe(self, request: Request, context: HueContext[Request]):
            seen["formats"] = context.formats
            seen["shortcuts"] = context.shortcuts
            return html.div("ok")

    formats = Formats(date="%d.%m.%Y")
    app = make_app(("/p", Probe), formats=formats, shortcuts=Shortcuts)
    async with client_for(app) as client:
        await client.get("/p/probe/", headers=AJAX_HEADERS)

    assert seen == {"formats": formats, "shortcuts": Shortcuts}


class Redirects(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Home", body=html.div("Home"))

    @router.fragment_post("save/")
    async def save(self, request: Request, context: HueContext[Request]):
        toast.success("Saved")
        return RedirectResponse("/r/", status_code=303)


def _with_sessions(app):
    app.add_middleware(HueRequestMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test")
    return app


async def test_a_toast_survives_a_redirect(client_for):
    app = _with_sessions(make_app(("/r", Redirects)))
    async with client_for(app) as client:
        await client.post("/r/save/", headers=AJAX_HEADERS)
        page = await client.get("/r/")
        again = await client.get("/r/")

    assert "Saved" in page.text
    # Shown once: the session lets go of it.
    assert "Saved" not in again.text


async def test_the_middleware_writes_nothing_when_nothing_was_raised(client_for):
    seen = {}

    app = _with_sessions(make_app(("/r", Redirects)))

    @app.get("/peek/")
    async def peek(request: Request) -> dict[str, bool]:
        seen["stored"] = SESSION_KEY in request.session
        return {}

    async with client_for(app) as client:
        await client.get("/r/")
        await client.get("/peek/")

    assert seen == {"stored": False}


class Declared(HueFragmentsView):
    router = Router[Request]()

    @router.fragment_get("items/{item}/")
    async def get_item(self, request: Request, context: HueContext[Request], item: str):
        return html.div("get-item")

    @router.fragment_post("items/new/")
    async def post_new(self, request: Request, context: HueContext[Request]):
        return html.div("post-new")

    @router.fragment_post("items/{item}/")
    async def post_item(
        self, request: Request, context: HueContext[Request], item: str
    ):
        return html.div("post-item")


class Shadowing(HueFragmentsView):
    router = Router[Request]()

    @router.fragment_get("items/{item}/")
    async def item(self, request: Request, context: HueContext[Request], item: str):
        return html.div(f"item {item}")

    @router.fragment_post("items/new/")
    async def new(self, request: Request, context: HueContext[Request]):
        return html.div("created")


async def test_routes_are_tried_in_the_order_they_were_declared(client_for):
    async with client_for(make_app(("/v", Declared))) as client:
        response = await client.post("/v/items/new/", headers=AJAX_HEADERS)

    assert "post-new" in response.text


async def test_a_405_for_one_path_does_not_answer_for_another(client_for):
    """
    The catch-all that lists a path's methods must not match a literal path
    registered after a parameterised one.
    """
    async with client_for(make_app(("/v", Shadowing))) as client:
        created = await client.post("/v/items/new/", headers=AJAX_HEADERS)
        refused = await client.post("/v/items/7/", headers=AJAX_HEADERS)

    assert created.status_code == 200
    assert refused.status_code == 405
    assert refused.headers["allow"] == "GET, HEAD"


async def test_types_imported_for_the_type_checker_alone_are_fine(client_for):
    async with client_for(make_app(("/t", TypingOnly))) as client:
        response = await client.get("/t/items/1/", headers=AJAX_HEADERS)

    # The int annotation still reaches FastAPI, which converts the parameter.
    assert "item 2" in response.text


class Files(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Files", body=html.div("Files"))

    @router.fragment_get("files/{rest:path}")
    async def file(self, request: Request, context: HueContext[Request], rest: str):
        page = self.router._url_for(request, PAGE_ROUTE)
        other = self.router._url_for(request, "file", rest="a b/50%.txt")
        return html.div(f"{page} {other}")


async def test_url_for_handles_a_path_converter_and_quotes_values(client_for):
    async with client_for(make_app(("/shop", Files))) as client:
        response = await client.get("/shop/files/x/y.txt", headers=AJAX_HEADERS)

    assert "/shop/ /shop/files/a%20b/50%25.txt" in response.text


async def test_a_prefix_that_repeats_the_template_is_kept_whole(client_for):
    async with client_for(make_app(("/files", Files))) as client:
        response = await client.get("/files/files/a/b", headers=AJAX_HEADERS)

    assert "/files/ /files/files/a%20b/50%25.txt" in response.text


async def test_a_value_that_repeats_the_template_is_not_taken_for_a_prefix(
    client_for,
):
    async with client_for(make_app(("", Files))) as client:
        response = await client.get("/files/files/a/b", headers=AJAX_HEADERS)

    assert "/ /files/a%20b/50%25.txt" in response.text


class Upload(HueFragmentsView):
    router = Router[Request]()

    @router.fragment_post("upload/")
    async def upload(
        self,
        request: Request,
        context: HueContext[Request],
        file: Annotated[UploadFile, File()],
    ):
        return html.div(f"{file.filename}: {len(await file.read())} bytes")


async def test_an_upload_stays_readable_in_its_handler(client_for):
    """
    Reading the form for hue's hooks leaves FastAPI's own copy of an upload
    readable, since both come from the one parsed form.
    """
    async with client_for(make_app(("/u", Upload))) as client:
        response = await client.post(
            "/u/upload/",
            files={"file": ("notes.txt", b"hello")},
            headers=AJAX_HEADERS,
        )

    assert "notes.txt: 5 bytes" in response.text
