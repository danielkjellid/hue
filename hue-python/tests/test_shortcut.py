import pytest

from hue import scope, shortcuts
from hue.context import HueContextArgs
from hue.js import unsafe
from hue.pages import create_page_base
from hue.renderer import render_tree
from hue.router import HueResponse
from hue.shortcuts import Shortcut, ShortcutRegistry, binding, parse_keys
from hue.ui import MenuItem
from tests._a11y import assert_attr, assert_no_selector, assert_selector
from tests._shortcuts import Shortcuts
from tests.conftest import MockRouter

_Page = create_page_base(css_url="/s.css", js_url="/a.js", html_title_factory=str)


@pytest.fixture
def request_scope():
    """
    The request's state, open as the router and the middleware open it.
    """
    with scope.request_scope():
        yield


class TestKeys:
    def test_a_chord_and_a_sequence_parse_to_their_keys(self):
        assert parse_keys(("Mod+K",)) == (("mod", "k"),)
        assert parse_keys(("g", "b")) == (("g",), ("b",))

    def test_modifiers_keep_the_order_they_were_written_in(self):
        # It is the order Kbd draws them in.
        assert parse_keys(("shift+mod+k",)) == (("shift", "mod", "k"),)

    def test_another_name_for_a_key_becomes_its_own(self):
        assert parse_keys(("ctrl+escape", "alt+arrowup")) == (
            ("ctrl", "esc"),
            ("alt", "up"),
        )

    @pytest.mark.parametrize(
        "steps",
        [
            (),
            ("mod",),
            ("mod+",),
            ("mod++",),
            ("cmd+k",),
            ("spcae",),
            ("shift+1",),
            ("shift+é",),
            ("é",),
            ("alt+/",),
            ("tab",),
            ("shift+enter",),
            ("esc",),
        ],
        ids=[
            "nothing",
            "a modifier alone",
            "no key",
            "the plus key",
            "an unknown modifier",
            "a key that is not one",
            "shift on a digit, which types another character",
            "shift on a letter outside ASCII",
            "a character outside ASCII",
            "alt on a symbol, which Option composes",
            "tab on its own, which moves focus",
            "enter with only shift, which presses a control",
            "esc on its own, which closes overlays",
        ],
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

    @pytest.mark.parametrize(
        ("first", "second"),
        [("mod+k", "mod+k"), ("mod+k", "ctrl+k"), ("mod+esc", "mod+escape")],
        ids=["the same", "mod and ctrl away from Apple", "two names for one key"],
    )
    def test_the_same_press_twice_is_refused(self, first, second):
        with pytest.raises(ValueError, match="same keys"):

            class _(ShortcutRegistry):
                a = Shortcut("A", first, href="/a/")
                b = Shortcut("B", second, href="/b/")

    def test_a_key_that_starts_a_sequence_is_refused(self):
        # G would run on the first press, so G then B could never finish.
        with pytest.raises(ValueError, match="never could"):

            class _(ShortcutRegistry):
                a = Shortcut("A", "g", href="/a/")
                b = Shortcut("B", "g", "b", href="/b/")

    def test_a_key_inside_a_sequence_is_refused(self):
        # B would run as soon as G then B was pressed, and G then B then C
        # could never get its last key.
        with pytest.raises(ValueError, match="never could finish"):

            class _(ShortcutRegistry):
                a = Shortcut("A", "b", href="/a/")
                b = Shortcut("B", "g", "b", "c", href="/b/")

    def test_a_shortcut_cannot_take_a_name_the_registry_uses(self):
        with pytest.raises(ValueError, match="uses itself"):

            class _(ShortcutRegistry):
                active = Shortcut("A", "a", href="/a/")

    def test_a_subclass_can_take_an_inherited_shortcut_out(self):
        class Fewer(Shortcuts):
            duplicate = None

        assert Shortcuts.duplicate not in Fewer.shortcuts

    def test_a_key_that_ends_a_sequence_is_allowed(self):
        # The browser prefers the longer match, so both stay reachable.
        class Both(ShortcutRegistry):
            a = Shortcut("A", "b", href="/a/")
            b = Shortcut("B", "g", "b", href="/b/")

        assert len(Both.shortcuts) == 2

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

    def test_a_scoped_shortcut_can_keep_what_it_was_declared_with(self, request_scope):
        class Declared(ShortcutRegistry):
            archive = Shortcut("Archive", "e", href="/archive/", scoped=True)

        shortcuts.use(Declared.archive)
        (archive,) = Declared.active()
        assert archive.href == "/archive/"

    def test_a_scoped_shortcut_needs_something_to_do(self, request_scope):
        with pytest.raises(ValueError):
            shortcuts.use(Shortcuts.archive)

    def test_use_outside_a_request_is_refused(self):
        with pytest.raises(RuntimeError):
            shortcuts.use(Shortcuts.archive, action=unsafe("archive()"))


class TestPage:
    @pytest.mark.asyncio
    async def test_a_page_binds_each_shortcut_that_is_on(
        self, shortcut_context_args, request_scope
    ):
        shortcuts.use(Shortcuts.archive, href="/invoices/2048/archive/")
        html = await render_tree(
            _Page(title="Invoices", body="Hello"),
            context_args=shortcut_context_args,
        )
        assert_attr(html, 'a[x-shortcut=\'["g", "b"]\']', "href", "/billing/")
        duplicate = "button[x-shortcut='[\"mod+d\"]']"
        assert_attr(html, duplicate, "x-on:click", "duplicate()")
        assert_attr(html, "a[x-shortcut='[\"e\"]']", "href", "/invoices/2048/archive/")
        # Hidden, and out of the accessibility tree: the rows announce them.
        assert_attr(html, "#hue-shortcuts", "aria-hidden", "true")
        # Synced, so a fragment that brings its own replaces this one.
        assert_attr(html, "#hue-shortcuts", "x-sync")

    @pytest.mark.asyncio
    async def test_an_href_can_be_built_from_the_request(self, context_args):
        class Reversed(ShortcutRegistry):
            home = Shortcut("Home", "g", "h", href=lambda request: "/from-request/")

        html = await render_tree(
            _Page(title="Home", body="Hello"),
            context_args=HueContextArgs(**context_args, shortcuts=Reversed),
        )
        assert_attr(html, "a[x-shortcut]", "href", "/from-request/")

    @pytest.mark.asyncio
    async def test_an_app_without_a_registry_binds_nothing(self, context_args):
        html = await render_tree(
            _Page(title="Home", body="Hello"), context_args=context_args
        )
        assert_no_selector(html, "[x-shortcut]")


class TestBinding:
    def test_keys_are_written_as_the_browser_spells_them(self):
        # KeyboardEvent.key, which aria-keyshortcuts uses too, so the browser
        # needs no table of key names to match or announce them.
        steps = parse_keys(("ctrl+esc", "alt+up", "f5", "mod+k"))
        assert binding(steps) == {
            "x-shortcut": '["ctrl+Escape", "alt+ArrowUp", "F5", "mod+k"]'
        }


class _AppRouter(MockRouter):
    """
    A router for an app with a shortcut registry, as hue-django's is with
    HUE_SHORTCUTS set.
    """

    def __init__(self, registry: type[ShortcutRegistry]) -> None:
        super().__init__()
        self.registry = registry

    def _get_context_args(self, request):
        return HueContextArgs(
            **super()._get_context_args(request), shortcuts=self.registry
        )


class TestFragments:
    async def _fragment(self, view, mock_request, registry=Shortcuts):
        wrapped = _AppRouter(registry)._wrap_view(view, require_ajax=True)
        request = mock_request(headers={"X-Alpine-Request": "true"})
        html, _ = await wrapped(None, request)
        return html

    @pytest.mark.asyncio
    async def test_a_fragment_that_uses_a_shortcut_rebinds_the_page(self, mock_request):
        # The swapped-in invoice says what its archive key archives now.
        async def invoice(view, request, context):
            shortcuts.use(Shortcuts.archive, action=unsafe("archive(2049)"))
            return MenuItem().shortcut(Shortcuts.archive)

        html = await self._fragment(invoice, mock_request)
        assert_attr(html, "#hue-shortcuts", "x-sync")
        archive = "button[x-shortcut='[\"e\"]']"
        assert_attr(html, archive, "x-on:click", "archive(2049)")

    @pytest.mark.asyncio
    async def test_a_page_wrapped_in_a_response_is_bound_once(self, mock_request):
        async def missing(view, request, context):
            shortcuts.use(Shortcuts.archive, action=unsafe("archive(1)"))
            return HueResponse(
                component=_Page(title="Gone", body="Gone"), status_code=404
            )

        html = await self._fragment(missing, mock_request)
        assert_selector(html, "#hue-shortcuts", count=1)

    @pytest.mark.asyncio
    async def test_a_fragment_that_uses_none_turns_the_scoped_ones_off(
        self, mock_request
    ):
        # The invoice it archived has been swapped away, so the key must not
        # go on archiving it.
        async def listing(view, request, context):
            return MenuItem().shortcut(Shortcuts.duplicate)

        html = await self._fragment(listing, mock_request)
        assert_attr(html, "#hue-shortcuts", "x-sync")
        assert_no_selector(html, "button[x-shortcut='[\"e\"]']")

    @pytest.mark.asyncio
    async def test_an_app_without_scoped_shortcuts_sends_no_bindings(
        self, mock_request
    ):
        class Global(ShortcutRegistry):
            home = Shortcut("Home", "g", "h", href="/")

        async def listing(view, request, context):
            return "Invoices"

        html = await self._fragment(listing, mock_request, registry=Global)
        assert_no_selector(html, "#hue-shortcuts")
