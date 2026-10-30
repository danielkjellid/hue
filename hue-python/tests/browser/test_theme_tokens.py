from htmy import html

from hue.ui import Card, CardBody, CardHeader, TextInput
from tests.browser.conftest import Show

LIGHT = {
    "field": "rgba(18, 18, 23, 0.04) 0px 1px 2px 0px",
    "raised": "rgba(18, 18, 23, 0.02) 0px 0px 0px 1px, "
    "rgba(18, 18, 23, 0.04) 0px 2px 6px 0px, "
    "rgba(18, 18, 23, 0.1) 0px 4px 8px 0px",
    "overlay": "rgba(18, 18, 23, 0.03) 0px 0px 0px 1px, "
    "rgba(18, 18, 23, 0.06) 0px 8px 16px -4px, "
    "rgba(18, 18, 23, 0.12) 0px 16px 32px -8px",
}


def _shadows(show: Show, theme: str) -> dict[str, str]:
    page = show(
        TextInput().name("email").label("Email"),
        Card()
        .variant("raised")
        .id("raised")
        .content(CardHeader().title("Raised"), CardBody().content("Body")),
        # No overlay renders open without a click, and the token is the point.
        html.div("Overlay", id="overlay", class_="shadow-overlay"),
        theme=theme,
    )
    # Tailwind leads every shadow with empty ring layers; only the token's
    # own layers say anything.
    shadow = (
        "(el) => getComputedStyle(el).boxShadow"
        ".replaceAll('rgba(0, 0, 0, 0) 0px 0px 0px 0px, ', '')"
    )
    return {
        "field": page.locator("input").evaluate(shadow),
        "raised": page.locator("#raised").evaluate(shadow),
        "overlay": page.locator("#overlay").evaluate(shadow),
    }


def test_light_shadows_are_the_light_tokens(show: Show) -> None:
    assert _shadows(show, "light") == LIGHT


def test_dark_shadows_are_the_dark_tokens(show: Show) -> None:
    assert _shadows(show, "dark") == {
        "field": "rgba(0, 0, 0, 0) 0px 0px 0px 0px",
        "raised": "rgba(0, 0, 0, 0.3) 0px 0px 0px 1px, "
        "rgba(0, 0, 0, 0.36) 0px 2px 6px 0px, "
        "rgba(0, 0, 0, 0.46) 0px 4px 10px 0px",
        "overlay": "rgba(0, 0, 0, 0.34) 0px 0px 0px 1px, "
        "rgba(0, 0, 0, 0.46) 0px 8px 20px -4px, "
        "rgba(0, 0, 0, 0.58) 0px 20px 40px -8px",
    }


def test_a_ring_survives_the_dark_field_shadow(show: Show) -> None:
    # A none in the field token would void the whole box-shadow list, ring
    # included.
    page = show(
        html.div("Ringed", id="r", class_="shadow-field ring-2 ring-accent"),
        theme="dark",
    )
    shadow = page.locator("#r").evaluate("el => getComputedStyle(el).boxShadow")
    assert "0px 0px 0px 2px" in shadow
