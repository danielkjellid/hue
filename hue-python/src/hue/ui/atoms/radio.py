from __future__ import annotations

from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.atoms._choice import (
    CHOICE_BOX,
    choice_row,
    description_id,
    label_id,
)
from hue.ui.atoms.text import required_marker
from hue.ui.base import ChainableComponent
from hue.ui.form import FieldControl
from hue.ui.molecules.field import error_component, hint_component
from hue.utils import classnames, render_if, render_when

# The dot is drawn by the box itself, because a native input takes no children.
_DOT = (
    "checked:before:content-[''] checked:before:size-[7px] "
    "checked:before:rounded-full checked:before:bg-accent-fg"
)


class Radio(ChainableComponent):
    """
    One choice inside a RadioGroup.

    The group owns the name and which option is selected, so a radio on its
    own has nothing to be exclusive with and is not documented alone.
    description() adds a second line under its label.

        Radio().value("eu").label("Europe")
    """

    category: ClassVar[str | None] = None

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
        selected: str | None,
        card: bool,
        disabled: bool,
        required: bool,
        form: str | None,
    ) -> None:
        """
        Called by the group, which owns everything a radio shares with its
        siblings.
        """
        self._props["name"] = name
        self._props["card"] = card
        self._props["checked"] = self._get_prop("value") == selected
        # Required goes on the options rather than the fieldset, which has no
        # such attribute - one marked radio makes the whole name required.
        self._props["required"] = required
        # The inputs are what a form submits, and a form attribute on the
        # fieldset around them ties only the fieldset to it.
        self._props["form"] = form
        if disabled:
            self._props["disabled"] = True

    def _render(self, context: Context) -> Component:
        value: str = self._get_prop("value", "")
        name: str = self._get_prop("name", "")
        disabled: bool = self._get_prop("disabled", False)
        card: bool = self._get_prop("card", False)
        input_id = f"{name}-{value}"

        label: str | None = self._get_prop("label")
        description: str | None = self._get_prop("description")

        return choice_row(
            html.input_(
                type="radio",
                name=name,
                id=input_id,
                value=value,
                class_=classnames(CHOICE_BOX, "rounded-full", _DOT),
                checked=self._get_prop("checked", False) or None,
                disabled=disabled or None,
                required=self._get_prop("required", False) or None,
                form=self._get_prop("form"),
                # An explicit name, so the description inside the label does
                # not become part of it.
                aria_labelledby=label_id(input_id) if label is not None else None,
                aria_describedby=(
                    description_id(input_id) if description is not None else None
                ),
                **self._get_base_html_attrs(),
            ),
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

        options: list[ComponentType] = []
        for child in self._children:
            if isinstance(child, Radio):
                child._apply_group(
                    name=name,
                    selected=self._get_prop("value"),
                    card=card,
                    disabled=disabled,
                    required=required,
                    form=self._attrs.get("form"),
                )
            options.append(child)

        return html.fieldset(
            render_if(
                legend,
                lambda text: html.legend(
                    text,
                    # A legend is the group's label, so it carries the same
                    # mark a field's label does when the answer is required.
                    render_when(required, required_marker()),
                    # The margin is the fieldset's own gap, written out: a
                    # legend is not a flex item of its fieldset, so the gap
                    # that spaces every other child never reaches it and the
                    # first option sits flush against the question.
                    class_=(
                        "mb-1.5 inline-flex items-center gap-[5px] "
                        "font-ui text-sm font-medium leading-[1.4] text-fg"
                    ),
                ),
            ),
            html.div(
                *options,
                class_=classnames(
                    "flex flex-col",
                    "gap-2" if card else "gap-3",
                ),
            ),
            render_if(hint, lambda text: hint_component(text, name)),
            render_if(error, lambda text: error_component(text, name)),
            class_=classnames("flex flex-col gap-1.5", self._get_prop("class_")),
            **{
                # The legend names the group, so no aria-label as well.
                "aria_describedby": self._describedby(
                    context,
                ),
                "aria_invalid": "true" if error is not None else None,
                "disabled": disabled or None,
                **self._get_base_html_attrs(),
            },
        )
