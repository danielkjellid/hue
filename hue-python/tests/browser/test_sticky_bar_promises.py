"""
Review tests for the sticky selected-rows bar, the raised Pagination step
and the Accordion that hears the reported field on the document.
"""

from typing import Any

import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.datatable import BulkAction, Filter, build_datatable_state
from hue.js import unsafe
from hue.ui import (
    Accordion,
    AccordionItem,
    Button,
    Card,
    CardBody,
    Column,
    DataTable,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    TextInput,
)
from tests.browser.conftest import Show
from tests.browser.test_data_navigation_promises import _coarse, _form, _pager
from tests.browser.test_datatable import _Router

_BAR = '[aria-label="Selected rows"]'


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
    key: str = "invoices",
    menus: bool = False,
    extras: bool = False,
) -> DataTable:
    columns = [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
    if menus:
        columns.append(Column("actions", "Actions", render=_menu))
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key=key,
            columns=columns,
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", "amount": str(n)} for n in range(rows)
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
                "archive": BulkAction("Archive", lambda request, ids: None),
                "export": BulkAction("Export", lambda request, ids: None),
            },
            page_size=rows,
        )
    )


def _tick_first(page: Page, key: str = "invoices") -> None:
    page.locator(f"#{key}").get_by_role("checkbox", name="Select INV-000").check()
    bar = page.locator(f"#{key} {_BAR}")
    expect(bar).to_be_visible()
    page.wait_for_function(
        f"() => getComputedStyle(document.querySelector('#{key} {_BAR}'))"
        ".transform === 'none'"
    )


# Whether the bar is in reach: inside the window and the box it scrolls in,
# and on top at its middle.
_IN_REACH = """(scroller) => {
    const bar = document.querySelector('#invoices [aria-label="Selected rows"]');
    const box = bar.getBoundingClientRect();
    const port = scroller
        ? document.querySelector(scroller).getBoundingClientRect()
        : { top: 0, bottom: innerHeight };
    const bottom = Math.min(port.bottom, innerHeight);
    if (box.top < Math.max(port.top, 0) || box.bottom > bottom) return false;
    const hit = document.elementFromPoint(box.left + 12, box.top + box.height / 2);
    return bar.contains(hit);
}"""


def _in_reach(page: Page, scroller: str | None = None) -> bool:
    return page.evaluate(_IN_REACH, scroller)


@pytest.mark.parametrize("width", [320, 390, 768, 1280])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_a_long_tables_bar_is_in_reach_from_the_top(
    show: Show, width: int, theme: str
) -> None:
    page = show(_long(), width=width, height=700, theme=theme)
    _tick_first(page)
    assert _in_reach(page)
    assert page.evaluate("document.documentElement.scrollWidth") <= width


def test_a_long_tables_bar_is_in_reach_in_a_card(show: Show) -> None:
    page = show(Card().content(CardBody().content(_long())), width=390, height=700)
    _tick_first(page)
    assert _in_reach(page)


def test_the_tables_own_sideways_band_keeps_the_bar_in_reach(show: Show) -> None:
    # A DataTable scrolls its rows sideways itself, which holds the bar no
    # more than the page does. A wrapper of the caller's own that sets
    # overflow would, which the docstring warns against.
    columns = [
        Column("invoice", "Invoice"),
        *[Column(f"c{n}", f"Column {n}") for n in range(8)],
    ]
    table = DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=columns,
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", **{f"c{c}": "wide value" for c in range(8)}}
                for n in range(40)
            ],
            identifier="invoice",
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
            page_size=40,
        )
    )
    page = show(table, width=320, height=700)
    assert page.evaluate(
        "(() => { const band = document.querySelector('#invoices table')"
        ".parentElement; return band.scrollWidth > band.clientWidth })()"
    )
    _tick_first(page)
    assert _in_reach(page)


def test_a_long_tables_bar_is_in_reach_in_an_app_shell(show: Show) -> None:
    page = show(
        html.div(
            _long(),
            id="shell",
            style="position: fixed; inset: 0; overflow-y: auto; padding: 16px",
        ),
        width=390,
        height=700,
    )
    _tick_first(page)
    assert _in_reach(page, "#shell")


