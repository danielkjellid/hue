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
        self._props["src"] = value
        return self

    def size(self, value: AvatarSize) -> Self:
        self._props["size"] = value
        return self

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
            # The wrapper is already labelled, so the image is decorative -
            # repeating the name in alt would announce it twice.
            body = (html.img(src=src, alt="", class_="size-full object-cover"),)
        elif name:
            body = (_initials(name),)
        else:
            # No picture and no name: whatever the caller put inside, such as an
            # icon or an overflow count.
            body = self._children

        return html.span(
            *body,
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
                "relative inline-flex items-center justify-center shrink-0",
                "overflow-hidden select-none bg-surface-active text-fg-muted",
                "font-ui font-semibold leading-none",
                _SIZE_CLASSES[size],
                "rounded-md" if shape == "square" else "rounded-full",
                self._get_prop("class_"),
            ),
            **{
                # An unlabelled role="img" announces an image with no name, so
                # a decorative avatar stays a plain span.
                **({"role": "img", "aria_label": label} if label else {}),
                **self._get_base_html_attrs(),
            },
        )


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
        # Avatar cannot end up announced twice however it was constructed.
        members = [
            html.span(
                child,
                class_="ring-2 ring-canvas rounded-full -ms-2.5 first:ms-0",
                aria_hidden="true",
            )
            for child in self._children
        ]

        if more is not None:
            # Built here rather than as an Avatar: the chip is not a person, and
            # layering its quieter colours over an Avatar's own would leave two
            # background utilities on one element, resolved by stylesheet order
            # rather than by intent. It shares only the size.
            members.append(
                html.span(
                    html.span(
                        f"+{more}",
                        class_=classnames(
                            "inline-flex items-center justify-center shrink-0",
                            "rounded-full bg-surface-sunken text-fg-subtle",
                            "font-ui font-semibold leading-none select-none",
                            _SIZE_CLASSES[size],
                        ),
                    ),
                    class_="ring-2 ring-canvas rounded-full -ms-2.5 first:ms-0",
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
