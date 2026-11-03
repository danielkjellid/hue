from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Badge, Table, Timeline, TimelineItem

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def release() -> Timeline:
    return (
        Timeline()
        .aria_label("Release v2.14.0")
        .content(
            TimelineItem()
            .title("Pull request #482 merged")
            .status("complete")
            .time("13:12", "2026-11-03T13:12")
            .content("Add index on invoices.customer_id."),
            TimelineItem()
            .title("Checks passed on main")
            .status("complete")
            .time("13:24", "2026-11-03T13:24")
            .details({"Commit": "3f9c2a1", "Ran": "pytest, mypy, ruff"}),
            TimelineItem()
            .title("Staging deploy failed")
            .status("failed")
            .time("13:51", "2026-11-03T13:51")
            .details({"Step": "Migration 0047", "Error": "Lock wait timeout"}),
            TimelineItem()
            .title("Production deploy")
            .status("current")
            .time("14:32", "2026-11-03T14:32")
            .content("Applying migration 0047_invoice_index."),
            TimelineItem().title("Smoke tests on production").status("upcoming"),
        )
    )


# States


def statuses() -> Timeline:
    return Timeline().content(
        TimelineItem().title("No status"),
        TimelineItem().title("Complete").status("complete"),
        TimelineItem().title("Failed").status("failed"),
        TimelineItem().title("Current").status("current"),
        TimelineItem().title("Upcoming").status("upcoming"),
    )


# Anatomy


def with_badge() -> Timeline:
    return Timeline().content(
        TimelineItem()
        .title("Staging deploy failed")
        .status("failed")
        .time("13:51")
        .content(Badge().variant("solid").content("Failed")),
        TimelineItem().title("Staging deploy succeeded").time("14:08"),
    )


# Dense


def audit_log() -> Timeline:
    return (
        Timeline()
        .dense()
        .aria_label("Audit log")
        .content(
            TimelineItem().title("Role changed to Admin").time("09:42"),
            TimelineItem().title("API key rotated").time("09:15"),
            TimelineItem()
            .title("Sign-in rejected, MFA timeout")
            .status("failed")
            .time("08:58"),
            TimelineItem().title("Invited to workspace").time("08:30"),
        )
    )


# Rail


def order_history() -> Timeline:
    return (
        Timeline()
        .rail()
        .aria_label("Order history")
        .content(
            TimelineItem().title("Order placed").status("complete").time("Mon"),
            TimelineItem().title("Packed and shipped").status("complete").time("Tue"),
            TimelineItem().title("Out for delivery").status("upcoming").time("Thu"),
            TimelineItem().title("Delivered").status("upcoming").time("Fri"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Building a Timeline"),
        pr.p(
            "`Timeline` renders an ordered list, and each `TimelineItem` is one "
            "event in it. The items render in the order given, so sort them "
            "before they reach `content()`. `aria_label()` names the list."
        ),
        pr.code(
            'Timeline().aria_label("Release v2.14.0").content(\n'
            '    TimelineItem().title("Checks passed").status("complete"),\n'
            '    TimelineItem().title("Production deploy").status("current"),\n'
            '    TimelineItem().title("Smoke tests").status("upcoming"),\n'
            ")"
        ),
        pr.h2("Status of a TimelineItem"),
        pr.p(
            "A `TimelineItem` without `status()` is a plain event, such as an "
            "entry in a log. It has a small muted dot for a marker, and a screen "
            "reader hears its title with nothing before it."
        ),
        pr.p(
            "`status()` makes the item a step in a process instead. Its marker "
            "changes fill and glyph with the status, and the status is read "
            "before the title. The line under a complete step or a plain event "
            "is solid, and the line under any other step is dashed."
        ),
        pr.h2("Content and details of a TimelineItem"),
        pr.p(
            "Whatever is passed to `content()` renders under the title in muted text."
        ),
        pr.p(
            "`details()` takes a mapping of labels to values. It turns the title "
            "into a button that shows them as a description list under the title "
            "and content. Outside a rail, once any item in a `Timeline` has "
            "details, every other item keeps room for the chevron, so the times "
            "stay in one column."
        ),
        pr.code(
            'TimelineItem().title("Staging deploy failed").status("failed")'
            ".details(\n"
            '    {"Step": "Migration 0047", "Error": "Lock wait timeout"}\n'
            ")"
        ),
        pr.h2("Dense and rail Timelines"),
        pr.p(
            "`dense()` shrinks the markers to 12px and sets the titles a step "
            "smaller. A complete marker drops its check there, and a failed one "
            "keeps a smaller cross. `rail()` moves each time out of the "
            "title row into a column at the start."
        ),
    )


PAGE = ComponentPage(
    Timeline,
    lede=(
        "A Timeline is an ordered list of events with a marker for each, for "
        "steps or activity read in the order they happened. An item is a plain "
        "event, or a step whose marker shows whether it is complete, current, "
        "upcoming or failed, and it can open a list of details under its title."
    ),
    usage=_usage,
    panels=[
        panel("Live", release, layout="stack"),
        panel("States", statuses, layout="stack"),
        panel("Anatomy", with_badge, layout="stack"),
        panel("Dense", audit_log, layout="stack"),
        panel("Rail", order_history, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The `Timeline` is an `ol`, so a screen reader counts the steps and "
            "reads them in order.",
        ),
        Note(
            "a11y",
            "Markers and connectors are `aria-hidden`. A step's status is read "
            'as a visually hidden prefix such as "Failed:", the current step '
            'carries `aria-current="step"` instead, and a plain event has no '
            "prefix.",
        ),
        Note(
            "a11y",
            "An item with `details()` has a `button` with `aria-expanded` and "
            "`aria-controls` pointing at its list. Enter and Space toggle it.",
        ),
    ],
    parts=[TimelineItem],
    related=[Table],
)
