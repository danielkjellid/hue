"""
The views of a Calendar: the time grid of a day or a week, the month, the
year and the agenda. Each is a function over the one _Draw a rendering
holds, which owns the words, the links and the events they share.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta

from htmy import html

from hue.types.core import ComponentType
from hue.ui._styles import FOCUS_RING_INSET
from hue.ui.atoms.button import Button
from hue.ui.molecules._days import (
    Event,
    Placed,
    Slot,
    minutes,
    month_grid,
    pack,
    place,
)
from hue.ui.molecules.calendar import (
    _AGENDA_DAYS,
    _DOT,
    _EVENT,
    _NUMBER,
    _NUMBER_LINK,
    _NUMBER_TODAY,
    _SOLID,
    _TINT,
    _Draw,
    _EventButton,
)
from hue.ui.molecules.empty import Empty
from hue.ui.molecules.popover import Popover
from hue.utils import classnames, render_if, render_when

# One hour of the time grid, in pixels, and where the grid opens: 07:30,
# just before most days start.
_HOUR = 48
_OPENS_AT = int(7.5 * _HOUR)
# Under this many minutes an event is one line, title then time; over this
# many pixels its title may wrap.
_SHORT = 45
_TALL = 70
# A month cell shows this many events, or one fewer and how many more.
_PER_CELL = 3
_HEAD = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"
_NUMBER_IN_TODAY = (
    "group-aria-[current=date]:bg-accent group-aria-[current=date]:text-accent-fg"
)
_WEEKEND = "bg-canvas-subtle"
# The hour and half-hour rules of a column, drawn as a background so they
# cost no elements. The sizes are the hour height above.
_HOUR_LINES = (
    "background-image: linear-gradient(var(--color-border) 1px, transparent 1px), "
    "linear-gradient(color-mix(in oklab, var(--color-border) 50%, transparent) "
    "1px, transparent 1px); "
    f"background-size: 100% {_HOUR}px; background-position: 0 0, 0 {_HOUR // 2}px"
)


@dataclass(frozen=True)
class _Bar:
    """
    An all-day event across the columns of a week, from the first it covers
    to the last, and whether it goes on past either end.
    """

    event: Event
    first: int
    last: int
    before: bool
    after: bool


# Day and week


def time_grid(draw: _Draw, days: list[date]) -> ComponentType:
    """
    A column per day over twenty-four hours, with the all-day events in
    a row above and the hours down the side.
    """
    placed = place(draw.events, days[0], days[-1], draw.formats)
    columns = f"grid-template-columns: 3.5rem repeat({len(days)}, minmax(0, 1fr))"
    bars = _bars(days, placed)
    return html.div(
        html.div(
            html.div(),
            *(_day_head(draw, day) for day in days),
            class_="grid border-b border-border",
            style=columns,
        ),
        html.div(
            html.div(
                "All day",
                class_=classnames(_HEAD, "flex items-center justify-end pe-2"),
            ),
            render_when(
                bool(bars),
                html.ul(
                    *(_bar(draw, bar) for bar in bars),
                    class_="grid gap-y-0.5 border-s border-border py-1",
                    style=(
                        f"grid-column: 2 / -1; grid-template-columns: "
                        f"repeat({len(days)}, minmax(0, 1fr)); "
                        "grid-auto-flow: row dense; grid-auto-rows: 1.25rem"
                    ),
                ),
                html.div(class_="min-h-7 border-s border-border"),
            ),
            class_="grid border-b border-border",
            style=columns,
        ),
        html.div(
            html.div(
                _hours(draw),
                *(_column(draw, day, placed.get(day, [])) for day in days),
                class_="grid",
                style=f"{columns}; height: {24 * _HOUR}px",
            ),
            class_="max-h-[42rem] overflow-y-auto",
            **{"x-init": f"$el.scrollTop = {_OPENS_AT}"},
        ),
        class_="flex flex-col",
    )


def _day_head(draw: _Draw, day: date) -> ComponentType:
    return draw.link(
        day,
        "day",
        html.span(draw.formats.day_abbreviations[day.weekday()], class_=_HEAD),
        html.span(str(day.day), class_=classnames(_NUMBER, _NUMBER_IN_TODAY)),
        label=draw.day_name(day),
        classes="group flex h-13 items-center justify-center gap-2 border-s "
        "border-border no-underline",
        link_classes="hover:bg-surface-hover",
        current=day == draw.today,
    )


def _bars(days: list[date], placed: dict[date, list[Placed]]) -> list[_Bar]:
    """
    Each all-day event once, across every shown day it covers. Keyed by
    identity: two events alike in every field are still two events.
    """
    found: dict[int, _Bar] = {}
    for index, day in enumerate(days):
        for each in placed.get(day, []):
            if each.event.timed:
                continue
            known = found.get(id(each.event))
            found[id(each.event)] = _Bar(
                each.event,
                index if known is None else known.first,
                index,
                each.continues_before if known is None else known.before,
                each.continues_after,
            )
    return list(found.values())


def _bar(draw: _Draw, bar: _Bar) -> ComponentType:
    return html.li(
        draw.chip(bar.event, bar.before, bar.after),
        class_=classnames("flex", {"ms-0.5": not bar.before, "me-0.5": not bar.after}),
        style=f"grid-column: {bar.first + 1} / {bar.last + 2}",
    )


def _hours(draw: _Draw) -> ComponentType:
    """
    The gutter. Decoration: every event says its own time.
    """
    return html.div(
        *(
            html.span(
                draw.clock(time(hour)),
                class_="absolute end-2 -translate-y-1/2 text-2xs tabular-nums "
                "text-fg-muted",
                style=f"top: {hour * _HOUR}px",
            )
            for hour in range(1, 24)
        ),
        aria_hidden="true",
        class_="relative",
    )


def _column(draw: _Draw, day: date, items: list[Placed]) -> ComponentType:
    timed = [each for each in items if each.event.timed]
    spans = [minutes(each, draw.formats) for each in timed]
    slots = pack(spans)
    return html.div(
        render_when(
            bool(timed),
            html.ul(
                *(
                    _timed(draw, each, span, slot)
                    for each, span, slot in zip(timed, spans, slots, strict=True)
                ),
                class_="absolute inset-0",
            ),
        ),
        render_when(day == draw.today, _now()),
        data_date=day.isoformat(),
        class_=classnames(
            "relative border-s border-border", {_WEEKEND: day.weekday() >= 5}
        ),
        style=_HOUR_LINES,
    )


def _timed(
    draw: _Draw, placed: Placed, span: tuple[int, int], slot: Slot
) -> ComponentType:
    event = placed.event
    start, end = span
    starts = event.moments(draw.formats)[0]
    height = max((end - start) * _HOUR // 60 - 2, 18)
    short = end - start < _SHORT
    if short:
        title_classes, time_classes = "min-w-0 truncate", "flex-none"
    elif height > _TALL:
        title_classes, time_classes = "line-clamp-3", "block truncate"
    else:
        title_classes, time_classes = "block truncate", "block truncate"
    button = _EventButton(
        event,
        draw.name(event),
        classnames(
            _EVENT,
            _TINT[event.color],
            FOCUS_RING_INSET,
            "h-full overflow-hidden py-0.5 leading-4",
            "flex items-baseline gap-1.5" if short else "block",
            # Squared where it runs on from the day before or into the
            # next, as an all-day bar is where the week cuts it.
            {
                "rounded-t-none": placed.continues_before,
                "rounded-b-none": placed.continues_after,
            },
        ),
    ).content(
        html.span(
            *draw._title_of(event),
            class_=classnames("font-semibold", title_classes),
        ),
        html.span(
            draw.clock(starts) if short else draw.times(event, end_day=False),
            class_=classnames("tabular-nums text-fg-muted", time_classes),
        ),
    )
    return html.li(
        draw.event(event, button),
        class_="absolute flex",
        style=(
            # The least height a line of text needs can still reach past
            # midnight, so the box moves up rather than out of the grid.
            f"top: {min(start * _HOUR // 60, 24 * _HOUR - height)}px; "
            f"height: {height}px; "
            f"left: calc({slot.column} / {slot.columns} * 100% + 2px); "
            f"width: calc(100% / {slot.columns} - 4px)"
        ),
    )


def _now() -> ComponentType:
    """
    The line at the time it is, moved every minute by the browser, which
    is the one clock that knows the reader's now.
    """
    # Assumes the browser's timezone is the one Formats moves events
    # into; where they differ, the line and the events disagree.
    return html.div(
        aria_hidden="true",
        class_="pointer-events-none absolute inset-x-0 z-10 h-0.5 bg-danger "
        "before:absolute before:-start-1 before:-top-[3px] before:size-2 "
        "before:rounded-full before:bg-danger",
        **{
            "x-data": (
                "{ minute: 0, tick() { const now = new Date(); "
                "this.minute = now.getHours() * 60 + now.getMinutes() } }"
            ),
            "x-init": "tick(); setInterval(() => tick(), 60000)",
            ":style": f"'top: ' + minute * {_HOUR} / 60 + 'px'",
        },
    )


# Month


def month(draw: _Draw) -> ComponentType:
    """
    A table with a column per weekday and six rows of weeks. A table
    rather than a grid widget: every event is a control to read and
    open, and browse-mode table navigation already announces the
    weekday with each cell.
    """
    formats = draw.formats
    rows = month_grid(draw.cursor, draw.start)
    if draw.weekdays:
        rows = tuple(tuple(day for day in row if day.weekday() < 5) for row in rows)
    placed = place(draw.events, rows[0][0], rows[-1][-1], formats)
    return html.table(
        html.caption(formats.month(draw.cursor), class_="sr-only"),
        html.thead(
            html.tr(
                *(
                    html.th(
                        formats.day_abbreviations[day.weekday()],
                        scope="col",
                        abbr=formats.day_names[day.weekday()],
                        class_=classnames(_HEAD, "border-b border-border py-2"),
                    )
                    for day in rows[0]
                )
            )
        ),
        html.tbody(
            *(
                html.tr(*(_cell(draw, day, placed.get(day, [])) for day in row))
                for row in rows
            ),
            class_="[&_tr:last-child_td]:border-b-0",
        ),
        class_="w-full table-fixed border-collapse",
    )


def _cell(draw: _Draw, day: date, items: list[Placed]) -> ComponentType:
    outside = (day.year, day.month) != (draw.cursor.year, draw.cursor.month)
    shown = items if len(items) <= _PER_CELL else items[: _PER_CELL - 1]
    more = len(items) - len(shown)
    return html.td(
        draw.number(day),
        render_when(
            bool(shown),
            html.ul(
                *(draw.item(each) for each in shown),
                class_="mt-1 flex flex-col gap-0.5",
            ),
        ),
        render_when(more > 0, _more(draw, day, items, more)),
        data_date=day.isoformat(),
        class_=classnames(
            "h-28 overflow-hidden border-e border-b border-border p-1 align-top "
            "last:border-e-0",
            {
                _WEEKEND: outside or day.weekday() >= 5,
                "text-fg-subtle": outside,
            },
        ),
    )


def _more(draw: _Draw, day: date, items: list[Placed], count: int) -> ComponentType:
    """
    The rest of a day's events, in a popover headed by the day.
    """
    name = draw.formats.day(day)
    return (
        Popover()
        .title(name)
        .placement("bottom-start", fixed=True)
        .trigger(
            Button()
            .variant("ghost")
            .size("xs")
            .aria_label(f"+{count} more, {name}")
            .class_("mt-0.5")
            .content(f"+{count} more")
        )
        .content(
            html.ul(
                *(draw.item(each) for each in items),
                class_="flex flex-col gap-0.5",
            )
        )
    )


# Year


def year(draw: _Draw) -> ComponentType:
    year = draw.cursor.year
    placed = place(draw.events, date(year, 1, 1), date(year, 12, 31), draw.formats)
    return html.div(
        *(_mini(draw, date(year, month, 1), placed) for month in range(1, 13)),
        class_="grid grid-cols-[repeat(auto-fill,minmax(14rem,1fr))] gap-x-8 "
        "gap-y-6 p-4",
    )


def _mini(draw: _Draw, month: date, placed: dict[date, list[Placed]]) -> ComponentType:
    """
    One small month: its days as links to their day view, each with a
    dot when something is on.
    """
    formats = draw.formats
    rows = [
        row
        for row in month_grid(month, draw.start)
        if any(day.month == month.month for day in row)
    ]
    return html.table(
        html.caption(
            formats.month_names[month.month - 1],
            class_="pb-1 text-start font-ui text-sm font-semibold",
        ),
        html.thead(
            html.tr(
                *(
                    html.th(
                        formats.day_abbreviations[day.weekday()][0],
                        scope="col",
                        abbr=formats.day_names[day.weekday()],
                        class_=classnames(_HEAD, "pb-1 text-center"),
                    )
                    for day in rows[0]
                )
            )
        ),
        html.tbody(
            *(
                html.tr(
                    *(
                        html.td(
                            render_when(
                                day.month == month.month,
                                _year_day(draw, day, len(placed.get(day, []))),
                            ),
                            class_="p-0 text-center",
                        )
                        for day in row
                    )
                )
                for row in rows
            )
        ),
        class_="w-full table-fixed border-collapse",
    )


def _year_day(draw: _Draw, day: date, count: int) -> ComponentType:
    label = draw.day_name(day)
    if count:
        label += f", {count} event" if count == 1 else f", {count} events"
    return draw.link(
        day,
        "day",
        html.time(str(day.day), datetime=day.isoformat()),
        render_when(
            count > 0,
            html.span(
                aria_hidden="true",
                class_="absolute bottom-0.5 size-1 rounded-full bg-current",
            ),
        ),
        label=label,
        classes=classnames(_NUMBER, _NUMBER_TODAY, "relative"),
        link_classes=_NUMBER_LINK,
        current=day == draw.today,
    )


# Agenda


def agenda(draw: _Draw) -> ComponentType:
    """
    The next thirty days with something on, each day a heading over
    its list; an Empty when none of them has.
    """
    formats = draw.formats
    first = draw.cursor
    last = first + timedelta(days=_AGENDA_DAYS - 1)
    placed = place(draw.events, first, last, formats)
    days = sorted(placed)
    if not days:
        return (
            Empty()
            .title("Nothing scheduled")
            .description(f"{formats.day(first)} to {formats.day(last)}.")
        )
    return html.div(
        *(_agenda_day(draw, day, placed[day]) for day in days),
        class_="flex flex-col divide-y divide-border px-4",
    )


def _agenda_day(draw: _Draw, day: date, items: list[Placed]) -> ComponentType:
    formats = draw.formats
    return html.section(
        html.div(
            draw.number(day),
            html.span(
                formats.day_abbreviations[day.weekday()],
                html.br(),
                f"{formats.month_names[day.month - 1]} {day.year}",
                class_="text-xs leading-tight text-fg-muted",
            ),
            class_="flex items-center gap-2 self-start",
        ),
        html.ul(
            *(html.li(_agenda_row(draw, each), class_="flex") for each in items),
            class_="flex flex-col gap-0.5",
        ),
        data_date=day.isoformat(),
        class_="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-4 py-3",
    )


def _agenda_row(draw: _Draw, placed: Placed) -> ComponentType:
    event = placed.event
    formats = draw.formats
    if event.timed:
        when = draw.times(event, end_day=False)
    else:
        first, last = event.span(formats)
        total = (last - first).days + 1
        nth = (placed.day - first).days + 1
        when = "All day" if total == 1 else f"Day {nth} of {total}"
    button = _EventButton(
        event,
        draw.name(event),
        classnames(
            "grid w-full cursor-pointer grid-cols-[6.5rem_auto_minmax(0,1fr)] "
            "items-center gap-3 rounded-md px-2.5 py-2 text-start text-sm "
            "text-fg hover:bg-surface-hover",
            FOCUS_RING_INSET,
        ),
    ).content(
        html.span(when, class_="text-xs tabular-nums text-fg-muted"),
        html.span(aria_hidden="true", class_=classnames(_DOT, _SOLID[event.color])),
        html.span(
            html.span(*draw._title_of(event), class_="font-semibold"),
            render_if(
                event.location,
                lambda text: html.span(text, class_="ms-2 text-fg-muted"),
            ),
            class_="min-w-0 truncate",
        ),
    )
    return draw.event(event, button)
