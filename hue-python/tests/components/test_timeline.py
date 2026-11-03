import pytest

from hue.renderer import render_tree
from hue.ui import Timeline, TimelineItem
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _release() -> Timeline:
    return (
        Timeline()
        .aria_label("Release")
        .content(
            TimelineItem().title("Release requested"),
            TimelineItem()
            .title("Merged")
            .status("complete")
            .time("13:12", "2026-11-03T13:12"),
            TimelineItem().title("Staging deploy").status("failed"),
            TimelineItem().title("Production deploy").status("current"),
            TimelineItem().title("Smoke tests").status("upcoming"),
        )
    )


class TestTimeline:
    @pytest.mark.asyncio
    async def test_an_ordered_list_whose_status_is_read_as_text(self, context_args):
        html = await render_tree(_release(), context_args=context_args)
        assert_selector(html, "ol > li", count=5)
        # The marker is decoration, so the status has to be in the words, and
        # a plain event, which has none, says nothing before its title.
        assert_selector(html, "li span[aria-hidden=true]", count=10)
        spoken = [s.get_text() for s in select(html, "li .sr-only")]
        assert spoken == ["Complete: ", "Failed: ", "Not started: "]
        assert [li.get("aria-current") for li in select(html, "li")] == [
            None,
            None,
            None,
            "step",
            None,
        ]
        assert_attr(html, "time", "datetime", "2026-11-03T13:12")

    @pytest.mark.asyncio
    async def test_details_make_the_title_a_disclosure_of_its_own(self, context_args):
        html = await render_tree(
            Timeline().content(
                TimelineItem().title("Checks").details({"Commit": "3f9c2a1"}),
                TimelineItem().title("Deploy").details({"Region": "eu-north-1"}),
                TimelineItem().title("Plain"),
            ),
            context_args=context_args,
        )
        buttons = select(html, "li button")
        assert len(buttons) == 2
        assert all(b["type"] == "button" for b in buttons)
        assert_attr(html, "li button", ":aria-controls", "$id('hue-timeline-details')")
        assert_attr(html, "li dl", ":id", "$id('hue-timeline-details')")
        # Each item mints its own id, so two panels cannot share one.
        assert_selector(html, "li[x-id]", count=2)
        assert_no_selector(html, "li:last-child[x-id], li:last-child button")

    @pytest.mark.asyncio
    async def test_a_rail_with_no_times_renders_no_column(self, context_args):
        html = await render_tree(
            Timeline().rail().content(TimelineItem().title("Placed")),
            context_args=context_args,
        )
        # The marker and the body, with no empty rail cell before them.
        assert len(select(html, "li")[0].find_all(recursive=False)) == 2

    @pytest.mark.asyncio
    async def test_empty_details_render_no_panel(self, context_args):
        # A panel with no scope around it throws in Alpine.
        html = await render_tree(
            Timeline().content(TimelineItem().title("Checks").details({})),
            context_args=context_args,
        )
        assert_no_selector(html, "dl, button, [x-show]")

    @pytest.mark.asyncio
    async def test_details_without_a_title_raise(self, context_args):
        with pytest.raises(ValueError, match="needs a title"):
            await render_tree(
                TimelineItem().details({"Commit": "3f9c2a1"}),
                context_args=context_args,
            )
