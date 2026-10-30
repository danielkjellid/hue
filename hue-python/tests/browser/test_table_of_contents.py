from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Accordion, AccordionItem, Disclosure, TableOfContents
from tests.browser.conftest import Show

NAMES = ("Alpha", "Beta", "Gamma")


def _sections() -> list[html.section]:
    return [
        html.section(html.h2(name, id=name.lower()), html.div(style="height: 600px"))
        for name in NAMES
    ]


def _in_container(*, below: int = 0) -> tuple[object, ...]:
    """
    Contents for a panel that scrolls, with page height to spare so a page
    scroll would show, and below pixels of page above the panel.
    """
    return (
        TableOfContents().of("#doc"),
        html.div(style=f"height: {below}px"),
        html.div(
            html.p("Intro", style="height: 200px"),
            *_sections(),
            id="doc",
            style="height: 300px; overflow-y: auto",
        ),
        html.div(style="height: 2000px"),
    )


def _entry(page: Page, name: str):  # type: ignore[no-untyped-def]
    return page.get_by_role("navigation").get_by_role("link", name=name)


def _heading_top(page: Page, name: str) -> float:
    """
    How far a heading sits below the top of the panel it scrolls in.
    """
    return page.evaluate(
        "(id) => document.getElementById(id).getBoundingClientRect().top"
        " - document.getElementById('doc').getBoundingClientRect().top",
        name.lower(),
    )


def _doc_scroll(page: Page) -> float:
    return page.evaluate("document.getElementById('doc').scrollTop")


