from htmy import html
from playwright.sync_api import Page, expect

from hue.js import unsafe
from hue.ui import Accordion, AccordionItem, Disclosure, TextInput
from tests.browser.conftest import Show
from tests.browser.test_disclosure import guarded_fields, guarded_form, submit


def test_opening_one_section_closes_the_other(show: Show) -> None:
    # A later item can start open.
    page = show(
        Accordion().content(
            AccordionItem().title("Billing").content("About billing"),
            AccordionItem().title("Plans").open().content("About plans"),
        )
    )
    expect(page.get_by_text("About billing")).to_be_hidden()
    page.get_by_role("button", name="Billing").press("Enter")
    expect(page.get_by_text("About billing")).to_be_visible()
    expect(page.get_by_text("About plans")).to_be_hidden()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_multiple_keeps_both_open(show: Show) -> None:
    page = show(
        Accordion()
        .multiple()
        .content(
            AccordionItem().title("Billing").open().content("About billing"),
            AccordionItem().title("Plans").content("About plans"),
        )
    )
    page.get_by_role("button", name="Plans").press("Space")
    expect(page.get_by_text("About plans")).to_be_visible()
    expect(page.get_by_text("About billing")).to_be_visible()


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


# Sections opened by an invalid field.


def _form(*parts: object) -> object:
    return html.form(
        *parts,
        html.button("Save", type="submit"),
        action="/saved",
        method="get",
    )


def _field(name: str) -> TextInput:
    return TextInput().name(name).label(name.title()).required()


def _expanded(page: Page, title: str) -> str | None:
    return page.get_by_role("button", name=title).get_attribute("aria-expanded")


def _frames(page: Page) -> None:
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )


def test_only_the_reported_fields_section_opens_and_takes_focus(show: Show) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").open().content("Nothing to fill"),
                AccordionItem().title("Plans").content(_field("plan")),
                AccordionItem().title("Extras").content(_field("extra")),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    plan = page.get_by_role("textbox", name="Plan")
    expect(plan).to_be_focused()
    expect(plan).to_be_visible()
    _frames(page)
    assert _expanded(page, "Extras") == "false"


def test_a_reported_field_nested_in_the_open_section_keeps_it(show: Show) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem()
                .title("Billing")
                .open()
                .content(Disclosure().title("Card").closed().content(_field("card"))),
                AccordionItem().title("Plans").content(_field("plan")),
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    card = page.get_by_role("textbox", name="Card")
    expect(card).to_be_focused()
    expect(card).to_be_visible()
    _frames(page)
    assert _expanded(page, "Billing") == "true"
    assert _expanded(page, "Plans") == "false"


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


def test_two_accordions_each_open_their_own_section(show: Show) -> None:
    # The one-at-a-time guard belongs to each accordion, so the second
    # accordion's invalid section still opens.
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").content(_field("card"))
            ),
            Accordion().content(AccordionItem().title("Plans").content(_field("plan"))),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Card")).to_be_focused()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_a_second_accordion_keeps_the_section_the_reader_had_open(
    show: Show,
) -> None:
    page = show(
        _form(
            Accordion().content(
                AccordionItem().title("Billing").content(_field("card"))
            ),
            Accordion().content(
                AccordionItem().title("Notes").open().content("Notes text"),
                AccordionItem().title("Plans").content(_field("plan")),
            ),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Card")).to_be_focused()
    expect(page.get_by_text("Notes text")).to_be_visible()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_a_field_reported_outside_the_accordion_leaves_its_open_section(
    show: Show,
) -> None:
    # The browser reports the name above the accordion, so nothing in the
    # accordion is shown to the reader, and the section they had open stays.
    page = show(
        _form(
            _field("name"),
            Accordion().content(
                AccordionItem().title("Billing").open().content("Billing text"),
                AccordionItem().title("Plans").content(_field("plan")),
            ),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Name")).to_be_focused()
    _frames(page)
    assert _expanded(page, "Plans") == "false"
    assert page.get_by_text("Billing text").is_visible()


def _plans() -> Accordion:
    return Accordion().content(
        AccordionItem()
        .title("Billing")
        .open()
        .content(
            TextInput()
            .name("card")
            .label("Card")
            .x_on("input", unsafe("$el.form.checkValidity()"))
        ),
        AccordionItem().title("Plans").content(_field("plan")),
    )


def test_an_invalid_field_in_another_form_does_not_open_a_section(
    show: Show,
) -> None:
    page = show(
        html.form(_field("search"), id="other"),
        _form(_plans()),
    )
    page.evaluate("document.getElementById('other').reportValidity()")
    expect(page.get_by_role("textbox", name="Search")).to_be_focused()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "false"
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Plan")).to_be_focused()


def test_checking_validity_while_typing_leaves_the_open_section(show: Show) -> None:
    # A form that enables Save as it becomes valid checks itself on every
    # keystroke. Nothing is reported, so nothing the reader has open closes.
    page = show(_form(_plans()))
    card = page.get_by_role("textbox", name="Card")
    card.press_sequentially("42")
    _frames(page)
    assert card.is_visible()
    assert page.evaluate("document.activeElement.name") == "card"
    assert _expanded(page, "Plans") == "false"


def test_a_removed_accordion_leaves_no_listener_behind(show: Show) -> None:
    # A listener left behind throws, which the fixture reports.
    page = show(html.div(_form(_plans()), id="region"))
    page.evaluate("document.getElementById('region').remove()")
    page.evaluate(
        "(() => { const i = document.createElement('input'); i.required = true;"
        " document.body.append(i); i.checkValidity(); })()"
    )


def test_a_form_keeps_its_own_submitting_state_inside_a_section(show: Show) -> None:
    item = AccordionItem().title("One").open().content(*guarded_fields())
    page = show(guarded_form(Accordion().content(item)))
    submit(page)
