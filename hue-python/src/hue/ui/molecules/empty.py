from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type EmptyVariant = Literal["neutral", "danger"]
type HeadingLevel = Literal["h1", "h2", "h3", "h4", "h5", "h6"]

# Only the icon chip changes tone; the layout is the same either way.
_ICON_CLASSES: dict[EmptyVariant, str] = {
    "neutral": "bg-surface-sunken border-border text-fg-subtle",
    "danger": "bg-danger-subtle border-danger-border text-danger-text",
}

_HEADING_TAGS: dict[HeadingLevel, Callable[..., ComponentType]] = {
    "h1": html.h1,
    "h2": html.h2,
    "h3": html.h3,
    "h4": html.h4,
    "h5": html.h5,
    "h6": html.h6,
}


class Empty(ChainableComponent):
    """
    What to show where content would have been.

    icon(), title(), description() and actions() are all optional. variant()
    tints the icon, compact() tightens the padding, and title() takes a heading
    level for an empty state that stands in for a page.

        Empty().title("No invoices yet").actions(Button().content("Create"))
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .icon(HueIcon("inbox"))
            .title("No invoices yet")
            .description("Invoices appear here once your first order is paid.")
        )

    def variant(self, value: EmptyVariant) -> Self:
        self._props["variant"] = value
        return self

    def compact(self, value: bool = True) -> Self:
        """
        Tighten the padding for an empty state inside a card or a table.
        """
        self._props["compact"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def title(self, value: str, *, heading: HeadingLevel | None = None) -> Self:
        """
        The line that says what is missing.

        Pass heading to render it as a real heading rather than bold text,
        which is worth doing whenever the empty state stands in for a whole
        page or section and belongs in the document outline.
        """
        self._props["title"] = value
        self._props["heading"] = heading
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def actions(self, *values: ComponentType) -> Self:
        self._props["actions"] = values
        return self

    def _render(self, context: Context) -> Component:
        variant: EmptyVariant = self._get_prop("variant", "neutral")
        compact: bool = self._get_prop("compact", False)
        icon: ComponentType | None = self._get_prop("icon")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        actions: tuple[ComponentType, ...] = self._get_prop("actions", ())
        heading: HeadingLevel | None = self._get_prop("heading")

        children: list[ComponentType] = []

        if icon is not None:
            children.append(
                html.span(
                    icon,
                    class_=classnames(
                        "mb-2 flex size-12 items-center justify-center",
                        "rounded-lg border [&_svg]:size-5.5",
                        _ICON_CLASSES[variant],
                    ),
                )
            )

        if title is not None:
            title_classes = "font-ui text-md font-bold"
            children.append(
                html.div(title, class_=title_classes)
                if heading is None
                else _HEADING_TAGS[heading](title, class_=title_classes)
            )

        if description is not None:
            children.append(
                html.p(
                    description,
                    # Measured in characters: a description that runs the full
                    # width of a table is not centred copy, it is a paragraph.
                    class_="max-w-[42ch] text-sm leading-[1.55] text-fg-muted",
                )
            )

        if actions:
            children.append(html.div(*actions, class_="mt-4 flex gap-2"))

        return html.div(
            *children,
            class_=classnames(
                "flex flex-col items-center gap-2 text-center",
                "px-4 py-8" if compact else "px-6 py-12",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
