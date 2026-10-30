from typing import Any

import pytest
from htmy import html
from playwright.sync_api import Page, Route, expect

from hue.datatable import BulkAction, Filter, build_datatable_state
from hue.router import Router
from hue.ui import (
    Button,
    Card,
    CardBody,
    Column,
    DataTable,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    Panel,
)
from tests.browser.conftest import Show
from tests.browser.test_pagination import ROWS, coarse


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
    page.get_by_role("checkbox", name="Select all").nth(1).check()
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


def _sent_by_enter(page: Page) -> str:
    with page.expect_request(lambda request: request.method == "GET") as sent:
        page.keyboard.press("Enter")
    return sent.value.url


def test_escape_empties_the_search_and_keeps_its_name(show: Show) -> None:
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
    field.press("Enter")
    expect(field).to_have_attribute("name", "invoices-q")
    field.press_sequentially("2048")
    field.press("Enter")
    page.wait_for_url("**invoices-q=2048**")


def test_a_search_deleted_by_hand_sends_no_query_then_the_next(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.fill("2050")
    page.wait_for_url("**invoices-q=2050**")
    field.fill("")
    page.wait_for_function("() => !location.search.includes('2050')")
    assert "invoices-q" not in page.evaluate("location.search")
    expect(field).to_be_focused()
    assert "invoices-q" not in _sent_by_enter(page)
    # The name comes back after the empty submit, or the next search would
    # go out without its parameter.
    field.fill("2048")
    page.wait_for_url("**invoices-q=2048**")


def test_enter_twice_in_an_empty_search_keeps_its_name(show: Show) -> None:
    # Two submits closer than the timer that gives the box its name back.
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.focus()
    assert "invoices-q" not in _sent_by_enter(page)
    page.keyboard.press("Enter")
    expect(field).to_have_attribute("name", "invoices-q")
    # A name lost for good is a search box that never searches again.
    with page.expect_request(lambda r: "invoices-q=2050" in r.url, timeout=3000):
        field.press_sequentially("2050")
        field.press("Enter")


def test_two_submits_in_one_task_keep_the_name(show: Show) -> None:
    page = show(_table("invoices"))
    page.evaluate(
        "(() => { const f = document.querySelector('[type=search]').form;"
        " f.requestSubmit(); f.requestSubmit(); })()"
    )
    expect(page.get_by_role("searchbox")).to_have_attribute("name", "invoices-q")


def test_rapid_typing_then_enter_sends_what_was_typed(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.press_sequentially("2050")
    with page.expect_request(lambda r: "invoices-q=2050" in r.url):
        field.press("Enter")


def test_a_search_typed_while_an_empty_one_is_in_flight_is_sent(show: Show) -> None:
    page = show(_table("invoices"))
    held: list[Route] = []
    page.route(lambda url: "?" in url, lambda route: held.append(route))
    page.get_by_role("searchbox").focus()
    page.keyboard.press("Enter")
    with page.expect_request(lambda r: "invoices-q=7" in r.url):
        page.keyboard.type("7")
        page.keyboard.press("Enter")
    # Left pending: closing the page drops them quietly, where an abort would
    # log a failed fetch for the fixture to catch.


def test_two_tables_searches_keep_their_own_names(show: Show) -> None:
    page = show(_table("first"), _table("second"))
    one = page.locator("#first").get_by_role("searchbox")
    two = page.locator("#second").get_by_role("searchbox")
    one.focus()
    assert "first-q" not in _sent_by_enter(page)
    two.fill("2050")
    page.wait_for_url("**second-q=2050**")
    expect(one).to_have_attribute("name", "first-q")
    expect(two).to_have_attribute("name", "second-q")


def _bar(page: Page):  # type: ignore[no-untyped-def]
    return page.get_by_role("group", name="Selected rows")


def test_escape_from_an_action_clears_the_bar_and_keeps_focus(show: Show) -> None:
    page = show(_table("invoices"))
    page.get_by_role("checkbox", name="Select INV-2050").check()
    expect(_bar(page)).to_be_visible()
    expect(_bar(page)).to_contain_text("1 selected")
    page.get_by_role("button", name="Archive").focus()
    page.keyboard.press("Escape")
    expect(_bar(page)).to_be_hidden()
    assert page.evaluate("document.activeElement !== document.body")
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


def _scrolled_clear_of_the_bar(page: Page, scroller: str) -> None:
    # Scroll to the end on every check: the bar sliding in, and the room made
    # for it, both add to what there is to scroll after the first try.
    for target in (_PAGE_2, "#invoices-rows"):
        page.wait_for_function(
            f"([a, b]) => {{ const s = {scroller}; s.scrollTop = s.scrollHeight;"
            f" return ({_APART})([a, b]) }}",
            arg=[target, _BAR],
        )


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
    _scrolled_clear_of_the_bar(page, "document.scrollingElement")


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
    _scrolled_clear_of_the_bar(page, "document.body")


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
    _scrolled_clear_of_the_bar(page, "document.getElementById('shell')")


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


# A table long enough that its bar sticks, wherever it scrolls.


def _menu(row: Any) -> Any:
    return (
        DropdownMenu()
        .label(f"Actions for {row['invoice']}")
        .trigger(Button().variant("ghost").content(f"Act on {row['invoice']}"))
        .content(MenuItem().content("Duplicate"), MenuItem().content("Delete"))
    )


def _long(
    rows: int = 40,
    *,
    columns: int = 0,
    menus: bool = False,
    extras: bool = False,
    confirm: bool = False,
    page_size: int | None = None,
) -> DataTable:
    cols = [
        Column("invoice", "Invoice"),
        Column("amount", "Amount", align="end"),
        *[Column(f"c{n}", f"Column {n}") for n in range(columns)],
    ]
    if menus:
        cols.append(Column("actions", "Actions", render=_menu))
    delete = (
        BulkAction(
            "Delete",
            lambda request, ids: None,
            variant="danger",
            confirm=Dialog().destructive().title("Delete these invoices?"),
        )
        if confirm
        else BulkAction("Archive", lambda request, ids: None)
    )
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=cols,
            rows=lambda request, asked: [
                {
                    "invoice": f"INV-{n:03}",
                    "amount": str(n),
                    **{f"c{c}": "wide value" for c in range(columns)},
                }
                for n in range(rows)
            ],
            identifier="invoice",
            search="Search invoices",
            filters=[
                Filter(
                    "status",
                    "Status",
                    options=[(s, s.title()) for s in ("paid", "due", "void", "late")],
                )
            ]
            if extras
            else (),
            hideable=["amount"] if extras else (),
            actions={
                "delete" if confirm else "archive": delete,
                "export": BulkAction("Export", lambda request, ids: None),
            },
            page_size=page_size or rows,
        )
    )


