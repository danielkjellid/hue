import pytest

from hue.renderer import render_tree
from hue.ui import Button, DropdownMenu, Kbd, MenuItem, MenuLabel, MenuSeparator
from hue.ui.atoms.icon import HueIcon
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _menu(*items):
    return (
        DropdownMenu()
        .label("Project actions")
        .trigger(Button().variant("outline").content("Project actions"))
        .content(*(items or (MenuItem().content("Duplicate"),)))
    )


class TestDropdownMenu:
    @pytest.mark.asyncio
    async def test_the_trigger_opens_it_and_says_so(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(html, "button[aria-haspopup]", "aria-haspopup", "menu")
        assert_attr(html, "button[aria-haspopup]", ":aria-expanded", "open")
        assert_attr(
            html, "button[aria-haspopup]", "@keydown.down.prevent", "open = true"
        )

    @pytest.mark.asyncio
    async def test_the_arrow_keys_walk_the_items_and_wrap(self, context_args):
        # Without this a menu is a list of buttons the arrow keys ignore.
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(
            html, '[role="menu"]', "x-on:keydown.down.prevent", "$focus.wrap().next()"
        )
        assert_attr(
            html,
            '[role="menu"]',
            "x-on:keydown.up.prevent",
            "$focus.wrap().previous()",
        )
        assert_attr(html, '[role="menu"]', "x-effect")

    @pytest.mark.asyncio
    async def test_escape_closes_it_and_hands_focus_back(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-on:keydown.escape.window", "if (open) close()")

    @pytest.mark.asyncio
    async def test_the_menu_is_named(self, context_args):
        # The trigger's own name is read first; this is the group the items
        # belong to.
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(html, '[role="menu"]', "aria-label", "Project actions")

    @pytest.mark.asyncio
    async def test_it_hangs_off_the_trigger(self, context_args):
        html = await render_tree(
            _menu().placement("bottom-end"), context_args=context_args
        )
        assert_attr(
            html, '[role="menu"]', "x-anchor.bottom-end.offset.6", "$refs.trigger"
        )


class TestMenuItem:
    @pytest.mark.asyncio
    async def test_hovering_moves_focus_so_one_item_is_active(self, context_args):
        # Otherwise the ring sits on the item the keyboard left and the
        # highlight on the one the pointer is over, and two rows look active.
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(
            html,
            '[role="menuitem"]',
            "x-on:mouseenter",
            "$el.focus({ preventScroll: true })",
        )

    @pytest.mark.asyncio
    async def test_picking_one_closes_the_menu(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(html, '[role="menuitem"]', "x-on:click", "close()")

    # href(): both branches
    @pytest.mark.asyncio
    async def test_an_item_with_a_destination_is_a_link(self, context_args):
        html = await render_tree(
            _menu(MenuItem().href("/settings").content("Settings")),
            context_args=context_args,
        )
        assert_attr(html, 'a[role="menuitem"]', "href", "/settings")

    @pytest.mark.asyncio
    async def test_an_item_without_one_is_a_button(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_selector(html, 'button[role="menuitem"]')

    # checkable(): both branches
    @pytest.mark.asyncio
    async def test_a_checkable_item_answers_its_own_click(self, context_args):
        html = await render_tree(
            _menu(MenuItem().checkable().checked().content("Public link")),
            context_args=context_args,
        )
        assert_attr(html, '[role="menuitemcheckbox"]', ":aria-checked", "checked")
        assert_attr(html, '[role="menuitemcheckbox"]', "x-data", "{ checked: true }")
        assert_selector(html, "span.checkmark")

    @pytest.mark.asyncio
    async def test_an_ordinary_item_has_no_tick(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_no_selector(html, "span.checkmark")

    # disabled(): both branches
    @pytest.mark.asyncio
    async def test_a_disabled_item_stays_in_the_menu(self, context_args):
        # Out of reach but still announced: an action that disappears when it
        # cannot be used leaves nothing to explain why.
        html = await render_tree(
            _menu(MenuItem().disabled().content("Transfer ownership")),
            context_args=context_args,
        )
        assert_attr(html, '[role="menuitem"]', "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_an_enabled_item_says_nothing(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_no_selector(html, "[aria-disabled]")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_the_danger_variant_is_the_only_coloured_item(self, context_args):
        html = await render_tree(
            _menu(MenuItem().variant("danger").content("Delete")),
            context_args=context_args,
        )
        assert_selector(html, '[role="menuitem"].text-danger-text')

    @pytest.mark.asyncio
    async def test_the_default_variant_takes_the_menu_colour(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_selector(html, '[role="menuitem"].text-fg')

    # icon() and shortcut(): both branches
    @pytest.mark.asyncio
    async def test_an_item_can_carry_an_icon_and_a_shortcut(self, context_args):
        html = await render_tree(
            _menu(
                MenuItem()
                .icon(HueIcon("copy"))
                .shortcut(Kbd("mod", "D"))
                .content("Duplicate")
            ),
            context_args=context_args,
        )
        assert_selector(html, '[role="menuitem"] svg')
        assert_selector(html, '[role="menuitem"] kbd')

    @pytest.mark.asyncio
    async def test_a_bare_item_is_just_its_label(self, context_args):
        html = await render_tree(_menu(), context_args=context_args)
        assert_no_selector(html, '[role="menuitem"] svg')
        assert_no_selector(html, '[role="menuitem"] kbd')


class TestMenuParts:
    @pytest.mark.asyncio
    async def test_a_separator_is_a_rule(self, context_args):
        html = await render_tree(_menu(MenuSeparator()), context_args=context_args)
        assert_selector(html, '[role="menu"] hr')

    @pytest.mark.asyncio
    async def test_a_label_heads_a_run_of_items(self, context_args):
        html = await render_tree(
            _menu(MenuLabel().content("Sharing")), context_args=context_args
        )
        assert_selector(html, '[role="menu"] div.uppercase')
