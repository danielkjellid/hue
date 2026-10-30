import pytest

from hue.renderer import render_tree
from hue.ui import Panel


class TestPanel:
    @pytest.mark.asyncio
    async def test_renders_its_label_hint_and_content(self, context_args):
        html = await render_tree(
            Panel().label("Scale").hint("14px is the default").content("Specimen"),
            context_args=context_args,
        )
        assert "Scale" in html
        assert "14px is the default" in html
        assert "Specimen" in html