def test_a_long_tables_bar_is_in_reach_in_a_dialog(show: Show) -> None:
    page = show(
        Dialog().title("Invoices").size("lg").open().content(_long()),
        width=1280,
        height=700,
    )
    expect(page.get_by_role("dialog")).to_be_visible()
    _tick_first(page)
    page.wait_for_function("(s) => !!document.querySelector(s)", arg=_BAR)
    assert _in_reach(page)


def test_a_long_tables_bar_is_in_reach_in_a_drawer(show: Show) -> None:
    page = show(
        Drawer().title("Invoices").side("end").open().content(_long()),
        width=1280,
        height=700,
    )
    expect(page.get_by_role("dialog")).to_be_visible()
    _tick_first(page)
    assert _in_reach(page)


def test_a_short_table_shows_its_bar_under_the_pager(show: Show) -> None:
    page = show(_long(3), width=390, height=800)
    _tick_first(page)
    assert _in_reach(page)
    assert page.evaluate(
        "document.querySelector('#invoices-rows').getBoundingClientRect().bottom"
        f" <= document.querySelector('#invoices {_BAR}').getBoundingClientRect().top"
    )


def test_a_second_table_takes_the_selection_and_its_own_bar(show: Show) -> None:
    page = show(_long(3, key="first"), _long(3, key="second"), width=390)
    _tick_first(page, "first")
    _tick_first(page, "second")
    expect(page.locator(f"#first {_BAR}")).to_be_hidden()
    expect(page.locator(f"#second {_BAR}")).to_contain_text("1 selected")


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
    expect(page.locator(f"#invoices {_BAR}")).to_be_hidden()
    expect(status).to_have_text("")
    assert page.evaluate(
        "document.activeElement !== document.body"
        f" && !document.querySelector('#invoices {_BAR}')"
        ".contains(document.activeElement)"
    )


def test_escape_from_an_action_clears_and_keeps_focus_on_the_page(show: Show) -> None:
    page = show(_long(3), width=390)
    _tick_first(page)
    page.get_by_role("button", name="Archive").focus()
    page.keyboard.press("Escape")
    expect(page.locator(f"#invoices {_BAR}")).to_be_hidden()
    assert page.evaluate("document.activeElement !== document.body")


def test_a_row_menu_opens_over_the_bar(show: Show) -> None:
    page = show(_long(menus=True), width=1280, height=700)
    _tick_first(page)
    # The row whose trigger sits just above the stuck bar.
    bar_top = page.evaluate(
        f"document.querySelector('#invoices {_BAR}').getBoundingClientRect().top"
    )
    trigger = page.evaluate(
        """(top) => [...document.querySelectorAll('button')]
            .filter((b) => b.textContent.trim().startsWith('Act on'))
            .filter((b) => b.getBoundingClientRect().bottom < top - 4)
            .at(-1).textContent.trim()""",
        bar_top,
    )
    page.get_by_role("button", name=trigger).click()
    item = page.get_by_role("menuitem", name="Delete")
    expect(item).to_be_visible()
    covered = page.evaluate(
        f"""() => {{
            const bar = document.querySelector('#invoices {_BAR}')
                .getBoundingClientRect();
            const menu = [...document.querySelectorAll('[role=menu]')]
                .find((m) => m.checkVisibility());
            const box = menu.getBoundingClientRect();
            const y = Math.max(box.top, bar.top) + 4;
            if (y > Math.min(box.bottom, bar.bottom)) return 'no overlap';
            return menu.contains(document.elementFromPoint(box.left + 8, y))
                ? 'menu on top' : 'menu under the bar';
        }}"""
    )
    assert covered == "menu on top"


