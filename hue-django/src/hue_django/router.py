import re

from django.http import HttpRequest
from django.middleware.csrf import get_token

from hue.context import HueContextArgs
from hue.router import Router as HueRouter


class Router[T_Request](HueRouter[T_Request]):
    """
    Django-specific router that extends the base Router.

    Handles Django URL pattern syntax like "comments/<int:comment_id>/".

    Example:
        class MyView(HueView):
            router = DjangoRouter[HttpRequest]()

            @router.get("/")
            async def index(self, request: HttpRequest):
                return html.div("Index")

            @router.ajax_get("comments/<int:comment_id>/")
            async def comment(self, request: HttpRequest, comment_id: int):
                return html.div(f"Comment {comment_id}")
    """

    def _parse_path_params(self, path: str) -> tuple[str, list[str]]:
        """
        Parse Django URL pattern parameters from path.

        Django uses syntax like <int:comment_id> or <str:username>.

        Example:
            "comments/<int:comment_id>/" -> (
                "comments/<int:comment_id>/", ["comment_id"]
            )
            "users/<str:username>/posts/" -> (
                "users/<str:username>/posts/", ["username"]
            )

        Returns:
            Tuple of (django_path_pattern, list_of_param_names)
        """
        # Find all <type:name> patterns (Django URL pattern syntax)
        param_pattern = r"<(\w+):(\w+)>"
        matches = re.findall(param_pattern, path)
        param_names = [name for _, name in matches]

        # The path is already in Django URL pattern format, just return it
        return path, param_names

    def _get_context_args(
        self, view_instance: object, request: HttpRequest
    ) -> HueContextArgs[HttpRequest]:
        """
        Get Django-specific context arguments.

        Returns request and CSRF token for Django.
        """
        return HueContextArgs[HttpRequest](
            request=request,
            csrf_token=get_token(request),
        )
