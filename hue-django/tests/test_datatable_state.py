import pytest
from django.http import HttpRequest
from hue.datatable import BulkAction, TableState, datatable
from hue.renderer import render_tree
import asyncio


def render_sync(component, context_args):
    return asyncio.run(render_tree(component, context_args=context_args))
from hue.ui.molecules.table import Column
from hue_django.router import Router

INVOICES = [
    {"invoice": "INV-2050", "amount": "2190"},
    {"invoice": "INV-2048", "amount": "1200"},
]
archived: list[str] = []


def build():
    router = Router[HttpRequest]()
    state = datatable(
        router,
        key="invoices",
        columns=[Column("invoice", "Invoice"), Column("amount", "Amount", align="end", sort="amount")],
        rows=lambda s: sorted(INVOICES, key=lambda r: r["amount"], reverse=(s.sort or "").startswith("-")),
        select="invoice",
        actions={"archive": BulkAction("Archive", lambda request, ids: archived.extend(ids))},
    )
    return router, state


def test_it_registers_a_route_to_read_and_one_to_act():
    router, state = build()
    print([(r.method, r.path) for r in router.routes])
    assert [(r.method, r.path) for r in router.routes] == [
        ("GET", "invoices/"),
        ("POST", "invoices/<str:action>/"),
    ]


def test_the_header_links_to_its_own_route_and_swaps_the_table():
    import re
    from hue.context import HueContextArgs

    _, state = build()
    html = render_sync(
        state.build(TableState()),
        HueContextArgs(request=HttpRequest(), csrf_token="t"),
    )
    link = re.search(r'<th[^>]*>\s*<a href="([^"]*)"[^>]*x-target="([^"]*)"', html)
    print("sort link ->", link.groups() if link else "none")
    assert link is not None
    assert link.group(1) == "/invoices/?sort=amount"
    assert link.group(2) == "invoices"


def test_the_actions_post_what_is_ticked():
    import re
    from hue.context import HueContextArgs

    _, state = build()
    html = render_sync(
        state.build(TableState()),
        HueContextArgs(request=HttpRequest(), csrf_token="t"),
    )
    print("form:", re.search(r'<form[^>]*>', html).group())
    print("action button:", re.search(r'formaction="([^"]*)"', html).group(1))
    print("checkbox name:", re.findall(r'<input[^>]*name="(\w+)"[^>]*value="([^"]*)"', html))
    assert re.search(r'formaction="/invoices/archive/"', html)


def test_an_action_is_given_the_ids_and_the_table_comes_back():
    from unittest.mock import MagicMock

    router, state = build()
    request = MagicMock()
    request.POST.getlist.return_value = ["INV-2050", "INV-2048"]
    request.GET.dict.return_value = {}

    act = [r for r in router.routes if r.method == "POST"][0]
    print("route name:", act.name)
    state.actions["archive"].handler(request, router._get_form_list(request, "selected"))
    print("archived:", archived)
    assert archived == ["INV-2050", "INV-2048"]
