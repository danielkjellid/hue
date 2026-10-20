from __future__ import annotations

import json
import re
from datetime import date, datetime, time
from typing import Any, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.formats import DAY_DIRECTIVES, TIME_DIRECTIVES, Formats
from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import (
    CONTROL_SIZES,
    FOCUS_RING_INSET,
    GROUP_SHELL,
    GROUPED_CONTROL,
    ControlSize,
)
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.form import FieldControl
from hue.ui.molecules import _overlay
from hue.ui.molecules.combobox import _TOKEN, _TOKEN_REMOVE
from hue.ui.molecules.date_picker import (
    DatePicker,
    DatePickerMode,
    DayRules,
    Weekday,
    _days,
)
from hue.ui.molecules.field import (
    Field,
    error_component,
    error_id,
    hint_component,
    hint_id,
)
from hue.utils import classnames, render_if, render_when

type _Kind = Literal["single", "range", "multiple", "datetime", "time"]

# The anchor flips the popover but never shrinks it, so on a phone, where
# two stacked months are taller than the room on either side of a field,
# it scrolls inside a height that fits one side.
_POPOVER = classnames(
    "z-70 max-h-[calc(50dvh-3rem)] max-w-[calc(100vw-2rem)] overflow-auto",
    "sm:max-h-[calc(100dvh-2rem)]",
    "rounded-lg border border-border bg-surface-raised p-3 shadow-raised",
    "outline-none",
)
_PRESET = classnames(
    "h-8 cursor-pointer rounded-sm px-2 text-start text-sm text-fg",
    "hover:bg-surface-hover aria-pressed:bg-surface-active aria-pressed:font-bold",
    "disabled:cursor-not-allowed disabled:opacity-40",
    FOCUS_RING_INSET,
)
_SLOT = classnames(
    "flex h-8 flex-none cursor-pointer items-center justify-center rounded-sm",
    "text-sm tabular-nums text-fg hover:bg-surface-hover",
    "aria-selected:bg-accent aria-selected:text-accent-fg",
    "aria-selected:hover:bg-accent-hover",
    FOCUS_RING_INSET,
    # The accent ring would vanish into the selected fill.
    "aria-selected:focus-visible:inset-ring-accent-fg",
)

# The design's range presets. date-input.js holds the days behind each, in
# this order, since only the reader's browser knows the reader's today.
_PRESETS = (
    "Today",
    "Yesterday",
    "Last 7 days",
    "Last 30 days",
    "This month",
    "Last month",
    "Next 7 days",
)

# How the grid picks for each kind of field. A day and a time pick one day.
_MODES: dict[_Kind, DatePickerMode] = {
    "single": "single",
    "range": "range",
    "multiple": "multiple",
    "datetime": "single",
    "time": "single",
}

# Between the ends of a range, as date-input.js writes it.
_TO = " \N{EN DASH} "

# How a strftime directive reads in a placeholder. A weekday is dropped,
# since nobody has to type one.
_UNFILLED = {
    "%Y": "YYYY",
    "%m": "MM",
    "%-m": "M",
    "%d": "DD",
    "%-d": "D",
    "%e": "D",
    "%B": "Month",
    "%b": "Mon",
    "%H": "HH",
    "%I": "hh",
    "%-I": "h",
    "%M": "mm",
    "%p": "AM",
}


def _unfilled(format: str) -> str:
    """
    The format with nothing in it: %d.%m.%Y reads DD.MM.YYYY.
    """
    return re.sub(r"%-?.", lambda m: _UNFILLED.get(m.group(), ""), format).strip(" ,")


# What each kind of field reads back from its format.
_READS = {
    "time": TIME_DIRECTIVES.keys(),
    "datetime": DAY_DIRECTIVES.keys() | TIME_DIRECTIVES.keys(),
}


def _pattern(formats: Formats, kind: _Kind) -> str:
    return {"time": formats.time, "datetime": formats.datetime}.get(kind, formats.date)


