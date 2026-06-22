"""
Django-side deferred loading: skeletonise a layout now, fetch real content later.

This wraps the framework-agnostic helpers in hue.skeletonize with a guard that
matters in Django: skeleton generation must be data-free. to_skeleton is
synchronous and cannot drive the async ORM, but a data-bound component can still
hit the database during skeletonisation — e.g. a list that sizes itself from
len(queryset), which issues a COUNT. forbid_db_queries turns that mistake into a
loud failure under DEBUG instead of a silent re-introduction of the very I/O
deferral was meant to move off the critical path.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager

from django.conf import settings
from django.db import connections
from hue.skeletonize import defer as _defer
from hue.skeletonize import to_skeleton
from hue.types.core import Component


class SkeletonQueryError(RuntimeError):
    """Raised when skeleton generation triggers a database query."""


@contextmanager
def forbid_db_queries() -> Iterator[None]:
    """
    Fail loudly if any database query runs inside the block.

    A no-op when DEBUG is off, so production never pays for it or risks a false
    positive — the guard is a development assertion, not a runtime safeguard.
    """
    if not settings.DEBUG:
        yield
        return

    def _block(execute, sql, params, many, context):
        raise SkeletonQueryError(
            f"database query during skeleton generation: {sql.strip()[:120]}"
        )

    with ExitStack() as stack:
        for connection in connections.all():
            stack.enter_context(connection.execute_wrapper(_block))
        yield


def defer(
    *,
    layout: Component | Callable[[], Component],
    url: str,
    target: str,
    method: str = "get",
) -> Component:
    """
    Render layout's skeleton now and fetch the real content into its place.

    layout is the data-free shape of the eventual content — either a component
    or a zero-arg factory. Passing a factory lets the guard bracket construction
    too, so eager data loading there (the common mistake) is caught. The
    skeleton is built under forbid_db_queries; the returned region wires an
    Alpine AJAX fetch of url into target (see hue.skeletonize.defer).
    """
    with forbid_db_queries():
        component = layout() if callable(layout) else layout
        skeleton = to_skeleton(component)
    return _defer(skeleton=skeleton, url=url, target=target, method=method)
