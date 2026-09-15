import pytest

from hue.renderer import render_tree
from hue.ui import Switch
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestSwitch:
    @pytest.mark.asyncio
    async def test_announced_as_on_or_off_not_checked(self, context_args):
        # A native checkbox underneath, so it posts and toggles like one; the
        # role is only what changes how it is read out.
        html = await render_tree(
            Switch("notify").label("Email notifications"), context_args=context_args
        )
        assert_attr(html, "input", "type", "checkbox")
        assert_attr(html, "input", "role", "switch")

    # checked(): both branches
    @pytest.mark.asyncio
    async def test_starts_on(self, context_args):
        html = await render_tree(
            Switch("notify").label("N").checked(), context_args=context_args
        )
        assert_attr(html, "input", "checked")

    @pytest.mark.asyncio
    async def test_starts_off_by_default(self, context_args):
        # checked="false" would still leave it on.
        html = await render_tree(Switch("notify").label("N"), context_args=context_args)
        assert_no_selector(html, "input[checked]")

    # pending(): both branches
    @pytest.mark.asyncio
    async def test_pending_disables_it_and_says_why(self, context_args):
        # Otherwise the switch just refuses to move, with nothing to say a
        # round trip is what is holding it.
        html = await render_tree(
            Switch("notify").label("N").pending(), context_args=context_args
        )
        assert_attr(html, "input", "disabled")
        assert_selector(html, '[role="status"]')
        assert "Saving" in html

    @pytest.mark.asyncio
    async def test_not_pending_by_default(self, context_args):
        html = await render_tree(Switch("notify").label("N"), context_args=context_args)
        assert_no_selector(html, '[role="status"]')
        assert_no_selector(html, "input[disabled]")

    @pytest.mark.asyncio
    async def test_the_knob_travels_the_width_of_the_track(self, context_args):
        html = await render_tree(
            Switch("n").label("N").size("lg"), context_args=context_args
        )
        assert_selector(html, "input.w-\\[44px\\]")
        assert_selector(html, "input.checked\\:before\\:translate-x-\\[19px\\]")

    @pytest.mark.asyncio
    async def test_a_description_sits_under_the_label(self, context_args):
        html = await render_tree(
            Switch("n").label("N").description("Sent as things happen."),
            context_args=context_args,
        )
        assert_selector(html, "span.text-fg-muted")

    @pytest.mark.asyncio
    async def test_no_description_by_default(self, context_args):
        html = await render_tree(Switch("n").label("N"), context_args=context_args)
        assert_no_selector(html, "span.text-fg-muted")

    # size(): each one meets the label's first line in a different place, so
    # each carries its own offset rather than sharing one nudge.
    @pytest.mark.parametrize(
        ("size", "offset"),
        [("sm", "mt-px"), ("md", "mt-0"), ("lg", "-mt-\\[3px\\]")],
    )
    @pytest.mark.asyncio
    async def test_every_size_sits_on_the_first_line(self, context_args, size, offset):
        html = await render_tree(
            Switch("n").label("N").size(size), context_args=context_args
        )
        assert_selector(html, f"input.{offset}")

    # layout(): both branches
    @pytest.mark.asyncio
    async def test_horizontal_puts_the_text_first(self, context_args):
        # The scanning order a settings list wants: what can I change, then
        # the thing that changes it.
        html = await render_tree(
            Switch("n")
            .label("Two-factor")
            .description("A code every time.")
            .layout("horizontal"),
            context_args=context_args,
        )
        assert_selector(html, "label.justify-between")
        assert html.index("Two-factor") < html.index("<input")
        # Centred against the whole block, so no first-line offset applies.
        assert_no_selector(html, "input.mt-0")

    @pytest.mark.asyncio
    async def test_the_switch_leads_by_default(self, context_args):
        html = await render_tree(
            Switch("n").label("Two-factor"), context_args=context_args
        )
        assert_no_selector(html, "label.justify-between")
        assert html.index("<input") < html.index("Two-factor")
