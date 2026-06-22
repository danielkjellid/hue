import pytest

from hue import html
from hue.renderer import render_tree
from hue.skeletonize import defer, to_skeleton
from hue.ui import Button, Column, DataTable, Skeleton, Spacer, Stack, Text
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestToSkeleton:
    @pytest.mark.asyncio
    async def test_string_becomes_a_line(self, context_args):
        rendered = await render_tree(to_skeleton("hello"), context_args=context_args)
        assert "animate-pulse" in rendered

    @pytest.mark.asyncio
    async def test_blank_string_renders_nothing(self, context_args):
        rendered = await render_tree(to_skeleton("   "), context_args=context_args)
        assert "animate-pulse" not in rendered

    @pytest.mark.asyncio
    async def test_existing_skeleton_passes_through(self):
        bar = Skeleton().shape("circle")
        assert to_skeleton(bar) is bar

    @pytest.mark.asyncio
    async def test_sequence_maps_elementwise(self, context_args):
        mapped = to_skeleton([Text("a"), Text("b")])
        assert isinstance(mapped, tuple) and len(mapped) == 2
        # Splat the fragment as top-level children (how it's used nested in a tree).
        rendered = await render_tree(*mapped, context_args=context_args)
        assert_selector(rendered, "div.animate-pulse", count=2)

    @pytest.mark.asyncio
    async def test_leaf_uses_component_skeleton(self, context_args):
        """A component with its own skeleton() replaces the real markup."""
        rendered = await render_tree(
            to_skeleton(Button().content("Save")), context_args=context_args
        )
        assert_no_selector(rendered, "button")
        assert "Save" not in rendered
        assert "animate-pulse" in rendered

    @pytest.mark.asyncio
    async def test_container_preserves_layout_and_recurses(self, context_args):
        """A container keeps its layout classes; its children are skeletonised."""
        tree = (
            Stack()
            .direction("vertical")
            .spacing("md")
            .content(Text("Title").variant("title-1"), Button().content("Go"))
        )
        rendered = await render_tree(to_skeleton(tree), context_args=context_args)
        # Layout shell kept verbatim...
        assert "flex-col" in rendered and "space-y-5" in rendered
        # ...real content gone, replaced by placeholders.
        assert "Title" not in rendered and "Go" not in rendered
        assert_selector(rendered, ".flex.flex-col > div.animate-pulse", count=2)

    @pytest.mark.asyncio
    async def test_unknown_container_recurses_children(self, context_args):
        rendered = await render_tree(
            to_skeleton(html.div(Text("x"))), context_args=context_args
        )
        assert "x" not in rendered
        assert "animate-pulse" in rendered

    @pytest.mark.asyncio
    async def test_transform_does_not_mutate_original(self, context_args):
        """Skeletonising a tree leaves the original renderable and intact."""
        tree = Stack().content(Text("Original"))
        to_skeleton(tree)
        rendered = await render_tree(tree, context_args=context_args)
        assert "Original" in rendered


class TestComponentSkeletons:
    @pytest.mark.asyncio
    async def test_spacer_skeleton_keeps_gap_without_placeholder(self, context_args):
        """A spacer is blank space: its skeleton preserves the gap, no pulse bar."""
        rendered = await render_tree(
            to_skeleton(Spacer().spacing("lg")), context_args=context_args
        )
        assert "mb-8" in rendered  # the gap is preserved
        assert "animate-pulse" not in rendered  # but it's not a placeholder shape

    @pytest.mark.asyncio
    async def test_datatable_skeleton_is_a_table_not_a_line(self, context_args):
        """DataTable builds its rows in _render, so its skeleton must too."""
        table = DataTable().columns(
            [Column("Name", accessor="name"), Column("Email", accessor="email")]
        )
        rendered = await render_tree(to_skeleton(table), context_args=context_args)
        assert_selector(rendered, "table")
        # A header row plus the fallback body rows, each with placeholder cells.
        assert_selector(rendered, "thead th", count=2)
        assert_selector(rendered, "tbody tr", count=5)
        assert "animate-pulse" in rendered

    @pytest.mark.asyncio
    async def test_datatable_skeleton_uses_known_row_count(self, context_args):
        """When data is present its length informs the row count."""
        table = (
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "a"}, {"name": "b"}])
        )
        rendered = await render_tree(to_skeleton(table), context_args=context_args)
        assert_selector(rendered, "tbody tr", count=2)


class TestSkeletonOverride:
    @pytest.mark.asyncio
    async def test_instance_override_replaces_class_default(self, context_args):
        """skeleton_as wins over a component's own _skeleton_impl."""
        text = Text("anything").skeleton_as(Skeleton().lines(3))
        rendered = await render_tree(to_skeleton(text), context_args=context_args)
        # The 3-line override, not Text's single-line default.
        assert "flex flex-col gap-2" in rendered
        assert "w-3/4" in rendered

    @pytest.mark.asyncio
    async def test_override_accepts_a_lazy_factory(self, context_args):
        text = Text("x").skeleton_as(lambda: Skeleton().shape("circle"))
        rendered = await render_tree(to_skeleton(text), context_args=context_args)
        assert "rounded-full" in rendered

    @pytest.mark.asyncio
    async def test_override_on_container_wins_over_recursion(self, context_args):
        """An override on a container short-circuits child recursion."""
        tree = Stack().content(Text("a"), Text("b"))
        tree.skeleton_as(Skeleton().shape("rect"))
        rendered = await render_tree(to_skeleton(tree), context_args=context_args)
        # Single rect from the override; the children are not skeletonised.
        assert_selector(rendered, "div.animate-pulse", count=1)
        assert "flex-col" not in rendered


class TestDefer:
    @pytest.mark.asyncio
    async def test_wires_ajax_into_a_live_region(self, context_args):
        rendered = await render_tree(
            defer(
                skeleton=Skeleton().lines(2),
                url="/dash/content/",
                target="dash-body",
            ),
            context_args=context_args,
        )
        # The target region announces busy state politely to assistive tech.
        assert_attr(rendered, "div#dash-body", "role", "status")
        assert_attr(rendered, "div#dash-body", "aria-busy", "true")
        # On init it fetches the real content into itself.
        assert_attr(
            rendered,
            "div#dash-body",
            "x-init",
            "$ajax('/dash/content/', { method: 'get', target: 'dash-body' })",
        )
        # A screen-reader-only status label and the skeleton are both present.
        assert "Loading" in rendered
        assert "animate-pulse" in rendered

    @pytest.mark.asyncio
    async def test_custom_method(self, context_args):
        rendered = await render_tree(
            defer(
                skeleton=Skeleton(),
                url="/x/",
                target="t",
                method="post",
            ),
            context_args=context_args,
        )
        assert "method: 'post'" in rendered
