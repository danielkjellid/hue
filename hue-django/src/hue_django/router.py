import asyncio
import re
from typing import Any

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.middleware.csrf import get_token
from hue.context import HueContext, HueContextArgs
from hue.exceptions import BodyValidationError
from hue.router import HueResponse, PathParseResult, RawResponse, ViewFunc
from hue.router import Router as HueRouter

__all__ = ["BodyValidationError", "HueResponse", "RawResponse", "Router"]


class Router[T_Request: HttpRequest](HueRouter[T_Request]):
    """
    Django-specific router that extends the base Router.

    Handles Django URL pattern syntax like "comments/<int:comment_id>/".

    Example:
        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ) -> Page:
                return Page(...)

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
        """
        Parse Django URL pattern parameters from path.

        Django uses syntax like <int:comment_id> or <str:username>.
        """
        # Find all <type:name> patterns (Django URL pattern syntax)
        param_pattern = r"<(\w+):(\w+)>"
        matches = re.findall(param_pattern, path)
        param_names = [name for _, name in matches]

        return PathParseResult(path=path, param_names=param_names)

    def _get_context_args(self, request: T_Request) -> HueContextArgs[T_Request]:
        """
        Get Django-specific context arguments.

        Returns request and CSRF token for Django.
        """
        return HueContextArgs(
            request=request,
            csrf_token=get_token(request),
        )

    def _is_ajax_request(self, request: T_Request) -> bool:
        """
        Check if the request is an AJAX request using Django's request.META.

        Django stores HTTP headers in request.META with the HTTP_ prefix.
        """
        is_ajax_req = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
        is_alpine_ajax_req = request.META.get("HTTP_X_ALPINE_REQUEST") == "true"
        return is_ajax_req or is_alpine_ajax_req

    def _get_request_body(self, request: T_Request) -> str:
        """
        Get the raw request body as a string from Django's request.

        Django provides request.body as bytes, which we decode to UTF-8.
        """
        return request.body.decode("utf-8")

    def _get_request_content_type(self, request: T_Request) -> str:
        """
        Get the content type of the request from Django's request.

        Django stores content type in request.content_type.
        """
        return request.content_type or ""

    def _get_form_data(self, request: T_Request) -> dict:
        """
        Get form data from Django's request.POST.

        Django parses form data into request.POST (a QueryDict).
        We convert it to a regular dict for Pydantic.
        """
        # Convert QueryDict to regular dict
        # QueryDict.dict() returns a dict with single values (not lists)
        return request.POST.dict()

    async def _call_view_func(
        self,
        view_func: ViewFunc,
        view_instance: object,
        request: T_Request,
        context: HueContext[T_Request],
        **kwargs: Any,
    ) -> Any:
        """
        Django-specific view function caller.

        Wraps sync view functions with sync_to_async for proper ASGI compatibility.
        This prevents issues like duplicate requests or malformed responses when
        calling sync code (ORM, auth, etc.) from async context.
        """
        if asyncio.iscoroutinefunction(view_func):
            # Async function: call directly
            return await view_func(view_instance, request, context, **kwargs)

        # Sync function: wrap with sync_to_async
        return await sync_to_async(view_func)(view_instance, request, context, **kwargs)
