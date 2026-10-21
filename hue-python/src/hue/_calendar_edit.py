"""
What a declared calendar edits with: the dialog's fields, how they become an
Event, the popover's actions and the Undo a change offers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, replace
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import Any, NamedTuple

from htmy import html

from hue._calendar_state import (
    DELETE,
    DIALOG,
    MOVE,
    OVERLAPS,
    SAVE,
    BoundCalendar,
    CalendarState,
    Layer,
    overlap_id,
    read_clock,
    read_day,
    slot_id,
    zone_of,
)
from hue._declared import carried, csrf
from hue.formats import Formats
from hue.js import Expression, ajax, close, unsafe
from hue.types.core import ComponentType
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import TextInput
from hue.ui.atoms.native_select import NativeSelect
from hue.ui.atoms.switch import Switch
from hue.ui.atoms.textarea import Textarea
from hue.ui.molecules._calendar_views import FIRST, LAST, stamps
from hue.ui.molecules.calendar import Event
from hue.ui.molecules.date_input import DateInput, TimeInput
from hue.ui.molecules.dialog import Dialog
from hue.ui.molecules.form import Form
from hue.utils import render_if, render_when

# A new event with no time of its own starts at nine, and a new event
# runs an hour unless that would take it past the end of its day.
_NEW_STARTS = time(9)
_NEW_LASTS = timedelta(hours=1)

# The most days an event may run, a year, which is also the longest view.
# A draft past that would have events() asked for thousands of days at
# every change of a field.
_LONGEST = 366


@dataclass(frozen=True, slots=True)
class Posted:
    """
    The dialog's fields as the form posts them, every one text, so that a
    value that cannot be read is an error on its field and never a 422
    nobody drew. Each is posted under the key, like the state, so a page
    parameter called title is nobody's business but the page's.
    """

    id: str = ""
    title: str = ""
    all_day: str = ""
    starts: str = ""
    starts_time: str = ""
    ends: str = ""
    ends_time: str = ""
    layer: str = ""
    location: str = ""
    notes: str = ""
    repeat: str = ""
    # Set by Duplicate, which saves with no dialog open to keep a failure in.
    copy: str = ""
    # When the occurrence the reader took hold of started, as its button
    # stamps it, which tells it from the rest of a series.
    occurrence: str = ""
    # Set on the request an Undo makes, whose own toast offers no undo.
    undo: str = ""


FIELDS = tuple(each.name for each in fields(Posted))


def _exists(moment: datetime, zone: tzinfo) -> bool:
    """
    Whether a naive time is one the clocks in zone show that day. The hour
    they skip going forward is not, and zoneinfo would answer for it with
    the hour after and say nothing.
    """
    aware = moment.replace(tzinfo=zone)
    return aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == moment


# What a toast says once a change has been made.
_DONE = {
    "Create": "Created",
    "Save": "Saved",
    "Delete": "Deleted",
    "Move": "Moved",
    "Resize": "Resized",
}


class Undo(NamedTuple):
    """
    Which action an Undo posts to, and the fields it posts, under the key.
    """

    action: str
    fields: Mapping[str, str | None]


def said(verb: str, named: str, series: bool, *, undone: bool) -> str:
    """
    The toast's title. A series is said to move or go as a whole, since
    the app's save and delete are handed the one event the series is.
    """
    if undone:
        return f'{"Removed" if verb == "Delete" else "Restored"} "{named}"'
    if series and verb == "Move":
        return f'Moved all occurrences of "{named}"'
    if series and verb == "Delete":
        return f'Deleted "{named}" and its occurrences'
    return f'{_DONE[verb]} "{named}"'


def id_of(made: Any) -> str | None:
    """
    The id a save handler returned for a new event, as the id, the Event
    it saved or nothing. A bool is a yes, not an id.
    """
    if isinstance(made, Event):
        return made.id
    if isinstance(made, str | int) and not isinstance(made, bool):
        return str(made)
    return None


def undo_create(bound: BoundCalendar, draft: Event, made: str | None) -> Undo | None:
    if made is None:
        return None
    param = bound.declaration.param
    return Undo(DELETE, {param("id"): made, param("title"): draft.title})


def undo_delete(bound: BoundCalendar, was: Event | None) -> Undo | None:
    if was is None:
        return None
    param = bound.declaration.param
    fields = {
        **_fields(bound, _first(was)),
        param("id"): None,
        param("occurrence"): None,
    }
    return Undo(SAVE, fields)


def undo_save(bound: BoundCalendar, was: Event) -> Undo:
    """
    An edit put back: the fields events() had, a series from its first
    occurrence.
    """
    return Undo(SAVE, _fields(bound, _first(was)))


def undo_move(bound: BoundCalendar, was: Event, landed: Event) -> Undo:
    """
    A move put back: the times events() had, a series from its first
    occurrence, posted for the occurrence where the event landed.
    """
    param = bound.declaration.param
    fields = {
        **_when_fields(bound, _first(was)),
        param("id"): was.id,
        param("occurrence"): stamps(landed, bound.formats)[0],
    }
    return Undo(MOVE, fields)


def landing(bound: BoundCalendar, wanted: Event) -> Event | None:
    """
    The event focus lands on once the calendar is back: the one with this
    id, or this title for one save has not named, that starts where wanted
    does, else the first of them drawn.
    """
    same = [
        event
        for event in bound.events
        if (event.id == wanted.id if wanted.id else event.title == wanted.title)
    ]
    starts = stamps(wanted, bound.formats)[0]
    exact = (event for event in same if stamps(event, bound.formats)[0] == starts)
    return next(exact, same[0] if same else None)


def _first(event: Event) -> Event:
    """
    The event as it is stored: an occurrence of a series as its first one,
    anything else as it is.
    """
    first: Any = event.series_starts
    if first is None:
        return event
    ends = None if event.ends is None else first + (event.ends - event.starts)  # type: ignore[operator]
    return replace(event, starts=first, ends=ends)


def series_moved(
    was: Event, starts: Any, ends: Any, formats: Formats
) -> tuple[date | datetime, date | datetime] | None:
    """
    Where one occurrence of a series put at starts to ends puts the series:
    its first occurrence as many days on, at the new time of day and as
    long. Anything that is not a series goes where it was put. None when
    that first occurrence would start or end in an hour the clocks skip,
    which the occurrence that was moved was checked against for its own day
    only.
    """
    first = was.series_starts
    if first is None:
        return starts, ends
    moved = starts.date() if isinstance(starts, datetime) else starts
    day = formats.moment(first).date() if isinstance(first, datetime) else first
    day += moved - was.span(formats)[0]
    begins: Any = (
        datetime.combine(day, starts.time()) if isinstance(starts, datetime) else day
    )
    finishes = begins + (ends - starts)
    zone = zone_of(formats)
    if isinstance(begins, datetime) and zone is not None:
        if not (_exists(begins, zone) and _exists(finishes, zone)):
            return None
    return begins, finishes


# Why a series is refused when its first occurrence would land in that hour.
SERIES_SKIPPED = (
    "The series would start in an hour that is skipped when the clocks go forward."
)


def undo_button(
    bound: BoundCalendar,
    undo: Undo,
) -> Button:
    """
    The toast's Undo: the same route, told it is undoing, and the toast
    dismissed once it has been pressed. The answer says where focus goes,
    since the toast that had it is gone.
    """
    declared = bound.declaration
    request = ajax(
        bound.urls.act[undo.action],
        method="post",
        target=slot_id(bound.key),
        body={
            **dict(bound.query(bound.state)),
            **undo.fields,
            declared.param("undo"): "1",
        },
    )
    return (
        Button()
        .variant("outline")
        .size("xs")
        .content("Undo")
        .x_on("click", unsafe(f"{request}; dismiss()"))
    )


def when_posted(
    posted: Posted, errors: dict[str, str], zone: tzinfo | None
) -> tuple[date | datetime | None, date | datetime | None]:
    """
    When the posted fields say the event is, adding what is wrong with
    them to errors: whole days when all day is on, naive moments in the
    reader's time otherwise. A timed event has to end after it starts; a
    whole-day one may end on the day it starts. Neither runs past a year.
    """
    all_day = bool(posted.all_day)
    first = _drawn_day(posted.starts, "starts", errors)
    last = _drawn_day(posted.ends, "ends", errors)
    starts: date | datetime | None = first
    ends: date | datetime | None = last
    if not all_day:
        starts, ends = _clocked(first, last, posted, errors, zone)
    if starts is None or ends is None:
        return starts, ends
    if ends < starts:
        errors["ends" if all_day else "ends_time"] = "Ends before it starts."
    elif ends == starts and not all_day:
        errors["ends_time"] = "Starts and ends at the same time."
    elif first is not None and last is not None and (last - first).days > _LONGEST:
        errors["ends"] = "Ends more than a year after it starts."
    return starts, ends


def _drawn_day(text: str, name: str, errors: dict[str, str]) -> date | None:
    """
    A posted date a calendar can draw, or None with what is wrong with it
    in errors. Clamped here, which also keeps a moment in year 1 from
    overflowing when it is made aware.
    """
    day = read_day(text)
    if day is None:
        errors[name] = "Enter a date."
    elif not FIRST <= day <= LAST:
        errors[name] = f"Enter a date in the years {FIRST.year} to {LAST.year}."
        return None
    return day


def _clocked(
    first: date | None,
    last: date | None,
    posted: Posted,
    errors: dict[str, str],
    zone: tzinfo | None,
) -> tuple[datetime | None, datetime | None]:
    """
    The moments a timed event's fields say, adding what is wrong with the
    times to errors.

    With a zone, a time the clocks skip that day is refused rather than
    moved: made aware, 02:30 the night they go forward would come out as
    03:30, and an event typed to run until 03:30 would be no time at all.
    """
    opens, closes = read_clock(posted.starts_time), read_clock(posted.ends_time)
    if opens is None:
        errors["starts_time"] = "Enter a time."
    if closes is None:
        errors["ends_time"] = "Enter a time."
    starts = datetime.combine(first, opens) if first and opens else None
    ends = datetime.combine(last, closes) if last and closes else None
    if zone is None:
        return starts, ends
    skipped = "That time is skipped when the clocks go forward."
    if starts is not None and not _exists(starts, zone):
        errors["starts_time"] = skipped
        starts = None
    if ends is not None and not _exists(ends, zone):
        errors["ends_time"] = skipped
        ends = None
    return starts, ends


def prefilled(posted: Posted, asked: CalendarState, layers: Sequence[Layer]) -> Posted:
    """
    What a new event starts with where the request said nothing: the day
    the view is around, nine o'clock when no time was given, an hour that
    stops at the end of its day, and the first layer.
    """
    filled = posted
    if not posted.starts:
        filled = replace(filled, starts=asked.date.isoformat())
    if not filled.all_day and not filled.starts_time:
        filled = replace(filled, starts_time=_NEW_STARTS.strftime("%H:%M"))
    if not filled.ends:
        filled = replace(filled, ends=filled.starts)
    starts, opens = read_day(filled.starts), read_clock(filled.starts_time)
    if not filled.all_day and not filled.ends_time and starts and opens:
        later = datetime.combine(starts, opens) + _NEW_LASTS
        closes = time(23, 59) if later.date() != starts else later.time()
        filled = replace(filled, ends_time=closes.strftime("%H:%M"))
    if not posted.layer and layers:
        filled = replace(filled, layer=layers[0].key)
    return filled


def _fields(bound: BoundCalendar, event: Event) -> dict[str, str | None]:
    """
    An event as the dialog's fields, under the key, for the popover's
    actions to post and an Undo to post back.
    """
    given = {
        "id": event.id,
        "occurrence": stamps(event, bound.formats)[0],
        "title": event.title,
        "layer": event.layer,
        "location": event.location,
        "notes": event.notes,
        "repeat": event.repeat,
    }
    return {
        **{bound.declaration.param(name): value for name, value in given.items()},
        **_when_fields(bound, event),
    }


def _when_fields(bound: BoundCalendar, event: Event) -> dict[str, str | None]:
    """
    When an event is, as the dialog's fields under the key.
    """
    if event.timed:
        starts, ends = event.moments(bound.formats)
        when = {
            "starts": starts.date().isoformat(),
            "starts_time": starts.strftime("%H:%M"),
            "ends": ends.date().isoformat(),
            "ends_time": ends.strftime("%H:%M"),
        }
    else:
        first, last = event.span(bound.formats)
        when = {"all_day": "1", "starts": first.isoformat(), "ends": last.isoformat()}
    return {bound.declaration.param(name): value for name, value in when.items()}


def dialog(
    bound: BoundCalendar,
    posted: Posted,
    errors: Mapping[str, str],
    *,
    csrf_token: str,
) -> ComponentType:
    """
    The event dialog, open, over the posted fields: a new event, or an
    existing one when they carry an id. The form carries the
    framework's CSRF token, so it still posts where the script has
    failed and the browser submits it on its own.
    """
    declared, key = bound.declaration, bound.key
    editing = bool(posted.id)
    all_day = bool(posted.all_day)
    form_id = f"{key}-form"
    layers = [(layer.key, layer.name) for layer in declared.layers]
    week_start = bound.state.week_start
    # The controls are named under the key, which is also what makes
    # their ids the calendar's own on a page with two of them.
    param = declared.param

    def when(label: str, name: str) -> list[ComponentType]:
        day = read_day(getattr(posted, name))
        moment = read_clock(getattr(posted, f"{name}_time"))
        day_field = DateInput().name(param(name)).label(label)
        day_field.week_start(week_start)
        time_field = TimeInput().name(param(f"{name}_time")).label(f"{label} at")
        if day is not None:
            day_field.value(day)
        if moment is not None:
            time_field.value(moment)
        # Hidden rather than removed while all day is on, so the times
        # come back when it is switched off again. The route ignores
        # them for a whole-day event.
        return [day_field, html.div(time_field, **{"x-show": "!allDay"})]

    form = (
        Form()
        .id(form_id)
        .action(bound.urls.act[SAVE])
        .method("post")
        .errors({param(name): message for name, message in errors.items()})
        .class_("gap-4")
        .content(
            *carried(bound.query(bound.state)),
            csrf(declared, csrf_token),
            *carried(
                [(param("id"), posted.id), (param("occurrence"), posted.occurrence)]
                if editing
                else []
            ),
            _title_field(param("title"), posted.title),
            Switch()
            .name(param("all_day"))
            .label("All day")
            .checked(all_day)
            .x_model(unsafe("allDay")),
            html.div(
                *when("Starts", "starts"),
                *when("Ends", "ends"),
                class_="grid grid-cols-2 gap-3",
            ),
            render_when(
                bool(layers or declared.repeats),
                html.div(
                    render_when(
                        bool(layers),
                        NativeSelect()
                        .name(param("layer"))
                        .label("Calendar")
                        .options(layers)
                        .value(posted.layer or (layers[0][0] if layers else "")),
                    ),
                    render_when(
                        bool(declared.repeats),
                        NativeSelect()
                        .name(param("repeat"))
                        .label("Repeat")
                        .options([("", "Does not repeat"), *declared.repeats.items()])
                        .value(posted.repeat),
                    ),
                    class_="grid grid-cols-2 gap-3",
                ),
            ),
            TextInput()
            .name(param("location"))
            .label("Location")
            .value(posted.location)
            .placeholder("Room, address or link")
            .leading_icon(HueIcon("map-pin")),
            Textarea().name(param("notes")).label("Notes").value(posted.notes).rows(3),
            # Where the overlap warning lands, and announced when it
            # does, since it arrives while the reader is elsewhere.
            html.div(id=overlap_id(key), role="status"),
        )
    )
    form.x_data(f"{{ allDay: {json.dumps(all_day)} }}")
    # Asked again whenever a field settles, which the date and time
    # fields announce as a change once a value is read.
    form._attrs["x-on:change.debounce.200ms"] = _overlaps_check(bound)
    # Neither has a modifier. The route says what is wrong, on the
    # field, so the browser's own bubbles are not a second opinion.
    form._attrs.update({"x-target": slot_id(key), "novalidate": True})
    footer = [
        # Built only where there is a delete route to point it at.
        render_if(
            bound.urls.act.get(DELETE) if editing else None,
            lambda url: Button()
            .variant("ghost")
            .type("submit")
            .form(form_id)
            .formaction(url)
            .class_("me-auto text-danger-text")
            .content("Delete"),
        ),
        Button().variant("ghost").content("Cancel").x_on("click", close()),
        Button()
        .variant("primary")
        .type("submit")
        .form(form_id)
        .content("Save changes" if editing else "Save event"),
    ]
    return (
        Dialog()
        .open()
        .size("lg")
        .title("Edit event" if editing else "New event")
        .content(form)
        .footer(*footer)
    )


def _title_field(name: str, value: str) -> ComponentType:
    """
    The title, which the dialog opens on. The attribute is autofocus itself
    rather than x-autofocus alone: the focus trap reads the one and Alpine
    AJAX the other, and the dialog is only ever fetched, never on a page as
    it loads, so the attribute cannot steal focus there.
    """
    field = (
        TextInput()
        .name(name)
        .label("Title")
        .value(value)
        .placeholder("Design review")
        .autocomplete("off")
        .required()
        .x_autofocus()
    )
    field._attrs["autofocus"] = True
    return field


def _overlaps_check(bound: BoundCalendar) -> str:
    """
    The request the dialog makes when a field settles: the form as it
    stands, answered with the warning or with nothing.
    """
    url, target = bound.urls.act[OVERLAPS], overlap_id(bound.key)
    return (
        f"$ajax({json.dumps(url)}, {{ method: 'post', target: {json.dumps(target)}, "
        f"body: new FormData($el) }})"
    )


def overlap_warning(found: list[Event], formats: Formats) -> ComponentType:
    """
    Which events the draft overlaps, two by name and the rest counted, or
    nothing. A warning rather than a refusal: two meetings at once is a
    choice the reader may be making on purpose.
    """
    if not found:
        return ""

    def named(event: Event) -> str:
        starts, ends = event.moments(formats)
        return (
            f"{event.title} ({starts.strftime(formats.time)} to "
            f"{ends.strftime(formats.time)})"
        )

    text = " and ".join(named(event) for event in found[:2])
    if len(found) > 2:
        text += f" and {len(found) - 2} more"
    return html.p(
        HueIcon("triangle-alert").class_("mt-0.5 size-4 flex-none"),
        html.span(f"Overlaps {text}."),
        class_="flex items-start gap-2 text-sm text-warning-text",
    )


def event_actions(bound: BoundCalendar, event: Event) -> list[ComponentType]:
    """
    The popover's buttons: Edit opens the dialog over the event's fields,
    Duplicate saves a copy of them, Delete removes it. Each posts the state
    too, so the calendar comes back as it was.
    """
    declared = bound.declaration
    slot = slot_id(bound.key)
    carried: dict[str, Any] = dict(bound.query(bound.state))
    fields = {**carried, **_fields(bound, event)}

    def then_close(expression: Expression) -> Expression:
        # The popover first, which hands focus back to the event, so the
        # dialog that follows has somewhere to return it.
        return unsafe(f"{close()}; {expression}")

    actions: list[ComponentType] = []
    if declared.save is not None:
        actions.append(
            Button()
            .variant("outline")
            .size("sm")
            .content(HueIcon("pencil"), "Edit")
            .x_on(
                "click",
                then_close(
                    ajax(
                        bound.urls.act[DIALOG], method="post", target=slot, body=fields
                    )
                ),
            )
        )
        actions.append(
            Button()
            .variant("ghost")
            .size("sm")
            .content(HueIcon("copy"), "Duplicate")
            .x_on(
                "click",
                then_close(
                    ajax(
                        bound.urls.act[SAVE],
                        method="post",
                        target=slot,
                        # A copy of this occurrence alone, with a title that
                        # says so, the way the design duplicates.
                        body={
                            **fields,
                            declared.param("id"): None,
                            declared.param("repeat"): None,
                            declared.param("title"): f"{event.title} (copy)",
                            declared.param("copy"): "1",
                        },
                    )
                ),
            )
        )
    if declared.delete is not None and event.id is not None:
        actions.append(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Delete event")
            .class_("ms-auto")
            .content(HueIcon("trash-2"))
            .x_on(
                "click",
                then_close(
                    # The whole event, so the Undo can save it back.
                    ajax(
                        bound.urls.act[DELETE], method="post", target=slot, body=fields
                    )
                ),
            )
        )
    return actions
