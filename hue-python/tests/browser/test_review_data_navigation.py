"""
Review tests for the data and navigation fixes: the selected-rows bar's room,
the empty search, Pagination's narrow row, the swap title, sections opened by
an invalid field or by the contents, and the contents' own column.
"""

import pytest
from htmy import html
from playwright.sync_api import Page, Route, expect

from hue.ui import (
    Accordion,
    AccordionItem,
    Disclosure,
    Pagination,
    Tab,
    TableOfContents,
    Tabs,
    TextInput,
)
from tests.browser.conftest import ORIGIN, Show, render_page
from tests.browser.test_datatable import _table

# The empty search.


def test_a_search_typed_after_an_emptied_one_is_sent(show: Show) -> None:
    # The name comes back after the empty submit, or the next search would
    # go out without its parameter.
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.fill("2050")
    page.wait_for_url("**invoices-q=2050**")
    field.fill("")
    page.wait_for_function("() => !location.search.includes('2050')")
    expect(field).to_have_attribute("name", "invoices-q")
    field.fill("2048")
    page.wait_for_url("**invoices-q=2048**")
    expect(field).to_be_focused()


# Pagination.


def _pager(number: int, total: int = 15, *, siblings: int = 1) -> Pagination:
    return (
        Pagination()
        .id("pages")
        .target("rows")
        .page(number)
        .total_pages(total)
        .sibling_count(siblings)
        .href(lambda n: f"/?page={n}")
    )


def _coarse(page: Page) -> None:
    """
    Turn the page into a touch screen, whose controls are 44px tall.
    """
    session = page.context.new_cdp_session(page)
    session.send("Emulation.setTouchEmulationEnabled", {"enabled": True})
    page.wait_for_function("matchMedia('(pointer: coarse)').matches")


_NAV_ROWS = (
    "new Set([...document.querySelectorAll('nav > *')]"
    ".filter((child) => child.checkVisibility())"
    ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
)


