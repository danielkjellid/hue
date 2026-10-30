from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Accordion, AccordionItem, Checkbox, Disclosure, TextInput
from tests.browser.conftest import ORIGIN, Show


def _form(*sections: Disclosure) -> object:
    return html.form(
        *sections,
        html.button("Save", type="submit"),
        action="/saved",
        method="get",
    )


def _general(*fields: TextInput, closed: bool = True) -> Disclosure:
    return Disclosure().title("General").closed(closed).content(*fields)


def _saved(page: Page) -> list[str]:
    """
    The URLs the form was sent to, answered with an empty page.
    """
    sent: list[str] = []

    def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
        sent.append(request.url)
        route.fulfill(body="<title>Saved</title>", content_type="text/html")

    page.route(f"{ORIGIN}/saved*", fulfil)
    return sent


def test_the_trigger_toggles_the_section_by_click_and_key(show: Show) -> None:
    page = show(Disclosure().title("General").content("Inside"))
    trigger = page.get_by_role("button", name="General")
    region = page.get_by_role("region", name="General")
    expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(region).to_be_visible()
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "false")
    expect(page.get_by_text("Inside")).to_be_hidden()
    trigger.press("Enter")
    expect(region).to_be_visible()
    trigger.press("Space")
    expect(page.get_by_text("Inside")).to_be_hidden()


def test_two_sections_open_and_close_on_their_own(show: Show) -> None:
    page = show(
        Disclosure().title("General").content("One"),
        Disclosure().title("Pricing").content("Two"),
    )
    page.get_by_role("button", name="General").click()
    expect(page.get_by_text("One")).to_be_hidden()
    expect(page.get_by_text("Two")).to_be_visible()


def test_a_field_in_a_closed_section_is_still_sent(show: Show) -> None:
    page = show(_form(_general(TextInput().name("product_name").value("Lamp"))))
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    expect(page).to_have_title("Saved")
    assert "product_name=Lamp" in sent[0]


def test_a_required_empty_field_opens_its_section_and_takes_focus(show: Show) -> None:
    name = TextInput().name("product_name").label("Name").required()
    page = show(_form(_general(name)))
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    field = page.get_by_label("Name")
    expect(field).to_be_focused()
    expect(field).to_be_visible()
    expect(page.get_by_role("button", name="General")).to_have_attribute(
        "aria-expanded", "true"
    )
    assert sent == []


def test_a_valid_form_leaves_a_closed_section_closed(show: Show) -> None:
    page = show(
        _form(_general(TextInput().name("product_name").label("Name").value("Lamp")))
    )
    page.evaluate("document.querySelector('form').checkValidity()")
    expect(page.get_by_role("button", name="General")).to_have_attribute(
        "aria-expanded", "false"
    )


def test_enter_in_a_field_of_a_form_without_a_button_opens_it(show: Show) -> None:
    # A form whose one text field submits on Enter, with no button to click.
    # A checkbox does not stop that, so it can be the invalid one.
    page = show(
        html.form(
            TextInput().name("q").label("Search"),
            Disclosure()
            .title("General")
            .closed()
            .content(Checkbox().name("terms").label("Terms").required()),
            action="/saved",
            method="get",
        )
    )
    page.get_by_role("textbox", name="Search").press("Enter")
    expect(page.get_by_role("checkbox", name="Terms")).to_be_focused()


def test_a_field_in_nested_closed_sections_opens_both(show: Show) -> None:
    # Each section keeps its own state under the same names, so the inner
    # one opening must not stand in for the outer.
    deep = TextInput().name("deep").label("Deep").required()
    inner = Disclosure().title("Inner").closed().content(deep)
    page = show(_form(Disclosure().title("Outer").closed().content(inner)))
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Deep")).to_be_focused()
    expect(page.get_by_role("button", name="Outer")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_an_accordion_inside_a_closed_section_opens_for_its_field(
    show: Show,
) -> None:
    deep = TextInput().name("deep").label("Deep").required()
    page = show(
        _form(
            Disclosure()
            .title("Outer")
            .closed()
            .content(
                Accordion().content(
                    AccordionItem().title("S1").open().content("x"),
                    AccordionItem().title("S2").content(deep),
                )
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Deep")).to_be_focused()
    expect(page.get_by_role("button", name="S2")).to_have_attribute(
        "aria-expanded", "true"
    )
