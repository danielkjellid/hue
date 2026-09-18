from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING, SEGMENTED_ITEM, SEGMENTED_TRACK
from hue.ui.base import ChainableComponent, Clickable
from hue.utils import classnames

type SegmentedSize = Literal["sm", "md", "lg"]

# The track adds 3px of padding and a 1px border either side, so an option sits
# 8px shorter than the control height the size is named for.
_OPTION_HEIGHTS: dict[SegmentedSize, str] = {
    "sm": "h-6",
    "md": "h-7",
    "lg": "h-9",
}

# Square, so an icon-only option is not a lopsided slab.
_OPTION_WIDTHS: dict[SegmentedSize, str] = {
    "sm": "w-6",
    "md": "w-7",
    "lg": "w-9",
}

_OPTION_TEXT: dict[SegmentedSize, str] = {
    "sm": "text-xs",
    "md": "text-sm",
    "lg": "text-base",
}


class SegmentedOption(Clickable):
    """
    One option in a SegmentedControl.

    The control decides which option is selected, by matching value() against
    its own. label() names an option whose content is only an icon; with
    visible text the text names it.
    """

    category = None

    @classmethod
    def example(cls) -> Self:
        return cls().value("week").content("Week")

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def icon_only(self, label: str) -> Self:
        """
        Drop to a square option holding nothing but an icon.

        The label is required and becomes the accessible name, because an icon
        on its own has none.
        """
        self._props["icon_only"] = True
        self._props["label"] = label
        return self

    def _configure(
        self, *, size: SegmentedSize, selected: bool | None, interactive: bool
    ) -> None:
        """
        Called by the control, which owns size and selection.
        """
        self._props["size"] = size
        if selected is not None:
            self._props["selected"] = selected

        # Skipped when the caller already drives this option themselves, so the
        # control never fights a binding of their own.
        if interactive and ":aria-pressed" not in self._attrs:
            value = self._get_prop("value")
            self.x_on("click", unsafe(f"selected = {value!r}"))
            self.x_bind("aria-pressed", unsafe(f"selected === {value!r}"))

    def _render(self, context: HueContext) -> Component:
        size: SegmentedSize = self._get_prop("size", "md")
        label: str | None = self._get_prop("label")
        selected: bool | None = self._get_prop("selected")
        icon_only: bool = self._get_prop("icon_only", False)

        attrs = {
            "aria_label": label,
            # Left to the caller's own binding when there is one, so a control
            # driven by Alpine can decide this in the browser instead.
            "aria_pressed": None if selected is None else str(selected).lower(),
            **self._get_base_html_attrs(),
        }

        return html.button(
            *self._children,
            type="button",
            class_=classnames(
                SEGMENTED_ITEM,
                "aria-pressed:bg-surface aria-pressed:text-fg",
                "aria-pressed:shadow-segment",
                FOCUS_RING,
                _OPTION_HEIGHTS[size],
                _OPTION_TEXT[size],
                # Picked here rather than layered, since two padding-inline
                # utilities would resolve by stylesheet order.
                _OPTION_WIDTHS[size] if icon_only else "px-2.5",
                self._get_prop("class_"),
            ),
            **attrs,
        )


class SegmentedControl(ChainableComponent):
    """
    A row of options where exactly one is on.

    A radio group wearing a button costume, so it owns how its options look and
    marks the one matching value() as pressed. label() names the whole control,
    which is what tells a screen reader what is being chosen.

        SegmentedControl().label("Date range").value("week").content(...)
    """

    category = "Actions"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Date range")
            .value("week")
            .content(
                SegmentedOption().value("day").content("Day"),
                SegmentedOption().value("week").content("Week"),
                SegmentedOption().value("month").content("Month"),
            )
        )

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def value(self, value: str) -> Self:
        """
        Which option is on. Leave it unset when something else, such as an
        Alpine binding on the options, decides in the browser.
        """
        self._props["value"] = value
        return self

    def size(self, value: SegmentedSize) -> Self:
        """
        The control height the whole track adds up to.
        """
        self._props["size"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        size: SegmentedSize = self._get_prop("size", "md")
        label: str | None = self._get_prop("label")
        selected: str | None = self._get_prop("value")

        options: list[ComponentType] = []
        for child in self._children:
            if isinstance(child, SegmentedOption):
                child._configure(
                    size=size,
                    selected=None
                    if selected is None
                    else child._get_prop("value") == selected,
                    # With no value of its own the control has no state to keep,
                    # so selection belongs to whoever set it up that way.
                    interactive=selected is not None,
                )
            options.append(child)

        attrs = {
            "role": "group",
            "aria_label": label,
            # The server-rendered aria-pressed above is what paints first, so
            # the right option is already on before Alpine takes over.
            **({"x-data": f"{{ selected: {selected!r} }}"} if selected else {}),
            **self._get_base_html_attrs(),
        }

        return html.div(
            *options,
            class_=classnames(SEGMENTED_TRACK, self._get_prop("class_")),
            **attrs,
        )
