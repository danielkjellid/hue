from htmy import html

from hue.ui import Card, CardBody, CardHeader, TextInput
from tests.browser.conftest import Show


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


def test_every_shadow_token_flips_with_the_theme(show: Show) -> None:
    # The values are the stylesheet's to choose; what can break is the dark
    # block failing to reach a token.
    light, dark = _shadows(show, "light"), _shadows(show, "dark")
    assert all(light[token] != dark[token] for token in light), (light, dark)


def test_a_ring_survives_the_dark_field_shadow(show: Show) -> None:
    # A none in the field token would void the whole box-shadow list, ring
    # included.
    page = show(
        html.div("Ringed", id="r", class_="shadow-field ring-2 ring-accent"),
        theme="dark",
    )
    shadow = page.locator("#r").evaluate("el => getComputedStyle(el).boxShadow")
    assert "0px 0px 0px 2px" in shadow
