import re

from django.http import HttpRequest
from django.middleware.csrf import get_token
from hue.context import HueContextArgs
from hue.router import PathParseResult
from hue.router import Router as HueRouter


class Router[T_Request: HttpRequest](HueRouter[T_Request]):
    """
    Django-specific router that extends the base Router.

    Handles Django URL pattern syntax like "comments/<int:comment_id>/".

    Example:
        class MyView(HueView):
            router = Router[HttpRequest]()

            async def index(
                self, request: HttpRequest, context: HueContext[HttpRequest]
            ):
                return html.div("Index")

            @router.fragment_get("comments/<int:comment_id>/")
            async def comment(
                self,
                request: HttpRequest,
                context: HueContext[HttpRequest],
                comment_id: int,
            ):
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

        # The path is already in Django URL pattern format, just return it
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
