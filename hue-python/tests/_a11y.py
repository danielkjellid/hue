"""Accessibility-focused assertion helpers for component tests.

These parse the rendered HTML and assert on structure/attributes instead of
brittle substring matching. Shared across the per-component test modules, so
each conditional branch and ARIA invariant can be asserted in one readable call.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def select(html: str, selector: str) -> list[Tag]:
    return soup(html).select(selector)


def assert_selector(html: str, selector: str, *, count: int | None = None) -> None:
    """At least one (or exactly *count*) element matches *selector*."""
    matches = select(html, selector)
    if count is None:
        assert matches, f"expected an element matching {selector!r}, found none"
    else:
        assert len(matches) == count, (
            f"expected {count} element(s) matching {selector!r}, found {len(matches)}"
        )


def assert_no_selector(html: str, selector: str) -> None:
    """No element matches *selector* — the 'absent' branch of a conditional."""
    matches = select(html, selector)
    assert not matches, (
        f"expected no element matching {selector!r}, found {len(matches)}"
    )


def assert_attr(html: str, selector: str, attr: str, value: str | None = None) -> None:
    """First element matching *selector* has *attr* (optionally equal to *value*)."""
    matches = select(html, selector)
    assert matches, f"expected an element matching {selector!r}, found none"
    el = matches[0]
    assert el.has_attr(attr), f"{selector!r} is missing attribute {attr!r}"
    if value is not None:
        assert el[attr] == value, (
            f"{selector!r} has {attr}={el[attr]!r}, expected {value!r}"
        )


def assert_label_for(html: str, control_id: str) -> None:
    """A ``<label for=control_id>`` exists and a control with that id exists."""
    doc = soup(html)
    assert doc.select_one(f'label[for="{control_id}"]'), (
        f"no <label for={control_id!r}>"
    )
    assert doc.select_one(f'[id="{control_id}"]'), f"no element with id={control_id!r}"
