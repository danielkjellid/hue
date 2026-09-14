import pytest

from hue.renderer import render_tree
from hue.ui import Avatar, AvatarGroup
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestAvatar:
    @pytest.mark.asyncio
    async def test_derives_initials_from_a_name(self, context_args):
        # Initials are the default, not the fallback: a grid of identical grey
        # silhouettes says nothing.
        html = await render_tree(
            Avatar().name("Ada Lovelace"), context_args=context_args
        )
        assert "AL" in html
        assert_attr(html, 'span[role="img"]', "aria-label", "Ada Lovelace")

    @pytest.mark.asyncio
    async def test_single_word_name_takes_two_letters(self, context_args):
        html = await render_tree(Avatar().name("Madonna"), context_args=context_args)
        assert "MA" in html

    # src(): both branches
    @pytest.mark.asyncio
    async def test_image_is_decorative_because_the_wrapper_is_labelled(
        self, context_args
    ):
        html = await render_tree(
            Avatar().name("Grace Hopper").src("/grace.jpg"),
            context_args=context_args,
        )
        assert_attr(html, "img", "alt", "")
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper")
        assert "GH" not in html

    @pytest.mark.asyncio
    async def test_initials_when_there_is_no_image(self, context_args):
        html = await render_tree(
            Avatar().name("Grace Hopper"), context_args=context_args
        )
        assert_no_selector(html, "img")
        assert "GH" in html

    # status(): both branches. The dot is visual only, so it folds into the
    # avatar's own label rather than being a second thing to announce.
    @pytest.mark.asyncio
    async def test_status_folds_into_the_label(self, context_args):
        html = await render_tree(
            Avatar().name("Grace Hopper").status("online"), context_args=context_args
        )
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper, online")
        assert_selector(html, "span.bg-success")

    @pytest.mark.asyncio
    async def test_no_status_dot_by_default(self, context_args):
        html = await render_tree(
            Avatar().name("Grace Hopper"), context_args=context_args
        )
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper")
        assert_no_selector(html, "span.bg-success")

    # shape(): both branches
    @pytest.mark.asyncio
    async def test_default_shape_is_a_circle(self, context_args):
        html = await render_tree(Avatar().name("Ada"), context_args=context_args)
        assert_selector(html, "span.rounded-full")

    @pytest.mark.asyncio
    async def test_square_shape(self, context_args):
        html = await render_tree(
            Avatar().name("Ada").shape("square"), context_args=context_args
        )
        assert_selector(html, "span.rounded-md")
        assert_no_selector(html, 'span[role="img"].rounded-full')

    @pytest.mark.asyncio
    async def test_size_scales_the_type_with_the_circle(self, context_args):
        html = await render_tree(
            Avatar().name("Ada").size("xl"), context_args=context_args
        )
        assert_selector(html, "span.size-16")


class TestAvatarGroup:
    @pytest.mark.asyncio
    async def test_is_announced_as_one_thing(self, context_args):
        # Six separately-announced sets of initials is noise.
        html = await render_tree(
            AvatarGroup()
            .label("Ada Lovelace and 2 others")
            .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper")),
            context_args=context_args,
        )
        assert_selector(html, '[role="img"][aria-label="Ada Lovelace and 2 others"]')
        # Each member sits in a hidden wrapper, so an Avatar cannot end up
        # announced twice however it was built.
        assert_selector(html, 'span[aria-hidden="true"]', count=2)

    @pytest.mark.asyncio
    async def test_requires_a_label(self, context_args):
        # Without one the group announces nothing at all.
        with pytest.raises(ValueError, match="requires a label"):
            await render_tree(
                AvatarGroup().content(Avatar().name("Ada")),
                context_args=context_args,
            )

    # more(): both branches
    @pytest.mark.asyncio
    async def test_more_adds_an_overflow_chip(self, context_args):
        html = await render_tree(
            AvatarGroup()
            .label("Ada and 3 others")
            .more(3)
            .content(Avatar().name("Ada Lovelace")),
            context_args=context_args,
        )
        assert "+3" in html
        assert_selector(html, 'span[aria-hidden="true"]', count=2)

    @pytest.mark.asyncio
    async def test_no_overflow_chip_by_default(self, context_args):
        html = await render_tree(
            AvatarGroup().label("Ada").content(Avatar().name("Ada Lovelace")),
            context_args=context_args,
        )
        assert "+" not in select(html, '[role="img"]')[0].get_text()
        assert_selector(html, 'span[aria-hidden="true"]', count=1)


class TestAvatarContent:
    @pytest.mark.asyncio
    async def test_renders_arbitrary_content_when_it_is_not_a_person(
        self, context_args
    ):
        # An avatar-shaped box holding something other than a person - an
        # overflow count, an icon - keeps the sizing without inventing a name.
        html = await render_tree(Avatar().content("+3"), context_args=context_args)
        assert "+3" in html

    @pytest.mark.asyncio
    async def test_an_unnamed_avatar_is_not_an_unlabelled_image(self, context_args):
        # role="img" with nothing to announce is worse than no role at all.
        html = await render_tree(Avatar().content("+3"), context_args=context_args)
        assert_no_selector(html, '[role="img"]')
