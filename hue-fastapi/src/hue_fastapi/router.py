from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final
from urllib.parse import quote

from hue.context import HueContextArgs
from hue.router import HueResponse, PathParseResult, ViewFunc, WrappedViewFunc
from hue.router import Router as HueRouter
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request

from hue_fastapi.config import get_config

__all__ = ["HueResponse", "Router"]

# Starlette path parameters: {name} and {name:converter}.
_PATH_PARAM_RE: Final = re.compile(r"\{(\w+)(?::(\w+))?\}")

# Where the endpoint leaves what hue's synchronous hooks read off the request.
BODY_STATE: Final = "hue_raw_body"
FORM_STATE: Final = "hue_form_values"
MOUNT_STATE: Final = "hue_mount"

HANDLER_ATTR: Final = "__hue_handler__"

FORM_CONTENT_TYPES: Final = (
    "application/x-www-form-urlencoded",
    "multipart/form-data",
)


@dataclass(frozen=True, slots=True)
class Mount:
    """
    Where the view serving a request is mounted: the prefix it was included
    under, and the path of each of its routes by name.
    """

    # None when the path did not end in the route's own template, which
    # _url_for reports rather than linking to the wrong place.
    prefix: str | None
    paths: Mapping[str, str]

    @classmethod
    def of(cls, request: Request, template: str, paths: Mapping[str, str]) -> Mount:
        """
        The prefix is the request's path less the part the matched route's
        own template covers at its end.

        Worked out from the path because FastAPI cannot say which mount a
        request came through: two mounts of one view register the same names.
        """
        own = "/" + _PATH_PARAM_RE.sub(
            lambda m: str(request.path_params[m[1]]), template
        )
        path = request.url.path
        # Filled in from the values Starlette matched rather than matched as
        # a pattern: a path converter's value can repeat the prefix's text,
        # and only the values say where the prefix ends.
        # shortcut: a converter that normalises ("007" read as 7) leaves the
        # prefix unknown, so _url_for raises; spell such values back from the
        # raw path if a non-canonical URL ever has to build links.
        prefix = path[: len(path) - len(own)] if path.endswith(own) else None
        return cls(prefix=prefix, paths=paths)


class Router[T_Request: Request](HueRouter[T_Request]):
    """
    The hue router for FastAPI views, understanding Starlette's path syntax
    such as "comments/{comment_id:int}/".

        class CommentsView(HueView):
            router = Router[Request]()

            async def index(
                self, request: Request, context: HueContext[Request]
            ) -> Page:
                return Page(title="Comments", body=...)

            @router.fragment_get("comments/{comment_id}/")
            async def comment(
                self, request: Request, context: HueContext[Request], comment_id: int
            ) -> html.div:
                return html.div(f"Comment {comment_id}")
    """

    def _parse_path_params(self, path: str) -> PathParseResult:
        return PathParseResult(
            path=path, param_names=[m[1] for m in _PATH_PARAM_RE.finditer(path)]
        )

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        config = get_config(request.app)
        return HueContextArgs(
            request=request,
            csrf_token=config.csrf.get_token(request) if config.csrf else "",
            formats=config.formats,
            shortcuts=config.shortcuts,
        )

    def _path_param(self, name: str) -> str:
        return f"{{{name}}}"

    def _get_request_body(self, request: T_Request) -> str:
        # Read by the endpoint before dispatch: hue's hooks are synchronous and
        # Starlette's body is a coroutine. Decoded here, inside the router's
        # try, so a body that is not UTF-8 is a 422 rather than a 500.
        body: bytes = getattr(request.state, BODY_STATE, b"")
        return body.decode("utf-8")

    def _get_request_content_type(self, request: T_Request) -> str:
        return request.headers.get("content-type") or "application/json"

    def _get_form_values(self, request: T_Request) -> dict[str, list[str]]:
        return dict(getattr(request.state, FORM_STATE, None) or {})

    def _get_query_values(self, request: T_Request) -> dict[str, list[str]]:
        params = request.query_params
        return {name: params.getlist(name) for name in params}

    def _url_for(self, request: T_Request, name: str, **params: Any) -> str:
        """
        Where one of the serving view's routes lives, under the prefix the
        request came in through.

        Worked out from the route that matched rather than looked up by name,
        so the same view mounted twice links back into the mount the reader is
        already in.
        """
        mount: Mount | None = getattr(request.state, MOUNT_STATE, None)
        if mount is None or name not in mount.paths:
            raise LookupError(
                f"No route called {name!r} on the view serving this request. A "
                f"view can only build its own URLs, and only while it is the "
                f"one serving the request. A table links to the page it is "
                f"drawn on, so it has to be declared on a HueView, whose index "
                f"is that page."
            )
        if mount.prefix is None:
            raise LookupError(
                f"Could not tell where this view is mounted from {request.url.path!r}."
            )
        # Percent-encoded so a value cannot add a segment or a query; a path
        # converter keeps its slashes, since spanning them is what it is for.
        path = _PATH_PARAM_RE.sub(
            lambda m: quote(str(params[m[1]]), safe="/" if m[2] == "path" else ""),
            mount.paths[name],
        )
        return f"{mount.prefix}/{path}"

    def _form_fields(self) -> frozenset[str]:
        return frozenset({"csrf_token"})

    def _passes_through(self, error: Exception) -> bool:
        """
        Starlette's own answers, such as a 403 or a 404 raised as an
        HTTPException, are sent as Starlette sends them.
        """
        return isinstance(error, HTTPException)

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        # A sync handler or data fetch would otherwise block the event loop for
        # every other request.
        return await run_in_threadpool(func, *args)

    def _wrap_view(
        self, view_func: ViewFunc, require_ajax: bool = True
    ) -> WrappedViewFunc:
        wrapped = super()._wrap_view(view_func, require_ajax=require_ajax)
        # Keep the original handler reachable: the view reads its signature to
        # build a FastAPI endpoint that resolves path parameters and Depends
        # the way FastAPI users expect.
        setattr(wrapped, HANDLER_ATTR, view_func)
        return wrapped


async def preload_body(request: Request) -> None:
    """
    Read the request body once, before hue's synchronous hooks need it.
    """
    if request.headers.get("content-type", "").startswith(FORM_CONTENT_TYPES):
        form = await request.form()
        # Every value kept: a column of checkboxes is several under one name.
        # Uploads are left out, as hue reads text fields only.
        values = {
            name: [value for value in form.getlist(name) if isinstance(value, str)]
            for name in form
        }
        setattr(request.state, FORM_STATE, values)
    else:
        setattr(request.state, BODY_STATE, await request.body())
