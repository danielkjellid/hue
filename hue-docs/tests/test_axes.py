"""
Guard against controls that do nothing.

The playground and the variant grids are generated from a component's Literal
and bool modifiers, so a modifier that renders the same thing for every value
becomes a control the reader can click with no effect. It reads as a broken
page rather than as a component with nothing to show.
"""

from __future__ import annotations

import pytest

from hue_docs.discovery import ComponentDoc, discover
from hue_docs.registry import example_instance
from hue_docs.render import render_html_sync


def _renderings(doc: ComponentDoc, method: str, values: list[object]) -> set[str]:
    out = set()
    for value in values:
        instance = example_instance(doc)
        getattr(instance, method)(value)
        out.add(render_html_sync(instance))
    return out


@pytest.mark.parametrize("doc", discover(), ids=lambda doc: doc.name)
def test_every_axis_changes_the_example(doc: ComponentDoc) -> None:
    for axis in doc.axes:
        values = list(axis.values) if axis.kind == "enum" else [False, True]
        renderings = _renderings(doc, axis.method, values)
        assert len(renderings) > 1, (
            f"{doc.name}.{axis.method} renders identically for every value of "
            f"{values}, so its control does nothing. Either give the modifier "
            f"an effect the example can show, or take the Literal/bool out of "
            f"its signature so the docs stop offering it as a knob."
        )
