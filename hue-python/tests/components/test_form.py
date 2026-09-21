import pytest
from htmy import Context

from hue.renderer import render_tree
from hue.types.core import Component
from hue.ui import Form, TextInput
from hue.ui.base import ChainableComponent
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class _Fieldset(ChainableComponent):
    """
    Somebody else's layout, which is where a control usually ends up.
    """

    def _render(self, context: Context) -> Component:
        return TextInput().name("email").label("Email")


class TestForm:
    @pytest.mark.asyncio
    async def test_the_form_posts_where_it_was_told(self, context_args):
        html = await render_tree(Form().action("/sign-up/"), context_args=context_args)
        assert_attr(html, "form", "action", "/sign-up/")
        assert_attr(html, "form", "method", "post")

    @pytest.mark.asyncio
    async def test_the_method_can_be_something_else(self, context_args):
        html = await render_tree(Form().method("get"), context_args=context_args)
        assert_attr(html, "form", "method", "get")

    @pytest.mark.asyncio
    async def test_a_control_finds_the_error_the_form_was_given(self, context_args):
        html = await render_tree(
            Form()
            .errors({"email": "Already registered."})
            .content(TextInput().name("email").label("Email")),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-invalid", "true")
        assert_attr(html, "input", "aria-describedby", "email-error")
        assert_selector(html, "span#email-error[role=alert]", count=1)

    @pytest.mark.asyncio
    async def test_a_control_built_while_rendering_finds_it_too(self, context_args):
        # The case that has no answer without a context: nothing above a
        # control knows it exists, so nobody can hand it its error.
        html = await render_tree(
            Form().errors({"email": "Already registered."}).content(_Fieldset()),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-invalid", "true")

    @pytest.mark.asyncio
    async def test_a_control_the_form_says_nothing_about_is_left_alone(
        self, context_args
    ):
        html = await render_tree(
            Form()
            .errors({"email": "Already registered."})
            .content(TextInput().name("company").label("Company")),
            context_args=context_args,
        )
        assert_no_selector(html, "input[aria-invalid]")
        assert_no_selector(html, "[role=alert]")

    @pytest.mark.asyncio
    async def test_a_control_given_its_own_error_keeps_it(self, context_args):
        html = await render_tree(
            Form()
            .errors({"email": "Already registered."})
            .content(TextInput().name("email").label("Email").error("Not an address.")),
            context_args=context_args,
        )
        assert "Not an address." in html
        assert "Already registered." not in html

    @pytest.mark.asyncio
    async def test_a_control_outside_a_form_asks_and_hears_nothing(self, context_args):
        # An absent form is not a mistake, so this reads as no errors
        # rather than raising the way a stray Tab does.
        html = await render_tree(
            TextInput().name("email").label("Email"), context_args=context_args
        )
        assert_no_selector(html, "input[aria-invalid]")
