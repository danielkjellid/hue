"""
The declared table against a real database: the queries it makes, and
what an action is allowed to touch.
"""

import re
from typing import Any

from django.test import Client

from example.invoices.models import Invoice

_AJAX = {"HTTP_X_ALPINE_REQUEST": "true"}


def _references(html: str) -> list[str]:
    return re.findall(r">(INV-\d+)<", html)


def _read(**params: str) -> str:
    response = Client().get("/billing/", params, **_AJAX)
    assert response.status_code == 200
    return response.content.decode()


def _act(action: str, **posted: Any) -> Any:
    return Client().post(f"/billing/invoices/{action}/", posted, **_AJAX)


def test_the_page_draws_the_table(invoices):
    response = Client().get("/billing/")
    assert response.status_code == 200
    assert _references(response.content.decode()) == [
        "INV-4",
        "INV-3",
        "INV-2",
        "INV-1",
    ]


def test_the_rows_come_back_in_the_order_asked(invoices):
    assert _references(_read(sort="amount")) == ["INV-4", "INV-3", "INV-2", "INV-1"]
    assert _references(_read(sort="-amount")) == ["INV-1", "INV-2", "INV-3", "INV-4"]


def test_an_order_no_column_offers_is_ignored(invoices):
    # Handed to order_by as it stood, this would be a FieldError, and an
    # order on a field the table never shows.
    assert _references(_read(sort="archived")) == _references(_read())


def test_a_filter_and_a_search_narrow_together(invoices):
    assert _references(_read(status="paid", q="contoso")) == ["INV-3", "INV-1"]


def test_a_number_that_is_not_one_narrows_nothing(invoices):
    assert len(_references(_read(min="lots"))) == 4
    assert _references(_read(min="1000", sort="amount")) == ["INV-2", "INV-1"]


def test_a_page_past_the_last_is_the_last(invoices):
    Invoice.objects.bulk_create(
        Invoice(
            reference=f"INV-{number}",
            customer=invoices["INV-1"].customer,
            amount=1,
            status=Invoice.Status.PAID,
            issued_on=invoices["INV-1"].issued_on,
        )
        for number in range(5, 13)
    )
    # Twelve rows, ten to a page.
    assert len(_references(_read(page="999999999999999999999"))) == 2


def test_an_action_touches_only_rows_the_reader_could_see(invoices):
    # INV-2 is a draft and the table was filtered to paid ones, so no
    # checkbox on the page could have posted it.
    picked = [invoices["INV-1"].pk, invoices["INV-2"].pk]
    response = _act("archive", selected=picked, status="paid")
    assert response.status_code == 200
    archived = set(
        Invoice.objects.filter(archived=True).values_list("reference", flat=True)
    )
    assert archived == {"INV-1"}


def test_an_id_the_key_cannot_hold_picks_nothing(invoices):
    response = _act("archive", selected=["abc", invoices["INV-1"].pk])
    assert response.status_code == 200
    assert not Invoice.objects.filter(archived=True).exists()


def test_an_action_answers_in_the_state_it_was_done_in(invoices):
    response = _act("paid", selected=[invoices["INV-2"].pk], sort="amount")
    html = response.content.decode()
    assert Invoice.objects.get(reference="INV-2").status == Invoice.Status.PAID
    assert _references(html) == ["INV-4", "INV-3", "INV-2", "INV-1"]
    assert 'aria-sort="ascending"' in html


def test_an_action_the_table_does_not_have_is_not_found(invoices):
    assert _act("delete", selected=[invoices["INV-1"].pk]).status_code == 404


def test_the_rows_are_counted_and_sliced_in_the_database(
    invoices, django_assert_num_queries
):
    # One count and one page. A table that walked the queryset to find out
    # how long it is would make one query and read every row.
    with django_assert_num_queries(2):
        _read()


def test_an_action_says_what_it_did(invoices):
    # Counted from what the handler changed, which is the narrowed list and
    # not whatever was posted.
    picked = [invoices["INV-1"].pk, invoices["INV-2"].pk]
    html = _act("archive", selected=picked, status="paid").content.decode()
    assert "Archived 1 invoice" in html
    assert "Archived 2 invoices" not in html
