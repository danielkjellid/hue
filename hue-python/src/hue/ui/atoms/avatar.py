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

# The type scales with the circle, so initials stay optically centred.
_SIZE_CLASSES: dict[AvatarSize, str] = {
    "xs": "size-5 text-[8px]",
    "sm": "size-7 text-[11px]",
    "md": "size-9 text-sm",
    "lg": "size-11 text-md",
    "xl": "size-16 text-[24px]",
}

_STATUS_CLASSES: dict[AvatarStatus, str] = {
    "online": "bg-success",
    "away": "bg-warning",
    "busy": "bg-danger",
    "offline": "bg-fg-disabled",
}


def _css_url(src: str) -> str:
    """
    A URL safe to drop inside a CSS url() in an inline style.

    Quoted and escaped, so a stray quote or newline cannot end the declaration
    early and start one of its own.
    """
    escaped = src.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "").replace("\r", "")
    return f'"{escaped}"'


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
        A picture, drawn as the background of the avatar.

        A background rather than an img element because the wrapper already
        carries the name, so the picture is decorative either way - and when the
        URL is broken this falls back to the initials underneath instead of a
        broken-image icon in the middle of a face.
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

    def subtle(self, value: bool = True) -> Self:
        """
        Quieten the fill, for an avatar standing in for something other than a
        person - the count at the end of a group, say. It keeps the surface
        colour rather than the tint a face gets, so it reads as a label.
        """
        self._props["subtle"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        size: AvatarSize = self._get_prop("size", "md")
        shape: AvatarShape = self._get_prop("shape", "circle")
        name: str | None = self._get_prop("name")
        src: str | None = self._get_prop("src")
        status: AvatarStatus | None = self._get_prop("status")
        subtle: bool = self._get_prop("subtle", False)

        label = name
        if label is not None and status is not None:
            label = f"{label}, {status}"

        # The initials stay in the DOM behind a picture, so a URL that fails to
        # load leaves a name rather than an empty circle.
        body: tuple[ComponentType, ...]
        if name:
            body = (_initials(name),)
        else:
            # No name: whatever the caller put inside, such as an icon or the
            # count at the end of a group.
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
                    # A hairline, because a surface-coloured circle on a
                    # surface-coloured page is only its text otherwise.
                    "bg-surface text-fg-muted border border-border"
                    if subtle
                    else "bg-surface-active text-fg-muted",
                    "font-ui font-semibold leading-none",
                    "bg-cover bg-center" if src is not None else "",
                    radius,
                ),
                style=None if src is None else f"background-image:url({_css_url(src)})",
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
                _SIZE_CLASSES[size],
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
_MEMBER_CLASSES = "inline-flex rounded-full ring-2 ring-canvas -ms-2.5 first:ms-0"


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
        Append a "+N" chip for the people not shown.
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
        for child in self._children:
            if isinstance(child, Avatar):
                child._size_default(size)
            members.append(
                html.span(
                    child,
                    class_=_MEMBER_CLASSES,
                    aria_hidden="true",
                )
            )

        if more is not None:
            # An Avatar rather than a lookalike, so the count sits on exactly
            # the same baseline as the faces beside it. A hand-built span drifted
            # from the real thing the moment Avatar's markup changed.
            members.append(
                html.span(
                    Avatar().size(size).subtle().content(f"+{more}"),
                    class_=_MEMBER_CLASSES,
                    aria_hidden="true",
                )
            )

        return html.span(
            *members,
            class_=classnames("inline-flex items-center", self._get_prop("class_")),
            **{
                "role": "img",
                "aria_label": label,
                **self._get_base_html_attrs(),
            },
        )
