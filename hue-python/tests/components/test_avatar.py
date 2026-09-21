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
    async def test_a_picture_replaces_the_initials(self, context_args):
        # The picture is the face; initials underneath would only show through
        # wherever it does not quite cover.
        html = await render_tree(
            Avatar().name("Grace Hopper").src("/grace.jpg"),
            context_args=context_args,
        )
        assert "GH" not in html
        assert_attr(html, "img", "src", "/grace.jpg")
        # Empty alt, because the wrapper already carries the name - otherwise
        # the same person is announced twice.
        assert_attr(html, "img", "alt", "")
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper")

    @pytest.mark.asyncio
    async def test_no_picture_without_a_src(self, context_args):
        html = await render_tree(
            Avatar().name("Grace Hopper"), context_args=context_args
        )
        assert_no_selector(html, "img")

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
    async def test_a_square_avatar_rounds_its_corners(self, context_args):
        html = await render_tree(
            Avatar().name("Ada").square(), context_args=context_args
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
    async def test_size_reaches_the_members(self, context_args):
        # Otherwise the group and the count it ends with disagree about how big
        # a face is, which is what made the largest size look broken.
        html = await render_tree(
            AvatarGroup()
            .label("Ada and 3 others")
            .size("xl")
            .more(3)
            .content(Avatar().name("Ada Lovelace")),
            context_args=context_args,
        )
        assert_selector(html, "span.size-16")

    @pytest.mark.asyncio
    async def test_a_member_keeps_a_size_it_asked_for(self, context_args):
        html = await render_tree(
            AvatarGroup()
            .label("Ada")
            .size("xl")
            .content(Avatar().name("Ada Lovelace").size("sm")),
            context_args=context_args,
        )
        assert_selector(html, "span.size-7")

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

    @pytest.mark.asyncio
    async def test_members_are_separated_from_each_other(self, context_args):
        # The ring is what keeps overlapping circles apart. On a plain inline
        # span it was drawn around a line box rather than the avatar, so the
        # members ran together.
        html = await render_tree(
            AvatarGroup()
            .label("Ada and Grace")
            .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper")),
            context_args=context_args,
        )
        assert_selector(html, "span.inline-flex.rounded-full.ring-2", count=2)

    @pytest.mark.asyncio
    async def test_the_count_is_a_number_not_another_face(self, context_args):
        # A circle around it would read as one more person in the row rather
        # than as a count of the row.
        html = await render_tree(
            AvatarGroup()
            .label("Ada and 3 others")
            .more(3)
            .content(Avatar().name("Ada Lovelace")),
            context_args=context_args,
        )
        assert "+3" in html
        assert_selector(html, "span.inline-flex.rounded-full.ring-2", count=1)
        assert_no_selector(html, "span.rounded-full:-soup-contains('+3')")

    @pytest.mark.asyncio
    async def test_the_overlap_scales_with_the_avatars(self, context_args):
        # A fixed offset swallows a small face and barely touches a large one.
        small = await render_tree(
            AvatarGroup().label("Two").size("xs").content(Avatar(), Avatar()),
            context_args=context_args,
        )
        large = await render_tree(
            AvatarGroup().label("Two").size("xl").content(Avatar(), Avatar()),
            context_args=context_args,
        )
        assert_selector(small, r"span.-ms-1\.5", count=2)
        assert_selector(large, "span.-ms-4", count=2)

    @pytest.mark.asyncio
    async def test_earlier_members_stack_on_top(self, context_args):
        html = await render_tree(
            AvatarGroup()
            .label("Ada and Grace")
            .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper")),
            context_args=context_args,
        )
        wrappers = select(html, 'span[aria-hidden="true"]')
        assert [w["style"] for w in wrappers] == ["z-index:2", "z-index:1"]
