import json

import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Button, Command, CommandGroup, CommandItem, CommandShortcuts
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select
from tests._shortcuts import Shortcuts


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

    @pytest.mark.asyncio
    async def test_escape_closes_it_and_goes_no_further(self, context_args):
        # Stopped on the palette, so a page-wide Escape behind it hears
        # nothing; the scrim keeps a click's focus inside for it to work.
        html = await render_tree(_command(), context_args=context_args)
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape",
            "if (open) { $event.stopPropagation(); close() }",
        )
        assert_attr(html, "[x-on\\:click\\.self]", "tabindex", "-1")

    @pytest.mark.asyncio
    async def test_the_hotkey_toggles_the_palette(self, context_args):
        html = await render_tree(_command().hotkey("mod+K"), context_args=context_args)
        root = select(html, "[x-shortcut]")[0]
        assert root["x-shortcut"] == '["mod+k"]'
        # The palette is not something to click, so it takes the event.
        assert root["x-on:hue:shortcut.prevent"] == "open = !open"

    @pytest.mark.asyncio
    async def test_a_trigger_opens_it(self, context_args):
        html = await render_tree(
            _command().trigger(Button().content("Search")),
            context_args=context_args,
        )
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", "x-on:click", "open = true")

    @pytest.mark.asyncio
    async def test_the_empty_message_reaches_the_browser(self, context_args):
        # hueCommand(startsOpen, emptyMessage): a message in the wrong place
        # leaves the empty list saying nothing.
        html = await render_tree(
            Command().hotkey("mod+k").empty_message("Nothing here."),
            context_args=context_args,
        )
        data = select(html, "[x-data^=hueCommand]")[0]["x-data"]
        assert json.loads(f"[{data[len('hueCommand(') : -1]}]") == [
            False,
            "Nothing here.",
        ]


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

    @pytest.mark.asyncio
    async def test_an_href_draws_a_link(self, context_args):
        html = await self._item(
            CommandItem().label("Billing").href("/billing"), context_args
        )
        assert_attr(html, 'a[role="option"]', "href", "/billing")

    @pytest.mark.asyncio
    async def test_a_disabled_link_goes_nowhere(self, context_args):
        html = await self._item(
            CommandItem().label("Billing").href("/billing").disabled(), context_args
        )
        assert_no_selector(html, "a")
        assert_attr(html, '[role="option"]', "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_an_action_runs_on_the_command_event(self, context_args):
        html = await self._item(
            CommandItem().label("Create").action(unsafe("create()")), context_args
        )
        assert_attr(html, '[role="option"]', "x-on:command.stop", "create()")

    def test_an_action_must_be_an_expression(self):
        with pytest.raises(TypeError):
            CommandItem().action("create()")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_keywords_are_searched(self, context_args):
        html = await self._item(
            CommandItem().label("Theme").keywords("dark", "mode"), context_args
        )
        assert_attr(html, '[role="option"]', "data-keywords", "dark mode")

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


class TestCommandShortcuts:
    @pytest.mark.asyncio
    async def test_the_palette_lists_the_shortcuts_with_their_keys(
        self, shortcut_context_args
    ):
        # No page around it, as in a fragment: the registry is in the context.
        html = await render_tree(
            Command().content(CommandShortcuts()), context_args=shortcut_context_args
        )
        labels = [o["data-label"] for o in select(html, '[role="option"]')]
        assert labels == ["Duplicate", "Go to Billing"]
        assert "Navigate" in select(html, '[role="group"]')[0].get_text()
        billing = 'a[role="option"]'
        assert_attr(html, billing, "href", "/billing/")
        assert_attr(html, billing, "x-shortcut.describe", '["g", "b"]')
        assert select(html, f"{billing} kbd")
        # The page binds them; the palette only shows them.
        assert_no_selector(html, '[role="option"][x-shortcut]')

    @pytest.mark.asyncio
    async def test_listing_shortcuts_needs_an_app_with_some(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(
                Command().content(CommandShortcuts()), context_args=context_args
            )

    @pytest.mark.asyncio
    async def test_a_hotkey_that_collides_with_a_shortcut_is_refused(
        self, shortcut_context_args
    ):
        with pytest.raises(ValueError, match="same keys"):
            await render_tree(
                Command().hotkey("mod+d"), context_args=shortcut_context_args
            )

    @pytest.mark.parametrize(
        "row",
        [
            CommandItem().shortcut(Shortcuts.duplicate).href("/elsewhere/"),
            CommandItem().shortcut(Shortcuts.duplicate).action(unsafe("other()")),
            CommandItem().shortcut(Shortcuts.duplicate).disabled(),
        ],
        ids=["its own href", "its own action", "disabled"],
    )
    @pytest.mark.asyncio
    async def test_a_shortcut_row_does_nothing_else(self, row, shortcut_context_args):
        with pytest.raises(ValueError):
            await render_tree(
                Command().content(row), context_args=shortcut_context_args
            )
