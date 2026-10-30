"""
Regressions in the frames a table or a pager sits in: a pager in a parent
sized to it, and a Card or a Panel in a row or holding a long table.
"""

import pytest
from htmy import html

from hue.ui import Card, CardBody
from tests.browser.conftest import Show
from tests.browser.test_data_navigation_promises import _coarse
from tests.browser.test_layout_promises import _pager

# Pagination.


# A parent sized to its content, which gives the pager the width of its
# own content rather than none.
_SHRINKING = {
    "fit": lambda pager: html.div(pager, class_="w-fit"),
    "centred": lambda pager: html.div(pager, class_="mx-auto w-fit"),
    "pushed": lambda pager: html.div(html.div(pager, class_="ml-auto"), class_="flex"),
    "card": lambda pager: html.div(
        Card().content(CardBody().content(pager)), class_="flex"
    ),
}


@pytest.mark.parametrize("parent", list(_SHRINKING))
@pytest.mark.parametrize("width", [390, 1440])
def test_a_pager_keeps_its_width_in_a_parent_sized_to_it(
    show: Show, parent: str, width: int
) -> None:
    page = show(_SHRINKING[parent](_pager()), width=width)
    if width == 390:
        _coarse(page)
    assert page.evaluate("document.querySelector('nav').offsetWidth") > 200
    tops = page.evaluate(
        "new Set([...document.querySelectorAll('nav > *')]"
        ".filter((child) => child.checkVisibility())"
        ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
    )
    assert tops == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width
