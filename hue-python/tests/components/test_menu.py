import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.ui import (
    Button,
    DropdownMenu,
    MenuItem,
    MenuLabel,
    MenuSeparator,
    Tooltip,
)
from hue.ui.atoms.icon import HueIcon
from hue.ui.molecules import _overlay
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select
from tests._shortcuts import Shortcuts


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
        assert_attr(html, "button[aria-haspopup]", "x-bind:aria-expanded", "open")
        assert_attr(
            html, "button[aria-haspopup]", "x-on:keydown.down.prevent", "open = true"
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
    async def test_tab_leaves_the_menu_rather_than_walking_it(self, context_args):
        # Arrows move between items; Tab is how you get out. The items are
        # out of the tab order, so the browser's Tab already goes to whatever
        # follows the trigger - all the menu does is close, a tick later so
        # the focused item is still there when the browser looks.
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(
            html, "[x-data]", "x-on:keydown.tab", "$nextTick(() => open = false)"
        )
        assert_attr(html, '[role="menuitem"]', "tabindex", "-1")

    @pytest.mark.asyncio
    async def test_the_ring_stays_inside_the_item(self, context_args):
        # An offset ring is drawn outside the item, where it lands on the
        # panel's padding and past its edge.
        html = await render_tree(_menu(), context_args=context_args)
        assert_selector(html, '[role="menuitem"].focus-visible\\:inset-ring-2')

    @pytest.mark.asyncio
    async def test_escape_closes_it_and_hands_focus_back(self, context_args):
        # Stopped, so a dialog the menu sits in stays open.
        html = await render_tree(_menu(), context_args=context_args)
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape",
            "if (open) { $event.stopPropagation(); close() }",
        )
        assert_attr(html, '[role="menu"]', "tabindex", "-1")

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
            html,
            '[role="menu"]',
            "x-anchor.fixed.bottom-end.offset.6",
            _overlay.TRIGGER,
        )
        assert_selector(html, "button[aria-haspopup][data-hue-trigger]", count=1)

    @pytest.mark.asyncio
    async def test_a_tooltip_trigger_is_wired_through_to_its_control(
        self, context_args
    ):
        # The icon-only "More actions" button. Wired onto the tooltip's span,
        # the click lands in the tooltip's scope and aria-expanded on a span.
        menu = _menu().trigger(
            Tooltip().content("More actions").trigger(Button().icon_only("More"))
        )
        html = await render_tree(menu, context_args=context_args)
        assert_attr(html, "button[data-hue-trigger]", "x-on:click", "open = !open")
        assert_attr(html, "button[data-hue-trigger]", "aria-haspopup", "menu")
        assert_attr(html, "button[data-hue-trigger]", ":aria-describedby")
        assert_no_selector(html, "span[aria-haspopup], span[data-hue-trigger]")

    @pytest.mark.asyncio
    async def test_a_tooltip_with_no_control_wires_nothing(self, context_args):
        menu = _menu().trigger(Tooltip().content("More actions"))
        html = await render_tree(menu, context_args=context_args)
        assert_no_selector(html, "[aria-haspopup], [data-hue-trigger]")
        assert_attr(
            html, '[role="menu"]', "x-anchor.fixed.bottom-start.offset.6", "null"
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
    async def test_a_disabled_item_cannot_be_activated(self, context_args):
        # pointer-events-none stops the mouse but not Enter on the focused
        # item, so nothing may be listening for the click it becomes.
        html = await render_tree(
            _menu(
                MenuItem()
                .disabled()
                .on_click(unsafe("deleteProject()"))
                .content("Delete project"),
                MenuItem().disabled().href("/billing").content("Billing"),
            ),
            context_args=context_args,
        )
        items = select(html, '[role="menuitem"]')
        assert [item.name for item in items] == ["button", "a"]
        for item in items:
            assert not [attr for attr in item.attrs if "click" in attr]
            assert item.get("href") is None
            assert item.get("tabindex") == "-1"

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

    # icon()
    @pytest.mark.asyncio
    async def test_an_item_can_carry_an_icon(self, context_args):
        html = await render_tree(
            _menu(MenuItem().icon(HueIcon("copy")).content("Duplicate")),
            context_args=context_args,
        )
        assert_selector(html, '[role="menuitem"] svg')

    # shortcut(): both branches, and what it refuses
    @pytest.mark.asyncio
    async def test_a_shortcut_is_shown_announced_and_run(self, shortcut_context_args):
        item = MenuItem().shortcut(Shortcuts.duplicate)
        html = await render_tree(_menu(item), context_args=shortcut_context_args)
        row = '[role="menuitem"]'
        assert_selector(html, f"{row} kbd")
        # Its label, since the item has none of its own.
        assert "Duplicate" in select(html, row)[0].get_text()
        assert_attr(html, row, "@click", "duplicate()")
        # Announced, not bound: the page binds every shortcut once.
        assert_attr(html, row, "x-shortcut.describe", '["mod+d"]')
        assert_no_selector(html, "[x-shortcut]")
        # Kept out of the item, so rendering it again starts from nothing.
        assert "@click" not in item._attrs

    @pytest.mark.asyncio
    async def test_a_shortcut_brings_its_icon(self, context_args):
        class WithIcon(ShortcutRegistry):
            copy = Shortcut(
                "Copy", "alt+c", action=unsafe("copy()"), icon=HueIcon("copy")
            )

        html = await render_tree(
            _menu(MenuItem().shortcut(WithIcon.copy)),
            context_args={**context_args, "shortcuts": WithIcon},
        )
        assert_selector(html, '[role="menuitem"] svg')

    @pytest.mark.asyncio
    async def test_a_shortcut_with_an_href_makes_a_link(self, shortcut_context_args):
        html = await render_tree(
            _menu(MenuItem().shortcut(Shortcuts.billing)),
            context_args=shortcut_context_args,
        )
        assert_attr(html, 'a[role="menuitem"]', "href", "/billing/")
        assert_no_selector(html, '[role="menuitem"][\\@click]')

    @pytest.mark.parametrize(
        "item",
        [
            MenuItem().shortcut(Shortcuts.duplicate).on_click(unsafe("track()")),
            MenuItem()
            .shortcut(Shortcuts.duplicate)
            .x_on("click.stop", unsafe("track()")),
            MenuItem().shortcut(Shortcuts.duplicate).href("/elsewhere/"),
            MenuItem().shortcut(Shortcuts.duplicate).checkable(),
            MenuItem().shortcut(Shortcuts.duplicate).disabled(),
        ],
        ids=[
            "its own handler",
            "its own handler, with a modifier",
            "its own href",
            "checkable",
            "disabled",
        ],
    )
    @pytest.mark.asyncio
    async def test_a_shortcut_row_does_nothing_else(self, item, shortcut_context_args):
        # The keys only ever run the shortcut, so a click that did something
        # else, or a disabled row whose keys still worked, would disagree.
        with pytest.raises(ValueError):
            await render_tree(_menu(item), context_args=shortcut_context_args)

    @pytest.mark.asyncio
    async def test_a_shortcut_the_app_does_not_bind_is_refused(
        self, context_args, shortcut_context_args
    ):
        # Keys that do nothing are worse than no keys.
        with pytest.raises(ValueError):
            await render_tree(
                _menu(MenuItem().shortcut(Shortcuts.duplicate)),
                context_args=context_args,
            )
        with pytest.raises(ValueError):
            await render_tree(
                _menu(MenuItem().shortcut(Shortcuts.archive)),
                context_args=shortcut_context_args,
            )

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
