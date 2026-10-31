import pytest

from hue.renderer import render_tree
from hue.ui import Switch
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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

    @pytest.mark.asyncio
    async def test_starts_on(self, context_args):
        html = await render_tree(
            Switch("notify").label("N").checked(), context_args=context_args
        )
        assert_attr(html, "input", "checked")

    # submission_state(): every value, because a switch writes as it is
    # flipped and each stage of that write looks different.
    @pytest.mark.asyncio
    async def test_pending_disables_it_and_says_why(self, context_args):
        # Otherwise the switch just refuses to move, with nothing to say a
        # round trip is what is holding it.
        html = await render_tree(
            Switch("notify").label("N").submission_state("pending"),
            context_args=context_args,
        )
        assert_attr(html, "input", "disabled")
        assert select(html, '[role="status"] .sr-only')[0].text == "Saving"
        # It ends when the response lands, not when a timer says so.
        assert_no_selector(html, "[x-init]")

    @pytest.mark.parametrize(
        ("state", "announced"), [("success", "Saved"), ("error", "Not saved")]
    )
    @pytest.mark.asyncio
    async def test_an_outcome_is_named_not_just_coloured(
        self, context_args, state, announced
    ):
        # A tick that only means something if you can see it is not a report,
        # and a live region reads out its text, not its aria-label.
        html = await render_tree(
            Switch("notify").label("N").submission_state(state),
            context_args=context_args,
        )
        assert select(html, '[role="status"] .sr-only')[0].text == announced
        assert_no_selector(html, "input[disabled]")

    @pytest.mark.parametrize("state", ["success", "error"])
    @pytest.mark.asyncio
    async def test_an_outcome_clears_itself(self, context_args, state):
        # Nothing else is going to re-render this row, so a row left wearing
        # the outcome of a change made minutes ago is the default otherwise.
        html = await render_tree(
            Switch("notify").label("N").submission_state(state),
            context_args=context_args,
        )
        assert_attr(html, '[role="status"]', "x-show", "!settled")
        # Guarded on visibility: an outcome that expired while the row was
        # hidden - in a closed drawer, or a docs page showing every state at
        # once - was never reported at all.
        assert "checkVisibility" in html

    @pytest.mark.parametrize("state", ["success", "error"])
    @pytest.mark.asyncio
    async def test_an_outcome_can_be_held(self, context_args, state):
        # For an outcome that has to be read rather than glimpsed, and for
        # anywhere the row is not live.
        html = await render_tree(
            Switch("notify").label("N").submission_state(state).settle_after(None),
            context_args=context_args,
        )
        assert_selector(html, '[role="status"]')
        assert_no_selector(html, "[x-init]")

    @pytest.mark.asyncio
    async def test_horizontal_puts_the_text_first(self, context_args):
        # The scanning order a settings list wants: what can I change, then
        # the thing that changes it.
        html = await render_tree(
            Switch("n")
            .label("Two-factor")
            .description("A code every time.")
            .horizontal(),
            context_args=context_args,
        )
        assert html.index("Two-factor") < html.index("<input")

    @pytest.mark.asyncio
    async def test_named_by_its_label_alone(self, context_args):
        # The label wraps the control, so without this the description becomes
        # part of the switch's name and is read before "switch".
        html = await render_tree(
            Switch("n").label("Weekly digest").description("Every Monday."),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "n-label")
        assert_attr(html, "input", "aria-describedby", "n-description")
