import pytest
from htmy import html

from hue.palette import Color
from hue.theme import Ramp, Theme

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
_THEME = Theme(
    accent=_VIOLET,
    colors={
        "surface": Color("#FAFAFA", dark="#101010"),
        "danger": Color("#FF0000"),
    },
)
_TOKENS = ("accent", "accent-subtle", "surface", "danger", "success")


@pytest.mark.parametrize(
    "mode,expected",
    [
        (
            "light",
            [
                "rgb(109, 40, 217)",
                "rgb(245, 243, 255)",
                "rgb(250, 250, 250)",
                "rgb(255, 0, 0)",
                # Left out, so hue's own green-700.
                "rgb(30, 135, 76)",
            ],
        ),
        (
            "dark",
            [
                "rgb(139, 92, 246)",
                # The dark tint is the ramp's 500 at 14%, so it follows the
                # ramp. Chrome writes a mixed colour in this form.
                "color(srgb 0.545098 0.360784 0.964706 / 0.14)",
                "rgb(16, 16, 16)",
                # One value holds in both modes.
                "rgb(255, 0, 0)",
                "rgb(86, 217, 144)",
            ],
        ),
    ],
)
def test_a_theme_overrides_what_it_names_in_both_modes(show, mode, expected):
    page = show(
        *(html.div(class_=f"bg-{token} size-4", id=token) for token in _TOKENS),
        theme=mode,
        styled=_THEME,
    )
    assert [
        page.evaluate(
            f"getComputedStyle(document.getElementById('{t}')).backgroundColor"
        )
        for t in _TOKENS
    ] == expected
