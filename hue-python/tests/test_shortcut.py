import pytest

from hue import shortcuts
from hue.js import unsafe
from hue.pages import create_page_base
from hue.renderer import render_tree
from hue.shortcuts import Shortcut, ShortcutRegistry, parse_keys
from hue.ui import Command, CommandShortcuts
from tests._a11y import assert_attr, assert_no_selector, select
from tests._shortcuts import OnPage, Shortcuts


@pytest.fixture
def request_scope():
    """
    The list shortcuts.use() writes to, open as the router opens it.
    """
    token = shortcuts.open()
    yield
    shortcuts.close(token)


class TestKeys:
    def test_a_chord_and_a_sequence_parse_to_their_keys(self):
        assert parse_keys(("Mod+K",)) == (("mod", "k"),)
        assert parse_keys(("g", "b")) == (("g",), ("b",))

    @pytest.mark.parametrize(
        "steps",
        [(), ("mod",), ("mod+",), ("cmd+k",)],
        ids=["nothing", "a modifier alone", "no key", "an unknown modifier"],
    )
    def test_what_could_never_match_is_refused(self, steps):
        with pytest.raises(ValueError):
            parse_keys(steps)


class TestRegistry:
    def test_the_attributes_are_the_shortcuts_in_order(self):
        assert [s.name for s in Shortcuts.shortcuts] == [
            "billing",
            "duplicate",
            "archive",
        ]

    def test_the_same_keys_twice_are_refused_when_the_class_is_made(self):
        with pytest.raises(ValueError, match="same keys"):

            class _(ShortcutRegistry):
                a = Shortcut("A", "mod+k", href="/a/")
                b = Shortcut("B", "mod+k", href="/b/")

    def test_mod_and_ctrl_are_the_same_keys_away_from_apple(self):
        with pytest.raises(ValueError, match="same keys"):

            class _(ShortcutRegistry):
                a = Shortcut("A", "mod+k", href="/a/")
                b = Shortcut("B", "ctrl+k", href="/b/")

    def test_a_key_that_starts_a_sequence_is_refused(self):
        # G would run on the first press, so G then B could never finish.
        with pytest.raises(ValueError, match="never could"):

            class _(ShortcutRegistry):
                a = Shortcut("A", "g", href="/a/")
                b = Shortcut("B", "g", "b", href="/b/")

    def test_a_shortcut_needs_something_to_do_unless_scoped(self):
        with pytest.raises(ValueError):
            Shortcut("A", "a")
        Shortcut("A", "a", scoped=True)

    def test_an_action_must_be_an_expression(self):
        with pytest.raises(TypeError):
            Shortcut("A", "a", action="go()")  # type: ignore[arg-type]


class TestUse:
    def test_scoped_shortcuts_are_off_until_used(self, request_scope):
        assert Shortcuts.archive not in [a.shortcut for a in Shortcuts.active()]
        shortcuts.use(Shortcuts.archive, action=unsafe("archive(2048)"))
        (archive,) = [a for a in Shortcuts.active() if a.shortcut is Shortcuts.archive]
        assert archive.action == "archive(2048)"

    def test_a_shortcut_on_every_page_cannot_be_used(self, request_scope):
        with pytest.raises(ValueError):
            shortcuts.use(Shortcuts.billing)

    def test_a_scoped_shortcut_needs_something_to_do(self, request_scope):
        with pytest.raises(ValueError):
            shortcuts.use(Shortcuts.archive)

    def test_use_outside_a_request_is_refused(self):
        with pytest.raises(RuntimeError):
            shortcuts.use(Shortcuts.archive, action=unsafe("archive()"))


class TestPage:
    def _page(self, registry=None):
        return create_page_base(
            css_url="/s.css",
            js_url="/a.js",
            html_title_factory=str,
            shortcuts=registry,
        )

    @pytest.mark.asyncio
    async def test_a_page_binds_each_shortcut_that_is_on(
        self, context_args, request_scope
    ):
        shortcuts.use(Shortcuts.archive, href="/invoices/2048/archive/")
        Page = self._page(Shortcuts)
        html = await render_tree(
            Page(title="Invoices", body="Hello"), context_args=context_args
        )
        assert_attr(html, 'a[x-shortcut=\'["g", "b"]\']', "href", "/billing/")
        assert_attr(
            html, "button[x-shortcut='[\"mod+d\"]']", "x-on:click", "duplicate()"
        )
        assert_attr(html, "a[x-shortcut='[\"e\"]']", "href", "/invoices/2048/archive/")
        # Hidden, and out of the accessibility tree: the rows announce them.
        assert_attr(html, "div[hidden]", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_an_href_can_be_built_from_the_request(self, context_args):
        class Reversed(ShortcutRegistry):
            home = Shortcut("Home", "g", "h", href=lambda request: "/from-request/")

        html = await render_tree(
            self._page(Reversed)(title="Home", body="Hello"),
            context_args=context_args,
        )
        assert_attr(html, "a[x-shortcut]", "href", "/from-request/")

    @pytest.mark.asyncio
    async def test_a_page_without_a_registry_binds_nothing(self, context_args):
        html = await render_tree(
            self._page()(title="Home", body="Hello"), context_args=context_args
        )
        assert_no_selector(html, "[x-shortcut]")


class TestCommand:
    @pytest.mark.asyncio
    async def test_the_palette_lists_the_shortcuts_with_their_keys(self, context_args):
        html = await render_tree(
            OnPage(Command().content(CommandShortcuts())), context_args=context_args
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
    async def test_listing_shortcuts_needs_a_page_with_some(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(
                Command().content(CommandShortcuts()), context_args=context_args
            )

    @pytest.mark.asyncio
    async def test_a_hotkey_that_collides_with_a_shortcut_is_refused(
        self, context_args
    ):
        with pytest.raises(ValueError, match="same keys"):
            await render_tree(
                OnPage(Command().hotkey("mod+d")), context_args=context_args
            )
