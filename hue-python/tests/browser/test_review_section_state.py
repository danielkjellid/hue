from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Accordion, AccordionItem, Disclosure, TableOfContents, TextInput
from tests.browser.conftest import Show

# A caller's state around a section, under the names hue's own state used to
# have, and markup inside the section that reads and calls them.
_CALLER = (
    "{ open: 'caller-open', single: 'caller-single', shown: 'caller-shown', "
    "submitting: 'caller-submitting', called: 'no', "
    "toggle() { this.called = 'yes' } }"
)


def _reads_caller_state() -> tuple[object, ...]:
    return (
        html.span(
            id="read",
            **{"x-text": "[open, single, shown, submitting].join(' ')"},
        ),
        html.button("Call toggle", type="button", **{"x-on:click": "toggle()"}),
        html.span(id="called", **{"x-text": "called"}),
    )


def _check_caller_state(page: Page, region: str) -> None:
    expect(page.locator("#read")).to_have_text(
        "caller-open caller-single caller-shown caller-submitting"
    )
    page.get_by_role("button", name="Call toggle").click()
    expect(page.locator("#called")).to_have_text("yes")
    expect(page.get_by_role("region", name=region)).to_be_visible()


def test_a_disclosure_leaves_the_callers_names_to_the_caller(show: Show) -> None:
    page = show(
        html.div(
            Disclosure().title("Details").content(*_reads_caller_state()),
            **{"x-data": _CALLER},
        )
    )
    _check_caller_state(page, "Details")


def test_an_accordion_leaves_the_callers_names_to_the_caller(show: Show) -> None:
    page = show(
        html.div(
            Accordion().content(
                AccordionItem().title("One").open().content(*_reads_caller_state()),
                AccordionItem().title("Two").content("Second"),
            ),
            **{"x-data": _CALLER},
        )
    )
    _check_caller_state(page, "One")


def _own_widget() -> object:
    # A caller's own toggle inside a panel, under the names hue's state used.
    return html.div(
        html.button("More", type="button", **{"x-on:click": "open = !open"}),
        html.p("Widget body", **{"x-show": "open"}),
        **{"x-data": "{ open: false, shown: false, toggle() {} }"},
    )


def test_a_callers_own_toggle_inside_a_section_is_its_own(show: Show) -> None:
    page = show(
        Disclosure().title("Details").content(_own_widget()),
        Accordion().content(AccordionItem().title("One").open().content(_own_widget())),
    )
    for nth in (0, 1):
        page.get_by_role("button", name="More").nth(nth).click()
        expect(page.get_by_text("Widget body").nth(nth)).to_be_visible()
    for name in ("Details", "One"):
        trigger = page.get_by_role("button", name=name)
        trigger.click()
        expect(trigger).to_have_attribute("aria-expanded", "false")
        expect(trigger).to_be_focused()
        trigger.click()
        expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_text("Widget body")).to_have_count(2)
    for nth in (0, 1):
        expect(page.get_by_text("Widget body").nth(nth)).to_be_visible()


def test_a_disclosure_in_an_accordion_item_keeps_its_own_state(show: Show) -> None:
    page = show(
        Accordion().content(
            AccordionItem()
            .title("Outer")
            .open()
            .content(Disclosure().title("Inner").content("Inner body")),
            AccordionItem().title("Other").content("Other body"),
        )
    )
    inner = page.get_by_role("button", name="Inner")
    inner.click()
    expect(inner).to_have_attribute("aria-expanded", "false")
    expect(page.get_by_role("button", name="Outer")).to_have_attribute(
        "aria-expanded", "true"
    )
    page.get_by_role("button", name="Other").press("Enter")
    expect(page.get_by_text("Other body")).to_be_visible()
    page.get_by_role("button", name="Outer").press("Space")
    expect(inner).to_be_visible()
    expect(inner).to_have_attribute("aria-expanded", "false")
    inner.press("Enter")
    expect(page.get_by_text("Inner body")).to_be_visible()


def test_a_field_in_a_disclosure_in_a_closed_accordion_item_opens_both(
    show: Show,
) -> None:
    deep = TextInput().name("deep").label("Deep").required()
    page = show(
        html.form(
            Accordion().content(
                AccordionItem().title("First").open().content("x"),
                AccordionItem()
                .title("Second")
                .content(Disclosure().title("Inner").closed().content(deep)),
            ),
            html.button("Save", type="submit"),
            action="/saved",
            method="get",
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Deep")).to_be_focused()
    expect(page.get_by_role("button", name="Second")).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.get_by_role("button", name="Inner")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_checking_validity_while_typing_leaves_an_accordion_item_closed(
    show: Show,
) -> None:
    page = show(
        html.form(
            Accordion().content(
                AccordionItem()
                .title("First")
                .open()
                .content(TextInput().name("a").label("A")),
                AccordionItem()
                .title("Second")
                .content(TextInput().name("b").label("B").required()),
            ),
        )
    )
    page.get_by_role("textbox", name="A").fill("typed")
    page.evaluate("document.querySelector('form').checkValidity()")
    expect(page.get_by_role("button", name="Second")).to_have_attribute(
        "aria-expanded", "false"
    )
    expect(page.get_by_role("button", name="First")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_a_later_item_can_start_open(show: Show) -> None:
    page = show(
        Accordion().content(
            AccordionItem().title("One").content("Body one"),
            AccordionItem().title("Two").open().content("Body two"),
        )
    )
    expect(page.get_by_text("Body two")).to_be_visible()
    expect(page.get_by_text("Body one")).to_be_hidden()
    expect(page.get_by_role("button", name="Two")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_sections_toggle_by_key_right_to_left(show: Show) -> None:
    page = show(
        Disclosure().title("Details").closed().content("Disclosed"),
        Accordion().content(
            AccordionItem().title("One").open().content("Body one"),
            AccordionItem().title("Two").content("Body two"),
        ),
        dir="rtl",
    )
    details = page.get_by_role("button", name="Details")
    details.press("Enter")
    expect(page.get_by_text("Disclosed")).to_be_visible()
    expect(details).to_be_focused()
    page.get_by_role("button", name="Two").press("Space")
    expect(page.get_by_text("Body two")).to_be_visible()
    expect(page.get_by_text("Body one")).to_be_hidden()


def test_contents_open_an_accordion_item_inside_a_closed_disclosure(
    show: Show,
) -> None:
    page = show(
        html.div(
            TableOfContents().of("#doc"),
            style="position: fixed; top: 0; right: 0; width: 200px",
        ),
        html.div(
            html.h2("Intro", id="intro"),
            Disclosure()
            .title("More")
            .closed()
            .content(
                Accordion().content(
                    AccordionItem().title("First").open().content("First body"),
                    AccordionItem()
                    .title("Second")
                    .content(html.h2("Hidden", id="hidden"), html.p("Folded")),
                )
            ),
            html.div(style="height: 2000px"),
            id="doc",
        ),
    )
    page.get_by_role("link", name="Hidden").click()
    expect(page.get_by_text("Folded")).to_be_visible()
    expect(page.locator("#hidden")).to_be_focused()
