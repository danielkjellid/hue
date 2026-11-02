import re
from pathlib import Path
from typing import get_args

import pytest

import hue
from hue.pages import create_page_base
from hue.palette import Color
from hue.renderer import render_tree
from hue.theme import ColorToken, FontToken, RadiusToken, Ramp, Theme
from tests._a11y import select

_VIOLET = Ramp(
    [
        "#F5F3FF",
        "#EDE9FE",
        "#DDD6FE",
        "#C4B5FD",
        "#A78BFA",
        "#8B5CF6",
        "#7C3AED",
        "#6D28D9",
        "#5B21B6",
        "#4C1D95",
    ]
)


def test_the_token_names_are_the_stylesheets():
    # A token added to the stylesheet and not here cannot be themed, and one
    # renamed there leaves a name here that sets nothing.
    css = (Path(hue.__file__).parent / "static/styles/tailwind.input.css").read_text()
    block = css[css.index("@theme static {") :]
    block = block[: block.index("\n}")]
    for prefix, token, skipped in (
        ("color", ColorToken, set()),
        ("font", FontToken, set()),
        ("radius", RadiusToken, {"full"}),
    ):
        found = set(re.findall(rf"^\s*--{prefix}-([\w-]+):", block, re.MULTILINE))
        assert found - skipped == set(get_args(token.__value__)), prefix


@pytest.mark.parametrize(
    "build",
    [
        lambda: Ramp(["#fff"] * 9),
        lambda: Theme(colors={"surfce": Color("#fff")}),  # type: ignore[dict-item]
        lambda: Theme(fonts={"ui": "Inter} body {display:none"}),
        lambda: Theme(radii={"md": "4px</style><script>"}),
    ],
)
def test_a_theme_that_would_misfire_is_refused(build):
    with pytest.raises(ValueError):
        build()


@pytest.mark.asyncio
async def test_the_theme_sits_between_hues_stylesheet_and_the_apps(context_args):
    page = create_page_base(
        css_url="/hue.css",
        js_url="/hue.js",
        html_title_factory=lambda title: title,
        extra_css_urls=["/app.css"],
        theme=Theme(accent=_VIOLET),
    )
    html = await render_tree(page(title="t", body="b"), context_args=context_args)
    head = [
        tag.get("href") or tag.name for tag in select(html, "head link, head style")
    ]
    assert head == ["/hue.css", "style", "/app.css"]
