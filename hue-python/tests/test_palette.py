import re
from pathlib import Path

import pytest

import hue
from hue import palette


def test_every_preset_names_a_token_in_both_themes():
    # A preset is a var() of a token, which fails silently when the token is
    # renamed: the colour is just missing from the page.
    tokens = (
        Path(hue.__file__).parent / "static/styles/tailwind.input.css"
    ).read_text()
    for color in palette.ORDER:
        name = re.fullmatch(r"var\((--[\w-]+)\)", color.light)
        assert name and f"{name[1]}:" in tokens, color


@pytest.mark.parametrize(
    "value", ["red; background: url(//x)", 'red" onclick="x', "red}body{x:y"]
)
def test_a_colour_that_could_add_a_declaration_is_refused(value):
    # It is written into a style attribute, and a layer's colour can come
    # from whatever the app stored.
    with pytest.raises(ValueError, match="not a CSS colour"):
        palette.Color(value)
