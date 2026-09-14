from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui._styles import CONTROL_SHELL
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.text import Label
from hue.ui.base import ChainableComponent
from hue.utils import classnames

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

    hue's own controls build one for themselves, so reach for this directly
    when wrapping a control hue does not ship. html_for() has to name that
    control's id, which is what ties the label and the messages to it.

        Field().label("Region").html_for("region").content(my_select)
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Workspace URL")
            .hint("Used in every share link.")
            .html_for("workspace-url")
            .content(html.input_(id="workspace-url", class_=CONTROL_SHELL))
        )

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def html_for(self, value: str) -> Self:
        """
        The id of the control being wrapped.
        """
        self._props["html_for"] = value
        return self

    def hint(self, value: str) -> Self:
        """
        A note about what to enter, shown under the control.
        """
        self._props["hint"] = value
        return self

    def error(self, value: str) -> Self:
        """
        What is wrong with the value. Shown in place of the hint.
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
        control_id: str | None = self._get_prop("html_for")
        horizontal = layout == "horizontal"

        header: list[ComponentType] = []
        if label is not None:
            label_component = Label(label)
            if control_id is not None:
                label_component.html_for(control_id)
            header.append(
                label_component.required(self._get_prop("required", False))
                .disabled(self._get_prop("disabled", False))
                .hidden_label(self._get_prop("hidden_label", False))
            )
        # Laid beside the control, the hint belongs with the label: under a
        # 180px column it reads as part of the question, where under the
        # control it would sit in the next row's space.
        if horizontal and hint is not None:
            header.append(hint_component(hint, control_id))
        if trailing:
            header.append(html.span(*trailing, class_=TRAILING_CLASSES))

        # An error replaces the hint rather than joining it: two lines of
        # supporting text under one control is one more than anyone reads.
        messages: list[ComponentType] = []
        if error is not None:
            messages.append(error_component(error, control_id))
        elif hint is not None and not horizontal:
            messages.append(hint_component(hint, control_id))

        control: list[ComponentType] = [*self._children, *messages]

        return html.div(
            html.div(
                *header,
                class_=classnames(
                    "flex",
                    f"{_LABEL_COLUMN} flex-col items-start gap-0.5"
                    if horizontal
                    else "items-baseline justify-between gap-3",
                ),
            )
            if header
            else UNDEFINED,
            html.div(*control, class_="flex min-w-0 flex-1 flex-col gap-1.5")
            if horizontal
            else UNDEFINED,
            *(() if horizontal else control),
            class_=classnames(
                "flex",
                "flex-row items-start gap-6" if horizontal else "flex-col gap-1.5",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
