from __future__ import annotations

from datetime import date, datetime
from typing import override

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.js import call, unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING_INSET
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import _BaseInput
from hue.ui.molecules import _overlay
from hue.ui.molecules._days import WEEKDAYS, Weekday, weekday_head
from hue.ui.molecules.field import Field
from hue.utils import classnames

_PANEL = (
    "z-70 w-72 max-w-[calc(100vw-2rem)] rounded-lg border border-border "
    "bg-surface-raised p-3 shadow-raised"
)
# A day is the same disc as the events calendar's number, with today bold
# rather than filled, since filled is what the chosen day is here.
_DAY = (
    "grid size-8 cursor-pointer place-content-center rounded-full font-ui text-sm "
    "font-medium tabular-nums aria-[current=date]:font-bold "
    "aria-[current=date]:underline aria-[current=date]:underline-offset-4"
)
# One of two whole looks rather than a filled one layered on the plain one,
# where the plain hover would win on the chosen day. Written out whole so
# the stylesheet scan finds every class.
_PICKED = (
    "cell.selected ? 'bg-accent text-accent-fg hover:bg-accent-hover' "
    ": 'text-fg hover:bg-surface-hover'"
)


class DateInput(_BaseInput):
    """
    A text field for one date, written and submitted as YYYY-MM-DD, with a
    button that opens a month to pick it from.

    The picker is the APG date picker dialog: arrows move by day and week,
    Page Up and Page Down by month, Home and End to the ends of the week,
    Enter picks and Escape puts you back in the field. week_start() moves
    the first column.
    """

    _input_type = "text"
    category = "Inputs"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._props["week_start"] = "monday"
        # The format is the one thing a reader typing has to know.
        self._props["placeholder"] = "YYYY-MM-DD"

    @classmethod
    def example(cls) -> Self:
        return cls().name("starts").label("Start date")

    @override
    def value(self, value: date | str) -> Self:
        """
        The date it starts with. A datetime is refused: it would write its
        time into a field that holds a day.
        """
        if isinstance(value, datetime):
            raise ValueError("A DateInput holds a day. Pass value.date().")
        self._props["value"] = value.isoformat() if isinstance(value, date) else value
        return self

    def week_start(self, value: Weekday) -> Self:
        self._props["week_start"] = value
        return self

    @override
    def _get_extra_input_attrs(self) -> dict[str, object]:
        return {
            **super()._get_extra_input_attrs(),
            # The browser refuses to submit anything else, with JS or without.
            "pattern": r"\d{4}-\d{2}-\d{2}",
            "x-ref": "input",
        }

    def _inert(self) -> bool:
        # Disabled and readonly both refuse edits, so neither offers a picker.
        disabled: bool = self._get_prop("disabled", False)
        readonly: bool = self._get_prop("readonly", False)
        return disabled or readonly

    def _picker_ids(self) -> tuple[str, str]:
        input_id = self._input_id()
        return f"{input_id}-picker", f"{input_id}-picker-month"

    @override
    def _render(self, context: Context) -> Component:
        # The button, set the way PasswordInput sets its toggle. Inert, it is
        # disabled with no handler, and nothing opens.
        button = (
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Choose date")
            .content(HueIcon("calendar"))
        )
        if self._inert():
            button.disabled()
        else:
            _overlay.wire_trigger(button, popup="dialog", on={"click": "toggle()"})
            button.aria_controls(self._picker_ids()[0])
        self._props.setdefault("action", button)
        return super()._render(context)

    @override
    def _get_group_attrs(self) -> dict[str, object]:
        # What the panel hangs off: the whole field, not just the text.
        return {} if self._inert() else {"x-ref": "shell"}

    @override
    def _field(self, context: Context, control: ComponentType) -> Field:
        """
        The group and the picker beside it, in one scope, inside the Field.

        Overridden here rather than _control because the picker needs the
        context for its names. The scope sits on a wrapper rather than the
        group (PasswordInput puts its state on the group) because the panel
        is not a segment of the field: inside the group it would pick up the
        shell's hover border.
        """
        if self._inert():
            return super()._field(context, control)
        formats = Formats.from_context(context)
        start: Weekday = self._get_prop("week_start", "monday")
        state = call(
            "hueDateInput",
            WEEKDAYS.index(start),
            list(formats.month_names),
            list(formats.day_names),
        )
        wrapper = html.div(
            control,
            self._panel(formats, start),
            class_="relative",
            **{
                # open and close() are what CLOSE_ON_ESCAPE calls; close()
                # focuses the field before it hides the panel.
                **_overlay.overlay_root(state),
                # Where a click landed is where focus is; nothing to restore.
                "x-on:click.outside": "dismiss()",
                # Tab walks on to the next field, and the panel goes with it.
                "x-on:focusout": "leave($event)",
            },
        )
        return super()._field(context, wrapper)

    def _panel(self, formats: Formats, start: Weekday) -> ComponentType:
        panel_id, heading_id = self._picker_ids()
        day = html.button(
            type="button",
            class_=classnames(_DAY, FOCUS_RING_INSET),
            **{
                "x-show": "!cell.outside",
                "x-text": "cell.day",
                "x-bind:data-date": "cell.iso",
                "x-bind:tabindex": "cell.iso === focused ? 0 : -1",
                "x-bind:aria-label": "cell.label",
                "x-bind:aria-current": "cell.today ? 'date' : null",
                "x-bind:class": _PICKED,
                "x-on:click": "pick(cell.iso)",
            },
        )
        cell = html.td(
            day,
            class_="p-0 text-center",
            **{"x-bind:aria-selected": "cell.selected ? 'true' : null"},
        )
        return html.div(
            html.div(
                _step("Previous month", "chevron-left", "page(-1)"),
                html.h2(
                    id=heading_id,
                    aria_live="polite",
                    class_="font-ui text-sm font-bold text-fg",
                    **{"x-text": "heading"},
                ),
                _step("Next month", "chevron-right", "page(1)"),
                class_="flex items-center justify-between gap-2 pb-2",
            ),
            html.table(
                weekday_head(formats, start),
                html.tbody(
                    # Six weeks, always, drawn by Alpine: paging months
                    # happens in the browser, with no route to ask. Keyed by
                    # position, so the button holding focus is redrawn in
                    # place rather than removed, which would drop focus.
                    html.template(
                        html.tr(
                            html.template(
                                cell,
                                **{"x-for": "(cell, col) in week", ":key": "col"},
                            ),
                        ),
                        **{"x-for": "(week, row) in weeks", ":key": "row"},
                    ),
                ),
                role="grid",
                aria_labelledby=heading_id,
                class_="w-full border-collapse",
            ),
            id=panel_id,
            role="dialog",
            class_=_PANEL,
            **{
                **_overlay.accessible_name("DateInput", None, "Choose date"),
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                "x-anchor.bottom-start.offset.6": "$refs.shell",
                # Arrows, pages, Home, End, Enter and Space, in date-input.js.
                "x-on:keydown": "key($event)",
                **_overlay.HOLDS_FOCUS,
            },
        )


def _step(label: str, icon: str, action: str) -> ComponentType:
    return (
        Button()
        .variant("ghost")
        .size("xs")
        .icon_only(label)
        .x_on("click", unsafe(action))
        .content(HueIcon(icon))
    )
