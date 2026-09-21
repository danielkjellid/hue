from __future__ import annotations

from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui.atoms._choice import (
    CHOICE_BOX,
    choice_row,
    description_id,
    label_id,
)
from hue.ui.form import FormControl
from hue.ui.molecules.field import error_component
from hue.utils import classnames, render_if

# The tick and the dash are drawn by the box itself. A clipped square rather
# than an icon element, because a native input takes no children - and the
# indeterminate dash has to win over the tick when both states are set, which
# is what the not-checked ordering below is for.
_TICK = (
    "checked:not-indeterminate:before:content-[''] "
    "checked:not-indeterminate:before:size-[10px] "
    "checked:not-indeterminate:before:bg-accent-fg "
    "checked:not-indeterminate:before:checkmark"
)

_DASH = (
    "indeterminate:border-accent indeterminate:bg-accent "
    "indeterminate:before:content-[''] indeterminate:before:h-[2px] "
    "indeterminate:before:w-[9px] indeterminate:before:rounded-[1px] "
    "indeterminate:before:bg-accent-fg"
)


class Checkbox(FormControl):
    """
    A checkbox, built on the browser's own.

    The native control is styled rather than hidden behind a lookalike, so
    every keyboard, form and assistive-tech behaviour stays the browser's.
    description() adds a second line under the label - a choice says its
    extra sentence there rather than under the whole row, which is where a
    field puts its hint. variant("card") puts the row on a pressable surface.

        Checkbox().name("terms").label("I accept the terms").required()
    """

    category: ClassVar[str | None] = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().name("accept").label("I accept the terms")

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def checked(self, value: bool = True) -> Self:
        self._props["checked"] = value
        return self

    def indeterminate(self, value: bool = True) -> Self:
        """
        The mixed state, for a checkbox standing for several others that do
        not agree. It survives only until the next click, which is how the
        native control behaves.
        """
        self._props["indeterminate"] = value
        return self

    def description(self, value: str) -> Self:
        """
        A second line under the label, for what the choice actually does.
        """
        self._props["description"] = value
        return self

    def card(self, value: bool = True) -> Self:
        """
        Give the row a box of its own, for a checkbox that carries a
        description rather than a word.
        """
        self._props["card"] = value
        return self

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        checked: bool = self._get_prop("checked", False)
        indeterminate: bool = self._get_prop("indeterminate", False)
        error: str | None = self._error(context)
        label: str | None = self._get_prop("label")
        description: str | None = self._get_prop("description")
        card: bool = self._get_prop("card", False)
        input_id = self._input_id()

        # No explicit role: a native checkbox input already carries it. Boolean
        # attributes are true by presence, so False must omit them.
        input_attrs = self._control_attrs(
            context,
            type="checkbox",
            name=name,
            id=input_id,
            value=self._get_prop("value"),
            class_=classnames(CHOICE_BOX, "rounded-xs", _TICK, _DASH),
            checked=checked or None,
            disabled=disabled or None,
            required=required or None,
            aria_invalid="true" if error is not None else None,
            # An explicit name, so the description inside the label does not
            # become part of it.
            aria_labelledby=label_id(input_id) if label is not None else None,
            aria_describedby=self._describedby(
                context, description_id(input_id) if description is not None else None
            ),
        )
        if indeterminate:
            # The indeterminate DOM property has no HTML attribute; set it on
            # init so the CSS :indeterminate styles apply.
            input_attrs["x-init"] = "$el.indeterminate = true"

        return choice_row(
            html.input_(**input_attrs),
            control_id=input_id,
            label=label,
            description=description,
            disabled=disabled,
            card=card,
            messages=(render_if(error, lambda text: error_component(text, input_id)),),
            class_=self._get_prop("class_"),
        )
