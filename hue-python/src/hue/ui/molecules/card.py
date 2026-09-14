from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type CardVariant = Literal["bordered", "raised", "flat"]

_VARIANT_CLASSES: dict[CardVariant, str] = {
    "bordered": "bg-surface border-border",
    "raised": "bg-surface border-transparent shadow-raised",
    "flat": "bg-surface-sunken border-transparent",
}

_INTERACTIVE_CLASSES = classnames(
    "cursor-pointer text-start transition-[border-color,box-shadow]",
    "hover:border-border-hover hover:shadow-raised",
    FOCUS_RING,
)


class Card(ChainableComponent):
    """
    A container assembled from CardMedia, CardHeader, CardBody and CardFooter.

    variant() picks the edge treatment. href() renders the whole surface as a
    link and interactive() as a button, making it a single tab stop - so it
    cannot also hold its own buttons, which would nest interactive elements.

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
        Turn the whole card into a link.

        A real anchor, so middle-click and "open in new tab" work - a div with
        a click handler breaks both.
        """
        self._props["href"] = value
        return self

    def interactive(self, value: bool = True) -> Self:
        """
        Make the whole surface a button, for a card that acts rather than
        navigates. href() already implies this.
        """
        self._props["interactive"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: CardVariant = self._get_prop("variant", "bordered")
        href: str | None = self._get_prop("href")
        interactive: bool = self._get_prop("interactive", False)

        classes = classnames(
            "flex flex-col overflow-hidden rounded-lg border",
            _VARIANT_CLASSES[variant],
            _INTERACTIVE_CLASSES if (href is not None or interactive) else "",
            self._get_prop("class_"),
        )

        attrs = self._get_base_html_attrs()

        # A real anchor or button, never a div with a handler: one tab stop,
        # real keyboard activation, and middle-click still opens a new tab.
        if href is not None:
            return html.a(*self._children, href=href, class_=classes, **attrs)
        if interactive:
            return html.button(*self._children, type="button", class_=classes, **attrs)

        return html.div(*self._children, class_=classes, **attrs)


class CardMedia(ChainableComponent):
    """
    An image across the top of a card.

    Only the width is locked: the image keeps its own aspect ratio rather than
    being cropped into a fixed one.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().content(html.img(src="/cover.jpg", alt=""))

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "overflow-hidden bg-surface-sunken",
                "[&_img]:block [&_img]:w-full [&_img]:h-auto",
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

    def _render(self, context: HueContext) -> Component:
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")

        heading = []
        if title is not None:
            heading.append(
                html.div(
                    title,
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


class CardBody(ChainableComponent):
    """
    A card's content.

    Takes its top spacing from whatever sits above it, and pads itself when it
    stands alone.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().content("Card content")

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "px-5 pt-0 pb-5 first:pt-5 text-base",
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

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "flex items-center justify-end gap-2 px-5 py-4",
                "border-t border-border bg-surface-sunken",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
