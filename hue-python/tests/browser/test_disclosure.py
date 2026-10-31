import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Accordion, AccordionItem, Checkbox, Disclosure, TextInput
from tests.browser.conftest import ORIGIN, Show


def _form(*sections: object, novalidate: bool = False) -> object:
    return html.form(
        *sections,
        html.button("Save", type="submit"),
        action="/saved",
        method="get",
        novalidate=novalidate or None,
    )


def _general(*fields: TextInput, closed: bool = True) -> Disclosure:
    return Disclosure().title("General").closed(closed).content(*fields)


def _required(name: str) -> TextInput:
    return TextInput().name(name).label(name.title()).required()


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


def test_each_trigger_toggles_its_own_section_by_click_and_key(show: Show) -> None:
    page = show(
        Disclosure().title("General").content("Inside"),
        Disclosure().title("Pricing").content("Two"),
    )
    trigger = page.get_by_role("button", name="General")
    region = page.get_by_role("region", name="General")
    expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(region).to_be_visible()
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "false")
    expect(page.get_by_text("Inside")).to_be_hidden()
    expect(page.get_by_text("Two")).to_be_visible()
    trigger.press("Enter")
    expect(region).to_be_visible()
    trigger.press("Space")
    expect(page.get_by_text("Inside")).to_be_hidden()


def test_a_field_in_a_closed_section_is_still_sent(show: Show) -> None:
    page = show(_form(_general(TextInput().name("product_name").value("Lamp"))))
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    expect(page).to_have_title("Saved")
    assert "product_name=Lamp" in sent[0]


def test_a_required_empty_field_opens_its_section_and_takes_focus(show: Show) -> None:
    page = show(_form(_general(_required("name"))))
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    field = page.get_by_label("Name")
    expect(field).to_be_focused()
    expect(field).to_be_visible()
    expect(page.get_by_role("button", name="General")).to_have_attribute(
        "aria-expanded", "true"
    )
    assert sent == []


def test_a_novalidate_form_leaves_its_sections_closed(show: Show) -> None:
    page = show(
        _form(
            _general(_required("name")),
            Accordion().content(
                AccordionItem().title("Billing").open().content("Open"),
                AccordionItem().title("Plans").content(_required("plan")),
            ),
            novalidate=True,
        )
    )
    sent = _saved(page)
    page.get_by_role("button", name="Save").click()
    expect(page).to_have_title("Saved")
    assert len(sent) == 1


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
    inner = Disclosure().title("Inner").closed().content(_required("deep"))
    page = show(_form(Disclosure().title("Outer").closed().content(inner)))
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Deep")).to_be_focused()
    expect(page.get_by_role("button", name="Outer")).to_have_attribute(
        "aria-expanded", "true"
    )


def test_an_accordion_inside_a_closed_section_opens_for_its_field(
    show: Show,
) -> None:
    page = show(
        _form(
            Disclosure()
            .title("Outer")
            .closed()
            .content(
                Accordion().content(
                    AccordionItem().title("S1").open().content("x"),
                    AccordionItem().title("S2").content(_required("deep")),
                )
            )
        )
    )
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("textbox", name="Deep")).to_be_focused()
    expect(page.get_by_role("button", name="S2")).to_have_attribute(
        "aria-expanded", "true"
    )


def guarded_form(section: object) -> object:
    """
    A form with its own double-submit guard: a submitting flag of its own,
    and a Save inside the section that it disables.
    """
    return html.form(
        TextInput().name("email").label("Email"),
        section,
        **{
            "x-data": "{ submitting: false }",
            "x-on:submit.prevent": "submitting = true; $el.dataset.sent = 'yes'",
        },
    )


def guarded_fields() -> tuple[object, ...]:
    return (
        TextInput().name("a").label("A"),
        html.button("Save", type="submit", **{":disabled": "submitting"}),
        html.span(id="status", **{"x-text": "submitting ? 'Saving' : 'Idle'"}),
    )


def submit(page: Page) -> None:
    """
    Submit the guarded form, and see that it was sent and that its guard,
    read from inside the section, now holds.
    """
    page.get_by_role("button", name="Save").click()
    expect(page.locator("form")).to_have_attribute("data-sent", "yes")
    expect(page.locator("#status")).to_have_text("Saving")
    expect(page.get_by_role("button", name="Save")).to_be_disabled()


def test_a_form_keeps_its_own_submitting_state_inside_a_section(show: Show) -> None:
    # The section's own state must not shadow a name the form uses, or the
    # form's guard reads the section's flag and disables Save mid-click.
    page = show(guarded_form(Disclosure().title("Details").content(*guarded_fields())))
    submit(page)


# A caller's state around a section, under the names hue's own state used to
# have, and markup inside the section that reads and calls them.
_CALLER = (
    "{ open: 'caller-open', single: 'caller-single', shown: 'caller-shown', "
    "submitting: 'caller-submitting', called: 'no', "
    "toggle() { this.called = 'yes' } }"
)


@pytest.mark.parametrize("section", ["disclosure", "accordion"])
def test_a_scope_around_the_section_keeps_its_names(show: Show, section: str) -> None:
    # x_data() on the section raises, so this is where a caller's state goes.
    reads = (
        html.span(
            id="read",
            **{"x-text": "[open, single, shown, submitting].join(' ')"},
        ),
        html.button("Call toggle", type="button", **{"x-on:click": "toggle()"}),
        html.span(id="called", **{"x-text": "called"}),
    )
    page = show(
        html.div(
            Disclosure().title("Details").content(*reads)
            if section == "disclosure"
            else Accordion().content(
                AccordionItem().title("Details").open().content(*reads),
                AccordionItem().title("Two").content("Second"),
            ),
            **{"x-data": _CALLER},
        )
    )
    expect(page.locator("#read")).to_have_text(
        "caller-open caller-single caller-shown caller-submitting"
    )
    page.get_by_role("button", name="Call toggle").click()
    expect(page.locator("#called")).to_have_text("yes")
    trigger = page.get_by_role("button", name="Details")
    expect(page.get_by_role("region", name="Details")).to_be_visible()
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "false")


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
    for nth in (0, 1):
        expect(page.get_by_text("Widget body").nth(nth)).to_be_visible()