def _tick_first(page: Page) -> None:
    page.get_by_role("checkbox", name="Select INV-000").check()
    expect(page.locator(_BAR)).to_be_visible()
    page.wait_for_function(
        "bar => getComputedStyle(document.querySelector(bar)).transform === 'none'",
        arg=_BAR,
    )


# Whether the bar is in reach: inside the window and the box it scrolls in,
# and on top at its middle.
_IN_REACH = """(scroller) => {
    const bar = document.querySelector('[aria-label="Selected rows"]');
    const box = bar.getBoundingClientRect();
    const port = scroller
        ? document.querySelector(scroller).getBoundingClientRect()
        : { top: 0, bottom: innerHeight };
    const bottom = Math.min(port.bottom, innerHeight);
    if (box.top < Math.max(port.top, 0) || box.bottom > bottom) return false;
    const hit = document.elementFromPoint(box.left + 12, box.top + box.height / 2);
    return bar.contains(hit);
}"""

_FRAMES: dict[str, tuple[Any, str | None]] = {
    "page": (lambda table: table, None),
    "card": (lambda table: Card().content(CardBody().content(table)), None),
    "panel": (
        lambda table: Panel().label("Invoices").padding("none").content(table),
        None,
    ),
    "shell": (
        lambda table: html.div(
            table,
            id="shell",
            style="position: fixed; inset: 0; overflow-y: auto; padding: 16px",
        ),
        "#shell",
    ),
    "dialog": (
        lambda table: Dialog().title("Invoices").size("lg").open().content(table),
        None,
    ),
    "drawer": (
        lambda table: Drawer().title("Invoices").side("end").open().content(table),
        None,
    ),
}


