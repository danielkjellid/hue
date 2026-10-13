import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Button, Command, CommandGroup, CommandItem
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _command(*items):
    return Command().content(*(items or (CommandItem().label("Go to Billing"),)))


class TestCommand:
    @pytest.mark.asyncio
    async def test_a_modal_whose_field_is_a_combobox_for_a_listbox(self, context_args):
        html = await render_tree(_command(), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "aria-modal", "true")
        assert_attr(html, '[role="dialog"]', "aria-label", "Command palette")
        assert_attr(html, '[role="dialog"]', "x-trap.inert.noscroll", "open")
        field = 'input[role="combobox"]'
        assert_attr(html, field, "aria-autocomplete", "list")
        assert_attr(html, field, "aria-expanded", "true")
        assert_attr(html, field, ":aria-activedescendant", "active")
        assert_attr(html, '[role="listbox"]', "aria-label", "Command palette")

    @pytest.mark.asyncio
    async def test_the_trap_focuses_the_field(self, context_args):
        # Focused by the trap rather than by script, so the trap remembers
        # the trigger and gives focus back to it on close.
        html = await render_tree(_command(), context_args=context_args)
        assert_selector(html, '[role="dialog"] input[role="combobox"][autofocus]')

    @pytest.mark.asyncio
    async def test_label_names_the_palette(self, context_args):
        html = await render_tree(_command().label("Search"), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "aria-label", "Search")
        assert_attr(html, "input", "aria-label", "Search")

    @pytest.mark.asyncio
    async def test_nothing_matching_is_announced(self, context_args):
        html = await render_tree(
            _command().empty_message("No luck."), context_args=context_args
        )
        assert_selector(html, '[role="status"]')
        assert "No luck." in html

    # hotkey(): both branches
    @pytest.mark.asyncio
    async def test_the_hotkey_reaches_the_browser_in_lower_case(self, context_args):
        html = await render_tree(
            _command().hotkey("mod", "K"), context_args=context_args
        )
        assert '["mod", "k"]' in select(html, "[x-data]")[0]["x-data"]

    @pytest.mark.asyncio
    async def test_without_a_hotkey_none_is_bound(self, context_args):
        html = await render_tree(_command(), context_args=context_args)
        assert "[]" in select(html, "[x-data]")[0]["x-data"]

    # trigger(): both branches
    @pytest.mark.asyncio
    async def test_a_trigger_opens_it(self, context_args):
        html = await render_tree(
            _command().trigger(Button().content("Search")),
            context_args=context_args,
        )
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", "@click", "open = true")

    @pytest.mark.asyncio
    async def test_without_a_trigger_there_is_no_button(self, context_args):
        html = await render_tree(_command(), context_args=context_args)
        assert_no_selector(html, "button")


class TestCommandGroup:
    @pytest.mark.asyncio
    async def test_a_group_is_named_by_its_label(self, context_args):
        html = await render_tree(
            _command(
                CommandGroup()
                .label("Navigate")
                .content(CommandItem().label("Go to Billing"))
            ),
            context_args=context_args,
        )
        assert_attr(
            html, '[role="group"]', ":aria-labelledby", "$id('hue-command-group')"
        )
        assert "Navigate" in html


class TestCommandItem:
    async def _item(self, item, context_args):
        return await render_tree(_command(item), context_args=context_args)

    @pytest.mark.asyncio
    async def test_an_item_is_an_option_that_never_takes_focus(self, context_args):
        html = await self._item(CommandItem().label("Go to Billing"), context_args)
        assert_attr(html, '[role="option"]', "tabindex", "-1")
        assert_attr(html, '[role="option"]', "data-label", "Go to Billing")

    # href(): both branches
    @pytest.mark.asyncio
    async def test_an_href_draws_a_link(self, context_args):
        html = await self._item(
            CommandItem().label("Billing").href("/billing"), context_args
        )
        assert_attr(html, 'a[role="option"]', "href", "/billing")

    @pytest.mark.asyncio
    async def test_without_an_href_it_is_not_a_link(self, context_args):
        html = await self._item(CommandItem().label("Billing"), context_args)
        assert_no_selector(html, "a")

    @pytest.mark.asyncio
    async def test_a_disabled_link_goes_nowhere(self, context_args):
        html = await self._item(
            CommandItem().label("Billing").href("/billing").disabled(), context_args
        )
        assert_no_selector(html, "a")
        assert_attr(html, '[role="option"]', "aria-disabled", "true")

    # action(): both branches
    @pytest.mark.asyncio
    async def test_an_action_runs_on_the_command_event(self, context_args):
        html = await self._item(
            CommandItem().label("Create").action(unsafe("create()")), context_args
        )
        assert_attr(html, '[role="option"]', "x-on:command.stop", "create()")

    @pytest.mark.asyncio
    async def test_without_an_action_nothing_listens(self, context_args):
        html = await self._item(CommandItem().label("Create"), context_args)
        assert_no_selector(html, "[x-on\\:command\\.stop]")

    def test_an_action_must_be_an_expression(self):
        with pytest.raises(TypeError):
            CommandItem().action("create()")  # type: ignore[arg-type]

    # keywords(): both branches
    @pytest.mark.asyncio
    async def test_keywords_are_searched(self, context_args):
        html = await self._item(
            CommandItem().label("Theme").keywords("dark", "mode"), context_args
        )
        assert_attr(html, '[role="option"]', "data-keywords", "dark mode")

    @pytest.mark.asyncio
    async def test_without_keywords_only_the_label_is(self, context_args):
        html = await self._item(CommandItem().label("Theme"), context_args)
        assert_no_selector(html, "[data-keywords]")

    # description() and meta(): both branches
    @pytest.mark.asyncio
    async def test_description_and_meta_are_drawn(self, context_args):
        html = await self._item(
            CommandItem()
            .label("Create invoice")
            .description("Starts a draft")
            .meta("$1,200"),
            context_args,
        )
        text = select(html, '[role="option"]')[0].get_text()
        assert "Starts a draft" in text
        assert "$1,200" in text

    @pytest.mark.asyncio
    async def test_a_plain_item_is_only_its_label(self, context_args):
        html = await self._item(CommandItem().label("Create invoice"), context_args)
        assert select(html, '[role="option"]')[0].get_text(strip=True) == (
            "Create invoice"
        )
