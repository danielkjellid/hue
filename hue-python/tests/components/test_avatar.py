import pytest

from hue.renderer import render_tree
from hue.ui import Avatar, AvatarGroup
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestAvatar:
    @pytest.mark.parametrize(
        ("name", "initials"), [("Ada Lovelace", "AL"), ("Madonna", "MA")]
    )
    @pytest.mark.asyncio
    async def test_derives_initials_from_a_name(self, context_args, name, initials):
        # Initials are the default, not the fallback: a grid of identical grey
        # silhouettes says nothing.
        html = await render_tree(Avatar().name(name), context_args=context_args)
        assert initials in html
        assert_attr(html, 'span[role="img"]', "aria-label", name)

    @pytest.mark.asyncio
    async def test_a_picture_covers_the_initials(self, context_args):
        # The initials stay underneath for when the picture fails to load.
        html = await render_tree(
            Avatar().name("Grace Hopper").src("/grace.jpg"),
            context_args=context_args,
        )
        assert "GH" in html
        assert_attr(html, "img", "onerror", "this.remove()")
        # Empty alt, because the wrapper already carries the name - otherwise
        # the same person is announced twice.
        assert_attr(html, "img", "alt", "")
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper")

    @pytest.mark.asyncio
    async def test_status_folds_into_the_label(self, context_args):
        # The dot is visual only, so it is not a second thing to announce.
        html = await render_tree(
            Avatar().name("Grace Hopper").status("online"), context_args=context_args
        )
        assert_attr(html, 'span[role="img"]', "aria-label", "Grace Hopper, online")

    @pytest.mark.parametrize(
        "avatar", [Avatar().content("+3"), Avatar().name("   ")], ids=["none", "blank"]
    )
    @pytest.mark.asyncio
    async def test_an_unnamed_avatar_is_not_an_unlabelled_image(
        self, context_args, avatar
    ):
        # role="img" with nothing to announce is worse than no role at all.
        html = await render_tree(avatar, context_args=context_args)
        assert_no_selector(html, '[role="img"]')
        assert_no_selector(html, "[aria-label]")


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

    @pytest.mark.parametrize("label", [None, "  "])
    @pytest.mark.asyncio
    async def test_requires_a_label(self, context_args, label):
        # Without one the group announces nothing at all.
        group = AvatarGroup().content(Avatar().name("Ada"))
        if label is not None:
            group.label(label)
        with pytest.raises(ValueError, match="requires a label"):
            await render_tree(group, context_args=context_args)

    @pytest.mark.parametrize(("more", "wrappers"), [(3, 2), (0, 1)])
    @pytest.mark.asyncio
    async def test_more_adds_an_overflow_count(self, context_args, more, wrappers):
        html = await render_tree(
            AvatarGroup()
            .label("Ada and others")
            .more(more)
            .content(Avatar().name("Ada Lovelace")),
            context_args=context_args,
        )
        assert ("+3" in html) is (more == 3)
        assert "+0" not in html
        assert_selector(html, 'span[aria-hidden="true"]', count=wrappers)

    def test_more_cannot_be_negative(self):
        with pytest.raises(ValueError, match="negative"):
            AvatarGroup().more(-1)

    @pytest.mark.asyncio
    async def test_size_reaches_the_members_that_did_not_pick_one(self, context_args):
        # Otherwise the group and the count it ends with disagree about how big
        # a face is, which is what made the largest size look broken.
        html = await render_tree(
            AvatarGroup()
            .label("Ada, Grace and 3 others")
            .size("xl")
            .more(3)
            .content(
                Avatar().name("Ada Lovelace"),
                Avatar().name("Grace Hopper").size("sm"),
            ),
            context_args=context_args,
        )
        assert_selector(html, "span.size-16")
        assert_selector(html, "span.size-7", count=1)

    @pytest.mark.asyncio
    async def test_members_are_ringed_apart_and_the_count_is_not(self, context_args):
        # On a plain inline span the ring was drawn around a line box rather
        # than the avatar, so the members ran together. A ring around the
        # count would read as one more person rather than a count of the row.
        html = await render_tree(
            AvatarGroup()
            .label("Ada, Grace and 3 others")
            .more(3)
            .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper")),
            context_args=context_args,
        )
        assert_selector(html, "span.inline-flex.rounded-full.ring-2", count=2)
        assert_no_selector(html, "span.rounded-full:-soup-contains('+3')")
