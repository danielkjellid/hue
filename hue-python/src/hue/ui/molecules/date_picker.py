from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.form import FormControl
from hue.ui.molecules.field import error_component
from hue.utils import classnames, render_if

type DatePickerMode = Literal["single", "range", "multiple"]
type DatePickerSize = Literal["sm", "md"]
type Weekday = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]  # fmt: skip

# Monday first, as date.weekday() and Formats.day_names count.
WEEKDAYS: tuple[Weekday, ...] = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)  # fmt: skip

# Six weeks, always, so the grid keeps its height from month to month.
_CELLS = 42

# The cell carries the state, as attributes date-picker.js binds; the disc
# inside draws it. The cell's ::before is the band a range runs along, behind
# the disc, which is why the cell isolates: without a stacking context of its
# own the band would sink under the background of whatever holds the picker.
_CELL = classnames(
    "relative isolate p-0 px-px text-center outline-none focus-visible:z-10",
    "before:absolute before:inset-y-0 before:-z-10 before:bg-accent-subtle",
    "data-[band=inside]:before:inset-x-0",
    "data-[band=start]:before:start-1/2 data-[band=start]:before:end-0",
    "data-[band=end]:before:start-0 data-[band=end]:before:end-1/2",
    "data-preview:before:bg-accent-subtle/50",
)
# Each state's selector excludes the ones that outrank it, since Tailwind
# orders these variants by their own rules rather than by the class list.
_DISC = classnames(
    "relative grid place-items-center rounded-md font-medium tabular-nums text-fg",
    # FOCUS_RING, drawn by the disc for the focused cell so it takes its shape.
    "in-[td:focus-visible]:ring-2 in-[td:focus-visible]:ring-accent",
    "in-[td:focus-visible]:ring-offset-2 in-[td:focus-visible]:ring-offset-canvas",
    "in-[[data-date]:not([aria-disabled])]:cursor-pointer",
    "in-[[data-date]:not([aria-disabled],[data-filled])]:hover:bg-surface-hover",
    "in-aria-[current=date]:font-bold",
    "in-[[aria-current=date]:not([data-filled])]:inset-ring",
    "in-[[aria-current=date]:not([data-filled])]:inset-ring-fg",
    "in-data-filled:bg-accent in-data-filled:text-accent-fg",
    "in-data-filled:hover:bg-accent-hover",
    "in-aria-disabled:cursor-not-allowed in-aria-disabled:line-through",
    "in-aria-disabled:opacity-40",
    # The marker dot, in the disc's own colour so it shows on a filled day.
    "in-data-marked:after:absolute in-data-marked:after:bottom-1",
    "in-data-marked:after:start-1/2 in-data-marked:after:size-1",
    "in-data-marked:after:-translate-x-1/2 in-data-marked:after:rounded-full",
    "in-data-marked:after:bg-current",
)
_ITEM = classnames(
    "h-11 cursor-pointer rounded-md text-sm font-medium text-fg",
    "hover:bg-surface-hover data-current:font-bold",
    "data-current:not-aria-pressed:inset-ring",
    "data-current:not-aria-pressed:inset-ring-fg",
    "aria-pressed:bg-accent aria-pressed:text-accent-fg",
    "aria-pressed:hover:bg-accent-hover",
    FOCUS_RING,
)
_TITLE = classnames(
    "inline-flex h-control-xs items-center gap-1 rounded-sm px-2 font-ui",
    "text-base font-bold text-fg",
)

# Keyed by the Literal so mypy keeps it exhaustive: the disc, the weekday
# header, and the width of the jump panels, which is seven discs.
_SIZES: dict[DatePickerSize, tuple[str, str, str]] = {
    "sm": ("h-7.5 w-7 text-xs", "h-6 text-2xs", "w-52.5"),
    "md": ("h-9 w-8.5 text-sm", "h-7 text-xs", "w-63"),
}


