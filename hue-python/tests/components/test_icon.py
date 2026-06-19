import pytest

from hue.renderer import render_tree
from hue.ui import create_icon_base
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
