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


def test_escape_empties_the_search_and_keeps_focus(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.fill("2050")
    page.wait_for_url("**invoices-q=2050**")
    field.press("Escape")
    expect(field).to_have_value("")
    expect(field).to_be_focused()
    # An empty search leaves no trace in the URL, as an empty filter does not.
    page.wait_for_function("() => !location.search.includes('2050')")
    assert "invoices-q" not in page.evaluate("location.search")


def test_a_search_deleted_by_hand_leaves_no_parameter(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.fill("2050")
    page.wait_for_url("**invoices-q=2050**")
    field.fill("")
    page.wait_for_function("() => !location.search.includes('2050')")
    assert "invoices-q" not in page.evaluate("location.search")
    expect(field).to_be_focused()


def _bar(page: Page):  # type: ignore[no-untyped-def]
    return page.get_by_role("group", name="Selected rows")


def test_ticking_a_row_shows_the_bar_and_escape_clears_it(show: Show) -> None:
    page = show(_table("invoices"))
    page.get_by_role("checkbox", name="Select INV-2050").check()
    expect(_bar(page)).to_be_visible()
    expect(_bar(page)).to_contain_text("1 selected")
    page.keyboard.press("Escape")
    expect(_bar(page)).to_be_hidden()
    expect(page.get_by_role("checkbox", name="Select INV-2050")).not_to_be_checked()


def test_a_selection_in_one_table_clears_the_other(show: Show) -> None:
    page = show(_table("first"), _table("second"))
    page.locator("#first").get_by_role("checkbox", name="Select INV-2050").check()
    page.locator("#second").get_by_role("checkbox", name="Select INV-2050").check()
    expect(_bar(page).locator("visible=true")).to_have_count(1)
    expect(
        page.locator("#first").get_by_role("checkbox", name="Select INV-2050")
    ).not_to_be_checked()


# Where the bar's top rests, leaving out the slide it comes in with.
_BAR_TOP = (
    "(() => { const bar = document.querySelector('[aria-label=\"Selected rows\"]');"
    " return innerHeight - parseFloat(getComputedStyle(bar).bottom)"
    " - bar.offsetHeight })()"
)


def _uncovered(page: Page, selector: str) -> bool:
    return page.evaluate(
        """(selector) => {
            const el = document.querySelector(selector);
            const box = el.getBoundingClientRect();
            const hit = document.elementFromPoint(
                box.left + box.width / 2, box.top + box.height / 2);
            return el.contains(hit);
        }""",
        selector,
    )


def _ticked_at_the_foot(show: Show, *tables: DataTable) -> Page:
    """
    A phone whose window ends at the pager, with a row ticked, so the bar
    sits over the pager unless the page makes room for it.
    """
    page = show(*tables, width=390, height=900)
    pager = page.locator("#invoices-rows-pagination-page-2")
    bottom = page.evaluate(
        "() => document.querySelector('#invoices-rows').getBoundingClientRect().bottom"
    )
    page.set_viewport_size({"width": 390, "height": int(bottom)})
    page.get_by_role("checkbox", name="Select INV-2050").check()
    expect(_bar(page)).to_be_visible()
    expect(pager).to_be_visible()
    return page


def test_a_focused_page_link_is_not_under_the_bar(show: Show) -> None:
    page = _ticked_at_the_foot(show, _table("invoices"))
    page.locator("#invoices-rows-pagination-page-2").focus()
    page.wait_for_function(
        "() => document.querySelector('#invoices-rows-pagination-page-2')"
        f".getBoundingClientRect().bottom <= {_BAR_TOP}"
    )
    assert _uncovered(page, "#invoices-rows-pagination-page-2")


def test_the_page_scrolls_the_pager_clear_of_the_bar(show: Show) -> None:
    page = _ticked_at_the_foot(show, _table("invoices"))
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    # The band under the rows holds the count and the pager.
    assert page.evaluate(
        "() => document.querySelector('#invoices-rows').getBoundingClientRect()"
        f".bottom <= {_BAR_TOP}"
    )


def test_the_room_goes_with_the_bar(show: Show) -> None:
    page = _ticked_at_the_foot(show, _table("invoices"))
    page.keyboard.press("Escape")
    expect(_bar(page)).to_be_hidden()
    page.wait_for_function(
        "() => !document.documentElement.style.paddingBottom"
        " && !document.documentElement.style.scrollPaddingBottom"
    )
