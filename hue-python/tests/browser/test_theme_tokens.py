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
