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
from hue.ui import Column, DataTable, Skeleton
from hue.ui.base import ChainableComponent

from hue_django.skeletonize import SkeletonQueryError, defer, forbid_db_queries


class _QueryBackedList(ChainableComponent):
    """A list whose skeleton naively touches the database (the mistake to catch)."""

    def _render(self, context: HueContext[HttpRequest]) -> Component:
        return html.div()

    def _skeleton_impl(self) -> Component:
        # Stands in for len(queryset) evaluating a lazy queryset while the
        # skeleton is built. Overriding _skeleton_impl rather than skeleton() is
        # deliberate: it is the documented extension point, and the only one
        # to_skeleton recognises when deciding a component defines its own
        # placeholder instead of being a transparent container.
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
    assert "$ajax(" in rendered and "/c/" in rendered
    assert "REALDATA" not in rendered


def test_datatable_backed_by_a_queryset_is_allowed():
    """
    The common shape — a table over a lazy queryset — must skeletonise cleanly.

    DataTable's skeleton previously sized itself from len(self._data), which
    evaluates a queryset in full: it tripped this guard under DEBUG and silently
    loaded the whole table in production.
    """

    class _LazyQuerySet:
        """Stands in for a QuerySet: any measurement or iteration hits the DB."""

        def _query(self) -> None:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

        def __len__(self) -> int:
            self._query()
            return 3

        def __iter__(self):
            self._query()
            return iter(())

    def layout():
        columns = [Column("Name", accessor="name")]
        return DataTable().columns(columns).data(_LazyQuerySet())

    rendered = asyncio.run(_render(defer(layout=layout, url="/c/", target="t")))
    assert "animate-pulse" in rendered


@override_settings(DEBUG=False)
def test_guard_is_noop_when_not_debug():
    """Outside DEBUG the guard steps aside — it's a dev assertion, not runtime."""
    with forbid_db_queries():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # must not raise
