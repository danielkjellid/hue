import pytest
from htmy import html

from hue.ui import Accordion, AccordionItem, Button, Disclosure, Empty, Label, Text
from tests.browser.conftest import Show

TYPE = ("fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing")
VARIANTS = ["title-1", "title-2", "title-3", "subtitle-1", "subtitle-2", "body"]
FIGTREE = 'Figtree, ui-sans-serif, -apple-system, "Segoe UI", sans-serif'
HEADING = [FIGTREE, "14px", "700", "17.5px", "-0.28px"]


def _type(show_page, selector: str) -> list[str]:  # type: ignore[no-untyped-def]
    style = show_page.locator(selector).evaluate("(el) => getComputedStyle(el)")
    return [style[name] for name in TYPE]


def test_every_variant_looks_different_and_a_tag_does_not_change_it(
    show: Show,
) -> None:
    page = show(
        *(Text("Words").variant(v).id(v) for v in VARIANTS),  # type: ignore[arg-type]
        *(
            Text("Words").variant(v).tag(tag).id(f"{tag}-{v}")  # type: ignore[arg-type]
            for v in VARIANTS
            for tag in ("h1", "h6")
        ),
    )
    looks = {v: tuple(_type(page, f"#{v}")) for v in VARIANTS}
    assert len(set(looks.values())) == len(VARIANTS), looks
    for v in VARIANTS:
        for tag in ("h1", "h6"):
            assert tuple(_type(page, f"#{tag}-{v}")) == looks[v], (tag, v)


def test_every_plain_heading_keeps_the_heading_look(show: Show) -> None:
    page = show(
        *(getattr(html, f"h{n}")("Plain", id=f"h{n}") for n in range(1, 7)),
        html.h2(html.a("Linked", href="#x", id="a")),
    )
    for n in range(1, 7):
        assert _type(page, f"#h{n}") == HEADING, n
    assert _type(page, "#a")[4] == "-0.28px"


# A heading a component uses for structure says where it sits in the outline;
# the display tracking is for headings that look like headings.
def test_an_empty_title_reads_the_same_as_a_heading(show: Show) -> None:
    page = show(
        Empty().title("Nothing here").id("div"),
        Empty().title("Nothing here", heading="h2").id("h2"),
    )
    assert _type(page, "#h2 h2") == _type(page, "#div >> text=Nothing here")


def test_controls_in_a_heading_take_body_tracking(show: Show) -> None:
    page = show(
        Accordion().content(AccordionItem().title("Section").content("Body")),
        Disclosure().title("More").content("Body"),
        html.h2("Members ", Button().content("Invite").id("b")),
        html.h2("Members ", Button().content("Invite").class_("tracking-wide").id("w")),
    )
    assert _type(page, "h3 button >> nth=0") == [
        FIGTREE,
        "14px",
        "500",
        "21.7px",
        "normal",
    ]
    assert _type(page, "h3 button >> nth=1")[4] == "normal"
    assert _type(page, "#b")[4] == "normal"
    # A tracking class of the caller's own still wins.
    assert _type(page, "#w")[4] != "normal"


def test_a_heading_text_still_takes_its_own_classes(show: Show) -> None:
    page = show(Text("Words").tag("h2").class_("font-ui font-bold").id("h"))
    family, _, weight, _, _ = _type(page, "#h")
    assert (family, weight) == (FIGTREE, "700")


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
def test_text_sits_at_the_start_or_the_end_of_the_line(show: Show, dir: str) -> None:
    page = show(
        Text("שלום עולם").id("t"),
        Label("שלום").id("l").class_("w-full"),
        Text("שלום עולם").align("end").id("e"),
        dir=dir,
    )
    for selector in ("#t", "#l"):
        left, right = _edges(page, selector)
        assert (left if dir == "ltr" else right) < 1, selector
    left, right = _edges(page, "#e")
    assert (right if dir == "ltr" else left) < 1
