import pytest
from htmy import html
from playwright.sync_api import expect

from hue.ui import Accordion, AccordionItem, TextInput
from tests.browser.conftest import Show
from tests.browser.test_disclosure import guarded_fields, guarded_form, submit_by


def _faq(*, multiple: bool = False) -> Accordion:
    return (
        Accordion()
        .multiple(multiple)
        .content(
            AccordionItem().title("Billing").open().content("About billing"),
            AccordionItem().title("Plans").content("About plans"),
        )
    )


def test_opening_one_section_closes_the_other(show: Show) -> None:
    page = show(_faq())
    page.get_by_role("button", name="Plans").press("Enter")
    expect(page.get_by_text("About plans")).to_be_visible()
    expect(page.get_by_text("About billing")).to_be_hidden()
    expect(page.get_by_role("button", name="Billing")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_multiple_keeps_both_open(show: Show) -> None:
    page = show(_faq(multiple=True))
    page.get_by_role("button", name="Plans").press("Space")
    expect(page.get_by_text("About plans")).to_be_visible()
    expect(page.get_by_text("About billing")).to_be_visible()


def _form(*items: AccordionItem) -> object:
    return html.form(
        Accordion().content(*items),
        html.button("Save", type="submit"),
        action="/saved",
        method="get",
    )


def test_a_required_empty_field_opens_its_section_and_takes_focus(show: Show) -> None:
    page = show(
        _form(
            AccordionItem().title("Billing").open().content("Nothing to fill"),
            AccordionItem()
            .title("Plans")
            .content(TextInput().name("plan").label("Plan").required()),
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Plan")).to_be_focused()
    expect(page.get_by_role("button", name="Plans")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_the_first_invalid_section_stays_open_with_focus(show: Show) -> None:
    # One at a time: opening the second invalid section would close the
    # first, where the browser puts focus.
    page = show(
        _form(
            AccordionItem()
            .title("Billing")
            .content(TextInput().name("card").label("Card").required()),
            AccordionItem()
            .title("Plans")
            .content(TextInput().name("plan").label("Plan").required()),
        )
    )
    page.get_by_role("button", name="Save").click()
    card = page.get_by_role("textbox", name="Card")
    expect(card).to_be_focused()
    expect(card).to_be_visible()
    expect(page.get_by_role("textbox", name="Plan")).to_be_hidden()


def test_enter_in_a_field_opens_the_invalid_section(show: Show) -> None:
    # Enter in a field submits the form, as a click on Save does.
    page = show(
        _form(
            AccordionItem()
            .title("Billing")
            .open()
            .content(TextInput().name("card").label("Card")),
            AccordionItem()
            .title("Plans")
            .content(TextInput().name("plan").label("Plan").required()),
        )
    )
    page.get_by_role("textbox", name="Card").press("Enter")
    expect(page.get_by_role("textbox", name="Plan")).to_be_focused()


@pytest.mark.parametrize("how", ["click", "enter"])
def test_a_form_keeps_its_own_submitting_state_inside_a_section(
    show: Show, how: str
) -> None:
    item = AccordionItem().title("One").open().content(*guarded_fields())
    page = show(guarded_form(Accordion().content(item)))
    submit_by(page, how)
