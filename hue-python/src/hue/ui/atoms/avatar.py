from __future__ import annotations

from typing import Literal, cast

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type AvatarSize = Literal["xs", "sm", "md", "lg", "xl"]
type AvatarShape = Literal["circle", "square"]
type AvatarStatus = Literal["online", "away", "busy", "offline"]

_BOX_CLASSES: dict[AvatarSize, str] = {
    "xs": "size-5",
    "sm": "size-7",
    "md": "size-9",
    "lg": "size-11",
    "xl": "size-16",
}

# The type scales with the circle, so initials stay optically centred.
_TEXT_CLASSES: dict[AvatarSize, str] = {
    "xs": "text-[8px]",
    "sm": "text-[11px]",
    "md": "text-sm",
    "lg": "text-md",
    "xl": "text-[24px]",
}

_STATUS_CLASSES: dict[AvatarStatus, str] = {
    "online": "bg-success",
    "away": "bg-warning",
    "busy": "bg-danger",
    "offline": "bg-fg-disabled",
}


def _initials(name: str) -> str:
    """
    Two letters from a name: first and last for a full name, else the first two.
    """
    parts = name.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class Avatar(ChainableComponent):
    """
    A person, as a picture or their initials.

    name() gives both the initials and the accessible name; src() swaps the
    initials for an image. status() adds a dot, which folds into the label -
    "Grace Hopper, online" - rather than being announced separately.

        Avatar().name("Ada Lovelace").status("online")
    """

    category = "Media"

    @classmethod
    def example(cls) -> Self:
        return cls().name("Ada Lovelace").status("online")

    def name(self, value: str) -> Self:
        """
        Who this is. Becomes both the initials and the accessible name.
        """
        self._props["name"] = value
        return self

    def src(self, value: str) -> Self:
        """
        A picture of this person, hosted wherever the caller likes.

        It renders with an empty alt because the wrapper already carries the
        name, so the picture is decorative as far as a screen reader goes.
        """
        self._props["src"] = value
        return self

    def size(self, value: AvatarSize) -> Self:
        self._props["size"] = value
        return self

    def _size_default(self, value: AvatarSize) -> None:
        """
        Called by a group, which sizes its members unless they say otherwise.
        """
        self._props.setdefault("size", value)

    def shape(self, value: AvatarShape) -> Self:
        self._props["shape"] = value
        return self

    def status(self, value: AvatarStatus) -> Self:
        self._props["status"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        size: AvatarSize = self._get_prop("size", "md")
        shape: AvatarShape = self._get_prop("shape", "circle")
        name: str | None = self._get_prop("name")
        src: str | None = self._get_prop("src")
        status: AvatarStatus | None = self._get_prop("status")

        label = name
        if label is not None and status is not None:
            label = f"{label}, {status}"

        body: tuple[ComponentType, ...]
        if src is not None:
            # The picture is the face; initials underneath would only show
            # through wherever it does not quite cover.
            body = (
                html.img(
                    src=src,
                    alt="",
                    loading="lazy",
                    class_="size-full object-cover",
                ),
            )
        elif name:
            body = (_initials(name),)
        else:
            # No name and no picture: whatever the caller put inside, such as
            # an icon.
            body = self._children

        radius = "rounded-md" if shape == "square" else "rounded-full"

        return html.span(
            # The picture is clipped to the shape here rather than on the root,
            # so the status dot below can sit over the edge without being
            # trimmed to a wedge by the same overflow rule.
            html.span(
                *body,
                class_=classnames(
                    "flex size-full items-center justify-center overflow-hidden",
                    # An inset hairline, so a pale photo or a surface-coloured
                    # circle still has an edge on a light page. Drawn as an
                    # outline rather than a border because it costs no layout.
                    "outline-1 -outline-offset-1 outline-border",
                    "bg-surface-active text-fg-muted",
                    "font-ui font-semibold leading-none",
                    _TEXT_CLASSES[size],
                    radius,
                ),
            ),
            render_if(
                status,
                lambda value: html.span(
                    class_=classnames(
                        "absolute -end-px -bottom-px w-[30%] h-[30%]",
                        "min-w-2 min-h-2 rounded-full border-2 border-canvas",
                        _STATUS_CLASSES[cast("AvatarStatus", value)],
                    )
                ),
            ),
            class_=classnames(
                "relative inline-flex shrink-0 select-none",
                _BOX_CLASSES[size],
                radius,
                self._get_prop("class_"),
            ),
            **{
                # An unlabelled role="img" announces an image with no name, so
                # a decorative avatar stays a plain span.
                **({"role": "img", "aria_label": label} if label else {}),
                **self._get_base_html_attrs(),
            },
        )


# inline-flex so the wrapper shrink-wraps the avatar: as a plain inline span its
# box is a line box, and the ring meant to separate overlapping members was
# drawn around that instead of around the circle.
_MEMBER_CLASSES = "relative inline-flex rounded-full ring-2 ring-canvas first:ms-0"

# The overlap is a fraction of the avatar rather than a fixed distance, so a row
# of small faces is not stacked nearly on top of each other while a row of large
# ones barely touches.
_OVERLAP_CLASSES: dict[AvatarSize, str] = {
    "xs": "-ms-1.5",
    "sm": "-ms-2",
    "md": "-ms-2.5",
    "lg": "-ms-3",
    "xl": "-ms-4",
}


class AvatarGroup(ChainableComponent):
    """
    Several avatars overlapping, announced as one image.

    label() is required and describes the group as a whole, because its members
    are hidden from assistive tech. more() appends a "+N" chip.
    """

    category = "Media"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Ada Lovelace, Grace Hopper and 3 others")
            .more(3)
            .content(
                Avatar().name("Ada Lovelace"),
                Avatar().name("Grace Hopper"),
            )
        )

    def label(self, value: str) -> Self:
        """
        What the group as a whole is, e.g. "Ada, Grace and 3 others".
        """
        self._props["label"] = value
        return self

    def more(self, value: int) -> Self:
        """
        Add a "+N" for the people not shown.
        """
        self._props["more"] = value
        return self

    def size(self, value: AvatarSize) -> Self:
        self._props["size"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        label: str | None = self._get_prop("label")
        if label is None:
            raise ValueError(
                "AvatarGroup requires a label; call .label() with a summary of "
                "who is in the group, e.g. 'Ada Lovelace and 3 others'."
            )

        size: AvatarSize = self._get_prop("size", "md")
        more: int | None = self._get_prop("more")

        # Each child sits in a hidden wrapper rather than being modified, so an
        # Avatar cannot end up announced twice however it was constructed. The
        # size does reach them, so the group and the count it ends with cannot
        # disagree about how big a face is.
        members = []
        for index, child in enumerate(self._children):
            if isinstance(child, Avatar):
                child._size_default(size)
            members.append(
                html.span(
                    child,
                    class_=classnames(_MEMBER_CLASSES, _OVERLAP_CLASSES[size]),
                    # Earlier members stack on top of later ones, so the row
                    # reads left to right rather than the last face climbing
                    # over everything before it. Computed, so it cannot be a
                    # Tailwind class - nothing would scan it.
                    style=f"z-index:{len(self._children) - index}",
                    aria_hidden="true",
                )
            )

        if more is not None:
            # Just the number: a circle around it would read as one more face
            # in the row rather than as a count of the row.
            members.append(
                html.span(
                    f"+{more}",
                    class_=classnames(
                        "ms-2 font-ui font-semibold text-fg-subtle tabular-nums",
                        _TEXT_CLASSES[size],
                    ),
                    aria_hidden="true",
                )
            )

        return html.span(
            *members,
            # isolate keeps the members' stacking order to themselves rather
            # than letting it compete with whatever surrounds the group.
            class_=classnames(
                "isolate inline-flex items-center", self._get_prop("class_")
            ),
            **{
                "role": "img",
                "aria_label": label,
                **self._get_base_html_attrs(),
            },
        )
