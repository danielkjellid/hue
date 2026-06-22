"""
The no-query guard around skeleton generation.

Skeleton generation must be data-free. A component that sizes itself from data
(here, a stand-in that runs a query in its skeleton()) would re-introduce the
I/O deferral was meant to move off the critical path — the guard catches it.
"""

import asyncio

import pytest
from django.db import connection
from django.http import HttpRequest
from django.test import override_settings
from htmy import html
from hue.context import HueContext, HueContextArgs
from hue.renderer import render_tree
from hue.types.core import Component
from hue.ui import Skeleton
from hue.ui.base import ChainableComponent

from hue_django.skeletonize import SkeletonQueryError, defer, forbid_db_queries


class _QueryBackedList(ChainableComponent):
    """A list whose skeleton naively touches the database (the mistake to catch)."""

    def _render(self, context: HueContext[HttpRequest]) -> Component:
        return html.div()

    def skeleton(self) -> Component:
        # Stands in for `len(self._queryset)` issuing a COUNT during skeletonising.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Skeleton().lines(3)


async def _render(component: Component) -> str:
    context_args: HueContextArgs[object] = HueContextArgs(
        request=object(), csrf_token="tok"
    )
    return await render_tree(component, context_args=context_args)


def test_forbid_db_queries_raises_on_query():
    with pytest.raises(SkeletonQueryError, match="skeleton generation"):
        with forbid_db_queries():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")


def test_defer_rejects_query_backed_layout():
    """Building the skeleton of a data-touching layout fails loudly."""
    with pytest.raises(SkeletonQueryError):
        defer(layout=_QueryBackedList(), url="/c/", target="t")


def test_defer_allows_data_free_layout():
    """A data-free layout skeletonises cleanly and wires the AJAX fetch."""
    region = defer(layout=lambda: html.div(html.p("REALDATA")), url="/c/", target="t")
    rendered = asyncio.run(_render(region))
    assert "animate-pulse" in rendered
    assert "$ajax('/c/'" in rendered
    assert "REALDATA" not in rendered


@override_settings(DEBUG=False)
def test_guard_is_noop_when_not_debug():
    """Outside DEBUG the guard steps aside — it's a dev assertion, not runtime."""
    with forbid_db_queries():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # must not raise
