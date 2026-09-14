from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import CONTROL_SIZES, FIELD_SHELL, ControlSize
from hue.ui.form import FormControl
from hue.ui.molecules.field import FieldLayout
from hue.utils import classnames, render_if

_SELECT_CLASSES = classnames(
    FIELD_SHELL,
    "appearance-none cursor-pointer pe-8",
    # The chevron rides on the control rather than being a sibling element, so
    # nothing has to stay aligned over a box whose height changes with the
    # size. It is a theme token, because a data URI carries spaces and quotes
    # and so cannot survive inside a class attribute.
    "bg-select-chevron bg-no-repeat bg-[position:right_10px_center]",
)


class NativeSelect(FormControl):
    """
    A select built on the browser's own, for a short list of plain choices.

    The platform control means the phone picker, type-ahead and every
    assistive-tech behaviour come for free. Reach for Select instead when an
    option needs more than a line of text.

        NativeSelect("tz").label("Time zone").options([("utc", "UTC")])
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .name("region")
            .label("Region")
            .options([("eu", "Europe"), ("us", "North America")])
        )

    def options(self, value: list[tuple[str, str]]) -> Self:
        """
        The choices, as (value, label) pairs.
        """
        self._props["options"] = value
        return self

    def value(self, value: str) -> Self:
        """
        Which option starts selected.
        """
        self._props["value"] = value
        return self

    def placeholder(self, value: str) -> Self:
        """
        A first option standing in for no choice yet.

        Rendered disabled, so it can be read but not chosen back once a real
        option has been picked.
        """
        self._props["placeholder"] = value
        return self

    def size(self, value: ControlSize) -> Self:
        self._props["size"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def layout(self, value: FieldLayout) -> Self:
        self._props["layout"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        name = self._require_name()
        size: ControlSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        options: list[tuple[str, str]] = self._get_prop("options", [])
        selected: str | None = self._get_prop("value")
        placeholder: str | None = self._get_prop("placeholder")
        error: str | None = self._get_prop("error")
        control_id = self._input_id()

        children: list[ComponentType] = [
            # A placeholder is one more option, first and disabled, so it is
            # built here rather than spliced in afterwards.
            render_if(
                placeholder,
                lambda text: html.option(
                    text,
                    value="",
                    disabled=True,
                    selected=True if selected is None else None,
                ),
            ),
            *(
                html.option(
                    label,
                    value=value,
                    selected=True if value == selected else None,
                )
                for value, label in options
            ),
        ]

        select_attrs = self._control_attrs(
            name=name,
            id=control_id,
            class_=classnames(
                _SELECT_CLASSES, CONTROL_SIZES[size], self._get_prop("class_")
            ),
            disabled=disabled or None,
            required=required or None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=self._describedby(),
        )

        return self._field(html.select(*children, **select_attrs))
