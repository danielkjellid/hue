from __future__ import annotations

from typing import Any, Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type ItemVariant = Literal["plain", "bordered"]

_VARIANT_CLASSES: dict[ItemVariant, str] = {
    "plain": "border-transparent",
    "bordered": "border-border bg-surface",
}


class Item(ChainableComponent):
    """
    One row: media, a title and description, and actions.

    Title and description truncate rather than wrap. href() renders it as a
    link and interactive() as a button; otherwise it stays a plain container,
    since most of its uses sit inside something that owns the semantics.

    selected() sets aria-selected, which needs a role that supports selection -
    option, row, tab. Components built on Item set that role themselves.

        Item().title("Ada Lovelace").description("ada@example.com")
    """

    category = "Data"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("bordered")
            .title("Ada Lovelace")
            .description("ada@example.com · Owner")
        )

    def variant(self, value: ItemVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def media(self, value: ComponentType) -> Self:
        """
        What sits before the text: an avatar, an icon, a thumbnail.
        """
        self._props["media"] = value
        return self

    def actions(self, *values: ComponentType) -> Self:
        """
        What sits after the text, pinned to the trailing edge.
        """
        self._props["actions"] = values
        return self

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def interactive(self, value: bool = True) -> Self:
        self._props["interactive"] = value
        return self

    def selected(self, value: bool = True) -> Self:
        self._props["selected"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ItemVariant = self._get_prop("variant", "plain")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        media: ComponentType | None = self._get_prop("media")
        actions: tuple[ComponentType, ...] = self._get_prop("actions", ())
        href: str | None = self._get_prop("href")
        interactive: bool = self._get_prop("interactive", False)
        selected: bool = self._get_prop("selected", False)
        disabled: bool = self._get_prop("disabled", False)

        operable = href is not None or interactive

        # Selection replaces the variant's own surface rather than layering over
        # it: two background utilities on one element resolve by stylesheet
        # order, not by the order they are written, so the row would have been
        # selected or not depending on what Tailwind happened to emit last.
        surface = (
            "bg-accent-subtle border-accent-border"
            if selected
            else _VARIANT_CLASSES[variant]
        )

        classes = classnames(
            "flex w-full items-center gap-3 rounded-md border p-3 text-start",
            surface,
            classnames(
                "cursor-pointer transition-colors hover:bg-surface-hover",
                FOCUS_RING,
            )
            if operable and not disabled
            else "",
            "opacity-55 pointer-events-none" if disabled else "",
            self._get_prop("class_"),
        )

        body = html.span(
            render_if(
                title,
                lambda value: html.span(
                    value,
                    class_="block truncate font-ui text-base font-semibold text-fg",
                ),
            ),
            render_if(
                description,
                lambda value: html.span(
                    value,
                    class_="block truncate text-sm leading-snug text-fg-muted",
                ),
            ),
            *self._children,
            class_="min-w-0 flex-1",
        )

        children: list[ComponentType] = []
        if media is not None:
            children.append(
                html.span(media, class_="flex flex-none items-center justify-center")
            )
        children.append(body)
        if actions:
            children.append(
                html.span(*actions, class_="flex flex-none items-center gap-2")
            )

        attrs: dict[str, Any] = {
            "aria_selected": "true" if selected else None,
            **self._get_base_html_attrs(),
        }

        if href is not None:
            return html.a(
                *children,
                href=href,
                class_=classes,
                # A disabled link is not a thing, so it stops being a link.
                aria_disabled="true" if disabled else None,
                **attrs,
            )
        if interactive:
            return html.button(
                *children,
                type="button",
                class_=classes,
                disabled=disabled or None,
                **attrs,
            )

        return html.div(
            *children,
            class_=classes,
            aria_disabled="true" if disabled else None,
            **attrs,
        )