def test_click_scrolls_only_the_container(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Beta").click()
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")
    assert abs(_heading_top(page, "Beta")) < 2
    assert page.evaluate("window.scrollY") == 0


def test_click_focuses_the_heading(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Beta").click()
    expect(page.locator("#beta")).to_be_focused()


def test_back_retraces_each_click_in_a_container(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Alpha").click()
    _entry(page, "Beta").click()
    page.go_back()
    expect(_entry(page, "Alpha")).to_have_attribute("aria-current", "location")
    page.wait_for_function(
        "() => Math.abs(document.getElementById('alpha').getBoundingClientRect().top"
        " - document.getElementById('doc').getBoundingClientRect().top) < 2"
    )


def test_back_restores_a_container_scrolled_by_hand(show: Show) -> None:
    page = show(*_in_container())
    page.evaluate("document.getElementById('doc').scrollTop = 150")
    _entry(page, "Beta").click()
    page.go_back()
    page.wait_for_function("document.getElementById('doc').scrollTop === 150")


def test_back_restores_a_hand_scroll_over_the_fragment(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Alpha").click()
    # Somewhere the fragment #alpha does not point at.
    page.evaluate("document.getElementById('doc').scrollTop = 450")
    _entry(page, "Beta").click()
    page.go_back()
    expect(page).to_have_url("http://hue.test/#alpha")
    # Two frames, so a fragment scroll the browser runs late has had its turn.
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )
    assert _doc_scroll(page) == 450


def test_click_brings_an_out_of_view_container_into_view(show: Show) -> None:
    page = show(*_in_container(below=1500))
    _entry(page, "Beta").click()
    box = page.locator("#doc").bounding_box()
    assert box is not None
    assert 0 <= box["y"] and box["y"] + box["height"] <= 800


def test_page_back_and_forward_retrace_each_click(show: Show) -> None:
    page = show(TableOfContents(), *_sections())
    _entry(page, "Alpha").click()
    _entry(page, "Beta").click()
    page.go_back()
    expect(_entry(page, "Alpha")).to_have_attribute("aria-current", "location")
    page.go_forward()
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")


def test_nothing_to_scroll_marks_the_first_then_the_clicked(show: Show) -> None:
    page = show(TableOfContents(), *(html.h2(name, id=name.lower()) for name in NAMES))
    expect(_entry(page, "Alpha")).to_have_attribute("aria-current", "location")
    _entry(page, "Beta").click()
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")


def test_forward_in_a_container_returns_to_the_later_click(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Alpha").click()
    _entry(page, "Beta").click()
    page.go_back()
    expect(_entry(page, "Alpha")).to_have_attribute("aria-current", "location")
    page.go_forward()
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")
    page.wait_for_function(
        "() => Math.abs(document.getElementById('beta').getBoundingClientRect().top"
        " - document.getElementById('doc').getBoundingClientRect().top) < 2"
    )


def _folded(section: object) -> tuple[object, ...]:
    # The contents stay put, so clicking an entry never scrolls the page to
    # reach it and moves the mark on its own.
    return (
        html.div(
            TableOfContents().of("#doc"),
            style="position: fixed; top: 0; right: 0; width: 200px",
        ),
        html.div(
            *_sections(),
            section,
            html.div(style="height: 2000px"),
            id="doc",
        ),
    )


def _follows_into(page: Page, opened: str) -> None:
    _entry(page, "Hidden").click()
    expect(page.locator(opened)).to_be_visible()
    heading = page.locator("#hidden")
    expect(heading).to_be_focused()
    expect(_entry(page, "Hidden")).to_have_attribute("aria-current", "location")
    assert page.evaluate("location.hash") == "#hidden"
    page.wait_for_function(
        "() => Math.abs("
        "document.getElementById('hidden').getBoundingClientRect().top) < 2"
    )


def test_following_an_entry_in_a_closed_disclosure_opens_it(show: Show) -> None:
    page = show(
        *_folded(
            Disclosure()
            .title("More")
            .closed()
            .content(html.h2("Hidden", id="hidden"), html.p("Folded text"))
        )
    )
    _follows_into(page, "text=Folded text")


def test_following_an_entry_in_a_closed_accordion_item_opens_it(show: Show) -> None:
    # Opening it closes the open section above it, which moves the heading
    # after the click; the scroll lands where the heading ends up.
    page = show(
        *_folded(
            Accordion().content(
                AccordionItem()
                .title("First")
                .open()
                .content(html.div("Open text", style="height: 400px")),
                AccordionItem()
                .title("Second")
                .content(html.h2("Hidden", id="hidden"), html.p("Folded text")),
            )
        )
    )
    _follows_into(page, "text=Folded text")
    expect(page.get_by_text("Open text")).to_be_hidden()


def test_a_heading_nothing_opens_is_not_marked(show: Show) -> None:
    page = show(*_folded(html.div(html.h2("Hidden", id="hidden"), hidden=True)))
    _entry(page, "Beta").click()
    _entry(page, "Hidden").click()
    expect(_entry(page, "Beta")).to_have_attribute("aria-current", "location")
    assert page.evaluate("location.hash") == "#beta"


def _long_page() -> tuple[object, ...]:
    """
    Twelve sections, and contents in a fixed column too short to show
    every entry, which scrolls on its own.
    """
    return (
        html.div(
            TableOfContents().of("#doc"),
            id="column",
            style="position: fixed; top: 0; right: 0; width: 200px;"
            " max-height: 120px; overflow-y: auto",
        ),
        html.div(
            *[
                html.section(html.h2(f"Part {n:02}"), html.div(style="height: 400px"))
                for n in range(1, 13)
            ],
            id="doc",
            style="margin-right: 220px",
        ),
    )


def _in_column(page: Page, name: str) -> bool:
    return page.evaluate(
        """(name) => {
            const column = document.getElementById('column').getBoundingClientRect();
            const link = [...document.querySelectorAll('#column a')]
                .find((a) => a.textContent.trim() === name).getBoundingClientRect();
            return link.top >= column.top - 1 && link.bottom <= column.bottom + 1;
        }""",
        name,
    )


def test_the_active_entry_stays_inside_a_scrolling_column(show: Show) -> None:
    page = show(*_long_page(), width=1000, height=600)
    end = page.evaluate("document.documentElement.scrollHeight - innerHeight")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    expect(_entry(page, "Part 12")).to_have_attribute("aria-current", "location")
    page.wait_for_function(
        "() => document.querySelector('#column a[aria-current]')"
        ".getBoundingClientRect().bottom"
        " <= document.getElementById('column').getBoundingClientRect().bottom + 1"
    )
    assert _in_column(page, "Part 12")
    # The column scrolled, and the page stayed where the reader put it.
    assert page.evaluate("window.scrollY") == end
    page.evaluate("window.scrollTo(0, 0)")
    expect(_entry(page, "Part 01")).to_have_attribute("aria-current", "location")
    page.wait_for_function("() => document.getElementById('column').scrollTop === 0")


def _two_frames(page: Page) -> None:
    # So a fragment scroll the browser runs late has had its turn.
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )


def test_back_across_a_plain_fragment_link_restores_a_hand_scroll(show: Show) -> None:
    page = show(html.a("To gamma", href="#gamma"), *_in_container())
    _entry(page, "Alpha").click()
    page.evaluate("document.getElementById('doc').scrollTop = 500")
    page.wait_for_function("history.state?.hueTocScroll === 500")
    page.get_by_role("link", name="To gamma").click()
    expect(page).to_have_url("http://hue.test/#gamma")
    page.go_back()
    expect(page).to_have_url("http://hue.test/#alpha")
    _two_frames(page)
    assert _doc_scroll(page) == 500


def test_forward_restores_a_hand_scroll(show: Show) -> None:
    page = show(*_in_container())
    _entry(page, "Alpha").click()
    _entry(page, "Beta").click()
    page.evaluate("document.getElementById('doc').scrollTop = 1000")
    page.wait_for_function("history.state?.hueTocScroll === 1000")
    page.go_back()
    expect(page).to_have_url("http://hue.test/#alpha")
    page.go_forward()
    expect(page).to_have_url("http://hue.test/#beta")
    _two_frames(page)
    assert _doc_scroll(page) == 1000
