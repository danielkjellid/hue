import pytest

from hue.renderer import render_tree
from hue.ui import Alert, Button
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestAlert:
    @pytest.mark.asyncio
    async def test_the_icon_is_decorative(self, context_args):
        # The words say what the alert is; an announced icon would say it
        # twice, and "circle x" is not what it means anyway.
        html = await render_tree(
            Alert().variant("danger").title("T"), context_args=context_args
        )
        assert_selector(html, 'span[aria-hidden="true"] svg')

    # The role follows the variant: only danger is worth interrupting for.
    @pytest.mark.parametrize(
        ("variant", "role"),
        [("neutral", "status"), ("warning", "status"), ("danger", "alert")],
    )
    @pytest.mark.asyncio
    async def test_how_loudly_it_arrives_follows_the_variant(
        self, context_args, variant, role
    ):
        # Safe as a default: a live region that exists with its content
        # already in it is never announced, so a server-rendered alert is read
        # in document order. The role only does anything when one arrives
        # after the page, which is when it should.
        html = await render_tree(
            Alert().variant(variant).title("T"), context_args=context_args
        )
        assert_selector(html, f'[role="{role}"]')

    @pytest.mark.asyncio
    async def test_a_caller_who_knows_better_can_say_so(self, context_args):
        html = await render_tree(
            Alert().variant("danger").title("T").role("none"),
            context_args=context_args,
        )
        assert_no_selector(html, '[role="alert"]')

    @pytest.mark.asyncio
    async def test_dismissible_adds_a_named_close(self, context_args):
        html = await render_tree(
            Alert().title("T").dismissible(), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Dismiss")
        # Focus is handed on before the alert hides; hiding it with focus
        # inside drops focus to the body.
        assert "$handOff(box)" in select(html, "button")[0]["x-on:click"]
        # No wrapper, so the alert itself is the box a layout places.
        assert_no_selector(html, 'div [role="status"]')

    @pytest.mark.asyncio
    async def test_only_the_quiet_buttons_take_the_alerts_tone(self, context_args):
        # Applied to every button it repainted a solid one's label in the
        # alert's tone as well - pale pink on a pink fill, a contrast failure.
        # A ghost is toned in content() as on the actions row, so the same
        # button never reads differently in the two slots.
        html = await render_tree(
            Alert()
            .variant("danger")
            .title("T")
            .content(Button().variant("ghost").size("sm").content("In content"))
            .actions(
                Button().variant("danger").size("sm").content("Retry"),
                Button().variant("ghost").size("sm").content("Later"),
            ),
            context_args=context_args,
        )
        # On the alert itself, so it reaches both slots.
        root = select(html, '[role="alert"]')[0]
        assert "[&_[data-variant=ghost]]:text-current" in root["class"]
        assert "_button]:text-current" not in html
        # The solid one keeps the label its own variant gives it.
        assert_selector(html, '[data-variant="danger"].text-danger-fg')
