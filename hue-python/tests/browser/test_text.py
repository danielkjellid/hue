import pytest
from htmy import html

from hue.ui import Accordion, AccordionItem, Text
from tests.browser.conftest import Show

TYPE = ("fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing")


def _type(show_page, selector: str) -> list[str]:  # type: ignore[no-untyped-def]
    style = show_page.locator(selector).evaluate("(el) => getComputedStyle(el)")
    return [style[name] for name in TYPE]


@pytest.mark.parametrize("variant", ["title-1", "title-3", "subtitle-1", "body"])
@pytest.mark.parametrize("tag", ["h1", "h2", "h6"])
def test_a_heading_tag_does_not_change_the_look(
    show: Show, tag: str, variant: str
) -> None:
    page = show(
        Text("Words").variant(variant).id("p"),  # type: ignore[arg-type]
        Text("Words").variant(variant).tag(tag).id("h"),  # type: ignore[arg-type]
    )
    assert _type(page, "#h") == _type(page, "#p")


FIGTREE = 'Figtree, ui-sans-serif, -apple-system, "Segoe UI", sans-serif'


def test_a_plain_heading_keeps_the_heading_look(show: Show) -> None:
    page = show(html.h2("Plain", id="h"))
    assert _type(page, "#h") == [FIGTREE, "14px", "700", "17.5px", "-0.28px"]


def test_an_accordion_heading_keeps_the_heading_look(show: Show) -> None:
    page = show(Accordion().content(AccordionItem().title("Section").content("Body")))
    assert _type(page, "h3 button") == [FIGTREE, "14px", "500", "21.7px", "-0.28px"]


def test_a_heading_text_still_takes_its_own_classes(show: Show) -> None:
    page = show(Text("Words").tag("h2").class_("font-ui font-bold").id("h"))
    family, _, weight, _, _ = _type(page, "#h")
    assert (family, weight) == (FIGTREE, "700")