@pytest.mark.parametrize(
    ("width", "number"),
    [
        *[(width, n) for width in (360, 390) for n in (1, 2, 7, 8, 14, 15)],
        # 3 and 13 fill a one-page gap, the widest a narrow row gets.
        *[(320, n) for n in (1, 2, 3, 7, 8, 13, 14, 15)],
    ],
)
def test_a_touch_phone_shows_the_current_page_on_one_line(
    show: Show, width: int, number: int
) -> None:
    # A phone page's usual 16px gutter, rather than the harness's 32px.
    page = show(html.div(_pager(number), class_="-mx-4"), width=width)
    _coarse(page)
    current = page.locator(f"#pages-page-{number}")
    expect(current).to_be_visible()
    expect(current).to_have_attribute("aria-current", "page")
    expect(page.locator("#pages-page-1")).to_be_visible()
    expect(page.locator("#pages-page-15")).to_be_visible()
    assert page.evaluate(_NAV_ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


def test_tab_walks_every_visible_step_and_nothing_hidden(show: Show) -> None:
    page = show(_pager(8), width=320)
    visible = page.evaluate(
        "[...document.querySelectorAll('nav a')]"
        ".filter((a) => a.checkVisibility()).map((a) => a.textContent.trim())"
    )
    page.locator("body").focus()
    reached = []
    for _ in visible:
        page.keyboard.press("Tab")
        reached.append(page.evaluate("document.activeElement.textContent.trim()"))
    assert reached == visible


def test_the_rows_per_page_select_sits_beside_a_one_line_row(show: Show) -> None:
    page = show(
        _pager(8).total_records(148).page_size(10).page_sizes([10, 25]), width=390
    )
    _coarse(page)
    expect(page.get_by_label("Rows per page")).to_have_value("10")
    assert page.evaluate(_NAV_ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


@pytest.mark.parametrize("width", [320, 390, 768, 1280])
def test_a_tables_own_pager_stays_on_one_line_in_its_card(
    show: Show, width: int
) -> None:
    page = show(_table("invoices"), width=width)
    _coarse(page)
    pager = page.locator("nav[aria-label='Pagination']")
    expect(pager).to_be_visible()
    rows = page.evaluate(
        "new Set([...document.querySelectorAll('nav[aria-label=Pagination] > *')]"
        ".filter((child) => child.checkVisibility())"
        ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
    )
    assert rows == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width
    expect(page.locator("#invoices-rows-pagination-page-1")).to_have_attribute(
        "aria-current", "page"
    )


# The swap title.


def _rows(number: int) -> tuple[object, ...]:
    return (html.div(f"Rows of page {number}", id="rows"), _pager(number, 3))


def _serve(page: Page, title: str | None) -> None:
    def fulfil(route: Route) -> None:
        number = int(route.request.url.split("page=")[1])
        document = render_page(*_rows(number))  # type: ignore[arg-type]
        if title is None:
            document = document.replace("<title>Test</title>", "", 1)
        else:
            document = document.replace(">Test</title>", f">{title}</title>", 1)
        route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/?page=*", fulfil)


def test_a_response_with_no_title_leaves_the_title(show: Show) -> None:
    page = show(*_rows(1))
    _serve(page, None)
    page.locator("#pages-page-2").click()
    expect(page.locator("#rows")).to_have_text("Rows of page 2")
    expect(page).to_have_url(f"{ORIGIN}/?page=2")
    assert page.title() == "Test"


def test_a_swap_that_does_not_move_the_address_keeps_the_title(show: Show) -> None:
    page = show(
        html.form(
            html.input_(type="hidden", name="page", value="2"),
            html.button("Refresh", type="submit"),
            id="refresh",
            action="/",
            method="get",
            **{"x-target": "rows"},
        ),
        *_rows(1),
    )
    _serve(page, "Elsewhere")
    page.get_by_role("button", name="Refresh").click()
    expect(page.locator("#rows")).to_have_text("Rows of page 2")
    expect(page).to_have_url(f"{ORIGIN}/")
    assert page.title() == "Test"


def test_a_title_with_markup_characters_is_taken_as_text(show: Show) -> None:
    page = show(*_rows(1))
    _serve(page, "Q&amp;A &lt;2&gt;")
    page.locator("#pages-page-2").click()
    expect(page).to_have_title("Q&A <2>")


def test_a_tab_swap_takes_its_pages_title_and_back_its_own(show: Show) -> None:
    page = show(
        Tabs()
        .id("tabs")
        .label("Sections")
        .target("content")
        .current("/")
        .content(Tab().href("/").content("One"), Tab().href("/two").content("Two")),
        html.div("One", id="content"),
    )
    document = render_page(
        Tabs()
        .id("tabs")
        .label("Sections")
        .target("content")
        .current("/two")
        .content(Tab().href("/").content("One"), Tab().href("/two").content("Two")),
        html.div("Two", id="content"),
    ).replace(">Test</title>", ">Two</title>", 1)
    page.route(
        f"{ORIGIN}/two",
        lambda route: route.fulfill(body=document, content_type="text/html"),
    )
    page.get_by_role("link", name="Two").click()
    expect(page.locator("#content")).to_have_text("Two")
    expect(page).to_have_title("Two")
    page.go_back()
    expect(page.locator("#content")).to_have_text("One")
    expect(page).to_have_title("Test")


# Sections opened by an invalid field.


def _form(*parts: object, novalidate: bool = False) -> object:
    return html.form(
        *parts,
        html.button("Save", type="submit"),
        action="/saved",
        method="get",
        novalidate=novalidate or None,
    )


def _saved(page: Page) -> list[str]:
    sent: list[str] = []

    def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
        sent.append(request.url)
        route.fulfill(body="<title>Saved</title>", content_type="text/html")

    page.route(f"{ORIGIN}/saved*", fulfil)
    return sent


def _field(name: str) -> TextInput:
    return TextInput().name(name).label(name.title()).required()


def test_a_novalidate_form_leaves_its_sections_closed(show: Show) -> None:
    page = show(
        _form(
            Disclosure().title("General").closed().content(_field("name")),
            Accordion().content(
                AccordionItem().title("Billing").open().content("Open"),
                AccordionItem().title("Plans").content(_field("plan")),
            ),
            novalidate=True,
        )
    )
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    expect(page).to_have_title("Saved")
    assert len(sent) == 1


def test_multiple_opens_every_invalid_section_and_focuses_the_first(
    show: Show,
) -> None:
    page = show(
        _form(
            Accordion()
            .multiple()
            .content(
                AccordionItem().title("Billing").content(_field("card")),
                AccordionItem().title("Plans").content(_field("plan")),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Card")).to_be_focused()
    expect(page.get_by_role("textbox", name="Plan")).to_be_visible()
    for name in ("Billing", "Plans"):
        expect(page.get_by_role("button", name=name)).to_have_attribute(
            "aria-expanded", "true"
        )


def test_a_disclosure_in_a_closed_accordion_section_opens_both(show: Show) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").open().content("Open"),
                AccordionItem()
                .title("Plans")
                .content(
                    Disclosure().title("Advanced").closed().content(_field("plan"))
                ),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    plan = page.get_by_role("textbox", name="Plan")
    expect(plan).to_be_focused()
    expect(plan).to_be_visible()
    expect(page.get_by_role("button", name="Advanced")).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.get_by_text("Open", exact=True)).to_be_hidden()


def test_an_invalid_field_in_the_open_section_keeps_it_open(show: Show) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").open().content(_field("card")),
                AccordionItem().title("Plans").content(_field("plan")),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    card = page.get_by_role("textbox", name="Card")
    expect(card).to_be_focused()
    expect(card).to_be_visible()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_a_second_submit_reports_the_next_section(show: Show) -> None:
    # The first is filled in, and the one-at-a-time guard has reset, so the
    # next submit opens the other section.
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").content(_field("card")),
                AccordionItem().title("Plans").content(_field("plan")),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    card = page.get_by_role("textbox", name="Card")
    expect(card).to_be_focused()
    card.fill("4242")
    page.get_by_role("button", name="Save").click()
    plan = page.get_by_role("textbox", name="Plan")
    expect(plan).to_be_focused()
    expect(plan).to_be_visible()


def test_an_open_disclosure_still_focuses_its_invalid_field(show: Show) -> None:
    page = show(_form(Disclosure().title("General").content(_field("name"))))
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Name")).to_be_focused()


def test_two_accordions_each_open_their_own_section(show: Show) -> None:
    # The one-at-a-time guard belongs to each accordion, so the second
    # accordion's invalid section still opens.
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").content(_field("card")),
            ),
            Accordion().content(
                AccordionItem().title("Plans").content(_field("plan")),
            ),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Card")).to_be_focused()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "true"
    )


# The contents and folded sections.


def _entry(page: Page, name: str):  # type: ignore[no-untyped-def]
    return page.get_by_role("navigation").get_by_role("link", name=name)


def test_following_into_one_section_leaves_the_others_closed(show: Show) -> None:
    page = show(
        html.div(
            TableOfContents().of("#doc"),
            style="position: fixed; top: 0; right: 0; width: 200px",
        ),
        html.div(
            Disclosure()
            .title("One")
            .closed()
            .content(html.h2("First", id="first"), html.p("First text")),
            Disclosure()
            .title("Two")
            .closed()
            .content(html.h2("Second", id="second"), html.p("Second text")),
            html.div(style="height: 2000px"),
            id="doc",
        ),
    )
    _entry(page, "Second").click()
    expect(page.get_by_text("Second text")).to_be_visible()
    expect(page.get_by_text("First text")).to_be_hidden()
    expect(page.locator("#second")).to_be_focused()


def test_an_entry_in_an_open_section_is_followed_as_before(show: Show) -> None:
    page = show(
        html.div(
            TableOfContents().of("#doc"),
            style="position: fixed; top: 0; right: 0; width: 200px",
        ),
        html.div(
            html.div(style="height: 600px"),
            Disclosure()
            .title("One")
            .content(html.h2("Inside", id="inside"), html.p("Inside text")),
            html.div(style="height: 2000px"),
            id="doc",
        ),
    )
    _entry(page, "Inside").click()
    expect(page.locator("#inside")).to_be_focused()
    expect(_entry(page, "Inside")).to_have_attribute("aria-current", "location")
    assert page.evaluate("location.hash") == "#inside"
    page.wait_for_function(
        "() => Math.abs(document.getElementById('inside')"
        ".getBoundingClientRect().top) < 2"
    )


def test_contents_inside_the_scroller_they_list_never_scroll_it_themselves(
    show: Show,
) -> None:
    # The contents share the headings' scroller: keepInView must leave it
    # to the reader, and the page must not move.
    page = show(
        html.div(
            html.div(
                TableOfContents().of("#doc"),
                style="position: sticky; top: 0; float: right; width: 200px;",
            ),
            *[
                html.section(html.h2(f"Part {n:02}"), html.div(style="height: 400px"))
                for n in range(1, 13)
            ],
            id="doc",
            style="height: 400px; overflow-y: auto",
        ),
        html.div(style="height: 2000px"),
        width=1000,
        height=600,
    )
    page.evaluate("document.getElementById('doc').scrollTop = 1700")
    expect(_entry(page, "Part 05")).to_have_attribute("aria-current", "location")
    assert page.evaluate("document.getElementById('doc').scrollTop") == 1700
    assert page.evaluate("window.scrollY") == 0


def _two_frames(page: Page) -> None:
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )


def test_page_back_and_forward_file_nothing_for_a_page_scroll(show: Show) -> None:
    # A page-level contents has no container, so a page scroll coming to
    # rest files nothing on the entry, and Back still lands on the heading.
    page = show(
        html.div(
            TableOfContents().of("#doc"),
            style="position: fixed; top: 0; right: 0; width: 200px",
        ),
        html.div(
            *[
                html.section(
                    html.h2(name, id=name.lower()), html.div(style="height: 900px")
                )
                for name in ("Alpha", "Beta", "Gamma")
            ],
            id="doc",
        ),
        height=600,
    )
    _entry(page, "Beta").click()
    expect(page).to_have_url(f"{ORIGIN}/#beta")
    page.evaluate(
        "new Promise((r) => { addEventListener('scrollend', r, { once: true });"
        " scrollTo(0, 1500) })"
    )
    assert page.evaluate("history.state") is None
    _entry(page, "Gamma").click()
    expect(page).to_have_url(f"{ORIGIN}/#gamma")
    page.go_back()
    expect(page).to_have_url(f"{ORIGIN}/#beta")
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")
    page.go_forward()
    expect(page).to_have_url(f"{ORIGIN}/#gamma")
    expect(_entry(page, "Gamma")).to_have_attribute("aria-current", "location")


def test_a_field_reported_outside_the_accordion_leaves_its_open_section(
    show: Show,
) -> None:
    # The browser reports the name above the accordion, so nothing in the
    # accordion is shown to the reader, and the section they had open stays.
    page = show(
        html.form(
            TextInput().name("name").label("Name").required(),
            Accordion().content(
                AccordionItem().title("Billing").open().content("Billing text"),
                AccordionItem()
                .title("Plans")
                .content(TextInput().name("plan").label("Plan").required()),
            ),
            html.button("Save", type="submit"),
            action="/saved",
            method="get",
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Name")).to_be_focused()
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )
    assert (
        page.get_by_role("button", name="Plans").get_attribute("aria-expanded")
        == "false"
    )
    assert page.get_by_text("Billing text").is_visible()
