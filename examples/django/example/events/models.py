from datetime import UTC, date, datetime, time

from django.db import models
from django.utils import timezone
from hue.ui import Event


class Entry(models.Model):
    """
    Something on the calendar, or the first of a series of them.

    A whole-day entry keeps midnight at both ends, the end being the last
    day it covers, which is how an Event spells one. A series keeps its
    first occurrence and the rule; the rest are worked out when asked for.
    """

    class Layer(models.TextChoices):
        PRODUCT = "product", "Product"
        ENGINEERING = "eng", "Engineering"
        PERSONAL = "personal", "Personal"
        TIME_OFF = "off", "Time off"

    class Repeat(models.TextChoices):
        DAILY = "daily", "Every day"
        WEEKDAYS = "weekdays", "Every weekday"
        WEEKLY = "weekly", "Every week"
        MONTHLY = "monthly", "Every month"

    title = models.CharField(max_length=120)
    layer = models.CharField(max_length=10, choices=Layer.choices)
    all_day = models.BooleanField(default=False)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    repeat = models.CharField(max_length=10, choices=Repeat.choices, blank=True)
    location = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.title

    def event(self, starts: datetime, ends: datetime) -> Event:
        """
        One occurrence, at the moments given, as the calendar draws it,
        saying where its series starts, which a move shifts from.
        """
        first = timezone.localtime(self.starts) if self.repeat else None
        return Event(
            self.title,
            starts.date() if self.all_day else starts,
            ends.date() if self.all_day else ends,
            id=str(self.pk),
            location=self.location or None,
            notes=self.notes or None,
            repeat=self.repeat or None,
            layer=self.layer,
            series_starts=first.date() if first and self.all_day else first,
        )

    @classmethod
    def fields_of(cls, event: Event) -> dict[str, object]:
        """
        What the dialog's Event says, as the columns of one of these.
        """
        return {
            "title": event.title,
            "layer": event.layer or cls.Layer.PRODUCT,
            "all_day": not event.timed,
            "starts": _aware(event.starts),
            "ends": _aware(event.ends or event.starts),
            "repeat": event.repeat or "",
            "location": event.location or "",
            "notes": event.notes or "",
        }


def _aware(moment: date | datetime) -> datetime:
    """
    The dialog posts naive moments in the current timezone, and a whole day
    as a date; the column holds an aware moment either way.
    """
    if not isinstance(moment, datetime):
        moment = datetime.combine(moment, time.min)
    if timezone.is_aware(moment):
        return moment
    aware = timezone.make_aware(moment)
    # A time the clocks skip going forward is not one. zoneinfo answers for
    # it with the hour after and says nothing, which is said here instead;
    # the calendar refuses it before it gets this far.
    if timezone.localtime(aware.astimezone(UTC)).replace(tzinfo=None) != moment:
        raise ValueError(
            f"{moment:%H:%M} is skipped on {moment:%Y-%m-%d} in "
            f"{timezone.get_current_timezone_name()}, when the clocks go forward."
        )
    return aware