class DatePicker(FormControl):
    """
    A month to pick a day, a range or several days from, inline on the page.

    mode() picks how a click selects, months() shows several side by side,
    and min(), max() and unavailable() say which days refuse. markers() puts
    a dot under days that have something on them. The caption's title jumps
    by month and year. The days are submitted under name, one hidden field
    each, and x_model binds the same list of ISO dates.
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().name("due").label("Due date")

    def value(self, *days: date) -> Self:
        """
        The days selected to start with.
        """
        self._props["value"] = _days(*days)
        return self

    def mode(self, value: DatePickerMode) -> Self:
        self._props["mode"] = value
        return self

    def months(self, count: int) -> Self:
        """
        How many months show side by side. Only the first has Previous and
        only the last has Next.
        """
        if count < 1:
            raise ValueError("A DatePicker shows at least one month.")
        self._props["months"] = count
        return self

    def min(self, value: date) -> Self:
        """
        The first day that can be picked.
        """
        (self._props["min"],) = _days(value)
        return self

    def max(self, value: date) -> Self:
        """
        The last day that can be picked.
        """
        (self._props["max"],) = _days(value)
        return self

    def unavailable(self, *days: date | Weekday) -> Self:
        """
        Days that refuse a pick: dates, or weekdays by name for every one of
        them, as in unavailable("saturday", "sunday").
        """
        _days(*(day for day in days if not isinstance(day, str)))
        self._props["unavailable"] = days
        return self

    def markers(self, *days: date, label: str = "has events") -> Self:
        """
        Days with something on them, drawn with a dot. The label is added to
        each one's accessible name, since a dot says nothing to a screen
        reader.
        """
        self._props["markers"] = _days(*days)
        self._props["marker_label"] = label
        return self

    def week_start(self, value: Weekday) -> Self:
        self._props["week_start"] = value
        return self

    def size(self, value: DatePickerSize) -> Self:
        self._props["size"] = value
        return self

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        label: str | None = self._get_prop("label")
        mode: DatePickerMode = self._get_prop("mode", "single")
        months: int = self._get_prop("months", 1)
        size: DatePickerSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        start: Weekday = self._get_prop("week_start", "monday")
        error: str | None = self._error(context)
        formats = Formats.from_context(context)

        if label is None:
            raise ValueError(
                "DatePicker needs a label(): a group of month grids that "
                "announces nothing gives a screen reader no way to say what "
                "the days are for."
            )

        config = self._config(formats, mode, months, start)
        attrs = self._control_attrs(
            context,
            role="group",
            aria_label=label,
            aria_describedby=self._describedby(context),
            aria_invalid="true" if error is not None else None,
            # So focus can wait here while the panels swap.
            tabindex="-1",
            class_=classnames(
                "inline-flex flex-col gap-2 outline-none select-none",
                {"pointer-events-none opacity-50": disabled},
                self._get_prop("class_"),
            ),
            **{
                "x-data": call("hueDatePicker", config),
                "x-on:keydown": "key($event)",
                "x-on:click": "click($event)",
                "x-on:mouseover": "preview($event)",
                "x-on:mouseleave": "hover = null",
            },
        )
        # A div is no form's, so the form goes on the submitted fields. The
        # caller's x-model binds the list of days.
        form = attrs.pop("form", None)
        if "x-model" in attrs:
            attrs["x-modelable"] = "value"

        submitted = html.template(
            html.input_(
                type="hidden",
                name=name,
                form=form,
                # A disabled field is left out of what the form submits.
                disabled=disabled or None,
                **{":value": "day"},
            ),
            # Keyed by position: a range picked on one day holds it twice.
            **{"x-for": "(day, i) in value", ":key": "i"},
        )
        return html.div(
            submitted,
            *self._panels(formats, mode, months, size, start),
            render_if(error, lambda text: error_component(text, self._input_id())),
            **attrs,
        )

    def _config(
        self, formats: Formats, mode: DatePickerMode, months: int, start: Weekday
    ) -> dict[str, Any]:
        """
        What date-picker.js is handed: every day as ISO text, and the names
        from Formats, so a framework's translations reach the grid.
        """
        days: tuple[date, ...] = self._get_prop("value", ())
        value = sorted({day.isoformat() for day in days})
        limit = {"single": 1, "range": 2}.get(mode)
        if limit is not None and len(value) > limit:
            raise ValueError(f"A {mode} DatePicker cannot hold {len(value)} days.")
        blocked: tuple[date | Weekday, ...] = self._get_prop("unavailable", ())
        low: date | None = self._get_prop("min")
        high: date | None = self._get_prop("max")
        return {
            "mode": mode,
            "value": value,
            "months": months,
            "weekStart": WEEKDAYS.index(start),
            "min": low and low.isoformat(),
            "max": high and high.isoformat(),
            "unavailable": [d.isoformat() for d in blocked if isinstance(d, date)],
            "closed": [WEEKDAYS.index(d) for d in blocked if isinstance(d, str)],
            "markers": [d.isoformat() for d in self._get_prop("markers", ())],
            "markerLabel": self._get_prop("marker_label", ""),
            "disabled": self._get_prop("disabled", False),
            "monthNames": list(formats.month_names),
            "dayNames": list(formats.day_names),
        }

    def _panels(
        self,
        formats: Formats,
        mode: DatePickerMode,
        months: int,
        size: DatePickerSize,
        start: Weekday,
    ) -> list[ComponentType]:
        """
        The days, and the month and year panels the caption's title jumps
        to, one shown at a time.
        """
        disabled: bool = self._get_prop("disabled", False)
        width = _SIZES[size][2]
        return [
            html.div(
                *(
                    self._month(formats, m, mode, months, size, start)
                    for m in range(months)
                ),
                class_="flex flex-col gap-6 sm:flex-row",
                **{"x-show": "level === 'days'"},
            ),
            html.div(
                _caption(
                    _step("Previous year", "chevron-left", -12, disabled),
                    _title("year()", "monthsTitle", "choose year", disabled),
                    _step("Next year", "chevron-right", 12, disabled),
                ),
                html.div(
                    *(
                        html.button(
                            formats.month_names[i],
                            type="button",
                            class_=_ITEM,
                            **{"data-item": "", "x-bind": f"monthItem({i})"},
                        )
                        for i in range(12)
                    ),
                    class_=f"grid grid-cols-3 gap-1 {width}",
                ),
                class_="flex flex-col gap-1.5",
                **{"x-ref": "months", "x-show": "level === 'months'", "x-cloak": True},
            ),
            html.div(
                _caption(
                    _step("Previous years", "chevron-left", -144, disabled),
                    _title("decade()", "yearsTitle", "back to days", disabled),
                    _step("Next years", "chevron-right", 144, disabled),
                ),
                html.div(
                    *(
                        html.button(
                            type="button",
                            class_=_ITEM,
                            **{"data-item": "", "x-bind": f"yearItem({i})"},
                        )
                        for i in range(12)
                    ),
                    class_=f"grid grid-cols-3 gap-1 {width}",
                ),
                class_="flex flex-col gap-1.5",
                **{"x-show": "level === 'years'", "x-cloak": True},
            ),
        ]

    def _month(
        self,
        formats: Formats,
        m: int,
        mode: DatePickerMode,
        months: int,
        size: DatePickerSize,
        start: Weekday,
    ) -> ComponentType:
        """
        One month: its caption and its grid, labelled with the month it
        shows. Only the first caption's title jumps, so the button that
        moved focus is always one that stays on the page.
        """
        disabled: bool = self._get_prop("disabled", False)
        disc, head, _ = _SIZES[size]
        spacer = html.span(class_="size-control-xs")
        title = (
            _title(f"title({m})", "daysTitle", "choose month", disabled)
            if m == 0
            else html.span(class_=_TITLE, **{"x-text": f"title({m})"})
        )
        first = WEEKDAYS.index(start)
        columns = [(first + n) % 7 for n in range(7)]
        return html.div(
            _caption(
                _step("Previous month", "chevron-left", -1, disabled)
                if m == 0
                else spacer,
                title,
                _step("Next month", "chevron-right", 1, disabled)
                if m == months - 1
                else spacer,
            ),
            html.table(
                html.thead(
                    html.tr(
                        *(
                            html.th(
                                formats.day_abbreviations[d],
                                scope="col",
                                # What a screen reader announces as the column.
                                abbr=formats.day_names[d],
                                class_=f"{head} font-medium text-fg-muted",
                            )
                            for d in columns
                        )
                    )
                ),
                html.tbody(
                    *(
                        html.tr(
                            *(
                                html.td(
                                    html.span(
                                        class_=classnames(_DISC, disc),
                                        **{"x-text": f"number({m}, {row * 7 + col})"},
                                    ),
                                    class_=_CELL,
                                    **{"x-bind": f"day({m}, {row * 7 + col})"},
                                )
                                for col in range(7)
                            )
                        )
                        for row in range(_CELLS // 7)
                    )
                ),
                role="grid",
                aria_multiselectable="true" if mode != "single" else None,
                aria_required="true" if self._get_prop("required", False) else None,
                # Separate, because Chrome draws no box-shadow, so no focus ring,
                # on the cells of a collapsed table.
                class_="border-separate border-spacing-0",
                **{":aria-label": f"title({m})"},
            ),
            class_="flex flex-col gap-1.5",
        )


def _days(*days: date) -> tuple[date, ...]:
    """
    The picker holds days. A datetime would compare as text against the
    days it is checked with and quietly match none of them.
    """
    for day in days:
        if not isinstance(day, date) or isinstance(day, datetime):
            raise ValueError(f"A DatePicker takes dates, not {day!r}.")
    return days


def _caption(*parts: ComponentType) -> ComponentType:
    return html.div(*parts, class_="flex items-center justify-between gap-1")


def _step(label: str, icon: str, months: int, disabled: bool) -> ComponentType:
    button = (
        Button()
        .variant("ghost")
        .size("xs")
        .icon_only(label)
        .x_on("click", unsafe(f"page({months})"))
        .content(HueIcon(icon))
    )
    return button.disabled() if disabled else button


def _title(text: str, ref: str, action: str, disabled: bool) -> ComponentType:
    """
    The caption's title, a button that switches panels. What it shows is
    the month or the years; what pressing it does is said to a screen
    reader after that.
    """
    return html.button(
        html.span(**{"x-text": text}),
        html.span(f", {action}", class_="sr-only"),
        HueIcon("chevron-down").class_("size-3.5 text-fg-subtle"),
        type="button",
        disabled=disabled or None,
        class_=classnames(_TITLE, "cursor-pointer hover:bg-surface-hover", FOCUS_RING),
        **{"x-ref": ref, "x-on:click": "nextLevel()"},
    )
