import inspect
import re
from collections.abc import Callable
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings as django_settings
from django.core.exceptions import (
    BadRequest,
    PermissionDenied,
    SuspiciousOperation,
    ValidationError,
)
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django.middleware.csrf import get_token
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from hue.context import HueContext, HueContextArgs
from hue.formats import Formats
from hue.router import HueResponse, PathParseResult, ViewFunc
from hue.router import Router as HueRouter

from hue_django.conf import settings

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
        return HueContextArgs(
            request=request,
            csrf_token=get_token(request),
            formats=Formats(
                date=settings.HUE_DATE_FORMAT,
                datetime=settings.HUE_DATETIME_FORMAT,
                # The ORM hands aware datetimes over in UTC. Converted the way
                # a template converts them, into the current timezone.
                localize=timezone.localtime if django_settings.USE_TZ else None,
            ),
        )

    def _get_request_body(self, request: T_Request) -> str:
        return request.body.decode("utf-8")

    def _get_request_content_type(self, request: T_Request) -> str:
        return request.content_type or "application/json"

    def _get_form_data(self, request: T_Request) -> dict[str, Any]:
        return request.POST.dict()

    def _get_form_values(self, request: T_Request) -> dict[str, list[str]]:
        return {name: request.POST.getlist(name) for name in request.POST}

    def _get_query_values(self, request: T_Request) -> dict[str, list[str]]:
        return {name: request.GET.getlist(name) for name in request.GET}

    def _url_for(self, request: T_Request, name: str, **params: Any) -> str:
        """
        Reverse one of this router's routes, in the namespace the request
        came in through.

        The namespace rather than the view's app_name, because that is
        what survives being mounted: include() under a prefix, include()
        with a namespace of the caller's choosing, an include() inside
        another one, or the same view mounted twice - in which case the
        reader gets links back into the mount they are already in.
        """
        match = request.resolver_match
        namespace = match.namespace if match else ""
        target = f"{namespace}:{name}" if namespace else name
        try:
            return reverse(target, kwargs=params)
        except NoReverseMatch:
            raise NoReverseMatch(
                f"Django knows no route called {target!r}. A view's URLs are "
                f"reversed through the namespace the request arrived in "
                f"({namespace or 'none'}), so a view can only build its own, "
                f"and only while it is the one serving the request. A table "
                f"links to the page it is drawn on, so it has to be declared "
                f"on a HueView, whose index is that page."
            ) from None

    def _form_fields(self) -> frozenset[str]:
        return frozenset({"csrfmiddlewaretoken"})

    def _passes_through(self, error: Exception) -> bool:
        """
        Django's own answers: a 403, a 404 or a 400 is sent as Django sends
        it, not reported as a failure.
        """
        return isinstance(
            error, (PermissionDenied, Http404, SuspiciousOperation, BadRequest)
        )

    def _narrow_to(self, rows: Any, key: str, values: list[str]) -> Any:
        """
        Filters a queryset in the database, rather than walking every row
        that matches to find the few that were picked. Anything else is
        walked, as the base router does.
        """
        if isinstance(rows, QuerySet):
            try:
                return rows.filter(**{f"{key.replace('.', '__')}__in": values})
            except (ValueError, TypeError, ValidationError):
                # An id the field cannot hold, such as "abc" for an integer
                # key, is posted by nothing the table drew, so the whole
                # post picks nothing rather than guessing at the rest.
                return rows.none()
        return super()._narrow_to(rows, key, values)

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        """
        Runs the call in a thread, because the ORM raises
        SynchronousOnlyOperation for a query made on the event loop, and
        counting and slicing a queryset are both queries.
        """
        return await sync_to_async(func)(*args)

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
