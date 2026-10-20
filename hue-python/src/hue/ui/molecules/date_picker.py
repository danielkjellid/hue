from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, get_args

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import modelable
from hue.ui.form import FieldControl
from hue.ui.molecules.field import error_component, hint_component, legend_component
from hue.utils import classnames, render_if, render_when

type DatePickerMode = Literal["single", "range", "multiple"]
type DatePickerSize = Literal["sm", "md"]
type Weekday = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]  # fmt: skip

# Monday first, as date.weekday() and Formats.day_names count.
WEEKDAYS: tuple[Weekday, ...] = get_args(Weekday.__value__)

# Six weeks, always, so the grid keeps its height from month to month.
_WEEKS = 6

# The cell carries the state, as attributes date-picker.js binds; the disc
# inside draws it. The cell's ::before is the band a range runs along, behind
# the disc, which is why the cell isolates: without a stacking context of its
# own the band would sink under the background of whatever holds the picker.
_CELL = classnames(
    "relative isolate p-px text-center outline-none focus-visible:z-10",
    "before:absolute before:inset-y-0 before:-z-10 before:bg-accent-subtle",
    "data-[band=inside]:before:inset-x-0",
    "data-[band=start]:before:start-1/2 data-[band=start]:before:end-0",
    "data-[band=end]:before:start-0 data-[band=end]:before:end-1/2",
    "data-preview:before:bg-accent-subtle/50",
)
# Each state's selector excludes the ones that outrank it, since Tailwind
# orders these variants by their own rules rather than by the class list.
_DISC = classnames(
    "relative grid place-items-center rounded-md",
    "font-medium tabular-nums text-fg",
    "in-[fieldset:disabled]:text-fg-disabled",
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
    "in-aria-disabled:text-fg-disabled",
    # The marker dot, in the disc's own colour so it shows on a filled day.
    "in-data-marked:after:absolute in-data-marked:after:bottom-1",
    "in-data-marked:after:start-1/2 in-data-marked:after:size-1",
    "in-data-marked:after:-translate-x-1/2 in-data-marked:after:rounded-full",
    "in-data-marked:after:bg-current",
)
_ITEM = classnames(
    "h-control-lg cursor-pointer rounded-md text-sm font-medium text-fg",
    "hover:bg-surface-hover data-current:font-bold",
    "data-current:not-aria-pressed:inset-ring",
    "data-current:not-aria-pressed:inset-ring-fg",
    "aria-pressed:bg-accent aria-pressed:text-accent-fg",
    "aria-pressed:hover:bg-accent-hover",
    "disabled:cursor-not-allowed disabled:text-fg-disabled",
    FOCUS_RING,
)
_TITLE = classnames(
    "inline-flex h-control-xs items-center gap-1 rounded-md px-2 font-ui",
    "text-base font-bold text-fg in-[fieldset:disabled]:text-fg-disabled",
)

_DISC_SIZES: dict[DatePickerSize, str] = {
    "sm": "h-7.5 w-7 text-xs",
    "md": "h-9 w-8.5 text-sm",
}
_HEAD_SIZES: dict[DatePickerSize, str] = {
    "sm": "h-6 text-2xs",
    "md": "h-7 text-xs",
}
# The jump panels are as wide as seven discs.
# The least the panels take, so a jump panel is never narrower than a month.
_PANEL_WIDTHS: dict[DatePickerSize, str] = {
    "sm": "min-w-52.5",
    "md": "min-w-63",
}


@dataclass(frozen=True, kw_only=True)
class _Grid:
    """
    What the months are drawn with, read once in _render.
    """

    formats: Formats
    mode: DatePickerMode
    months: int
    size: DatePickerSize
    start: Weekday
    disabled: bool


class DayRules:
    """
    Which days refuse a pick, and which day a week starts on. Mixed into
    DatePicker and the fields that open one, so they take the same rules.
    """

    _props: dict[str, Any]  # provided by ChainableComponent

    # The props the modifiers below set, which a field hands on to its grid.
    KEYS = ("min", "max", "unavailable", "week_start")

    def min(self, value: date) -> Self:
        """
        The first day that can be picked or typed.
        """
        self._props["min"] = _days(value)[0]
        return self

    def max(self, value: date) -> Self:
        """
        The last day that can be picked or typed.
        """
        self._props["max"] = _days(value)[0]
        return self

    def unavailable(self, *days: date | Weekday) -> Self:
        """
        Days that refuse a pick: dates, or weekdays by name for every one of
        them, as in unavailable("saturday", "sunday").
        """
        _days(*(day for day in days if not isinstance(day, str)))
        for day in days:
            if isinstance(day, str) and day not in WEEKDAYS:
                raise ValueError(f"{day!r} is not a weekday: one of {WEEKDAYS}.")
        self._props["unavailable"] = days
        return self

    def week_start(self, value: Weekday) -> Self:
        self._props["week_start"] = value
        return self


