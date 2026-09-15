from __future__ import annotations

from typing import ClassVar, Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.text import Label
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type FieldLayout = Literal["stacked", "horizontal"]

# The label column in the horizontal layout. Wide enough for two or three
# words, so a settings page keeps one edge down the middle of the form.
_LABEL_COLUMN = "w-[180px] flex-none"

_SUPPORTING_TEXT = "text-xs leading-[1.45]"

# The trailing end of the header row: "Optional", a unit, a character count.
TRAILING_CLASSES = f"{_SUPPORTING_TEXT} font-normal text-fg-subtle"


def hint_id(control_id: str) -> str:
    """
    The id of the hint belonging to the control with this id.
    """
    return f"{control_id}-hint"


def error_id(control_id: str) -> str:
    """
    The id of the error belonging to the control with this id.
    """
    return f"{control_id}-error"


def hint_component(text: str, control_id: str | None = None) -> ComponentType:
    """
    A field's hint, as the controls and Field both render it.
    """
    return html.span(
        text,
        id=None if control_id is None else hint_id(control_id),
        class_=f"{_SUPPORTING_TEXT} text-fg-muted",
    )


def error_component(text: str, control_id: str | None = None) -> ComponentType:
    """
    A field's error, as the controls and Field both render it.

    role="alert" because an error usually appears in response to a submit the
    user has already made, and would otherwise go unannounced. The icon carries
    no meaning colour does not - it is there so the message does not rely on
    red alone.
    """
    return html.span(
        HueIcon("circle-alert").class_("mt-0.5 size-[13px] flex-none"),
        text,
        id=None if control_id is None else error_id(control_id),
        role="alert",
        class_=f"flex items-start gap-[5px] {_SUPPORTING_TEXT} text-danger-text",
    )


class Field(ChainableComponent):
    """
    The frame around a form control: its label, its hint and its error.

    Not documented on its own and not something to reach for directly: the
    controls build one for themselves, and their own modifiers - label(),
    hint(), error(), layout() - are the API. This is where those land.
    """

    category: ClassVar[str | None] = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def html_for(self, value: str) -> Self:
        """
        The id of the control being wrapped.
        """
        self._props["html_for"] = value
        return self

    def hint(self, value: str | None) -> Self:
        """
        A note about what to enter, shown under the control. None for no hint,
        so a control can pass its own straight through.
        """
        self._props["hint"] = value
        return self

    def error(self, value: str | None) -> Self:
        """
        What is wrong with the value. Shown in place of the hint. None for no
        error, so a control can pass its own straight through.
        """
        self._props["error"] = value
        return self

    def trailing(self, *values: ComponentType) -> Self:
        """
        The far end of the label row: "Optional", a unit, a character count.
        """
        self._props["trailing"] = values
        return self

    def layout(self, value: FieldLayout) -> Self:
        self._props["layout"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        """
        Keep the label for screen readers but take it off the screen, for a
        control whose purpose is already obvious from where it sits.
        """
        self._props["hidden_label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        layout: FieldLayout = self._get_prop("layout", "stacked")
        label: str | None = self._get_prop("label")
        hint: str | None = self._get_prop("hint")
        error: str | None = self._get_prop("error")
        trailing: tuple[ComponentType, ...] = self._get_prop("trailing", ())
        horizontal = layout == "horizontal"

        header: list[ComponentType] = [
            render_if(label, self._label),
            # Laid beside the control, the hint belongs with the label: under a
            # 180px column it reads as part of the question, where under the
            # control it would sit in the next row's space.
            render_if(hint if horizontal else None, self._hint),
            render_if(
                trailing or None,
                lambda items: html.span(*items, class_=TRAILING_CLASSES),
            ),
        ]

        # An error replaces the hint rather than joining it: two lines of
        # supporting text under one control is one more than anyone reads. In
        # the horizontal layout the hint has already gone up beside the label.
        control: list[ComponentType] = [
            *self._children,
            render_if(
                error,
                self._error,
                fallback=render_if(None if horizontal else hint, self._hint),
            ),
        ]

        # A label on its own, beside a control on its own, is one line against
        # one box: centring them is the only thing that reads as a row. The
        # moment either column has a second line - a hint under the label, an
        # error under the control - the two have to start at the same top edge
        # instead, or the label drifts down past the control it names.
        rows = (self._filled(header), self._filled(control))
        single_line = horizontal and all(len(items or ()) <= 1 for items in rows)
        row_alignment = "items-center" if single_line else "items-start"

        return html.div(
            render_if(
                self._filled(header),
                lambda items: html.div(
                    *items,
                    class_=classnames(
                        "flex",
                        f"{_LABEL_COLUMN} flex-col items-start gap-0.5"
                        if horizontal
                        else "items-baseline justify-between gap-3",
                    ),
                ),
            ),
            # Horizontal puts the control and its messages in their own column
            # beside the label; stacked has nothing to wrap them in.
            render_if(
                control if horizontal else None,
                lambda items: html.div(
                    *items, class_="flex min-w-0 flex-1 flex-col gap-1.5"
                ),
            ),
            *(() if horizontal else control),
            class_=classnames(
                "flex",
                f"flex-row gap-6 {row_alignment}" if horizontal else "flex-col gap-1.5",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )

    @staticmethod
    def _filled(items: list[ComponentType]) -> list[ComponentType] | None:
        """
        The items that will actually render, or None when none of them will.
        """
        rendered = [item for item in items if item is not UNDEFINED]
        return rendered or None

    def _label(self, text: str) -> ComponentType:
        control_id: str | None = self._get_prop("html_for")
        label = Label(text)
        if control_id is not None:
            label.html_for(control_id)
        return (
            label.required(self._get_prop("required", False))
            .disabled(self._get_prop("disabled", False))
            .hidden_label(self._get_prop("hidden_label", False))
        )

    def _hint(self, text: str) -> ComponentType:
        return hint_component(text, self._get_prop("html_for"))

    def _error(self, text: str) -> ComponentType:
        return error_component(text, self._get_prop("html_for"))
