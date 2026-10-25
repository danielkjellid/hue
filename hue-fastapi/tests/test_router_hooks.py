"""
The request hooks hue's core reads through, which a table, a filter and a
toast all depend on beyond what a single fragment exercises.
"""

from fastapi import HTTPException
from hue import html
from hue.context import HueContext
from hue.formats import Formats
from hue.router import PAGE_ROUTE
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.toast import toast
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from hue_fastapi import HueFragmentsView, HueRequestMiddleware, HueView, Page, Router
from hue_fastapi.middleware import SESSION_KEY
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


async def test_a_fragment_carries_its_toasts(client_for):
    class Saves(HueFragmentsView):
        router = Router[Request]()

        @router.fragment_post("save/")
        async def save(self, request: Request, context: HueContext[Request]):
            toast.success("Saved")
            return html.div("ok")

    async with client_for(make_app(("/s", Saves))) as client:
        response = await client.post("/s/save/", headers=AJAX_HEADERS)

    assert "Saved" in response.text


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
