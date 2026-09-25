import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

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


class Command(BaseCommand):
    help = "Start the database over with the same invoices every time."

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
