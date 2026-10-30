import pytest
from htmy import html

from hue.ui import Accordion, AccordionItem, Disclosure, Empty, Label, Text
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


# A heading a component uses for structure says where it sits in the outline;
# the display tracking is for headings that look like headings.
def test_an_empty_title_reads_the_same_as_a_heading(show: Show) -> None:
    page = show(
        Empty().title("Nothing here").id("div"),
        Empty().title("Nothing here", heading="h2").id("h2"),
    )
    assert _type(page, "#h2 h2") == _type(page, "#div >> text=Nothing here")


def test_an_accordion_trigger_takes_body_tracking(show: Show) -> None:
    page = show(
        Accordion().content(AccordionItem().title("Section").content("Body")),
        html.button("Plain", id="b"),
    )
    assert _type(page, "h3 button") == [FIGTREE, "14px", "500", "21.7px", "normal"]
    assert _type(page, "#b")[4] == "normal"


def test_a_disclosure_trigger_takes_body_tracking(show: Show) -> None:
    page = show(Disclosure().title("More").content("Body"))
    assert _type(page, "h3 button")[4] == "normal"


def test_a_heading_text_still_takes_its_own_classes(show: Show) -> None:
    page = show(Text("Words").tag("h2").class_("font-ui font-bold").id("h"))
    family, _, weight, _, _ = _type(page, "#h")
    assert (family, weight) == (FIGTREE, "700")


@pytest.mark.parametrize("tag", ["h1", "h2", "h3", "h4", "h5", "h6"])
def test_every_plain_heading_keeps_the_heading_look(show: Show, tag: str) -> None:
    page = show(getattr(html, tag)("Plain", id="h"))
    assert _type(page, "#h") == [FIGTREE, "14px", "700", "17.5px", "-0.28px"]


def test_a_link_in_a_plain_heading_is_heading_text(show: Show) -> None:
    page = show(html.h2(html.a("Linked", href="#x", id="a")))
    assert _type(page, "#a")[4] == "-0.28px"


@pytest.mark.parametrize(
    ("variant", "size", "weight"),
    [
        ("title-1", "48px", "700"),
        ("subtitle-1", "14px", "500"),
        ("body", "13px", "500"),
    ],
)
def test_the_variants_take_the_documented_type(
    show: Show, variant: str, size: str, weight: str
) -> None:
    page = show(Text("Words").variant(variant).id("t"))  # type: ignore[arg-type]
    assert _type(page, "#t")[1:3] == [size, weight]


def _edges(page, selector: str) -> tuple[float, float]:  # type: ignore[no-untyped-def]
    # Where the words sit inside their box, measured from each side.
    return page.locator(selector).evaluate(
        """el => {
            const range = document.createRange();
            range.selectNodeContents(el);
            const words = range.getBoundingClientRect();
            const box = el.getBoundingClientRect();
            return [words.left - box.left, box.right - words.right];
        }"""
    )


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_text_starts_at_the_start_of_the_line(show: Show, dir: str) -> None:
    page = show(
        Text("שלום עולם").id("t"),
        Label("שלום").id("l").class_("w-full"),
        dir=dir,
    )
    for selector in ("#t", "#l"):
        left, right = _edges(page, selector)
        assert (left if dir == "ltr" else right) < 1, selector


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_text_aligned_to_the_end_sits_at_the_end(show: Show, dir: str) -> None:
    page = show(Text("שלום עולם").align("end").id("t"), dir=dir)
    left, right = _edges(page, "#t")
    assert (right if dir == "ltr" else left) < 1
