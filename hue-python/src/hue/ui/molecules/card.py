from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type CardVariant = Literal["bordered", "raised", "flat"]

_VARIANT_CLASSES: dict[CardVariant, str] = {
    "bordered": "bg-surface border-border",
    "raised": "bg-surface border-transparent shadow-raised",
    "flat": "bg-surface-sunken border-transparent",
}

# The ring answers the title's own control only. A plain has-focus-visible
# would also light the whole card up when one of its footer buttons is
# focused. Every other control in the card, and a label that operates one,
# is lifted above the title's overlay, or the overlay would swallow its clicks.
_LINKED_CLASSES = classnames(
    "relative transition-[border-color,box-shadow]",
    "hover:border-border-hover hover:shadow-raised",
    "has-[[data-card-link]:focus-visible]:ring-2",
    "has-[[data-card-link]:focus-visible]:ring-accent",
    "has-[[data-card-link]:focus-visible]:ring-offset-2",
    "has-[[data-card-link]:focus-visible]:ring-offset-canvas",
    "[&_:is(a,button,input,select,textarea,summary,label,[tabindex],[role=button]):not([data-card-link])]:relative",
)

# The overlay is what makes the whole surface clickable while only the title
# is the control. The card is its containing block, so this element must stay
# unpositioned.
_STRETCHED_CONTROL = (
    "cursor-pointer text-start outline-none after:absolute after:inset-0"
)


# What moves from a linked card onto its title: what names the control and
# what activates it, including the wiring an overlay or a request puts on its
# trigger, and the mark an overlay finds its trigger by, since that is what it
# anchors to and gives focus back to. The rest (an id, x-show, x-data, other
# data attributes) describes the card as a whole, so moving it would hide,
# target or scope only the title.
_CONTROL_ATTRS = frozenset(
    {
        "aria_label",
        "aria_labelledby",
        "aria_describedby",
        "aria_keyshortcuts",
        "aria_haspopup",
        "aria_expanded",
        "aria_pressed",
        "aria_controls",
        "x_ref",
        "x_headers",
        "x_sync",
    }
)
_CONTROL_ATTR_PREFIXES = (
    "@click",
    "@keydown",
    "@keyup",
    "@ajax:",
    "x-on:click",
    "x-on:keydown",
    "x-on:keyup",
    "x-on:ajax:",
    "x-target",
    "data-hue-trigger",
)


def _is_control_attr(key: str) -> bool:
    if key.startswith(_CONTROL_ATTR_PREFIXES):
        return True
    bound = key.removeprefix("x-bind:").removeprefix(":")
    return bound.replace("-", "_") in _CONTROL_ATTRS


class Card(ChainableComponent):
    """
    A container assembled from CardMedia, CardHeader, CardBody and CardFooter.

    variant() picks the edge treatment. href() makes the header's title a link
    and interactive() a button, stretched over the whole card so it can be
    clicked anywhere. Other buttons in the card stay clickable on top of it.

        Card().content(CardHeader().title("Monthly revenue"), CardBody()...)
    """

    category = "Layout"

    @classmethod
    def example(cls) -> Self:
        return cls().content(
            CardHeader().title("Monthly revenue").description("Last 30 days"),
            CardBody().content("$48,290"),
        )

    def variant(self, value: CardVariant) -> Self:
        self._props["variant"] = value
        return self

    def href(self, value: str) -> Self:
        """
        Make the card a link to this URL.

        The link is a real anchor around the title, so middle-click and "open
        in new tab" work, and a screen reader reads the title rather than the
        whole card as its name.
        """
        self._props["href"] = value
        return self

    def interactive(self, value: bool = True) -> Self:
        """
        Make the card a button, for one that acts rather than navigates.
        href() already implies this.
        """
        self._props["interactive"] = value
        return self

    def _render(self, context: Context) -> Component:
        variant: CardVariant = self._get_prop("variant", "bordered")
        href: str | None = self._get_prop("href")
        linked = href is not None or self._get_prop("interactive", False)

        classes = classnames(
            "flex flex-col overflow-hidden rounded-lg border",
            _VARIANT_CLASSES[variant],
            _LINKED_CLASSES if linked else "",
            self._get_prop("class_"),
        )
        attrs = self._get_base_html_attrs()

        if not linked:
            return html.div(*self._children, class_=classes, **attrs)

        # The card hands the link to the first titled header among its own
        # children and to nothing else, so there is exactly one control
        # however many headers sit further down.
        found = next(
            (
                (i, child)
                for i, child in enumerate(self._children)
                if isinstance(child, CardHeader)
                and child._get_prop("title") is not None
            ),
            None,
        )
        if found is None:
            raise ValueError(
                "A card with href() or interactive() needs a CardHeader with a "
                "title placed directly in it: the title is the link, and the "
                "text that names it."
            )

        index, header = found
        link = _CardLink(href, {k: v for k, v in attrs.items() if _is_control_attr(k)})
        children = list(self._children)
        children[index] = header._render_linked(link)

        return html.div(
            *children,
            class_=classes,
            **{k: v for k, v in attrs.items() if not _is_control_attr(k)},
        )


@dataclass(frozen=True, slots=True)
class _CardLink:
    href: str | None
    attrs: dict[str, Any]


class CardMedia(ChainableComponent):
    """
    An image across the top of a card.

    The band is a fixed 16/9 and the image fills it, so a row of cards lines up
    whatever sizes the pictures happen to be.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().content(html.img(src="/assets/cover.svg", alt=""))

    def _render(self, context: Context) -> Component:
        return html.div(
            *self._children,
            # What a CardBody below it finds it by.
            data_card_media="",
            class_=classnames(
                "aspect-video overflow-hidden bg-surface-sunken",
                "[&_img]:block [&_img]:size-full [&_img]:object-cover",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class CardHeader(ChainableComponent):
    """
    A card's title and description.

    Children render on the trailing side of the header, opposite the title.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().title("Monthly revenue").description("Last 30 days")

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def _render(self, context: Context) -> Component:
        return self._render_linked(None)

    def _render_linked(self, link: _CardLink | None) -> ComponentType:
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")

        heading = []
        if title is not None:
            heading.append(
                html.div(
                    _title_control(title, link),
                    class_="font-ui text-md font-bold tracking-[-0.01em] text-fg",
                )
            )
        if description is not None:
            heading.append(
                html.div(
                    description, class_="mt-[3px] text-sm leading-normal text-fg-muted"
                )
            )

        return html.div(
            html.div(*heading, class_="min-w-0"),
            *self._children,
            class_=classnames(
                "flex items-start justify-between gap-4 px-5 pt-5 pb-3",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


def _title_control(title: str, link: _CardLink | None) -> ComponentType:
    if link is None:
        return title
    if link.href is not None:
        return html.a(
            title,
            href=link.href,
            data_card_link="",
            class_=_STRETCHED_CONTROL,
            **link.attrs,
        )
    return html.button(
        title,
        type="button",
        data_card_link="",
        class_=_STRETCHED_CONTROL,
        **link.attrs,
    )


class CardBody(ChainableComponent):
    """
    A card's content.

    Takes its top spacing from a header above it, and pads itself when it
    comes first or straight after media.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().content("Card content")

    def _render(self, context: Context) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "px-5 pt-0 pb-5 first:pt-5 [[data-card-media]+&]:pt-5 text-base",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class CardFooter(ChainableComponent):
    """
    A card's actions, on a tinted strip along the bottom.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().content("Footer")

    def _render(self, context: Context) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "flex items-center justify-end gap-2 px-5 py-4",
                "border-t border-border bg-surface-sunken",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
