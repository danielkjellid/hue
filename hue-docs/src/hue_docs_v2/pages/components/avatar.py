from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Avatar, AvatarGroup, Badge

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def ada_lovelace() -> Avatar:
    return Avatar().name("Ada Lovelace").size("lg").status("online")


# Sizes


def xs() -> Avatar:
    return Avatar().name("Ada Lovelace").size("xs")


def sm() -> Avatar:
    return Avatar().name("Ada Lovelace").size("sm")


def md() -> Avatar:
    return Avatar().name("Ada Lovelace").size("md")


def lg() -> Avatar:
    return Avatar().name("Ada Lovelace").size("lg")


def xl() -> Avatar:
    return Avatar().name("Ada Lovelace").size("xl")


# Anatomy


def initials() -> Avatar:
    return Avatar().name("Grace Hopper")


def single_name() -> Avatar:
    return Avatar().name("Plato")


def picture() -> Avatar:
    return Avatar().name("Ada Lovelace").src("https://i.pravatar.cc/128?img=5")


def icon() -> Avatar:
    return Avatar().content(Icon("user").class_("size-4"))


def square() -> Avatar:
    return Avatar().name("Northwind Ltd").square()


# Status


def online() -> Avatar:
    return Avatar().name("Grace Hopper").status("online")


def away() -> Avatar:
    return Avatar().name("Grace Hopper").status("away")


def busy() -> Avatar:
    return Avatar().name("Grace Hopper").status("busy")


def offline() -> Avatar:
    return Avatar().name("Grace Hopper").status("offline")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "An `Avatar` shows a person as their initials or a picture. `name()` "
            "sets both the initials and the accessible name, so most avatars "
            'need nothing else. `size()` defaults to `"md"`.'
        ),
        pr.code('Avatar().name("Ada Lovelace").size("sm")'),
        pr.h3("Initials"),
        pr.p(
            "An `Avatar` takes the first letters of the first and last words of "
            "the name, so Ada Augusta Lovelace becomes AL. A name of one word "
            "gives its first two letters, so Plato becomes PL. The initials "
            "are upper case either way."
        ),
        pr.h3("A picture"),
        pr.p(
            "`src()` lays an image over the initials, loaded lazily and "
            "cropped to fill the shape. An image that fails to load is removed, "
            "and the initials show instead. Keep `name()` alongside it. The image has "
            "an empty `alt`, and the `Avatar`'s accessible name still comes from "
            "`name()`."
        ),
        pr.code('Avatar().name("Ada Lovelace").src("https://example.com/ada.jpg")'),
        pr.h3("A status dot"),
        pr.p(
            '`status()` adds a dot at the bottom corner, one of `"online"`, `"away"`, '
            '`"busy"` or `"offline"`. The status joins the accessible name, so an '
            "`Avatar` named "
            'Grace Hopper with `status("online")` reads as "Grace Hopper, online".'
        ),
        pr.h3("An icon or a logo"),
        pr.p(
            "With no `name()` and no `src()`, an `Avatar` shows its children instead, "
            "such as an icon. `square()` rounds the corners instead of making a "
            "circle, for a logo or a product a circle would crop."
        ),
        pr.code(
            'Avatar().content(Icon("user").class_("size-4"))\n'
            'Avatar().name("Northwind Ltd").square()'
        ),
        pr.h3("Several people"),
        pr.p(
            "Put avatars in an `AvatarGroup` to overlap them and announce the "
            "row as one image with one label."
        ),
    )


PAGE = ComponentPage(
    Avatar,
    lede=(
        "An avatar shows a person as their initials or a picture, with an "
        "optional status dot. It comes in five sizes, round by default or "
        "square for a logo."
    ),
    usage=_usage,
    panels=[
        panel("Live", ada_lovelace, layout="center"),
        panel("Sizes", xs, sm, md, lg, xl),
        panel("Anatomy", initials, single_name, picture, icon, square),
        panel("Status", online, away, busy, offline),
    ],
    notes=[
        Note(
            "a11y",
            'An `Avatar` with a name renders `role="img"` with the name as its '
            "`aria-label`, so a screen reader reads the name and not the "
            "initials.",
        ),
        Note(
            "a11y",
            'The status joins the label, as in "Grace Hopper, online". The dot '
            "itself has no text.",
        ),
        Note(
            "a11y",
            'The picture from `src()` renders with `alt=""`, because the `Avatar` '
            "around it already carries the name.",
        ),
        Note(
            "note",
            "An `Avatar` with no name renders no role and no label, so it is "
            "decorative. Whatever it holds, such as an icon, has to carry its own "
            "name if it needs one.",
        ),
    ],
    related=[AvatarGroup, Badge],
)