@pytest.mark.parametrize(
    ("frame", "width"),
    [
        ("page", 320),
        ("page", 1280),
        ("card", 390),
        ("panel", 390),
        ("shell", 390),
        ("dialog", 1280),
        ("drawer", 1280),
    ],
)
def test_a_long_tables_bar_is_in_reach(show: Show, frame: str, width: int) -> None:
    wrap, scroller = _FRAMES[frame]
    page = show(wrap(_long()), width=width, height=700)
    _tick_first(page)
    assert page.evaluate(_IN_REACH, scroller)
    assert page.evaluate("document.documentElement.scrollWidth") <= width


def test_the_tables_own_sideways_band_keeps_the_bar_in_reach(show: Show) -> None:
    # A DataTable scrolls its rows sideways itself, which holds the bar no
    # more than the page does.
    page = show(_long(columns=8), width=320, height=700)
    assert page.evaluate(
        "(() => { const band = document.querySelector('#invoices table')"
        ".parentElement; return band.scrollWidth > band.clientWidth })()"
    )
    _tick_first(page)
    assert page.evaluate(_IN_REACH, None)


def test_tab_reaches_the_bars_actions_after_the_rows(show: Show) -> None:
    page = show(_long(3), width=390)
    _tick_first(page)
    names = []
    for _ in range(12):
        page.keyboard.press("Tab")
        names.append(
            page.evaluate(
                "document.activeElement.getAttribute('aria-label')"
                " || document.activeElement.textContent.trim()"
            )
        )
        if names[-1] == "Export":
            break
    assert "Clear selection" in names
    assert (
        names.index("Clear selection") < names.index("Archive") < names.index("Export")
    )


def test_clear_moves_focus_out_of_the_bar_and_empties_the_count(show: Show) -> None:
    page = show(_long(3), width=390)
    _tick_first(page)
    status = page.locator("#invoices [role=status]")
    expect(status).to_have_text("1 selected")
    page.get_by_role("button", name="Clear selection").click()
    expect(page.locator(_BAR)).to_be_hidden()
    expect(status).to_have_text("")
    assert page.evaluate(
        "document.activeElement !== document.body"
        f" && !document.querySelector('{_BAR}').contains(document.activeElement)"
    )


# Whether the overlay drawn from a box overlaps the bar on top of it.
_OVER_THE_BAR = """([bar, overlay]) => {
    const one = document.querySelector(bar).getBoundingClientRect();
    const box = overlay.getBoundingClientRect();
    const y = Math.max(box.top, one.top) + 4;
    const x = Math.max(box.left, one.left) + 4;
    if (y > Math.min(box.bottom, one.bottom)
        || x > Math.min(box.right, one.right)) return 'no overlap';
    return overlay.contains(document.elementFromPoint(x, y))
        ? 'on top' : 'under the bar';
}"""


def test_a_row_menu_opens_over_the_bar(show: Show) -> None:
    page = show(_long(menus=True), width=1280, height=700)
    _tick_first(page)
    # The row whose trigger sits just above the stuck bar.
    bar_top = page.evaluate(
        f"document.querySelector('{_BAR}').getBoundingClientRect().top"
    )
    trigger = page.evaluate(
        """(top) => [...document.querySelectorAll('button')]
            .filter((b) => b.textContent.trim().startsWith('Act on'))
            .filter((b) => b.getBoundingClientRect().bottom < top - 4)
            .at(-1).textContent.trim()""",
        bar_top,
    )
    page.get_by_role("button", name=trigger).click()
    expect(page.get_by_role("menuitem", name="Delete")).to_be_visible()
    menu = page.locator("[role=menu]").locator("visible=true").element_handle()
    assert page.evaluate(_OVER_THE_BAR, [_BAR, menu]) == "on top"


def test_the_filter_panel_opens_over_the_bar(show: Show) -> None:
    # One row, so the panel hangs down over where the bar sits.
    page = show(_long(1, extras=True), width=390, height=800)
    _tick_first(page)
    button = page.locator("#invoices button[aria-haspopup=dialog]").filter(
        has_text="Filter"
    )
    button.click()
    panel = page.locator(f"#{button.get_attribute('aria-controls')}")
    expect(panel).to_be_visible()
    assert page.evaluate(_OVER_THE_BAR, [_BAR, panel.element_handle()]) == "on top"


