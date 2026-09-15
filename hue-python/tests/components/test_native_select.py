import pytest

from hue.renderer import render_tree
from hue.ui import NativeSelect
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _select(**kwargs):
    return (
        NativeSelect()
        .name("tz")
        .label("Time zone")
        .options([("utc", "UTC"), ("oslo", "Europe/Oslo")])
    )


class TestNativeSelect:
    @pytest.mark.asyncio
    async def test_renders_a_labelled_native_select(self, context_args):
        # The platform control, so the phone picker and type-ahead come free.
        html = await render_tree(_select(), context_args=context_args)
        assert_attr(html, "label", "for", "tz")
        assert_selector(html, "select#tz")
        assert_selector(html, "option", count=2)

    # value(): both branches
    @pytest.mark.asyncio
    async def test_the_named_option_starts_selected(self, context_args):
        html = await render_tree(_select().value("oslo"), context_args=context_args)
        assert_attr(html, 'option[value="oslo"]', "selected")
        assert_no_selector(html, 'option[value="utc"][selected]')

    @pytest.mark.asyncio
    async def test_nothing_selected_by_default(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, "option[selected]")

    # placeholder(): both branches
    @pytest.mark.asyncio
    async def test_the_placeholder_cannot_be_chosen_back(self, context_args):
        # Disabled, so it reads as "nothing picked yet" rather than as an
        # option in its own right.
        html = await render_tree(
            _select().placeholder("Pick a time zone"), context_args=context_args
        )
        first = "option:first-of-type"
        assert_attr(html, first, "disabled")
        assert_attr(html, first, "selected")
        assert_attr(html, first, "value", "")

    @pytest.mark.asyncio
    async def test_a_value_beats_the_placeholder(self, context_args):
        html = await render_tree(
            _select().placeholder("Pick a time zone").value("utc"),
            context_args=context_args,
        )
        assert_no_selector(html, "option:first-of-type[selected]")
        assert_attr(html, 'option[value="utc"]', "selected")

    @pytest.mark.asyncio
    async def test_no_placeholder_by_default(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, "option[disabled]")

    @pytest.mark.asyncio
    async def test_the_chevron_travels_with_the_control(self, context_args):
        # A background image rather than a positioned sibling, so nothing has
        # to be aligned over a box whose height changes with the size.
        html = await render_tree(_select().size("lg"), context_args=context_args)
        assert_selector(html, "select.appearance-none")
        assert "bg-no-repeat" in html
        assert "h-control-lg" in html

    @pytest.mark.asyncio
    async def test_an_error_marks_it_invalid(self, context_args):
        html = await render_tree(
            _select().error("Pick a time zone."), context_args=context_args
        )
        assert_attr(html, "select", "aria-invalid", "true")
        assert_selector(html, '[role="alert"]#tz-error')
