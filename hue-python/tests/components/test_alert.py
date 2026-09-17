import pytest

from hue.renderer import render_tree
from hue.ui import Alert, Button
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestAlert:
    @pytest.mark.asyncio
    async def test_renders_a_title_and_description(self, context_args):
        html = await render_tree(
            Alert().title("Payment failed").content("The card was declined."),
            context_args=context_args,
        )
        assert "Payment failed" in html
        assert "The card was declined." in html

    @pytest.mark.parametrize(
        ("variant", "fill"),
        [
            ("neutral", "bg-surface-sunken"),
            ("info", "bg-info-subtle"),
            ("success", "bg-success-subtle"),
            ("warning", "bg-warning-subtle"),
            ("danger", "bg-danger-subtle"),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_variant_has_its_own_tone(self, context_args, variant, fill):
        html = await render_tree(
            Alert().variant(variant).title("T"), context_args=context_args
        )
        assert_selector(html, f"div.{fill}")

    @pytest.mark.asyncio
    async def test_the_icon_is_decorative(self, context_args):
        # The words say what the alert is; an announced icon would say it
        # twice, and "circle x" is not what it means anyway.
        html = await render_tree(
            Alert().variant("danger").title("T"), context_args=context_args
        )
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_an_icon_of_your_own_replaces_it(self, context_args):
        html = await render_tree(
            Alert().variant("info").icon("!").title("T"), context_args=context_args
        )
        assert_no_selector(html, "svg")

    # The role follows the variant: only danger is worth interrupting for.
    @pytest.mark.parametrize(
        ("variant", "role"),
        [
            ("neutral", "status"),
            ("info", "status"),
            ("success", "status"),
            ("warning", "status"),
            ("danger", "alert"),
        ],
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

    # dismissible(): both branches
    @pytest.mark.asyncio
    async def test_dismissible_adds_a_named_close(self, context_args):
        html = await render_tree(
            Alert().title("T").dismissible(), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Dismiss")
        assert_selector(html, "[x-data] [x-on\\:click]")

    @pytest.mark.asyncio
    async def test_not_dismissible_by_default(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_no_selector(html, "button")
        assert_no_selector(html, "[x-data]")

    @pytest.mark.asyncio
    async def test_an_alert_is_a_box(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_selector(html, "div.rounded-md")

    # actions(): both branches
    @pytest.mark.asyncio
    async def test_actions_take_the_alerts_own_tone(self, context_args):
        # A near-black ghost label surrounded by tinted copy, and an opaque
        # grey hover patch on a coloured fill, are both wrong here.
        html = await render_tree(
            Alert().variant("danger").title("T").actions("retry"),
            context_args=context_args,
        )
        assert_selector(html, "div.mt-3")
        assert "text-current" in html

    @pytest.mark.asyncio
    async def test_no_actions_by_default(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_no_selector(html, "div.mt-3")


class TestAlertTitleTone:
    @pytest.mark.asyncio
    async def test_the_title_is_a_step_louder_than_the_description(self, context_args):
        # Same weight and same colour made the two one block of text; the
        # title takes a deeper step of whatever tone it is inheriting.
        html = await render_tree(
            Alert().variant("danger").title("T").content("D"),
            context_args=context_args,
        )
        assert_selector(html, "div.text-stronger")

    @pytest.mark.asyncio
    async def test_the_icon_is_not_baseline_aligned(self, context_args):
        # An svg inside a non-flex span sits on the text baseline and rides
        # above the title it belongs to.
        html = await render_tree(
            Alert().variant("danger").title("T"), context_args=context_args
        )
        assert_selector(html, "span.mt-0\\.5.flex")

    @pytest.mark.asyncio
    async def test_only_the_quiet_buttons_take_the_alerts_tone(self, context_args):
        # Applied to every button it repaints a solid one's label in the
        # alert's tone as well - pale pink on a pink fill, which is the
        # contrast failure the rule exists to prevent.
        html = await render_tree(
            Alert()
            .variant("danger")
            .title("T")
            .actions(
                Button().variant("danger").size("sm").content("Retry"),
                Button().variant("ghost").size("sm").content("Later"),
            ),
            context_args=context_args,
        )
        # The & is escaped in the attribute, so match from past it.
        assert "data-variant=ghost]]:text-current" in html
        assert "_button]:text-current" not in html
        # The solid one keeps the label its own variant gives it.
        assert_selector(html, '[data-variant="danger"].text-danger-fg')

    @pytest.mark.asyncio
    async def test_a_ghost_is_toned_wherever_it_is_put(self, context_args):
        # On the actions row and in content() alike. Two slots that style
        # their contents differently is a trap: the same button reads wrong in
        # one of them with nothing on the page to say why.
        html = await render_tree(
            Alert()
            .variant("danger")
            .title("T")
            .content(Button().variant("ghost").size("sm").content("In content")),
            context_args=context_args,
        )
        assert_selector(html, "div.\\[\\&_\\[data-variant\\=ghost\\]\\]\\:text-current")
        assert_selector(html, '[data-variant="ghost"]')
