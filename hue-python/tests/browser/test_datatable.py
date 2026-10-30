from typing import Any

from playwright.sync_api import Page, expect

from hue.datatable import BulkAction, build_datatable_state
from hue.router import Router
from hue.ui import Column, DataTable
from tests.browser.conftest import Show


class _Router(Router[Any]):
    # Every link points back at the page, which the test server answers with
    # the same document, so a swap finds the same ids in it. No action is
    # sent, so none is registered.
    def fragment_post(self, path: str) -> Any:  # type: ignore[override]
        return lambda handler: handler

    def _path_param(self, name: str) -> str:
        return f"{{{name}}}"

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {}

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        return {}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        return "/"


def _table(key: str) -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key=key,
            columns=[
                Column("invoice", "Invoice", sort="invoice"),
                Column("amount", "Amount", align="end"),
            ],
            rows=lambda request, asked: [
                {"invoice": "INV-2050", "amount": "2190"},
                {"invoice": "INV-2048", "amount": "1200"},
            ],
            identifier="invoice",
            search="Search invoices",
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
            page_size=1,
        )
    )


def _keeps_focus_through_a_swap(page: Page, link: str) -> None:
    page.focus(link)
    # Marks the element focus is on, to tell the one the swap brings in.
    page.evaluate("() => { document.activeElement.dataset.old = '' }")
    page.keyboard.press("Enter")
    page.wait_for_function(
        f"() => document.querySelector({link!r}) && !('old' in "
        f"document.querySelector({link!r}).dataset)"
    )
    expect(page.locator(link)).to_be_focused()


def test_two_tables_tick_their_own_rows_from_select_all(show: Show) -> None:
    page = show(_table("first"), _table("second"))
    boxes = page.get_by_role("checkbox", name="Select all")
    ids = [boxes.nth(i).get_attribute("id") for i in range(2)]
    assert ids[0] != ids[1]
    boxes.nth(1).check()
    expect(page.locator("#first input[type=checkbox]:checked")).to_have_count(0)


def test_slash_reaches_the_search_from_a_checkbox(show: Show) -> None:
    page = show(_table("invoices"))
    page.get_by_role("checkbox", name="Select all").focus()
    page.keyboard.press("/")
    expect(page.get_by_role("searchbox")).to_be_focused()


def test_a_sort_link_keeps_focus_through_its_swap(show: Show) -> None:
    page = show(_table("invoices"))
    _keeps_focus_through_a_swap(page, "th a")


def test_a_page_link_keeps_focus_through_its_swap(show: Show) -> None:
    page = show(_table("invoices"))
    _keeps_focus_through_a_swap(page, "#invoices-rows-pagination-page-2")
