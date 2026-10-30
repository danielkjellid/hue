from __future__ import annotations

from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.atoms._choice import (
    CHOICE_BOX,
    choice_id,
    choice_row,
    description_id,
    label_id,
)
from hue.ui.base import ChainableComponent
from hue.ui.form import FieldControl
from hue.ui.molecules.field import (
    error_component,
    hint_component,
    legend_component,
    visible_hint,
)
from hue.utils import classnames, render_if

# The dot is drawn by the box itself, because a native input takes no children.
_DOT = (
    "checked:before:content-[''] checked:before:size-[7px] "
    "checked:before:rounded-full checked:before:bg-accent-fg"
)

# Set on the group, but meaningful only on the inputs inside it.
_INPUT_ATTRS = ("form", "x-model")


class Radio(ChainableComponent):
    """
    One choice inside a RadioGroup.

    The group owns the name and which option is selected, so a radio on its
    own has nothing to be exclusive with and is not documented alone.
    description() adds a second line under its label.

        Radio().value("eu").label("Europe")
    """

    category: ClassVar[str | None] = None

    def __init__(self) -> None:
        super().__init__()
        self._group_attrs: dict[str, object] = {}

    @classmethod
    def example(cls) -> Self:
        return cls().value("eu").label("Europe")

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _apply_group(
        self,
        *,
        name: str,
        group_id: str,
        selected: str | None,
        card: bool,
        disabled: bool,
        required: bool,
        input_attrs: dict[str, object],
    ) -> None:
        """
        Called by the group, which owns everything a radio shares with its
        siblings.
        """
        self._props["name"] = name
        self._props["group_id"] = group_id
        self._props["card"] = card
        self._props["checked"] = self._get_prop("value") == selected
        # Required goes on the options rather than the fieldset, which has no
        # such attribute - one marked radio makes the whole name required.
        self._props["required"] = required
        # Attributes set on the group that only mean something on an input.
        self._group_attrs = input_attrs
        if disabled:
            self._props["disabled"] = True

    def _render(self, context: Context) -> Component:
        value: str = self._get_prop("value", "")
        name: str = self._get_prop("name", "")
        disabled: bool = self._get_prop("disabled", False)
        card: bool = self._get_prop("card", False)
        # From the group's id rather than its name, so two groups sharing a
        # name are told apart by giving one of them an id.
        input_id = self._attrs.get("id") or choice_id(
            self._get_prop("group_id", name), value
        )

        label: str | None = self._get_prop("label")
        description: str | None = self._get_prop("description")

        own = {
            "type": "radio",
            "name": name,
            "id": input_id,
            "value": value,
            "class_": classnames(CHOICE_BOX, "rounded-full", _DOT),
            "checked": self._get_prop("checked", False) or None,
            "disabled": disabled or None,
            "required": self._get_prop("required", False) or None,
            # An explicit name, so the description inside the label does not
            # become part of it.
            "aria_labelledby": label_id(input_id) if label is not None else None,
            "aria_describedby": classnames(
                description_id(input_id) if description is not None else None,
                self._attrs.get("aria_describedby"),
            )
            or None,
        }
        # A None of our own means there is nothing to say, so it leaves
        # whatever the caller set in place.
        attrs = {
            **self._get_base_html_attrs(),
            **self._group_attrs,
            **{k: v for k, v in own.items() if v is not None},
        }

        return choice_row(
            html.input_(**attrs),
            control_id=input_id,
            label=label,
            description=description,
            disabled=disabled,
            card=card,
        )


class RadioGroup(FieldControl):
    """
    A set of choices where exactly one can be selected.

    A fieldset with a legend, so the question is announced with each option
    rather than only the option's own label. The group owns the name and the
    selection; the options carry their value and their text.

        RadioGroup().name("region").legend("Region").content(Radio().value("eu")...)
    """

    category: ClassVar[str | None] = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .name("region")
            .legend("Region")
            .value("eu")
            .content(
                Radio().value("eu").label("Europe"),
                Radio().value("us").label("North America"),
            )
        )

    def legend(self, value: str) -> Self:
        """
        The question the options answer.
        """
        self._props["legend"] = value
        return self

    def value(self, value: str) -> Self:
        """
        Which option starts selected.
        """
        self._props["value"] = value
        return self

    def card(self, value: bool = True) -> Self:
        """
        Give every option a box of its own, for a choice whose options
        carry a description rather than a word.
        """
        self._props["card"] = value
        return self

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        legend: str | None = self._get_prop("legend") or self._get_prop("label")
        card: bool = self._get_prop("card", False)
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        error: str | None = self._error(context)
        hint: str | None = self._get_prop("hint")
        control_id = self._input_id()

        fieldset_attrs = self._control_attrs(
            context,
            class_=classnames("flex flex-col gap-1.5", self._get_prop("class_")),
            # aria-invalid is not supported on a group or on a single radio in
            # ARIA 1.2, only on a radiogroup. The legend still names it.
            role="radiogroup",
            # The legend names the group, so no aria-label as well.
            aria_describedby=self._describedby(context),
            aria_invalid="true" if error is not None else None,
            disabled=disabled or None,
        )
        # The inputs are what a form submits and what holds a value, so form
        # and x-model go to them. On the fieldset, form ties only the fieldset
        # to the form, and Alpine ignores x-model.
        input_attrs = {
            key: fieldset_attrs.pop(key)
            for key in _INPUT_ATTRS
            if key in fieldset_attrs
        }

        options: list[ComponentType] = []
        for child in self._children:
            if isinstance(child, Radio):
                child._apply_group(
                    name=name,
                    group_id=control_id,
                    selected=self._get_prop("value"),
                    card=card,
                    disabled=disabled,
                    required=required,
                    input_attrs=input_attrs,
                )
            options.append(child)

        return html.fieldset(
            render_if(legend, lambda text: legend_component(text, required)),
            html.div(
                *options,
                class_=classnames(
                    "flex flex-col",
                    "gap-2" if card else "gap-3",
                ),
            ),
            render_if(
                visible_hint(hint, error), lambda text: hint_component(text, control_id)
            ),
            render_if(error, lambda text: error_component(text, control_id)),
            **fieldset_attrs,
        )