class _PickerInput(FieldControl):
    """
    What the date and time fields share: a text field, the button that
    opens the popover beside it, and the value submitted as ISO text in
    hidden fields under the name. The text itself is not submitted.
    """

    _icon = "calendar"
    _opens = "Choose date"

    def placeholder(self, value: str) -> Self:
        """
        What the empty field shows. The format it reads best, by default.
        """
        self._props["placeholder"] = value
        return self

    def size(self, value: ControlSize) -> Self:
        self._props["size"] = value
        return self

    def readonly(self, value: bool = True) -> Self:
        """
        Show the value but refuse edits. It is still submitted, and there is
        no popover.
        """
        self._props["readonly"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def horizontal(self, value: bool = True) -> Self:
        """
        Put the label beside the control rather than above it.
        """
        self._props["horizontal"] = value
        return self

    def _kind(self) -> _Kind:
        raise NotImplementedError

    def _committed(self, formats: Formats) -> list[str]:
        """
        The value as the ISO text submitted.
        """
        raise NotImplementedError

    def _body(
        self, formats: Formats, picker: DatePicker, kind: _Kind, label: str
    ) -> ComponentType:
        """
        What the popover holds.
        """
        raise NotImplementedError

    def _picker(self, kind: _Kind) -> DatePicker:
        """
        The grid the popover holds, from this field's own refusals. A
        TimeInput has none to draw, but date-input.js builds on its data.
        """
        picker = DatePicker().mode(_MODES[kind])
        keys = ("min", "max", "unavailable", "week_start", "disabled", "required")
        picker._props.update({k: self._props[k] for k in keys if k in self._props})
        return picker

    def _field(self, context: Context, control: ComponentType) -> Field:
        # The error is drawn inside the control, where date-input.js can
        # change it, and the hint with it unless it sits beside the label.
        horizontal: bool = self._get_prop("horizontal", False)
        hint: str | None = self._get_prop("hint")
        return (
            super()
            ._field(context, control)
            .hint(hint if horizontal else None)
            .error(None)
        )

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        formats = Formats.from_context(context)
        kind = self._kind()
        pattern = _pattern(formats, kind)
        readable = _READS.get(kind, DAY_DIRECTIVES.keys())
        for directive in re.findall(r"%(-?.)", pattern):
            if directive != "%" and directive not in readable:
                raise ValueError(
                    f"A {type(self).__name__} cannot read %{directive} back, "
                    f"which its format {pattern!r} writes. It reads "
                    f"{' '.join(sorted(f'%{d}' for d in readable))} and %%."
                )
        size: ControlSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        readonly: bool = self._get_prop("readonly", False)
        required: bool = self._get_prop("required", False)
        horizontal: bool = self._get_prop("horizontal", False)
        hint: str | None = self._get_prop("hint")
        label: str = self._get_prop("label") or name
        error = self._error(context)
        inert = disabled or readonly
        control_id = self._input_id()
        popover_id = f"{control_id}-picker"
        committed = self._committed(formats)
        picker = self._picker(kind)
        start: Weekday = self._get_prop("week_start", "monday")

        placeholder: str | None = self._get_prop("placeholder")
        if placeholder is None:
            placeholder = _placeholder(pattern, kind)
        written = _written(kind, committed, formats)
        caller = self._attrs.get("aria_describedby")
        hinted = classnames(hint_id(control_id) if hint else None, caller) or None
        errored = classnames(
            hint_id(control_id) if hint and horizontal else None,
            error_id(control_id),
            caller,
        )
        attrs = self._control_attrs(
            context,
            type="text",
            id=control_id,
            class_=classnames(GROUPED_CONTROL, CONTROL_SIZES[size], "tabular-nums"),
            placeholder=placeholder,
            value=written,
            # As wide as what it holds, so a range is not cut off where the
            # field sits in something that sizes to its content.
            size=max(len(placeholder), len(written or "")) + 1,
            autocomplete="off",
            spellcheck="false",
            disabled=disabled or None,
            readonly=readonly or None,
            # The text of a multiple field is empty once a day is added, so
            # the browser would refuse a form that has days.
            required=(required and kind != "multiple") or None,
            aria_required="true" if required and kind == "multiple" else None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=errored if error is not None else hinted,
            **{
                "x-ref": "input",
                "x-model": "text",
                ":aria-invalid": "error ? 'true' : null",
                ":aria-describedby": (
                    f"error ? {json.dumps(errored)} : {json.dumps(hinted)}"
                ),
                "x-on:blur": "commitText()",
                "x-on:keydown": "inputKey($event)",
            },
        )
        # A div is no form's, so the form goes on the submitted fields.
        form = attrs.pop("form", None)

        button = (
            Button()
            .variant("ghost")
            .size("xs" if size == "sm" else "sm")
            .icon_only(self._opens)
            .content(HueIcon(self._icon))
        )
        if inert:
            button.disabled()
        else:
            _overlay.wire_trigger(button, popup="dialog", on={"click": "toggle()"})
            button.aria_controls(popover_id)

        config: dict[str, Any] = {
            **picker._config(formats, _MODES[kind], _months(kind), start),
            "kind": kind,
            "committed": committed,
            "inert": inert,
            "error": error,
            "formats": {
                "date": formats.date,
                "datetime": formats.datetime,
                "time": formats.time,
            },
            "dayAbbreviations": list(formats.day_abbreviations),
            "monthAbbreviations": list(formats.month_abbreviations),
            "step": self._get_prop("step", 15),
        }
        root_attrs: dict[str, object] = {
            "x-data": call("hueDateInput", config),
            # The grid's own handlers, which hueDatePicker expects on the
            # root it is spread into.
            "x-on:keydown": "key($event)",
            "x-on:click": "click($event)",
            "x-on:mouseover": "preview($event)",
            "x-on:mouseleave": "hover = null",
            "x-on:click.outside": "if (open) dismiss()",
            # Tab walks on to the next field, and the popover goes with it.
            "x-on:focusout": "leave($event)",
        }
        caller_model = self._attrs.get("x-model")
        if caller_model:
            root_attrs["x-modelable"] = "committed"
            root_attrs["x-model"] = caller_model

        submitted = html.template(
            html.input_(
                type="hidden",
                name=name,
                form=form,
                # A disabled field is left out of what the form submits.
                disabled=disabled or None,
                **{":value": "each"},
            ),
            # By position: a range of one day holds the same day twice.
            **{"x-for": "(each, i) in committed", ":key": "i"},
        )
        shell = html.div(
            html.input_(**attrs),
            html.span(button, class_="flex items-center pe-1"),
            class_=classnames(GROUP_SHELL, self._get_prop("class_")),
            **{"x-ref": "shell"},
        )
        popover = html.div(
            self._body(formats, picker, kind, label),
            id=popover_id,
            role="dialog",
            aria_label=label,
            class_=_POPOVER,
            **{
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                # Fixed, because a Dialog clips what overflows its panel and
                # a date field in a dialog is the common case.
                "x-anchor.fixed.bottom-start.offset.6": "$refs.shell",
                **_overlay.HOLDS_FOCUS,
            },
        )
        chips = html.ul(
            html.template(
                html.li(
                    html.span(**{"x-text": "dayText(day)"}),
                    html.button(
                        HueIcon("x").class_("size-3"),
                        type="button",
                        disabled=inert or None,
                        class_=_TOKEN_REMOVE,
                        **{
                            ":aria-label": "removeLabel(day)",
                            "x-on:click": "removeDay(day)",
                        },
                    ),
                    class_=_TOKEN,
                ),
                **{"x-for": "day in committed", ":key": "day"},
            ),
            aria_label=label,
            class_="flex flex-wrap gap-1",
            **{"x-show": "committed.length"},
        )
        return self._field(
            context,
            html.div(
                submitted,
                shell,
                render_when(not inert, popover),
                render_when(kind == "multiple", chips),
                render_if(
                    None if horizontal else hint,
                    lambda text: html.div(
                        hint_component(text, control_id),
                        class_="contents",
                        **{"x-show": "!error"},
                    ),
                ),
                # One element for the server's error and a typed one, so
                # both look and read the same.
                html.div(
                    error_component(
                        html.span(error or "", **{"x-text": "error"}), control_id
                    ),
                    class_="contents",
                    **{"x-show": "error", "x-cloak": error is None or None},
                ),
                tabindex="-1",
                class_="flex flex-col gap-1.5 outline-none",
                **root_attrs,
            ),
        )


def _placeholder(pattern: str, kind: _Kind) -> str:
    unfilled = _unfilled(pattern)
    return f"{unfilled}{_TO}{unfilled}" if kind == "range" else unfilled


def _written(kind: _Kind, committed: list[str], formats: Formats) -> str | None:
    """
    The text the field starts with, as date-input.js writes it once it runs.
    """
    if not committed or kind == "multiple":
        return None
    if kind == "time":
        return formats.write(formats.time, time.fromisoformat(committed[0]))
    if kind == "datetime":
        return formats.write(formats.datetime, datetime.fromisoformat(committed[0]))
    return _TO.join(
        formats.write(formats.date, date.fromisoformat(day)) for day in committed
    )


def _months(kind: _Kind) -> int:
    return 2 if kind == "range" else 1


def _foot(*items: ComponentType) -> ComponentType:
    return html.div(
        *items, class_="flex items-center gap-2 border-t border-border pt-3"
    )


def _action(
    text: str, action: str, variant: Literal["ghost", "primary"] = "ghost"
) -> Button:
    return (
        Button().variant(variant).size("xs").content(text).x_on("click", unsafe(action))
    )


def _spacer() -> ComponentType:
    return html.span(class_="flex-1")


def _times(formats: Formats, step: int, label: str) -> ComponentType:
    """
    A listbox of the day's times, step minutes apart, labelled as the
    server writes them.
    """
    slots = (time(m // 60, m % 60) for m in range(0, 24 * 60, step))
    return html.div(
        *(
            html.div(
                formats.write(formats.time, slot),
                role="option",
                class_=_SLOT,
                **{
                    "data-time": slot.strftime("%H:%M"),
                    "x-bind": call("slotItem", slot.strftime("%H:%M")),
                },
            )
            for slot in slots
        ),
        role="listbox",
        aria_label=label,
        class_=classnames(
            "relative flex max-h-72 w-24 flex-none flex-col gap-0.5",
            "overflow-y-auto p-0.5",
        ),
        **{"x-ref": "times"},
    )


def _step(minutes: int) -> int:
    if not 1 <= minutes <= 12 * 60:
        raise ValueError("A time list steps between 1 and 720 minutes.")
    return minutes


class _CalendarInput(DayRules, _PickerInput):
    """
    A field whose popover holds a month grid, refusing the same days a
    DatePicker does.
    """

    def _grid(self, formats: Formats, picker: DatePicker) -> ComponentType:
        mode: DatePickerMode = picker._get_prop("mode")
        start: Weekday = self._get_prop("week_start", "monday")
        return html.div(*picker._panels(formats, mode, _months(mode), "md", start))


class DateInput(_CalendarInput):
    """
    A text field for a day, a range or several days, with a button that
    opens a month to pick them from.

    mode() picks which, as on DatePicker; a range shows two months and
    Apply and Cancel, and can offer presets. Typed text is read on Enter
    and when the field loses focus, from ISO, 20.10.2026, 20 Oct 2026 or
    today. The days are submitted as YYYY-MM-DD under name, one hidden
    field each, and x_model binds the same list.
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().name("starts").label("Start date")

    def value(self, *days: date) -> Self:
        """
        The days it starts with: one, the two ends of a range, or several.
        A datetime is refused, since the field holds days.
        """
        self._props["value"] = _days(*days)
        return self

    def mode(self, value: DatePickerMode, *, presets: bool = False) -> Self:
        """
        One day, a range or several days. A range can offer presets, such
        as Last 7 days, around today.
        """
        if presets and value != "range":
            raise ValueError("Only a range DateInput has presets.")
        self._props["mode"] = value
        self._props["presets"] = presets
        return self

    def _kind(self) -> _Kind:
        mode: DatePickerMode = self._get_prop("mode", "single")
        return mode

    def _committed(self, formats: Formats) -> list[str]:
        days: tuple[date, ...] = self._get_prop("value", ())
        kind = self._kind()
        if kind == "single" and len(days) > 1:
            raise ValueError(f"A single DateInput cannot hold {len(days)} days.")
        if kind == "range" and len(days) not in (0, 2):
            raise ValueError("A range DateInput holds both of its ends, or none.")
        if kind == "multiple":
            days = tuple(set(days))
        return sorted(day.isoformat() for day in days)

    def _body(
        self, formats: Formats, picker: DatePicker, kind: _Kind, label: str
    ) -> ComponentType:
        grid = self._grid(formats, picker)
        if kind == "single":
            return grid
        if kind == "multiple":
            return html.div(
                grid,
                _foot(_spacer(), _action("Done", "close()")),
                class_="flex flex-col gap-3",
            )
        main = html.div(
            grid,
            _foot(
                html.span(
                    aria_live="polite",
                    class_="text-sm text-fg-muted tabular-nums",
                    **{"x-text": "summary()"},
                ),
                _spacer(),
                _action("Cancel", "close()"),
                _action("Apply", "apply()", "primary").x_bind(
                    "disabled", unsafe("value.length < 2")
                ),
            ),
            class_="flex flex-col gap-3",
        )
        presets = html.div(
            *(
                html.button(
                    text,
                    type="button",
                    class_=_PRESET,
                    **{"x-bind": f"preset({i})"},
                )
                for i, text in enumerate(_PRESETS)
            ),
            role="group",
            aria_label="Presets",
            class_=classnames(
                "flex flex-row flex-wrap gap-0.5 border-b border-border pb-3",
                "sm:w-36 sm:flex-none sm:flex-col sm:flex-nowrap sm:border-e",
                "sm:border-b-0 sm:pe-3 sm:pb-0",
            ),
        )
        if not self._get_prop("presets", False):
            return main
        return html.div(presets, main, class_="flex flex-col gap-3 sm:flex-row")


class DateTimeInput(_CalendarInput):
    """
    A text field for a day and a time, with a button that opens a month
    beside a list of times.

    step() sets the minutes between times, 15 by default, and Now picks
    the next of them. Typed text is a day, then a time if it has one, as
    in 2026-10-20 14:30. The value is submitted as YYYY-MM-DDTHH:MM, in
    the reader's time when Formats localizes.
    """

    category = "Inputs"
    _opens = "Choose date and time"

    @classmethod
    def example(cls) -> Self:
        return cls().name("publish_at").label("Publish at")

    def value(self, value: datetime) -> Self:
        self._props["value"] = value
        return self

    def step(self, minutes: int) -> Self:
        self._props["step"] = _step(minutes)
        return self

    def _kind(self) -> _Kind:
        return "datetime"

    def _committed(self, formats: Formats) -> list[str]:
        moment: datetime | None = self._get_prop("value")
        if moment is None:
            return []
        local = formats.moment(moment).replace(tzinfo=None)
        return [local.isoformat(timespec="minutes")]

    def _body(
        self, formats: Formats, picker: DatePicker, kind: _Kind, label: str
    ) -> ComponentType:
        return html.div(
            html.div(
                self._grid(formats, picker),
                _times(formats, self._get_prop("step", 15), "Time"),
                class_="flex gap-3",
            ),
            _foot(_action("Now", "now()"), _spacer(), _action("Done", "close()")),
            class_="flex flex-col gap-3",
        )


class TimeInput(_PickerInput):
    """
    A text field for a time of day, with a button that opens a list of
    times step() minutes apart, 15 by default.

    Typed text reads 14:30, 1430, 2:30 pm or 9a, and is written back the
    way Formats.time writes it, which also decides between a 12 and a 24
    hour list. The value is submitted as HH:MM.
    """

    category = "Inputs"
    _icon = "clock"
    _opens = "Choose time"

    @classmethod
    def example(cls) -> Self:
        return cls().name("reminder").label("Reminder")

    def value(self, value: time) -> Self:
        self._props["value"] = value
        return self

    def step(self, minutes: int) -> Self:
        self._props["step"] = _step(minutes)
        return self

    def _kind(self) -> _Kind:
        return "time"

    def _committed(self, formats: Formats) -> list[str]:
        moment: time | None = self._get_prop("value")
        if moment is None:
            return []
        return [moment.replace(tzinfo=None).isoformat(timespec="minutes")]

    def _body(
        self, formats: Formats, picker: DatePicker, kind: _Kind, label: str
    ) -> ComponentType:
        return _times(formats, self._get_prop("step", 15), label)