def _overlaps_on_top(page: Page, trigger: str) -> str:
    button = page.locator("#invoices button[aria-haspopup=dialog]").filter(
        has_text=trigger
    )
    button.click()
    panel_id = button.get_attribute("aria-controls")
    expect(page.locator(f"#{panel_id}")).to_be_visible()
    return page.evaluate(
        """([bar, id]) => {
            const box1 = document.querySelector(bar).getBoundingClientRect();
            const panel = document.getElementById(id);
            const box = panel.getBoundingClientRect();
            const y = Math.max(box.top, box1.top) + 4;
            const x = Math.max(box.left, box1.left) + 4;
            if (y > Math.min(box.bottom, box1.bottom)
                || x > Math.min(box.right, box1.right)) return 'no overlap';
            return panel.contains(document.elementFromPoint(x, y))
                ? 'on top' : 'under the bar';
        }""",
        [f"#invoices {_BAR}", panel_id],
    )


def test_the_filter_panel_opens_over_the_bar(show: Show) -> None:
    # One row, so the panel hangs down over where the bar sits.
    page = show(_long(1, extras=True), width=390, height=800)
    _tick_first(page)
    assert _overlaps_on_top(page, "Filter") == "on top"


# Pagination's raised step.


def test_tab_walks_the_narrow_row_in_order(show: Show) -> None:
    page = show(html.div(_pager(8), class_="-mx-4"), width=320)
    _coarse(page)
    visible = page.evaluate(
        "[...document.querySelectorAll('nav a')]"
        ".filter((a) => a.checkVisibility()).map((a) => a.id || a.textContent)"
    )
    page.locator("body").focus()
    reached = []
    for _ in visible:
        page.keyboard.press("Tab")
        reached.append(
            page.evaluate(
                "document.activeElement.id || document.activeElement.textContent"
            )
        )
        assert page.evaluate("getComputedStyle(document.activeElement).zIndex") == "10"
    assert reached == visible


# The Accordion that hears the reported field on the document.


def _plans() -> Accordion:
    return Accordion().content(
        AccordionItem()
        .title("Billing")
        .open()
        .content(TextInput().name("card").label("Card")),
        AccordionItem()
        .title("Plans")
        .content(TextInput().name("plan").label("Plan").required()),
    )


def test_two_accordions_on_a_page_each_hear_their_own_field(show: Show) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem()
                .title("Billing")
                .content(TextInput().name("card").label("Card").required())
            ),
            Accordion().content(
                AccordionItem().title("Notes").open().content("Notes text"),
                AccordionItem()
                .title("Plans")
                .content(TextInput().name("plan").label("Plan").required()),
            ),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Card")).to_be_focused()
    expect(page.get_by_text("Notes text")).to_be_visible()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_an_invalid_field_in_another_form_does_not_open_a_section(
    show: Show,
) -> None:
    page = show(
        html.form(TextInput().name("q").label("Search").required(), id="other"),
        _form(_plans()),
    )
    page.evaluate("document.getElementById('other').reportValidity()")
    expect(page.get_by_role("textbox", name="Search")).to_be_focused()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Plan")).to_be_focused()


def test_a_removed_accordion_leaves_no_listener_behind(show: Show) -> None:
    page = show(
        html.div(_form(_plans()), id="region"), TextInput().name("x").label("X")
    )
    page.evaluate("document.getElementById('region').remove()")
    page.evaluate(
        "(() => { const i = document.createElement('input'); i.required = true;"
        " document.body.append(i); i.checkValidity(); })()"
    )


def test_checking_validity_while_typing_leaves_the_open_section(show: Show) -> None:
    # A form that enables Save as it becomes valid checks itself on every
    # keystroke. Nothing is reported, so nothing the reader has open closes.
    page = show(
        _form(
            Accordion().content(
                AccordionItem()
                .title("Billing")
                .open()
                .content(
                    TextInput()
                    .name("card")
                    .label("Card")
                    .x_on("input", unsafe("$el.form.checkValidity()"))
                ),
                AccordionItem()
                .title("Plans")
                .content(TextInput().name("plan").label("Plan").required()),
            )
        )
    )
    card = page.get_by_role("textbox", name="Card")
    card.press_sequentially("42")
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )
    assert card.is_visible()
    assert page.evaluate("document.activeElement.name") == "card"
    assert (
        page.get_by_role("button", name="Plans").get_attribute("aria-expanded")
        == "false"
    )