class DatePicker(DayRules, FieldControl):
    """
    A month to pick a day, a range or several days from, inline on the page.

    mode() picks how a click selects, months() shows several side by side,
    and min(), max() and unavailable() say which days refuse. markers() puts
    a dot under days that have something on them. The caption's title jumps
    by month and year. The label is the legend over the months. The days
    are submitted under name, one hidden field each, and x_model binds the
    same list of ISO dates.
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

    def hidden_label(self, value: bool = True) -> Self:
        """
        Keep the legend for screen readers but take it off the screen, for a
        picker whose purpose is plain from where it sits.
        """
        self._props["hidden_label"] = value
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
        required: bool = self._get_prop("required", False)
        hidden_label: bool = self._get_prop("hidden_label", False)
        start: Weekday = self._get_prop("week_start", "monday")
        error: str | None = self._error(context)
        hint: str | None = self._get_prop("hint")
        control_id = self._input_id()

        if label is None:
            raise ValueError(
                "DatePicker needs a label(): a group of month grids that "
                "announces nothing gives a screen reader no way to say what "
                "the days are for."
            )

        grid = _Grid(
            formats=Formats.from_context(context),
            mode=mode,
            months=months,
            size=size,
            start=start,
            disabled=disabled,
        )
        attrs = self._control_attrs(
            context,
            aria_describedby=self._describedby(context),
            aria_invalid="true" if error is not None else None,
            # So focus can wait here while the panels swap.
            tabindex="-1",
            class_=classnames(
                "inline-flex min-w-0 flex-col gap-2 outline-none select-none",
                {"pointer-events-none": disabled},
                self._get_prop("class_"),
            ),
            disabled=disabled or None,
            **{
                "x-data": call("hueDatePicker", self._config(grid)),
                "x-on:keydown": "key($event)",
                "x-on:click": "click($event)",
                "x-on:mouseover": "preview($event)",
                "x-on:mouseleave": "hover = null",
            },
        )
        # A fieldset's form ties only the fieldset, so it goes on the
        # submitted fields. The caller's x-model binds the list of days.
        form = attrs.pop("form", None)
        model = attrs.pop("x-model", None)
        if model is not None:
            attrs.update(modelable(model, "value"))

        submitted = html.template(
            html.input_(
                type="hidden",
                name=name,
                form=form,
                # A disabled field is left out of what the form submits.
                disabled=disabled or None,
                **{":value": "iso"},
            ),
            # Keyed by position: a range picked on one day holds it twice.
            **{"x-for": "(iso, i) in days()", ":key": "i"},
        )
        # Hidden fields are never validated, so required is held by an empty
        # one the browser does check, required until the pick is complete. A
        # value would be emptied by a form reset while the days stay picked.
        # Focus it lands on goes on to the grid.
        enforced = html.input_(
            type="text",
            form=form,
            tabindex="-1",
            aria_hidden="true",
            class_="sr-only",
            **{
                "x-bind:required": f"days().length < {2 if mode == 'range' else 1}",
                "x-on:focus": "focusedCell()?.focus()",
            },
        )
        return html.fieldset(
            legend_component(label, required, hidden=hidden_label),
            submitted,
            render_when(required, enforced),
            *self._panels(grid),
            render_if(hint, lambda text: hint_component(text, control_id)),
            render_if(error, lambda text: error_component(text, control_id)),
            **attrs,
        )

    def _config(self, grid: _Grid) -> dict[str, Any]:
        """
        What date-picker.js is handed: every day as ISO text, and the names
        from Formats, so a framework's translations reach the grid.
        """
        days: tuple[date, ...] = self._get_prop("value", ())
        # A range on one day posts that day twice, and needs both back to be
        # complete. Only several days can repeat one by mistake.
        iso = [day.isoformat() for day in days]
        mode = grid.mode
        value = sorted(set(iso) if mode == "multiple" else iso)
        limit = {"single": 1, "range": 2}.get(mode)
        if limit is not None and len(value) > limit:
            raise ValueError(f"A {mode} DatePicker cannot hold {len(value)} days.")
        blocked: tuple[date | Weekday, ...] = self._get_prop("unavailable", ())
        low: date | None = self._get_prop("min")
        high: date | None = self._get_prop("max")
        return {
            "mode": mode,
            "value": value,
            "months": grid.months,
            "weekStart": WEEKDAYS.index(grid.start),
            "min": low and low.isoformat(),
            "max": high and high.isoformat(),
            "unavailable": [d.isoformat() for d in blocked if isinstance(d, date)],
            "closed": [WEEKDAYS.index(d) for d in blocked if isinstance(d, str)],
            "markers": [d.isoformat() for d in self._get_prop("markers", ())],
            "markerLabel": self._get_prop("marker_label", ""),
            "disabled": grid.disabled,
            "monthNames": list(grid.formats.month_names),
            "monthNamesInDate": list(grid.formats.month_names_in_date),
            "dayNames": list(grid.formats.day_names),
        }

    def _panels(self, grid: _Grid) -> list[ComponentType]:
        """
        The days, and the month and year panels the caption's title jumps
        to, one shown at a time. All three share one grid cell and the
        hidden ones are only invisible, so the picker keeps the size of the
        largest rather than jumping as they swap.
        """
        disabled = grid.disabled
        width = _PANEL_WIDTHS[grid.size]

        def shown(level: str) -> dict[str, str]:
            return {"x-bind:class": f"{{ invisible: level !== '{level}' }}"}

        return [
            html.div(
                html.div(
                    *(self._month(grid, m) for m in range(grid.months)),
                    class_="flex flex-col gap-6 [grid-area:1/1] sm:flex-row",
                    **shown("days"),
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
                                grid.formats.month_names[i],
                                type="button",
                                class_=_ITEM,
                                **{"data-item": "", "x-bind": f"monthItem({i})"},
                            )
                            for i in range(12)
                        ),
                        class_="grid grid-cols-3 gap-1",
                    ),
                    class_="invisible flex flex-col gap-1.5 [grid-area:1/1]",
                    **{"x-ref": "months", **shown("months")},
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
                        class_="grid grid-cols-3 gap-1",
                    ),
                    class_="invisible flex flex-col gap-1.5 [grid-area:1/1]",
                    **shown("years"),
                ),
                class_=f"grid {width}",
            )
        ]

    def _month(self, grid: _Grid, m: int) -> ComponentType:
        """
        One month: its caption and its grid, labelled with the month it
        shows. Only the first caption's title jumps, so the button that
        moved focus is always one that stays on the page.
        """
        disabled = grid.disabled
        disc = classnames(_DISC, _DISC_SIZES[grid.size])
        spacer = html.span(class_="size-control-xs")
        title = (
            _title(f"title({m})", "daysTitle", "choose month", disabled)
            if m == 0
            else html.span(class_=_TITLE, **{"x-text": f"title({m})"})
        )
        first = WEEKDAYS.index(grid.start)
        columns = [(first + n) % 7 for n in range(7)]
        return html.div(
            _caption(
                _step("Previous month", "chevron-left", -1, disabled)
                if m == 0
                else spacer,
                title,
                _step("Next month", "chevron-right", 1, disabled)
                if m == grid.months - 1
                else spacer,
            ),
            html.table(
                html.thead(
                    html.tr(
                        *(
                            html.th(
                                grid.formats.day_abbreviations[d],
                                scope="col",
                                # What a screen reader announces as the column.
                                abbr=grid.formats.day_names[d],
                                class_=classnames(
                                    _HEAD_SIZES[grid.size],
                                    "font-medium text-fg-muted",
                                    "in-[fieldset:disabled]:text-fg-disabled",
                                ),
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
                                        class_=disc,
                                        **{"x-text": f"number({m}, {row * 7 + col})"},
                                    ),
                                    class_=_CELL,
                                    **{"x-bind": f"day({m}, {row * 7 + col})"},
                                )
                                for col in range(7)
                            )
                        )
                        for row in range(_WEEKS)
                    )
                ),
                role="grid",
                aria_multiselectable="true" if grid.mode != "single" else None,
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
            raise ValueError(f"Pass a date, not {day!r}.")
    return days


def _caption(*parts: ComponentType) -> ComponentType:
    return html.div(*parts, class_="flex items-center justify-between gap-1")


def _step(label: str, icon: str, months: int, disabled: bool) -> ComponentType:
    return (
        Button()
        .variant("ghost")
        .size("xs")
        .icon_only(label)
        .x_on("click", unsafe(f"page({months})"))
        .disabled(disabled)
        .content(HueIcon(icon))
    )


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
