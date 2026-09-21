from __future__ import annotations

from typing import ClassVar, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms._choice import (
    ChoiceLayout,
    choice_row,
    description_id,
    label_id,
)
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.spinner import Spinner
from hue.ui.form import FormControl
from hue.ui.molecules.field import error_component
from hue.utils import classnames, render_if

type SwitchSize = Literal["sm", "md", "lg"]

#: Where an immediate write has got to. A switch takes effect as it is
#: flipped, so unlike every other control in the form group it has a round
#: trip to report on.
type SubmissionState = Literal["none", "pending", "success", "error"]

# How long a finished state stays up before the row goes quiet again. Long
# enough to read, short enough to be gone before the next change. Not an enum
# or a flag, so the docs do not offer it as a knob that does nothing until a
# finished state is showing.
_SETTLE_MS = 2400

# Icon and tone for the two states that finish. Announced through a label on
# the wrapper, because a tick that only means something if you can see it is
# not a report at all.
_FINISHED: dict[str, tuple[str, str, str]] = {
    "success": ("circle-check", "text-success", "Saved"),
    "error": ("circle-alert", "text-danger", "Not saved"),
}

# Track, knob, and how far the knob travels. The knob is drawn by the track
# itself, because a native input takes no children.
_SIZES: dict[SwitchSize, str] = {
    "sm": ("w-[30px] h-[17px] before:size-[13px] checked:before:translate-x-[13px]"),
    "md": ("w-[36px] h-[20px] before:size-[16px] checked:before:translate-x-[16px]"),
    "lg": ("w-[44px] h-[25px] before:size-[21px] checked:before:translate-x-[19px]"),
}

# What it takes to sit the track on the middle of the label's first line,
# which is 19px tall. One offset per size, because a track that is 17, 20 or
# 25px tall does not meet that line in the same place - a single nudge tuned
# for the smallest left the other two visibly high.
_ALIGNMENT: dict[SwitchSize, str] = {
    "sm": "mt-px",
    "md": "mt-0",
    "lg": "-mt-[3px]",
}

_TRACK = classnames(
    "relative flex-none cursor-pointer appearance-none rounded-full",
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
    rather than checked or unchecked. submission_state() reports the round
    trip, since the change is saved as it is made. A finished state clears
    itself; settle_after(None) holds it. description() adds a second line
    under the label.

        Switch().name("notify").label("Email notifications").checked()
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

    def layout(self, value: ChoiceLayout) -> Self:
        """
        Put the text first and the switch at the far end of the row.

        The arrangement a settings list wants: what can I change, then the
        thing that changes it.
        """
        self._props["layout"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def submission_state(self, value: SubmissionState) -> Self:
        """
        How the write that this switch started is going.

        "pending" also disables the switch, so the delay is visible rather
        than the control simply refusing to move. "success" and "error" clear
        themselves after a couple of seconds, so a row cannot be left wearing
        the outcome of a change made long ago.
        """
        self._props["submission_state"] = value
        return self

    def settle_after(self, value: int | None) -> Self:
        """
        How long a finished state stays up, in milliseconds. None holds it.

        Hold it for an outcome that has to be read rather than glimpsed - a
        failure the user has to act on - or anywhere the row is not live, such
        as a page showing what the states look like.
        """
        self._props["settle_after"] = value
        return self

    def _indicator(self, state: SubmissionState) -> ComponentType:
        """
        The icon beside the label. No text: the row already says what it is,
        and the name is on the icon for anything that cannot see it.
        """
        if state == "pending":
            return Spinner().size("xs").muted().aria_label("Saving")

        icon, tone, label = _FINISHED[state]
        # It clears itself rather than waiting for another render: the request
        # that set it was the last one anybody was going to make on this row.
        # The countdown only starts if the row is on screen, because an
        # outcome that expired while it was hidden was never reported at all.
        settle_after: int | None = self._get_prop("settle_after", _SETTLE_MS)
        settling = (
            {}
            if settle_after is None
            else {
                "x-data": "{ settled: false }",
                "x-init": (
                    "if ($el.checkVisibility?.() ?? $el.offsetParent !== null) "
                    f"setTimeout(() => settled = true, {settle_after})"
                ),
                "x-show": "!settled",
            }
        )
        return html.span(
            HueIcon(icon).class_(f"size-4 {tone}"),
            role="status",
            aria_label=label,
            class_="inline-flex",
            **settling,
        )

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        size: SwitchSize = self._get_prop("size", "md")
        layout: ChoiceLayout = self._get_prop("layout", "inline")
        state: SubmissionState = self._get_prop("submission_state", "none")
        disabled: bool = self._get_prop("disabled", False) or state == "pending"
        error: str | None = self._error(context)
        label: str | None = self._get_prop("label")
        description: str | None = self._get_prop("description")
        input_id = self._input_id()

        # A native checkbox underneath, so it posts and toggles like one; the
        # role is what changes how it is announced.
        control = html.input_(
            **self._control_attrs(
                context,
                type="checkbox",
                role="switch",
                name=name,
                id=input_id,
                class_=classnames(
                    _TRACK,
                    _SIZES[size],
                    # Centred against the whole block in the horizontal row,
                    # where there is no first line to line up with.
                    _ALIGNMENT[size] if layout == "inline" else None,
                    self._get_prop("class_"),
                ),
                checked=self._get_prop("checked", False) or None,
                disabled=disabled or None,
                required=self._get_prop("required", False) or None,
                aria_invalid="true" if error is not None else None,
                # An explicit name, so the description inside the label does
                # not become part of it.
                aria_labelledby=label_id(input_id) if label is not None else None,
                aria_describedby=self._describedby(
                    context,
                    description_id(input_id) if description is not None else None,
                ),
            )
        )

        return choice_row(
            control,
            control_id=input_id,
            label=label,
            description=description,
            disabled=disabled,
            variant="inline",
            layout=layout,
            status=UNDEFINED if state == "none" else self._indicator(state),
            messages=(render_if(error, lambda text: error_component(text, input_id)),),
        )
