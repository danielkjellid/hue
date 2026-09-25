from datetime import date
from decimal import Decimal

import pytest

from example.invoices.models import Customer, Invoice


@pytest.fixture
def invoices(db: None) -> dict[str, Invoice]:
    """
    Four invoices, two paid and two drafts, known by reference.
    """
    contoso = Customer.objects.create(name="Contoso Ltd")
    northwind = Customer.objects.create(name="Northwind Traders")
    made = [
        Invoice(reference="INV-1", customer=contoso, amount=Decimal("2190.00"),
                status=Invoice.Status.PAID, issued_on=date(2026, 3, 1)),
        Invoice(reference="INV-2", customer=northwind, amount=Decimal("1200.00"),
                status=Invoice.Status.DRAFT, issued_on=date(2026, 3, 2)),
        Invoice(reference="INV-3", customer=contoso, amount=Decimal("840.00"),
                status=Invoice.Status.PAID, issued_on=date(2026, 3, 3)),
        Invoice(reference="INV-4", customer=northwind, amount=Decimal("415.00"),
                status=Invoice.Status.DRAFT, issued_on=date(2026, 3, 4)),
    ]
    Invoice.objects.bulk_create(made)
    return {invoice.reference: invoice for invoice in Invoice.objects.all()}
