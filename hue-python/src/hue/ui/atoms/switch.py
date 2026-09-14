from __future__ import annotations

from typing import ClassVar, Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms._choice import choice_row
from hue.ui.atoms.spinner import Spinner
from hue.ui.form import FormControl
from hue.ui.molecules.field import error_component, hint_component
from hue.utils import classnames, render_if

type SwitchSize = Literal["sm", "md", "lg"]

# Track, knob, and how far the knob travels. The knob is drawn by the track
# itself, because a native input takes no children.
_SIZES: dict[SwitchSize, str] = {
    "sm": ("w-[30px] h-[17px] before:size-[13px] checked:before:translate-x-[13px]"),
    "md": ("w-[36px] h-[20px] before:size-[16px] checked:before:translate-x-[16px]"),
    "lg": ("w-[44px] h-[25px] before:size-[21px] checked:before:translate-x-[19px]"),
}

_TRACK = classnames(
    "relative mt-px flex-none cursor-pointer appearance-none rounded-full",
    "bg-border-strong transition-colors duration-200",
    "enabled:hover:bg-fg-subtle",
    "checked:bg-accent checked:enabled:hover:bg-accent-hover",
    "disabled:cursor-not-allowed disabled:opacity-45",
    # The knob. White in both themes, because it sits on the accent either
    # way, and a shadow so it reads as lifted off the track.
    "before:absolute before:top-[2px] before:left-[2px] before:content-['']",
    "before:rounded-full before:bg-white before:shadow-[0_1px_2px_rgb(18_18_23/0.28)]",
    "before:transition-transform before:duration-200 before:ease-out",
    FOCUS_RING,
)


class Switch(FormControl):
    """
    An on/off control that takes effect immediately.

    role="switch" rather than a checkbox, so it is announced as on or off
    rather than checked or unchecked. pending() covers the round trip when the
    change is saved as it is made.

        Switch("notify").label("Email notifications").checked()
    """

    category: ClassVar[str | None] = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().name("notify").label("Email notifications").checked()

    def checked(self, value: bool = True) -> Self:
        self._props["checked"] = value
        return self

    def size(self, value: SwitchSize) -> Self:
        self._props["size"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def pending(self, value: bool = True) -> Self:
        """
        The change is being saved. Disables the control and puts a labelled
        spinner beside it, so the delay is visible rather than the switch
        just refusing to move.
        """
        self._props["pending"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        name = self._require_name()
        size: SwitchSize = self._get_prop("size", "md")
        pending: bool = self._get_prop("pending", False)
        disabled: bool = self._get_prop("disabled", False) or pending
        error: str | None = self._get_prop("error")
        hint: str | None = self._get_prop("hint")
        input_id = self._input_id()

        # A native checkbox underneath, so it posts and toggles like one; the
        # role is what changes how it is announced.
        control = html.input_(
            **self._control_attrs(
                type="checkbox",
                role="switch",
                name=name,
                id=input_id,
                class_=classnames(_TRACK, _SIZES[size], self._get_prop("class_")),
                checked=self._get_prop("checked", False) or None,
                disabled=disabled or None,
                required=self._get_prop("required", False) or None,
                aria_invalid="true" if error is not None else None,
                aria_describedby=self._describedby(),
            )
        )

        return choice_row(
            control,
            control_id=input_id,
            label=self._get_prop("label"),
            description=self._get_prop("description"),
            disabled=disabled,
            variant="inline",
            messages=(
                render_if(
                    pending or None,
                    lambda _: Spinner().size("xs").muted().label("Saving"),
                ),
                render_if(hint, lambda text: hint_component(text, input_id)),
                render_if(error, lambda text: error_component(text, input_id)),
            ),
        )
