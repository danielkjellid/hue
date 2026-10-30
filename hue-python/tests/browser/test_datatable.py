from typing import Any

from htmy import html
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


# The bar sticks to the foot of whatever the table scrolls in, inside the
# table, so it can cover nothing the reader cannot scroll out from under it.

_PAGE_2 = "#invoices-rows-pagination-page-2"

# Whether two elements' boxes overlap, once the bar has slid in.
_APART = """([a, b]) => {
    const bar = document.querySelector('[aria-label="Selected rows"]');
    if (getComputedStyle(bar).transform !== 'none') return false;
    const one = document.querySelector(a).getBoundingClientRect();
    const two = document.querySelector(b).getBoundingClientRect();
    return one.bottom <= two.top || two.bottom <= one.top;
}"""

_BAR = '[aria-label="Selected rows"]'


def _tick(page: Page) -> None:
    page.get_by_role("checkbox", name="Select INV-2050").check()
    expect(_bar(page)).to_be_visible()


def _end_of(page: Page, scroller: str) -> None:
    page.evaluate(f"(() => {{ const s = {scroller}; s.scrollTop = s.scrollHeight }})()")


def _clear_of_the_bar(page: Page) -> None:
    page.wait_for_function(_APART, arg=[_PAGE_2, _BAR])
    page.wait_for_function(_APART, arg=["#invoices-rows", _BAR])


def _at_the_foot(show: Show, *components: object) -> Page:
    """
    A phone whose window ends at the pager, so a stuck bar sits over it.
    """
    page = show(*components, width=390, height=900)
    bottom = page.evaluate(
        "() => document.querySelector('#invoices-rows').getBoundingClientRect().bottom"
    )
    page.set_viewport_size({"width": 390, "height": int(bottom)})
    return page


def test_the_bar_sits_in_the_table_and_sticks_to_the_foot(show: Show) -> None:
    page = _at_the_foot(show, _table("invoices"), html.div(style="height: 900px"))
    _tick(page)
    # Inside the frame, so its scope and its place go with the table.
    assert page.evaluate(
        f"document.getElementById('invoices').contains(document.querySelector('{_BAR}'))"
    )
    page.wait_for_function(
        f"() => Math.abs(innerHeight - 24 - document.querySelector('{_BAR}')"
        ".getBoundingClientRect().bottom) < 1"
    )


def test_a_focused_page_link_is_not_under_the_bar(show: Show) -> None:
    page = _at_the_foot(show, _table("invoices"), html.div(style="height: 900px"))
    _tick(page)
    page.locator(_PAGE_2).focus()
    page.wait_for_function(_APART, arg=[_PAGE_2, _BAR])


def test_a_focused_row_checkbox_is_not_under_the_bar(show: Show) -> None:
    page = show(_table("invoices"), html.div(style="height: 900px"), width=390)
    box = "#invoices input[type=checkbox][name]:not([name=hue-select-all])"
    _tick(page)
    top = page.evaluate(f"document.querySelector('{box}').getBoundingClientRect().top")
    # The window ends just under the box, where the stuck bar is.
    page.set_viewport_size({"width": 390, "height": int(top) + 30})
    page.evaluate("document.activeElement.blur()")
    page.locator(box).focus()
    page.wait_for_function(_APART, arg=[box, _BAR])


def test_the_pager_scrolls_clear_of_the_bar_on_the_page(show: Show) -> None:
    page = _at_the_foot(show, _table("invoices"))
    _tick(page)
    _end_of(page, "document.scrollingElement")
    _clear_of_the_bar(page)


def test_the_pager_scrolls_clear_in_an_overflow_x_wrapper(show: Show) -> None:
    page = _at_the_foot(show, html.div(_table("invoices"), style="overflow-x: auto"))
    _tick(page)
    _end_of(page, "document.scrollingElement")
    _clear_of_the_bar(page)


def test_the_pager_scrolls_clear_in_a_body_that_scrolls(show: Show) -> None:
    page = show(
        html.style(
            "html { overflow: hidden } html, body { height: 100%; overflow-y: auto }"
        ),
        html.div(style="height: 900px"),
        _table("invoices"),
        width=390,
        height=600,
    )
    _tick(page)
    _end_of(page, "document.body")
    _clear_of_the_bar(page)


def test_the_pager_scrolls_clear_in_an_app_shell(show: Show) -> None:
    page = show(
        html.div(
            html.div(style="height: 600px"),
            _table("invoices"),
            id="shell",
            style="position: fixed; inset: 0; overflow-y: auto; padding: 16px",
        ),
        width=390,
        height=600,
    )
    _tick(page)
    _end_of(page, "document.getElementById('shell')")
    _clear_of_the_bar(page)


def test_the_page_and_its_padding_are_left_alone(show: Show) -> None:
    page = show(_table("invoices"), width=390)
    page.evaluate("document.documentElement.style.paddingBottom = '40px'")
    _tick(page)
    page.keyboard.press("Escape")
    expect(_bar(page)).to_be_hidden()
    assert page.evaluate("document.documentElement.style.paddingBottom") == "40px"
    assert page.evaluate("document.body.getAttribute('style')") is None


def test_what_follows_the_table_moves_by_the_bar_at_most(show: Show) -> None:
    page = show(_table("invoices"), html.p("After", id="after"), width=390)
    before = page.evaluate(
        "document.getElementById('after').getBoundingClientRect().top"
    )
    _tick(page)
    page.wait_for_function(_APART, arg=["#after", _BAR])
    after = page.evaluate(
        "document.getElementById('after').getBoundingClientRect().top"
    )
    grown = page.evaluate(
        f"(() => {{ const bar = document.querySelector('{_BAR}');"
        " const style = getComputedStyle(bar);"
        " return bar.offsetHeight + parseFloat(style.marginTop)"
        " + parseFloat(style.marginBottom) })()"
    )
    assert 0 <= after - before <= grown
