import inspect
import re
from typing import Any

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.middleware.csrf import get_token
from hue.context import HueContext, HueContextArgs
from hue.router import HueResponse, PathParseResult, ViewFunc
from hue.router import Router as HueRouter

__all__ = ["HueResponse", "Router"]

# Django path syntax: <name> or <converter:name>.
_PATH_PARAM_RE = re.compile(r"<(?:\w+:)?(\w+)>")


class Router[T_Request: HttpRequest](HueRouter[T_Request]):
    """
    The hue router for Django views, understanding Django's path syntax such as
    "comments/<int:comment_id>/".

        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Page:
                return Page(title="Comments", body=...)

            @router.fragment_get("comments/<int:comment_id>/")
            async def comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                comment_id: int,
            ) -> html.div:
                return html.div(f"Comment {comment_id}")
    """

    def _parse_path_params(self, path: str) -> PathParseResult:
        return PathParseResult(path=path, param_names=_PATH_PARAM_RE.findall(path))

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        return HueContextArgs(request=request, csrf_token=get_token(request))

    def _get_request_body(self, request: T_Request) -> str:
        return request.body.decode("utf-8")

    def _get_request_content_type(self, request: T_Request) -> str:
        return request.content_type or "application/json"

    def _get_form_data(self, request: T_Request) -> dict[str, Any]:
        return request.POST.dict()

    def _get_form_list(self, request: T_Request, name: str) -> list[str]:
        return request.POST.getlist(name)

    def _get_query_params(self, request: T_Request) -> dict[str, str]:
        return request.GET.dict()

    async def _call_view_func(
        self,
        view_func: ViewFunc,
        view_instance: object,
        request: T_Request,
        context: HueContext[T_Request],
        **kwargs: Any,
    ) -> Any:
        """
        Run sync handlers in a thread via sync_to_async.

        Handlers are dispatched from an async context, so calling sync code (ORM,
        auth) directly raises SynchronousOnlyOperation. That 500 has no AJAX
        target, so Alpine AJAX falls back to a native form resubmit, which the
        server then rejects as non-AJAX. Running sync handlers in a thread avoids
        the whole cascade.
        """
        if inspect.iscoroutinefunction(view_func):
            return await view_func(view_instance, request, context, **kwargs)
        return await sync_to_async(view_func)(view_instance, request, context, **kwargs)
