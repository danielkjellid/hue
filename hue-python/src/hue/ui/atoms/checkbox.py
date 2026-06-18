from __future__ import annotations

from typing import ClassVar, override

from htmy import PropertyValue, Tag, html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.text import Text
from hue.ui.base import ChainableComponent
from hue.utils import classes_if_else, classnames, render_if


# htmy's html module has no <path> element, so define one (it has <svg> but not
# the shape elements that go inside it).
class path(Tag):
    __slots__: tuple[str, ...] = ()


def _icon(path_d: str, class_: str) -> html.svg:
    """
    A 24x24 stroked icon used inside the checkbox box.
    """
    return html.svg(
        path(
            d=path_d,
            stroke="currentColor",
            stroke_width="3",
            stroke_linecap="round",
            stroke_linejoin="round",
            fill="none",
        ),
        viewBox="0 0 24 24",
        fill="none",
        class_=class_,
    )


# The check mark and the indeterminate dash, centred over the box and revealed
# by the input's state via the peer variants below.
_CHECK_PATH = "M5 13l4 4L19 7"
_DASH_PATH = "M6 12h12"

_ICON_CLASSES = "pointer-events-none absolute inset-0 m-auto size-3.5 text-white"


def _get_box_classes(*, disabled: bool, aria_invalid: bool) -> str:
    """Classes for the visual box that reflects the (peer) input's state."""
    return classnames(
        [
            "absolute inset-0 rounded-md border bg-background shadow-xs",
            "transition-colors duration-100",
            # 2px inset focus ring, shown only on keyboard focus.
            "outline-primary peer-focus-visible:outline",
            "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2",
        ],
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
        "border-destructive" if aria_invalid else None,
    )


class Checkbox(ChainableComponent):
    """
    An accessible checkbox built on a native input type=checkbox.

    The native input is visually hidden but keeps full keyboard, focus, and
    form-submission behaviour; a styled box sibling reflects its state through
    Tailwind's peer variants (checked, indeterminate, focus, hover). The
    mixed-state dash is driven via Alpine x-init because the indeterminate DOM
    property has no HTML attribute, and error_text marks the field invalid.

        Checkbox().name("terms").label("I accept the terms").required()
    """

    category: ClassVar[str] = "Inputs"

    def __init__(self) -> None:
        super().__init__()
        self._name: str | None = None

    @classmethod
    def example(cls) -> Self:
        """
        A representative instance, used by the docs site for previews.
        """
        return cls().name("accept").label("I accept the terms")

    def x_model(self, value: str) -> Self:
        """Two-way bind this checkbox to Alpine data."""
        self._attrs["x-model"] = value
        return self

    def name(self, value: str) -> Self:
        self._name = value
        return self

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def checked(self, value: bool = True) -> Self:
        self._props["checked"] = value
        return self

    def indeterminate(self, value: bool = True) -> Self:
        self._props["indeterminate"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def help_text(self, value: str) -> Self:
        self._props["help_text"] = value
        return self

    def error_text(self, value: str) -> Self:
        self._props["error_text"] = value
        return self

    # ------------------------------------------------------------------
    # Computed helpers
    # ------------------------------------------------------------------

    def _get_aria_invalid(self) -> bool:
        return self._get_prop("error_text") is not None

    def _get_aria_describedby(self) -> str | None:
        ids = [
            f"{self._name}-description" if self._get_prop("help_text") else None,
            f"{self._name}-error" if self._get_prop("error_text") else None,
        ]
        filtered = [v for v in ids if v is not None]
        return " ".join(filtered) if filtered else None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    @override
    def _render(self, context: HueContext[object]) -> Component:
        if self._name is None:
            raise ValueError(
                f"{type(self).__name__} requires a name — "
                + "pass it to the constructor or call .name()."
            )

        label_text: str | None = self._get_prop("label")
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        indeterminate: bool = self._get_prop("indeterminate", False)
        help_text_val = self._get_prop("help_text")
        error_text_val = self._get_prop("error_text")
        aria_invalid = self._get_aria_invalid()

        input_id: str = self._attrs.get("id", self._name)

        # No explicit role="checkbox": a native <input type="checkbox"> already
        # carries that implicit ARIA role, so adding it would be redundant.
        input_attrs: dict[str, PropertyValue] = {
            "type": "checkbox",
            "name": self._name,
            "id": input_id,
            "value": self._get_prop("value"),
            "class_": "peer sr-only",
            "checked": self._get_prop("checked"),
            "disabled": disabled or None,
            "required": required or None,
            "aria_invalid": aria_invalid or None,
            "aria_describedby": self._get_aria_describedby(),
        }
        if indeterminate:
            # The indeterminate DOM property has no HTML attribute; set it on
            # init so the CSS :indeterminate (peer) styles apply.
            input_attrs["x-init"] = "$el.indeterminate = true"
        input_attrs = {k: v for k, v in input_attrs.items() if v is not None}

        # Let base attrs (id, ARIA, Alpine) fill only what we haven't set above.
        for key, val in self._get_base_html_attrs().items():
            if key not in input_attrs:
                input_attrs[key] = val

        cursor = "cursor-not-allowed" if disabled else "cursor-pointer"

        # The clickable box: a <label> wrapping the (visually hidden) input, the
        # styled box, and the check/dash icons — all peer siblings of the input.
        box = html.label(
            html.input_(**input_attrs),
            html.span(
                class_=_get_box_classes(disabled=disabled, aria_invalid=aria_invalid)
            ),
            # The check shows only when checked AND not indeterminate, so the
            # indeterminate dash always wins when both states are set.
            _icon(
                _CHECK_PATH,
                f"{_ICON_CLASSES} hidden peer-[:checked:not(:indeterminate)]:block",
            ),
            _icon(_DASH_PATH, f"{_ICON_CLASSES} hidden peer-indeterminate:block"),
            for_=input_id,
            # mt-0.5 centres the 20px box with the 24px (leading-6) first line of
            # the label while the row stays top-aligned for multi-line text.
            class_=classnames("relative mt-0.5 inline-flex size-5 shrink-0", cursor),
        )

        # The text column sits beside the box so the label, help, and error text
        # all align with the label rather than the box.
        text_items = [
            render_if(
                label_text,
                lambda lt: html.label(
                    lt,
                    render_if(
                        required or None,
                        lambda _: html.span("*", class_="text-destructive"),
                    ),
                    for_=input_id,
                    class_=classnames(
                        "inline-flex items-center gap-1 select-none",
                        "text-sm leading-6 text-surface-900",
                        cursor,
                    ),
                ),
            ),
            render_if(
                help_text_val,
                lambda ht: Text(ht)
                .variant("body")
                .muted()
                .tag(html.span)
                .id(f"{self._name}-description"),
            ),
            render_if(
                error_text_val,
                lambda et: Text(et)
                .variant("body")
                .destructive()
                .role("alert")
                .id(f"{self._name}-error"),
            ),
        ]

        children: list[ComponentType] = [box]
        if label_text or help_text_val or error_text_val:
            children.append(html.div(*text_items, class_="flex flex-col gap-1"))

        return html.div(
            *children,
            class_=classnames(
                "flex items-start gap-2",
                "opacity-50" if disabled else None,
            ),
        )
