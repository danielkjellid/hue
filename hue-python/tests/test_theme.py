import re
from dataclasses import fields
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

import hue
from hue import theme
from hue.pages import create_page_base
from hue.renderer import render_tree
from hue.theme import Accent, Corners, Fonts, Theme
from tests._a11y import select

_VIOLET = [
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


def test_every_token_in_the_stylesheet_has_one_field():
    # A token added to the stylesheet and not here cannot be themed, and a
    # field whose token was renamed there sets nothing.
    css = (Path(hue.__file__).parent / "static/styles/tailwind.input.css").read_text()
    block = css[css.index("@theme static {") :]
    block = block[: block.index("\n}")]
    in_css = set(re.findall(r"^\s*(--(?:color|font|radius)-[\w-]+):", block, re.M))
    hints = get_type_hints(Theme, vars(theme))
    reached = []
    for field in fields(Theme):
        group = get_args(hints[field.name])[0]
        assert set(group._TOKENS) == {f.name for f in fields(group)}, group
        reached += [token.format(tone=field.name) for token in group._TOKENS.values()]
    assert len(reached) == len(set(reached))
    assert set(reached) == in_css - {"--radius-full"}


@pytest.mark.parametrize(
    "build",
    [
        lambda: Accent.from_scale(_VIOLET[:9]),
        lambda: Fonts(ui="Inter} body {display:none"),
        lambda: Corners(control="4px</style><script>"),
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
        theme=Theme(accent=Accent.from_scale(_VIOLET)),
    )
    html = await render_tree(page(title="t", body="b"), context_args=context_args)
    head = [
        tag.get("href") or tag.name for tag in select(html, "head link, head style")
    ]
    assert head == ["/hue.css", "style", "/app.css"]
