from htmy import html

from hue.ui import Panel, Stack
from tests.browser.conftest import Show
from tests.browser.test_datatable import _long


def test_a_panel_without_padding_clips_what_runs_past_its_frame(show: Show) -> None:
    page = show(
        Panel()
        .id("panel")
        .label("Wide")
        .padding("none")
        .content(html.div(style="width: 2000px; height: 40px")),
        width=320,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
    assert page.evaluate(
        "document.getElementById('panel').getBoundingClientRect().right <= 320"
    )


def test_a_panel_beside_another_shrinks_around_a_wide_table(show: Show) -> None:
    page = show(
        Stack()
        .horizontal()
        .content(
            Panel()
            .id("one")
            .class_("flex-1")
            .padding("none")
            .content(_long(3, columns=8)),
            Panel().id("two").class_("flex-1").content("Two"),
        ),
        width=320,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


def test_a_panel_in_a_sidebar_keeps_its_width_and_header(show: Show) -> None:
    page = show(
        html.div(
            html.aside(
                Panel()
                .id("panel")
                .label("Filters")
                .hint("3 on")
                .content(html.div("Body", id="body")),
                class_="w-64 shrink-0",
            ),
            html.div(html.div(style="width: 2000px"), class_="flex-1"),
            class_="flex gap-4",
        ),
        width=1280,
    )
    sizes = page.evaluate(
        "(() => { const p = document.getElementById('panel').getBoundingClientRect();"
        " const head = document.querySelector('#panel > div').getBoundingClientRect();"
        " return [p.width, head.height] })()"
    )
    assert sizes[0] == 256
    assert sizes[1] > 20
