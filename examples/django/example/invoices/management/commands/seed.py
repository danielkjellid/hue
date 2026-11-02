import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from example.events.models import Entry
from example.invoices.models import Customer, Invoice

_CUSTOMERS = [
    "Contoso Ltd",
    "Northwind Traders",
    "Fabrikam Inc",
    "Adventure Works",
    "Tailspin Toys",
    "Wide World Importers",
    "Litware Inc",
    "Proseware",
]


# The calendar's entries, as days from the Monday of this week and a time,
# so the week you open it on is the busy one whatever the date. A pair of
# days is a whole-day entry, the second being the last day it covers.
_ENTRIES: list[tuple[str, str, tuple[Any, ...], tuple[Any, ...], dict[str, str]]] = [
    (
        "Standup",
        "eng",
        (-14, 9),
        (-14, 9, 15),
        {"repeat": "weekdays", "location": "Huddle room"},
    ),
    (
        "Product sync",
        "product",
        (-14, 10),
        (-14, 10, 45),
        {"repeat": "weekly", "location": "Room 3B"},
    ),
    ("Morning run", "personal", (-13, 7), (-13, 8), {"repeat": "weekly"}),
    ("1:1 with design lead", "product", (-11, 14), (-11, 14, 30), {"repeat": "weekly"}),
    ("Quarterly planning", "product", (-6,), (-5,), {}),
    (
        "Design review: date picker v2",
        "product",
        (1, 13),
        (1, 14, 30),
        {
            "location": "Room 3B",
            "notes": "Walk the range state matrix and the contrast audit.",
        },
    ),
    (
        "Contrast audit",
        "eng",
        (2, 10),
        (2, 12),
        {"notes": "Check every fill step against 4.5:1."},
    ),
    ("Pairing: range selection", "eng", (2, 11), (2, 12, 30), {}),
    ("Token naming workshop", "product", (2, 11, 30), (2, 12, 15), {}),
    ("Release 2.4 freeze", "eng", (3,), (4,), {}),
    ("Dentist", "personal", (3, 15), (3, 15, 45), {}),
    ("Retro", "product", (4, 15), (4, 16), {}),
    ("Deploy window", "eng", (4, 20), (4, 22), {}),
    ("Docs sprint", "eng", (8,), (10,), {}),
    ("Accessibility office hours", "eng", (9, 13), (9, 14), {"repeat": "monthly"}),
    ("Time off", "off", (15,), (19,), {}),
]


def _at(monday: date, when: tuple[Any, ...]) -> datetime:
    days, *clock = when
    return timezone.make_aware(
        datetime.combine(monday + timedelta(days=days), time(*clock))
    )


class Command(BaseCommand):
    help = "Start the database over with the same invoices and events every time."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--count", type=int, default=64)

    def handle(self, *args: Any, count: int, **options: Any) -> None:
        # Seeded, so a bug seen once can be seen again after a reseed.
        chance = random.Random(2050)
        Invoice.objects.all().delete()
        Customer.objects.all().delete()
        customers = Customer.objects.bulk_create(
            Customer(name=name) for name in _CUSTOMERS
        )
        start = date(2026, 1, 5)
        Invoice.objects.bulk_create(
            Invoice(
                reference=f"INV-{2000 + number}",
                customer=chance.choice(customers),
                amount=Decimal(chance.randrange(4000, 480000)) / 100,
                status=chance.choice(Invoice.Status.values),
                issued_on=start + timedelta(days=number * 3),
            )
            for number in range(count)
        )
        self.stdout.write(f"Seeded {count} invoices for {len(customers)} customers.")

        Entry.objects.all().delete()
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        Entry.objects.bulk_create(
            Entry(
                title=title,
                layer=layer,
                all_day=len(starts) == 1,
                starts=_at(monday, starts),
                ends=_at(monday, ends),
                **extra,
            )
            for title, layer, starts, ends, extra in _ENTRIES
        )
        self.stdout.write(f"Seeded {len(_ENTRIES)} events around this week.")
