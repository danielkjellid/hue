import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Button, Dialog, Popover, Tooltip
from hue.ui.molecules import _overlay
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

# close() is what the footer actions call, so it is part of the state the
# dialog renders rather than an internal detail.
_STATE = "{{ open: {open}, close() {{ this.open = false }} }}"


def _dialog():
    return (
        Dialog()
        .title("Invite teammates")
        .description("They will get a join link.")
        .trigger(Button().content("Invite"))
    )


class TestDialog:
    @pytest.mark.asyncio
    async def test_the_trigger_opens_it_and_says_so(self, context_args):
        # Without this the dialog renders and nothing can ever show it.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, "button", "x-on:click", "open = true")

    @pytest.mark.asyncio
    async def test_the_triggers_own_binding_survives(self, context_args):
        # Both used to be written under :aria-expanded, so the dialog's
        # replaced the caller's.
        dialog = _dialog().trigger(
            Button().content("Invite").x_bind("aria-expanded", unsafe("busy"))
        )
        html = await render_tree(dialog, context_args=context_args)
        assert_attr(html, "button", ":aria-expanded", "busy")
        assert_attr(html, "button", "x-bind:aria-expanded", "open")
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", "x-bind:aria-expanded", "open")

    @pytest.mark.asyncio
    async def test_the_triggers_own_click_handler_survives(self, context_args):
        # Both used to be written under @click, so the dialog's replaced it.
        dialog = _dialog().trigger(
            Button().content("Invite").on_click(unsafe("track('invite')"))
        )
        html = await render_tree(dialog, context_args=context_args)
        assert_attr(html, "button", "@click", "track('invite')")
        assert_attr(html, "button", "x-on:click", "open = true")

    @pytest.mark.asyncio
    async def test_it_is_modal_and_named_by_its_title(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "aria-modal", "true")
        assert_attr(html, '[role="dialog"]', ":aria-labelledby")

    # The name: title, label, or neither
    @pytest.mark.asyncio
    async def test_without_a_title_the_label_names_it(self, context_args):
        dialog = Dialog().label("Invite teammates").content("Who should join?")
        html = await render_tree(dialog, context_args=context_args)
        assert_attr(html, '[role="dialog"]', "aria-label", "Invite teammates")
        assert_no_selector(html, "[\\:aria-labelledby]")

    @pytest.mark.asyncio
    async def test_a_dialog_with_no_name_is_refused(self, context_args):
        with pytest.raises(ValueError, match="needs an accessible name"):
            await render_tree(Dialog().content("?"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_focus_is_trapped_and_the_page_behind_is_inert(self, context_args):
        # inert takes the page out of the tab order, noscroll stops it moving
        # under the scrim, and the trap returns focus to whatever opened it.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "x-trap.inert.noscroll", "open")

    # destructive(): both branches
    @pytest.mark.asyncio
    async def test_destructive_is_an_alertdialog_that_reads_its_description(
        self, context_args
    ):
        html = await render_tree(_dialog().destructive(), context_args=context_args)
        assert_selector(html, '[role="alertdialog"]')
        assert_attr(html, '[role="alertdialog"]', ":aria-describedby")

    @pytest.mark.asyncio
    async def test_an_ordinary_dialog_leaves_the_description_to_be_read(
        self, context_args
    ):
        # Announced with the title it would be said before the reader has any
        # use for it; in order, it arrives where it belongs.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_selector(html, '[role="dialog"]')
        assert_no_selector(html, "[\\:aria-describedby]")

    # dismissible(): both branches
    @pytest.mark.asyncio
    async def test_dismissible_by_default(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, 'button[aria-label="Close"]', "aria-label", "Close")
        assert_selector(html, "[x-on\\:click\\.self]")

    @pytest.mark.asyncio
    async def test_only_a_press_that_began_on_the_scrim_closes_it(self, context_args):
        # A drag that selects text in the panel and lets go over the scrim is
        # still a click on the scrim, and must not close it.
        html = await render_tree(_dialog(), context_args=context_args)
        scrim = "[x-on\\:click\\.self]"
        pressed = "$el.huePressed = $event.target === $el"
        assert_attr(html, scrim, "x-on:pointerdown", pressed)
        assert_attr(html, scrim, "x-on:click.self", "if ($el.huePressed) close()")

    @pytest.mark.asyncio
    async def test_undismissible_keeps_escape(self, context_args):
        # A modal with no way out is a trap, whatever the question was.
        html = await render_tree(
            _dialog().dismissible(False), context_args=context_args
        )
        assert_no_selector(html, 'button[aria-label="Close"]')
        assert_no_selector(html, "[x-on\\:click\\.self]")
        assert_no_selector(html, "[x-on\\:pointerdown]")
        # On the overlay and stopped there, so a popover inside closes on
        # its own and a page-wide Escape behind it hears nothing.
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape",
            "if (open) { $event.stopPropagation(); close() }",
        )
        # The scrim takes a click's focus, so Escape still reaches it after
        # a click on the panel's text or beside it.
        assert_attr(html, "[x-show]", "tabindex", "-1")

    # open(): both branches
    @pytest.mark.asyncio
    async def test_it_starts_closed(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-data", _STATE.format(open="false"))

    @pytest.mark.asyncio
    async def test_started_open_it_hands_focus_to_the_trigger_on_close(
        self, context_args
    ):
        # The trap only returns focus to what had it before; a dialog open
        # from the start had nothing, and focus would land on the body.
        html = await render_tree(_dialog().open(), context_args=context_args)
        state = select(html, "[x-data]")[0]["x-data"]
        assert state.startswith("{ open: true")
        assert f"{_overlay.TRIGGER}?.focus()" in state

    @pytest.mark.asyncio
    async def test_started_open_it_finds_a_trigger_inside_a_tooltip(self, context_args):
        # An x-ref on the button would register in the tooltip's scope, out
        # of the dialog's sight, so it is found by its mark instead.
        dialog = _dialog().trigger(
            Tooltip().content("Invite").trigger(Button().icon_only("Invite"))
        )
        html = await render_tree(dialog.open(), context_args=context_args)
        assert f"{_overlay.TRIGGER}?.focus()" in select(html, "[x-data]")[0]["x-data"]
        assert_selector(html, "button[data-hue-trigger]")
        assert_no_selector(html, "[x-ref]")

    @pytest.mark.asyncio
    async def test_started_open_with_no_trigger_it_takes_none_from_its_content(
        self, context_args
    ):
        # The first trigger inside would be the nested popover's.
        dialog = (
            Dialog()
            .title("Filters")
            .open()
            .content(Popover().title("Help").trigger(Button().content("Help")))
        )
        html = await render_tree(dialog, context_args=context_args)
        assert "querySelector" not in select(html, "[x-data]")[0]["x-data"]

    @pytest.mark.asyncio
    async def test_it_docks_to_the_bottom_edge_below_sm(self, context_args):
        # A box floating in the middle of a phone screen is a worse drawer, so
        # below sm the panel is the drawer's bottom sheet, grabber and all.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_selector(html, '[role="dialog"].rounded-t-xl.sm\\:rounded-xl')
        assert_selector(html, "div.items-end.sm\\:items-center")
        assert_attr(html, '[role="dialog"] > div.sm\\:hidden', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_the_body_scrolls_rather_than_pushing_the_footer_out(
        self, context_args
    ):
        html = await render_tree(
            _dialog().content("a lot of text").footer("ok"),
            context_args=context_args,
        )
        assert_selector(html, "div.min-h-0.overflow-y-auto")
