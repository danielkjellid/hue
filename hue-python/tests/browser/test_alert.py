from htmy import html
from playwright.sync_api import expect

from hue.js import unsafe
from hue.ui import Alert, Banner, Button, Dialog, Popover, Stack, TextInput
from tests.browser.conftest import Show


def test_dismissing_the_last_hands_focus_back(show: Show) -> None:
    page = show(
        Button().content("Before"),
        Banner().title("Saved").dismissible(),
    )
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press(" ")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Before")).to_be_focused()


def test_a_caller_x_data_and_x_show_still_work_with_dismiss(show: Show) -> None:
    alert = (
        Banner()
        .x_data("{ note: 'from the caller' }")
        .x_show(unsafe("true"))
        .title("Saved")
        .content(html.span(**{"x-text": "note"}))
        .dismissible()
    )
    page = show(alert, Button().content("Next"))
    expect(page.get_by_text("from the caller")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Next")).to_be_focused()


def test_an_alert_the_caller_reveals_later_can_still_be_dismissed(show: Show) -> None:
    holder = html.div(
        Button().content("Show").on_click(unsafe("shown = true")),
        Alert().x_show(unsafe("shown")).x_cloak().title("Saved").dismissible(),
        Button().content("After"),
        **{"x-data": "{ shown: false }"},
    )
    page = show(holder)
    expect(page.get_by_text("Saved")).to_be_hidden()
    page.get_by_role("button", name="Show").click()
    expect(page.get_by_text("Saved")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="After")).to_be_focused()


def test_a_dismissible_alert_takes_a_width_and_a_flex_class(show: Show) -> None:
    # The dismiss state lives on the button, so a class on the alert still
    # sizes the alert rather than a wrapper around it.
    page = show(
        html.div(
            Stack()
            .align_items("items-start")
            .content(Banner().class_("w-full").title("Wide").dismissible()),
            style="width:600px",
        ),
        html.div(
            Alert().class_("flex-1").title("Grows").dismissible(),
            Button().content("Undo"),
            style="display:flex;gap:8px;width:600px",
        ),
    )
    wide = page.get_by_role("status").first.bounding_box()
    grows = page.get_by_role("status").last.bounding_box()
    button = page.get_by_role("button", name="Undo").bounding_box()
    assert wide is not None and grows is not None and button is not None
    assert wide["width"] == 600
    assert abs(grows["width"] + 8 + button["width"] - 600) < 1


def test_dismissing_in_a_stack_leaves_one_gap(show: Show) -> None:
    page = show(
        Stack().content(
            Button().content("Before"),
            Banner().title("Saved").dismissible(),
            Button().content("After"),
        )
    )
    before = page.get_by_role("button", name="Before").bounding_box()
    alert = page.get_by_role("status").bounding_box()
    assert before is not None and alert is not None
    gap = alert["y"] - (before["y"] + before["height"])
    page.get_by_role("button", name="Dismiss").click()
    expect(page.get_by_text("Saved")).to_be_hidden()
    after = page.get_by_role("button", name="After").bounding_box()
    assert after is not None
    assert abs(after["y"] - (before["y"] + before["height"]) - gap) < 1


def test_dismissing_with_nothing_else_focusable_focuses_the_holder(
    show: Show,
) -> None:
    page = show(html.div(Alert().title("Saved").dismissible(), id="holder"))
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.locator("#holder")).to_be_focused()
    expect(page.locator("#holder")).to_have_attribute("tabindex", "-1")


def test_dismissing_one_of_two_alerts_moves_to_the_other(show: Show) -> None:
    page = show(
        Alert().title("First").dismissible(),
        Alert().title("Second").dismissible(),
    )
    page.get_by_role("button", name="Dismiss").first.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("First")).to_be_hidden()
    expect(page.get_by_text("Second")).to_be_visible()
    expect(page.get_by_role("button", name="Dismiss")).to_be_focused()


def test_dismissing_with_focus_elsewhere_leaves_focus_alone(show: Show) -> None:
    page = show(
        TextInput().name("note").label("Note"),
        Alert().title("Saved").dismissible(),
        Button().content("After"),
    )
    page.get_by_label("Note").focus()
    page.get_by_role("button", name="Dismiss").dispatch_event("click")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_label("Note")).to_be_focused()


def test_dismissing_inside_a_dialog_keeps_focus_in_the_dialog(show: Show) -> None:
    page = show(
        Dialog().title("Holder").open().content(Alert().title("Saved").dismissible()),
        Button().content("Outside"),
    )
    dialog = page.get_by_role("dialog", name="Holder")
    expect(dialog).to_be_visible()
    page.get_by_role("button", name="Dismiss").last.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(dialog).to_be_visible()
    # Somewhere a keyboard user can go on from: inside the dialog, and not
    # on the hidden close button.
    page.wait_for_function(
        "() => { const el = document.activeElement;"
        " return document.querySelector('[role=dialog]').contains(el)"
        " && el.getClientRects().length > 0 }",
        timeout=3000,
    )


def test_dismissing_in_a_popover_stays_in_the_popover(show: Show) -> None:
    popover = (
        Popover()
        .title("Notes")
        .trigger(Button().content("Notes"))
        .content(Alert().title("Saved").dismissible(), Button().content("Inside"))
    )
    page = show(popover, Button().content("After"))
    page.get_by_role("button", name="Notes").click()
    expect(page.get_by_role("dialog", name="Notes")).to_be_visible()
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Inside")).to_be_focused()


def test_dismissing_outside_any_dialog_still_reaches_the_page(show: Show) -> None:
    # A dialog elsewhere on the page is not the one the alert sits in.
    page = show(
        Alert().title("Saved").dismissible(),
        html.div(Button().content("Next")),
        Dialog().title("Elsewhere").trigger(Button().content("Open")),
    )
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Next")).to_be_focused()