def test_a_confirmation_covers_the_page_and_escape_steps_back(show: Show) -> None:
    page = show(
        html.header(
            html.a("Home", href="/elsewhere"),
            id="head",
            class_="sticky top-0 z-30 h-14 bg-surface",
        ),
        _long(confirm=True),
        width=390,
        height=700,
    )
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_be_visible()
    # The scrim covers a sticky header and the bar's other buttons.
    for target in ("#head", f"{_BAR} button:last-child"):
        assert page.evaluate(
            "(sel) => { const b = document.querySelector(sel).getBoundingClientRect();"
            " const hit = document.elementFromPoint(b.left + 10, b.top + 10);"
            " return document.querySelector('[role=alertdialog]').parentElement"
            ".contains(hit) }",
            target,
        ), target
    # Once the dialog holds focus, as it does by the time anyone can press a
    # key.
    page.wait_for_function(
        "() => document.activeElement?.closest('[role=alertdialog]') !== null"
    )
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    # The selection outlives the first Escape, focus is back on Delete, and
    # the bar drops back under the page's overlays.
    expect(page.locator(_BAR)).to_be_visible()
    expect(page.locator(_BAR).get_by_role("button", name="Delete")).to_be_focused()
    page.wait_for_function(
        f"getComputedStyle(document.querySelector('{_BAR}')).zIndex === '20'"
    )
    page.keyboard.press("Escape")
    expect(page.locator(_BAR)).to_be_hidden()


def test_the_confirmation_posts_the_picked_rows(show: Show) -> None:
    page = show(_long(3, confirm=True))
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    with page.expect_request(lambda request: request.method == "POST") as sent:
        page.get_by_role("alertdialog").get_by_role("button", name="Delete").click()
    assert "INV-000" in (sent.value.post_data or "")
    expect(page.get_by_role("alertdialog")).to_be_hidden()


@pytest.mark.parametrize("width", [320, 1280])
def test_the_pager_stays_on_one_line_in_the_tables_frame(
    show: Show, width: int
) -> None:
    table = _long(100, page_size=1)
    page = show(html.div(table, class_="-mx-4"), width=width)
    if width == 320:
        coarse(page)
    expect(page.locator("nav[aria-label=Pagination]")).to_be_visible()
    assert page.evaluate(ROWS.replace("'nav'", "'nav[aria-label=Pagination]'")) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


# The last column.


def _three() -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[
                Column("invoice", "Invoice"),
                Column("amount", "Amount"),
                Column("status", "Status"),
            ],
            rows=lambda request, asked: [
                {"invoice": "INV-1", "amount": "1", "status": "paid"}
            ],
            hideable=["invoice", "amount", "status"],
            group_by="status",
        )
    )


def test_the_keyboard_cannot_hide_the_last_column(show: Show) -> None:
    page = show(_three())
    page.get_by_role("button", name="Columns", exact=True).click()
    boxes = [page.get_by_role("checkbox", name=n) for n in ("Invoice", "Amount")]
    for box in boxes:
        box.focus()
        page.keyboard.press("Space")
        expect(box).not_to_be_checked()
    status = page.get_by_role("checkbox", name="Status")
    expect(status).to_be_disabled()
    expect(status).to_be_checked()
    # Focus stays on the box just unticked, not lost to the page.
    expect(boxes[1]).to_be_focused()
    page.keyboard.press("Tab")
    expect(status).not_to_be_focused()
    boxes[0].focus()
    page.keyboard.press("Space")
    expect(status).to_be_enabled()


def test_reset_gives_the_last_box_back(show: Show) -> None:
    page = show(_three())
    page.get_by_role("button", name="Columns", exact=True).click()
    page.get_by_role("checkbox", name="Invoice").uncheck()
    page.get_by_role("checkbox", name="Amount").uncheck()
    expect(page.get_by_role("checkbox", name="Status")).to_be_disabled()
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Reset filters and columns").click()
    page.get_by_role("button", name="Columns", exact=True).click()
    for name in ("Invoice", "Amount", "Status"):
        expect(page.get_by_role("checkbox", name=name)).to_be_enabled()
        expect(page.get_by_role("checkbox", name=name)).to_be_checked()
