import pytest

from hue.renderer import render_tree
from hue.ui import Button, Toast, ToastRegion
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestToast:
    @pytest.mark.asyncio
    async def test_it_takes_its_timer_from_the_region_and_stops_for_a_reader(
        self, context_args
    ):
        # The region is what times a toast, so a specimen outside one stays.
        # WCAG 2.2.1: a message that leaves on its own has to be stoppable.
        html = await render_tree(
            Toast().variant("success").title("Invoice sent"),
            context_args=context_args,
        )
        assert_attr(
            html, "[x-data]", "x-init", "ms = $data.hueToastDuration ?? 0; start(ms)"
        )
        assert_attr(html, "[x-data]", "x-on:mouseenter", "stop()")
        assert_attr(html, "[x-data]", "x-on:mouseleave", "resume()")
        assert_attr(html, "[x-data]", "x-on:focusin", "stop()")

    # duration(): both branches
    @pytest.mark.asyncio
    async def test_a_toast_that_was_staying_does_not_leave_after_a_hover(
        self, context_args
    ):
        # resume() checks the number the toast was given; without that, the
        # hover is what starts a sticky toast counting down.
        html = await render_tree(
            Toast().title("Exporting").duration(None), context_args=context_args
        )
        assert "resume() { if (this.ms) this.start(2600) }" in str(html)

    @pytest.mark.asyncio
    async def test_a_duration_is_milliseconds(self, context_args):
        html = await render_tree(
            Toast().title("Saved").duration(2000), context_args=context_args
        )
        assert_attr(html, "[x-data]", "x-init", "ms = 2000; start(ms)")

    @pytest.mark.asyncio
    async def test_no_duration_is_a_toast_that_stays(self, context_args):
        html = await render_tree(
            Toast().title("Exporting").duration(None), context_args=context_args
        )
        assert_attr(html, "[x-data]", "x-init", "ms = 0; start(ms)")

    # variant(): the failure is the one that is announced assertively
    @pytest.mark.asyncio
    async def test_a_failure_is_mirrored_into_the_announcer(self, context_args):
        # Polite means "when you get a moment", which a failure cannot wait
        # for. Read off the element, so a toast cloned in the browser
        # announces what it actually says rather than the template's blanks.
        html = await render_tree(
            Toast().variant("danger").title("Could not send").description("Try again"),
            context_args=context_args,
        )
        assert_attr(
            html,
            "[x-data]",
            "x-init",
            "ms = $data.hueToastDuration ?? 0; start(ms); "
            "$data.announce?.($el.innerText.trim())",
        )

    @pytest.mark.asyncio
    async def test_anything_else_is_left_to_the_polite_region(self, context_args):
        html = await render_tree(
            Toast().variant("success").title("Invoice sent"), context_args=context_args
        )
        assert_attr(
            html, "[x-data]", "x-init", "ms = $data.hueToastDuration ?? 0; start(ms)"
        )

    @pytest.mark.asyncio
    async def test_the_loading_variant_spins_instead_of_an_icon(self, context_args):
        html = await render_tree(
            Toast().variant("loading").title("Exporting"), context_args=context_args
        )
        assert_selector(html, '[role="status"]')

    # description(), action() and dismissible(): both branches each
    @pytest.mark.asyncio
    async def test_the_parts_are_there_when_they_are_given(self, context_args):
        html = await render_tree(
            Toast()
            .variant("danger")
            .title("Could not send")
            .description("The mail server rejected the address.")
            .action(Button().content("Retry")),
            context_args=context_args,
        )
        assert_selector(html, "[data-toast-description]")
        assert_selector(html, "div.mt-2 button")
        assert_selector(html, 'button[aria-label="Dismiss"]')

    @pytest.mark.asyncio
    async def test_a_bare_toast_is_a_line_of_text(self, context_args):
        html = await render_tree(
            Toast().title("Copied to clipboard").dismissible(False),
            context_args=context_args,
        )
        assert_selector(html, "[data-toast-title]")
        assert_no_selector(html, "[data-toast-description]")
        assert_no_selector(html, "div.mt-2")
        assert_no_selector(html, 'button[aria-label="Dismiss"]')


class TestToastRegion:
    @pytest.mark.asyncio
    async def test_the_live_region_is_there_before_anything_is_in_it(
        self, context_args
    ):
        # One created together with its content is never read out.
        html = await render_tree(ToastRegion(), context_args=context_args)
        assert_attr(html, "#hue-toasts", "aria-live", "polite")
        assert_attr(html, "#hue-toast-announcer", "role", "alert")

    @pytest.mark.asyncio
    async def test_it_collects_toasts_from_every_request(self, context_args):
        # x-sync puts it in the targets of every Alpine AJAX request, and
        # append keeps the toasts already on screen.
        html = await render_tree(ToastRegion(), context_args=context_args)
        assert_attr(html, "#hue-toasts", "x-sync")
        assert_attr(html, "#hue-toasts", "x-merge", "append")

    @pytest.mark.asyncio
    async def test_the_region_sets_the_default_a_toast_takes(self, context_args):
        # Toasts inside it inherit the number through the Alpine scope.
        html = await render_tree(
            ToastRegion().default_duration(8000), context_args=context_args
        )
        assert "hueToastDuration: 8000" in str(html)

    @pytest.mark.asyncio
    async def test_it_carries_the_markup_the_client_clones(self, context_args):
        # $toast builds its toast from these, so a toast raised in the browser
        # is the same element as one raised on the server.
        html = await render_tree(ToastRegion(), context_args=context_args)
        assert_selector(html, 'template[data-variant="success"]')
        assert_selector(html, 'template[data-variant="loading"]', count=1)
