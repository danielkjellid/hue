from __future__ import annotations

import json
from decimal import Decimal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui.form import FieldControl
from hue.utils import classnames, render_when

# The readout. A fixed minimum width and tabular figures, so the row does not
# shift as the number under the thumb changes width.
_READOUT = (
    "inline-flex h-control-sm min-w-[52px] flex-none items-center justify-center "
    "rounded-sm border border-border bg-surface-sunken px-2 "
    "font-mono text-sm tabular-nums text-fg-muted"
)

_TICKS = "mt-0.5 flex justify-between text-2xs tabular-nums text-fg-subtle"


def _number(value: float) -> str:
    """
    The value as a person writes it: 1000000 rather than 1e+06, 12 rather than 12.0.
    """
    return format(Decimal(str(value)), "f").removesuffix(".0")


class Slider(FieldControl):
    """
    A range input, always paired with the number it is setting.

    A slider alone cannot say what it has landed on, and for anything billable
    the exact value is the point - so show_value() is on by default, in the
    label row where a textarea puts its counter.

        Slider().name("seats").label("Team seats").min(1).max(50).value(12)
    """

    category = "Inputs"

    def min(self, value: float) -> Self:
        self._props["min"] = value
        return self

    def max(self, value: float) -> Self:
        self._props["max"] = value
        return self

    def step(self, value: float) -> Self:
        self._props["step"] = value
        return self

    def value(self, value: float) -> Self:
        self._props["value"] = value
        return self

    def show_value(self, value: bool = True) -> Self:
        """
        The readout beside the track. On by default; turn it off only where
        the number is already somewhere else on the row.
        """
        self._props["show_value"] = value
        return self

    def prefix(self, value: str) -> Self:
        """
        What goes in front of the number in the readout, such as a currency.
        """
        self._props["prefix"] = value
        return self

    def suffix(self, value: str) -> Self:
        """
        What goes after the number in the readout, such as a unit.
        """
        self._props["suffix"] = value
        return self

    def ticks(self, *values: str) -> Self:
        """
        Labels under the track, spread from one end to the other.
        """
        self._props["ticks"] = values
        return self

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        low: float = self._get_prop("min", 0)
        high: float = self._get_prop("max", 100)
        current: float = self._get_prop("value", low)
        show_value: bool = self._get_prop("show_value", True)
        prefix: str = self._get_prop("prefix", "")
        suffix: str = self._get_prop("suffix", "")
        ticks: tuple[str, ...] = self._get_prop("ticks", ())
        disabled: bool = self._get_prop("disabled", False)
        error: str | None = self._error(context)
        control_id = self._input_id()

        # The fill is a gradient stop on the track, so it has to be recomputed
        # as the thumb moves; the readout reads the same number. Both are one
        # expression over the same state, which is why neither is bundled.
        span = high - low or 1
        fill = f"`--slider-fill: ${{((value - {low}) / {span}) * 100}}%`"

        # With a unit, the number alone is not what the readout says, so the
        # track announces the same text. The unit stays out of every other
        # expression; here it has to be in one, so it goes in as JSON strings.
        unit: dict[str, str] = {}
        if prefix or suffix:
            unit = {
                "aria-valuetext": f"{prefix}{_number(current)}{suffix}",
                ":aria-valuetext": (
                    f"{json.dumps(prefix)} + value + {json.dumps(suffix)}"
                ),
            }

        track = html.input_(
            **self._control_attrs(
                context,
                type="range",
                name=name,
                id=control_id,
                class_=classnames("slider", self._get_prop("class_")),
                min=low,
                max=high,
                step=self._get_prop("step"),
                value=current,
                disabled=disabled or None,
                aria_invalid="true" if error is not None else None,
                aria_describedby=self._describedby(context),
                **{"x-model.number": "value", ":style": fill, **unit},
            )
        )

        field = self._field(
            context,
            html.div(
                track,
                render_when(
                    bool(ticks),
                    html.div(*(html.span(tick) for tick in ticks), class_=_TICKS),
                ),
                class_="flex flex-col",
            ),
        )

        # The readout goes in the label row, where the guide puts it and where
        # a textarea puts its counter: beside the track it would take width
        # from the one thing on the row that needs it.
        if show_value:
            field.trailing(
                html.span(
                    # Only the number is bound, so the prefix and suffix are
                    # text and never part of an expression. It is rendered as
                    # well, so the box is right before Alpine runs.
                    prefix,
                    html.span(_number(current), x_text="value"),
                    suffix,
                    class_=_READOUT,
                )
            )

        # The state sits on the field, the only element holding both the track
        # and the readout.
        return field.x_data({"value": current})
