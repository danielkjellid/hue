from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Views and Router"),
        pr.lead(
            "hue-fastapi connects Hue's AJAX-first router to FastAPI. A "
            "`HueView` serves a full page and the fragments that update it. A "
            "`HueFragmentsView` serves fragments only. Each one hands FastAPI "
            "an `APIRouter` to include."
        ),
        pr.p(
            "The ",
            pr.link("Django views", "/django/views/"),
            " guide covers the same classes in hue-django.",
        ),
        pr.h2("HueView"),
        pr.p(
            "A `HueView` defines an `index` method that returns a `Page` for "
            "the first, ordinary GET. Its fragment routes are declared on a "
            "`Router` and only answer AJAX requests. `index` can be sync or "
            "async, and it is not AJAX-only."
        ),
        pr.code(
            "from fastapi import FastAPI\n"
            "from hue import html\n"
            "from hue.context import HueContext\n"
            "from hue_fastapi import HueView, Page, Router\n"
            "from starlette.requests import Request\n\n"
            "class CommentsView(HueView):\n"
            "    router = Router[Request]()\n\n"
            "    async def index(\n"
            "        self, request: Request, context: HueContext[Request]\n"
            "    ) -> Page:\n"
            '        return Page(title="Comments", body=html.div("All comments"))\n\n'
            '    @router.fragment_get("comments/{comment_id:int}/")\n'
            "    async def comment(\n"
            "        self,\n"
            "        request: Request,\n"
            "        context: HueContext[Request],\n"
            "        comment_id: int,\n"
            "    ) -> html.div:\n"
            '        return html.div(f"Comment {comment_id}")\n\n'
            "app = FastAPI()\n"
            'app.include_router(CommentsView.api_router, prefix="/comments")'
        ),
        pr.p(
            "A `HueView` with no `router` attribute serves its `index` alone. "
            "One with no `index` raises a `ValueError` when its `api_router` "
            "is first read."
        ),
        pr.h2("HueFragmentsView"),
        pr.p(
            "A `HueFragmentsView` groups fragment routes that have no page of "
            "their own. It has no `index`, every route is AJAX-only, and it "
            "must declare a `router`. Without one, reading `api_router` raises "
            "a `ValueError`."
        ),
        pr.code(
            "from hue import html\n"
            "from hue.context import HueContext\n"
            "from hue_fastapi import HueFragmentsView, Router\n"
            "from starlette.requests import Request\n\n"
            "class CommentFragments(HueFragmentsView):\n"
            "    router = Router[Request]()\n\n"
            '    @router.fragment_get("latest/")\n'
            "    async def latest(\n"
            "        self, request: Request, context: HueContext[Request]\n"
            "    ) -> html.div:\n"
            '        return html.div("Latest comments")\n\n'
            'app.include_router(CommentFragments.api_router, prefix="/fragments")'
        ),
        pr.h2("Including a view with api_router"),
        pr.p(
            "`api_router` is a class property that returns a FastAPI "
            "`APIRouter` holding every route of the view. Pass it to "
            "`app.include_router` with the prefix the view lives under. Hue "
            "builds it once per class, the first time it is read, and never "
            "changes the `router` you declared, so a subclass of a `HueView` "
            "gets its own `index`. The `app_name` class property is the "
            "lowercased class name."
        ),
        pr.p(
            "The routes are left out of the OpenAPI schema. The app also needs "
            "`configure_hue` before a view renders. ",
            pr.link("Setup", "/fastapi/setup/"),
            " covers it.",
        ),
        pr.h2("Router and HTTP methods"),
        pr.p(
            "`hue_fastapi.Router` is Hue's router with the FastAPI parts "
            "added. It reads Starlette's path syntax, takes the CSRF token, "
            "date formats and shortcuts from the app's configuration, and "
            "reads the request body before the handler runs."
        ),
        pr.bullets(
            [
                "There is a decorator for every common verb: `fragment_get`, "
                "`fragment_post`, `fragment_put`, `fragment_patch` and "
                "`fragment_delete`. Several of them can share one path.",
                "A GET route answers HEAD as well.",
                "A method the path does not support gets a 405 whose `Allow` "
                "header lists every method the path does support.",
                "Routes are tried in the order they are declared, so declare "
                '`"items/new/"` before `"items/{item}/"` when both take the '
                "same method.",
                "Each route is named after its handler, lowercased. Pass "
                "`name=` to the decorator to choose another.",
            ]
        ),
        pr.h2("Path parameters"),
        pr.p(
            "Paths use Starlette's syntax, `{name}` or `{name:converter}`, "
            "and each captured value reaches the handler as a keyword "
            "argument. A converter decides whether the path matches at all, "
            "so `/comments/abc/` against `{comment_id:int}` is a 404. A plain "
            "`{comment_id}` with a `comment_id: int` annotation matches "
            "anything, and FastAPI answers a value that is not a number with "
            "a 422 before the handler runs."
        ),
        pr.code(
            '@router.fragment_get("files/{rest:path}")\n'
            "async def file(\n"
            "    self, request: Request, context: HueContext[Request], rest: str\n"
            ") -> html.div:\n"
            "    return html.div(rest)"
        ),
        pr.h2("Handler signatures"),
        pr.p(
            "A hue-fastapi handler takes the view, the request and the "
            "context first, whatever it calls them. Hue fills those three "
            "and `body`. Every other parameter is given to FastAPI, so path "
            "parameters, query parameters, `Depends` and uploads resolve the "
            "way they do on any FastAPI endpoint. The same holds for "
            "`index`."
        ),
        pr.code(
            "from fastapi import Depends\n\n"
            "async def current_user() -> str:\n"
            '    return "ada"\n\n'
            "class SearchView(HueView):\n"
            "    router = Router[Request]()\n\n"
            "    async def index(\n"
            "        self, request: Request, context: HueContext[Request]\n"
            "    ) -> Page:\n"
            '        return Page(title="Search", body=html.div("Search"))\n\n'
            '    @router.fragment_get("results/")\n'
            "    async def results(\n"
            "        self,\n"
            "        request: Request,\n"
            "        context: HueContext[Request],\n"
            '        q: str = "",\n'
            "        user: str = Depends(current_user),\n"
            "    ) -> html.div:\n"
            '        return html.div(f"{user} searched for {q}")'
        ),
        pr.bullets(
            [
                "FastAPI reads each parameter's annotation, so a type it "
                "needs has to be imported at runtime. A missing import raises "
                "a `TypeError` that names the parameter when `api_router` is "
                "built. On a handler with no `body`, the `Request` and "
                "`HueContext` annotations are never evaluated, so they can "
                "be imported under `TYPE_CHECKING`. A handler with a `body` "
                "resolves all of its annotations, and raises a `TypeError` "
                "when the class is defined if one of them is not importable.",
                "A sync handler runs in a thread pool, so it does not block "
                "the event loop.",
                "A handler can return a Starlette response, such as a "
                "`RedirectResponse`. It is sent unchanged, apart from the "
                "CSRF cookie when the request minted a token.",
                "An `HTTPException` raised in a handler is answered by "
                "FastAPI as usual.",
                "To send a status code other than 200 with a fragment, "
                "return a `HueResponse` from `hue_fastapi.router`.",
            ]
        ),
        pr.h2("Request bodies"),
        pr.p(
            "Declare a parameter named `body` with a Pydantic model as its "
            "type, and the router validates the request body into it. A JSON "
            "body is decoded as JSON. Anything else is read as form fields, "
            "where a list field keeps every value posted under its name. "
            "`body` is not passed to FastAPI, so the endpoint FastAPI builds "
            "does not declare the model."
        ),
        pr.code(
            "from pydantic import BaseModel\n\n"
            "class Archive(BaseModel):\n"
            "    reason: str\n\n"
            '@router.fragment_post("comments/{comment_id:int}/archive/")\n'
            "async def archive(\n"
            "    self,\n"
            "    request: Request,\n"
            "    context: HueContext[Request],\n"
            "    comment_id: int,\n"
            "    body: Archive,\n"
            ") -> html.div:\n"
            '    return html.div(f"Archived {comment_id}: {body.reason}")'
        ),
        pr.p(
            "A body that fails validation, or is not valid JSON or UTF-8, "
            "never reaches the handler. The view answers with "
            "`handle_body_validation_error(request, exc)`, which returns a "
            "plain-text 422 by default. Override it on the view to render "
            "the errors back into the form. `exc.errors` holds Pydantic's "
            "details. To send a body from the page, see ",
            pr.link("Actions and requests", "/actions/"),
            ".",
        ),
        pr.h2("AJAX-only fragment routes"),
        pr.p(
            "Every fragment route requires an AJAX request. The router "
            "accepts one with an `X-Requested-With: XMLHttpRequest` or an "
            "`X-Alpine-Request: true` header, which Alpine AJAX sends. "
            "Without either, the response is a 400 with the text "
            "`AJAX request required`. Only the `index` of a `HueView` answers "
            "a plain browser request."
        ),
        pr.h2("Mounting a view twice"),
        pr.p(
            "The same view can be included under more than one prefix. When "
            "Hue builds a link to one of the view's own routes, as a ",
            pr.link("data table", "/data-tables/"),
            " does for its page and its actions, the router's `_url_for` "
            "takes the prefix from the path of the current request. A reader "
            "on `/a/` gets links under `/a/`, and one on `/b/` gets links "
            "under `/b/`. Values are percent-encoded, and a `path` converter "
            "keeps its slashes.",
        ),
        pr.code(
            'app.include_router(CommentsView.api_router, prefix="/comments")\n'
            'app.include_router(CommentsView.api_router, prefix="/archive")'
        ),
        pr.p(
            "`_url_for` only builds URLs for the view serving the request, so "
            "a data table has to be declared on a `HueView`, whose `index` is "
            "the page it links to. It raises a `LookupError` when the path "
            "does not end in the matched route's own path. That happens when "
            "a converter rewrites the value, such as `007` read as `7` by an "
            "`int` converter."
        ),
        pr.h2("Testing views with TestClient"),
        pr.p(
            "Test a view with FastAPI's `TestClient`. Send "
            "`X-Requested-With: XMLHttpRequest` to a fragment route, or it "
            "answers 400. When CSRF is on, an unsafe request also needs the "
            "token. Load a page first so the client holds the cookie, then "
            "send the cookie's value in `X-CSRFToken`. Without the token the "
            "answer is a 403, before the AJAX check runs."
        ),
        pr.code(
            "from fastapi.testclient import TestClient\n\n"
            'AJAX = {"X-Requested-With": "XMLHttpRequest"}\n\n'
            "client = TestClient(app)\n"
            'client.get("/comments/")  # sets the csrftoken cookie\n'
            'token = client.cookies["csrftoken"]\n\n'
            "response = client.post(\n"
            '    "/comments/comments/3/archive/",\n'
            '    data=Archive(reason="duplicate").model_dump(),\n'
            '    headers={**AJAX, "X-CSRFToken": token},\n'
            ")\n"
            "assert response.status_code == 200"
        ),
    )


PAGE = GuidePage(
    slug="fastapi/views",
    title="Views and Router",
    nav_label="Views and Router",
    group="FastAPI",
    order=0,
    build=_build,
)
