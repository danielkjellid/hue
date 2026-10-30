from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Avatar, AvatarGroup

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def reviewers() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper, Alan Turing and 3 others")
        .more(3)
        .content(
            Avatar().name("Ada Lovelace"),
            Avatar().name("Grace Hopper"),
            Avatar().name("Alan Turing"),
        )
    )


# Sizes


def xs() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 2 others")
        .size("xs")
        .more(2)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def sm() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 2 others")
        .size("sm")
        .more(2)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def md() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 2 others")
        .size("md")
        .more(2)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def lg() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 2 others")
        .size("lg")
        .more(2)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def xl() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 2 others")
        .size("xl")
        .more(2)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


# Anatomy


def everyone_shown() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace and Grace Hopper")
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def with_a_count() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace, Grace Hopper and 12 others")
        .more(12)
        .content(Avatar().name("Ada Lovelace"), Avatar().name("Grace Hopper"))
    )


def with_pictures() -> AvatarGroup:
    return (
        AvatarGroup()
        .label("Ada Lovelace and Grace Hopper")
        .content(
            Avatar().name("Ada Lovelace").src("https://i.pravatar.cc/128?img=5"),
            Avatar().name("Grace Hopper").src("https://i.pravatar.cc/128?img=9"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "An `AvatarGroup` overlaps a row of Avatars and announces them as "
            "one image. `label()` is required. It is the only thing a screen "
            "reader hears, so it names the people in the row, the ones behind "
            "the count included."
        ),
        pr.code(
            "(\n"
            "    AvatarGroup()\n"
            '    .label("Ada Lovelace, Grace Hopper and 3 others")\n'
            "    .more(3)\n"
            "    .content(\n"
            '        Avatar().name("Ada Lovelace"),\n'
            '        Avatar().name("Grace Hopper"),\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "An `AvatarGroup` without a label raises a `ValueError` when it "
            "renders, so a group with no accessible name cannot reach the page."
        ),
        pr.h3("The count"),
        pr.p(
            "`more(3)` ends the row with +3, for people the row does not show. "
            "The `AvatarGroup` does not count its children for you, and the "
            "number is not part of the accessible name, so say it in `label()` "
            "too."
        ),
        pr.h3("Size"),
        pr.p(
            "`size()` on the `AvatarGroup` sizes every `Avatar` in it, and the count "
            'and the overlap with them. `size()` defaults to `"md"`. An `Avatar` that '
            "sets its own `size()` keeps it."
        ),
        pr.h3("Stacking order"),
        pr.p(
            "Earlier Avatars sit on top of later ones, so the row reads from "
            "the start. Each member gets a ring in the canvas colour, "
            "which separates the overlapping faces."
        ),
    )


PAGE = ComponentPage(
    AvatarGroup,
    lede=(
        "An avatar group overlaps several avatars in one row, with an optional "
        "count for the people it leaves out. A screen reader hears it as one "
        "image with one label."
    ),
    usage=_usage,
    panels=[
        panel("Live", reviewers, layout="center"),
        panel("Sizes", xs, sm, md, lg, xl, hint="`size()` reaches every member"),
        panel("Anatomy", everyone_shown, with_a_count, with_pictures),
    ],
    notes=[
        Note(
            "a11y",
            'The `AvatarGroup` renders `role="img"` with `label()` as its '
            "`aria-label`. Every member and the count are `aria-hidden`, so the "
            "row is announced once.",
        ),
        Note(
            "warn",
            "The +N count is hidden from screen readers. Include the people it "
            "stands for in `label()`.",
        ),
        Note(
            "note",
            "`label()` is required. Rendering an `AvatarGroup` without one raises a "
            "`ValueError`.",
        ),
    ],
    related=[Avatar],
)
