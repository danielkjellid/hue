"""
The state a declared table reads off a request and writes back into every
URL it builds. The routes and the drawing are tested against a real Django
view in hue-django; this is the value on its own.
"""

import pytest

from hue.datatable import Filter, TableState


def _state() -> TableState:
    return TableState(
        sort="-amount",
        query="n",
        page=3,
        filters={"status": ("paid", "draft"), "min": ("500",)},
        hidden=("customer",),
    )


def test_every_part_of_the_state_is_a_parameter():
    assert _state().params() == {
        "sort": "-amount",
        "q": "n",
        "status": "paid,draft",
        "min": "500",
        "hide": "customer",
        "page": "3",
    }


def test_what_is_not_asked_for_is_left_out():
    assert TableState().params() == {}


def test_changing_the_page_keeps_it():
    assert _state().replace(page=4).page == 4


def test_changing_anything_else_goes_back_to_the_first_page():
    changed = _state().replace(sort="amount")
    assert changed.sort == "amount"
    assert changed.page == 1
    assert changed.query == "n"


def test_without_an_answer_takes_off_only_that_answer():
    assert _state().without("status", "paid").chosen("status") == ("draft",)


def test_without_a_value_takes_off_the_whole_filter():
    left = _state().without("status")
    assert left.chosen("status") == ()
    assert left.value("min") == "500"


def test_a_chip_says_the_option_it_came_from():
    status = Filter("status", "Status", options=[("paid", "Paid")])
    assert status.labelled("paid") == "Paid"


def test_a_typed_answer_is_its_own_label():
    assert Filter("min", "Minimum amount", numeric=True).labelled("500") == "500"


@pytest.mark.parametrize(
    ("declared", "value", "accepted"),
    [
        (Filter("status", "Status", options=[("paid", "Paid")]), "paid", True),
        (Filter("status", "Status", options=[("paid", "Paid")]), "void", False),
        (Filter("min", "Minimum", numeric=True), "1000.50", True),
        (Filter("min", "Minimum", numeric=True), "abc", False),
        (Filter("min", "Minimum", numeric=True), "NaN", False),
        (Filter("q", "Customer"), "Contoso, Ltd", True),
    ],
)
def test_a_filter_says_which_answers_it_accepts(declared, value, accepted):
    assert declared.accepts(value) is accepted


def test_an_option_cannot_hold_the_comma_between_answers():
    # The URL joins a filter's answers with commas, so this one would be
    # read back as two answers nobody offered and never be ticked.
    with pytest.raises(ValueError, match=r"'net,30'.*comma"):
        Filter("terms", "Terms", options=[("net,30", "Net 30")])
