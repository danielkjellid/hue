from __future__ import annotations

from typing import ClassVar, override

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.form import FormControl
from hue.utils import classes_if_else, classnames, render_if

# The check mark and the indeterminate dash sit centred over the box and are
# revealed by the input's state through the peer variants.
_ICON_CLASSES = "pointer-events-none absolute inset-0 m-auto size-3.5 text-white"


def _get_box_classes(*, disabled: bool, invalid: bool) -> str:
    """
    Classes for the visual box that reflects the (peer) input's state.
    """
    return classnames(
        "absolute inset-0 rounded-md border bg-background shadow-xs",
        "transition-colors duration-100",
        # 2px inset focus ring, shown only on keyboard focus.
        "outline-primary peer-focus-visible:outline",
        "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2",
        classes_if_else(
            disabled,
            [
                "border-surface-200 bg-surface-100",
                "peer-checked:border-surface-300 peer-checked:bg-surface-300",
                "peer-indeterminate:border-surface-300",
                "peer-indeterminate:bg-surface-300",
            ],
            [
                "border-surface-300 peer-hover:border-surface-400",
                "peer-checked:border-primary peer-checked:bg-primary",
                "peer-indeterminate:border-primary peer-indeterminate:bg-primary",
            ],
        ),
        {"border-destructive": invalid},
    )


class Checkbox(FormControl):
    """
    An accessible checkbox built on a native input type=checkbox.

    The native input is visually hidden but keeps full keyboard, focus, and
    form-submission behaviour; a styled box sibling reflects its state through
    Tailwind's peer variants (checked, indeterminate, focus, hover). The
    mixed-state dash is driven via Alpine x-init because the indeterminate DOM
    property has no HTML attribute, and error_text marks the field invalid.

        Checkbox("terms").label("I accept the terms").required()
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
        self._props["indeterminate"] = value
        return self

    @override
    def _render(self, context: HueContext[object]) -> Component:
        name = self._require_name()
        label_text: str | None = self._get_prop("label")
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        checked: bool = self._get_prop("checked", False)
        indeterminate: bool = self._get_prop("indeterminate", False)
        invalid = self._get_prop("error_text") is not None
        input_id = self._input_id()

        # No explicit role: a native checkbox input already carries it. Boolean
        # attributes are true by presence, so False must omit them.
        input_attrs = self._control_attrs(
            type="checkbox",
            name=name,
            id=input_id,
            value=self._get_prop("value"),
            class_="peer sr-only",
            checked=checked or None,
            disabled=disabled or None,
            required=required or None,
            aria_invalid=invalid or None,
            aria_errormessage=self._error_id(),
            aria_describedby=self._describedby(),
        )
        if indeterminate:
            # The indeterminate DOM property has no HTML attribute; set it on
            # init so the CSS :indeterminate (peer) styles apply.
            input_attrs["x-init"] = "$el.indeterminate = true"

        cursor = "cursor-not-allowed" if disabled else "cursor-pointer"

        # The clickable box: a label wrapping the visually hidden input, the
        # styled box, and the check/dash icons, all peer siblings of the input.
        # The check shows only when checked and not indeterminate, so the dash
        # always wins when both states are set.
        box = html.label(
            html.input_(**input_attrs),
            html.span(class_=_get_box_classes(disabled=disabled, invalid=invalid)),
            HueIcon("check").class_(
                f"{_ICON_CLASSES} hidden peer-[:checked:not(:indeterminate)]:block"
            ),
            HueIcon("minus").class_(f"{_ICON_CLASSES} hidden peer-indeterminate:block"),
            for_=input_id,
            # mt-0.5 centres the 20px box with the 24px (leading-6) first line of
            # the label while the row stays top-aligned for multi-line text.
            class_=classnames("relative mt-0.5 inline-flex size-5 shrink-0", cursor),
        )

        # The text column sits beside the box so the label, help, and error text
        # all align with the label rather than the box.
        text_items: list[ComponentType] = [
            render_if(
                label_text,
                lambda text: html.label(
                    text,
                    html.span("*", class_="text-destructive")
                    if required
                    else UNDEFINED,
                    for_=input_id,
                    class_=classnames(
                        "inline-flex items-center gap-1 select-none",
                        "text-sm leading-6 text-surface-900",
                        cursor,
                    ),
                ),
            ),
            self._help_text_component(),
            self._error_text_component(),
        ]

        has_text = bool(
            label_text or self._get_prop("help_text") or self._get_prop("error_text")
        )

        return html.div(
            box,
            html.div(*text_items, class_="flex flex-col gap-1")
            if has_text
            else UNDEFINED,
            class_=classnames(
                "flex items-start gap-2",
                {"opacity-50": disabled},
                self._get_prop("class_"),
            ),
        )
