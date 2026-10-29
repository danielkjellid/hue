import pytest

from hue.assets import icons_path
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import create_icon_base
from hue.ui.atoms.icon import _format_attr_name, directory_resolver
from tests._a11y import assert_attr, assert_no_selector, assert_selector

# A minimal icon set used by the tests — exercises elements (rect, line, g)
# that are not plain <path>/<circle>, plus a hard-coded width/height.
_BOX_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'width="24" height="24" fill="none">'
    '<g stroke="currentColor"><rect x="3" y="3" width="18" height="18" />'
    '<line x1="3" y1="3" x2="21" y2="21" /></g></svg>'
)


def _icon_base(markup: str = _BOX_SVG):
    return create_icon_base(resolver=lambda name: markup)


class TestIcon:
    """Tests for the bring-your-own-icon component."""

    @pytest.mark.asyncio
    async def test_renders_inline_svg(self, context_args):
        html = await render_tree(_icon_base()("box"), context_args=context_args)
        assert_selector(html, "svg")
        # viewBox is camelCase, so assert on the raw markup rather than via the
        # (case-folding) HTML parser.
        assert 'viewBox="0 0 24 24"' in html

    @pytest.mark.asyncio
    async def test_preserves_all_svg_elements(self, context_args):
        # The old allowlist only kept <path>/<circle>; <g>/<rect>/<line> must
        # survive now that the markup is inlined verbatim.
        html = await render_tree(_icon_base()("box"), context_args=context_args)
        assert_selector(html, "svg g")
        assert_selector(html, "svg rect")
        assert_selector(html, "svg line")

    @pytest.mark.asyncio
    async def test_strips_hardcoded_dimensions(self, context_args):
        # width/height would override CSS sizing utilities like size-4.
        html = await render_tree(_icon_base()("box"), context_args=context_args)
        assert 'width="24"' not in html
        assert 'height="24"' not in html

    @pytest.mark.asyncio
    async def test_class_is_merged(self, context_args):
        html = await render_tree(
            _icon_base()("box").class_("size-4 text-primary"),
            context_args=context_args,
        )
        assert_selector(html, "svg.size-4")
        assert_selector(html, "svg.text-primary")

    @pytest.mark.asyncio
    async def test_id_and_aria_label_apply_to_svg(self, context_args):
        html = await render_tree(
            _icon_base()("box").id("logo").aria_label("Box"),
            context_args=context_args,
        )
        assert_attr(html, "svg", "id", "logo")
        assert_attr(html, "svg", "aria-label", "Box")

    @pytest.mark.asyncio
    async def test_decorative_by_default(self, context_args):
        html = await render_tree(_icon_base()("box"), context_args=context_args)
        assert_attr(html, "svg", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_aria_label_suppresses_decorative_default(self, context_args):
        html = await render_tree(
            _icon_base()("box").aria_label("Box"),
            context_args=context_args,
        )
        assert_no_selector(html, "svg[aria-hidden]")

    @pytest.mark.asyncio
    async def test_empty_name_renders_nothing(self, context_args):
        html = await render_tree(_icon_base()(), context_args=context_args)
        assert_no_selector(html, "svg")

    @pytest.mark.asyncio
    async def test_missing_icon_raises(self, context_args):
        Icon = create_icon_base(icons_dir="/tmp/hue-no-such-icons")
        with pytest.raises(RuntimeError, match="not found"):
            await render_tree(Icon("ghost"), context_args=context_args)

    def test_directory_resolver_reads_an_icon_in_the_directory(self, tmp_path):
        (tmp_path / "box.svg").write_text(_BOX_SVG)
        assert directory_resolver(str(tmp_path))("box") == _BOX_SVG

    def test_directory_resolver_follows_a_symlink_inside_the_directory(self, tmp_path):
        # An icon set can be a folder of links into a vendored package.
        vendored = tmp_path / "vendor"
        vendored.mkdir()
        (vendored / "box.svg").write_text(_BOX_SVG)
        icons = tmp_path / "icons"
        icons.mkdir()
        (icons / "box.svg").symlink_to(vendored / "box.svg")
        assert directory_resolver(str(icons))("box") == _BOX_SVG

    @pytest.mark.parametrize("name", ["../secret", "{root}/secret"])
    def test_directory_resolver_rejects_a_name_outside_the_directory(
        self, tmp_path, name
    ):
        # An icon name can come from request data, and the markup is inlined
        # unescaped, so reading an svg from elsewhere on disk would be stored XSS.
        icons = tmp_path / "icons"
        icons.mkdir()
        (tmp_path / "secret.svg").write_text(_BOX_SVG)
        resolve = directory_resolver(str(icons))
        with pytest.raises(ValueError, match="outside the icon directory"):
            resolve(name.format(root=tmp_path))

    @pytest.mark.asyncio
    async def test_svg_without_viewbox_raises(self, context_args):
        Icon = _icon_base('<svg xmlns="http://www.w3.org/2000/svg"><rect /></svg>')
        with pytest.raises(RuntimeError, match="viewBox"):
            await render_tree(Icon("bad"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_custom_resolver_is_used(self, context_args):
        calls: list[str] = []

        def resolver(name: str) -> str:
            calls.append(name)
            return _BOX_SVG

        Icon = create_icon_base(resolver=resolver)
        await render_tree(Icon("anything"), context_args=context_args)
        assert calls == ["anything"]

    def test_create_icon_base_requires_a_source(self):
        with pytest.raises(ValueError, match="icons_dir or a resolver"):
            create_icon_base()

    @pytest.mark.asyncio
    async def test_alpine_attrs_survive_on_rendered_svg(self, context_args):
        # End-to-end check that base-mixin Alpine attrs reach the <svg> intact:
        # they must not be rewritten the way aria_* keys are (see the contract
        # test below for why).
        html = await render_tree(
            _icon_base()("box")
            .x_data("{ open: false }")
            .x_on("click", unsafe("open = true")),
            context_args=context_args,
        )
        assert_attr(html, "svg", "x-data", "{ open: false }")
        assert_attr(html, "svg", "@click", "open = true")


def test_hues_own_icons_carry_no_title():
    # A title shows as a hover tooltip and joins the text of whatever the
    # icon sits in, so a button labelled Shipping read "Shipping chevron-down".
    titled = [p.name for p in icons_path().glob("*.svg") if "<title" in p.read_text()]
    assert titled == []


class TestAttrNameContract:
    """
    Pin the htmy attribute-name formatting that _svg_attrs depends on.

    _svg_attrs merges the component's attrs with the SVG file's and runs its
    dedup + decorative-default check in htmy's *formatted* key namespace, via
    _format_attr_name (which is htmy's own Formatter.format_name). If an htmy
    upgrade changed that formatting, the breakage would be silent — so assert the
    two behaviours we rely on here, where it fails loudly instead.
    """

    def test_aria_underscores_become_hyphens(self):
        # Load-bearing: the decorative-default check keys off "aria-label"/"role",
        # but the mixins store these as aria_label/aria_hidden.
        assert _format_attr_name("aria_label") == "aria-label"
        assert _format_attr_name("aria_hidden") == "aria-hidden"

    def test_alpine_and_ajax_attrs_pass_through(self):
        # Alpine/AJAX keys carry no underscores, so they must survive verbatim.
        alpine = (
            "x-data",
            "@click",
            ":src",
            "x-transition:enter.start",
            "@ajax:before",
        )
        for name in alpine:
            assert _format_attr_name(name) == name
