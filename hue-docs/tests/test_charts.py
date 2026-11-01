"""
A chart's description is what a screen reader hears in place of the drawing,
so the demo data has to bear it out.
"""

from __future__ import annotations

from hue.ui.molecules.chart import Chart

from hue_docs.pages import COMPONENTS


def test_a_series_said_to_beat_its_comparison_every_time_does() -> None:
    checked = 0
    for page in COMPONENTS:
        for panel in page.panels:
            for example in panel.examples:
                chart = example()
                if not isinstance(chart, Chart):
                    continue
                props = chart._props
                if "compare" not in props or " every " not in props["description"]:
                    continue
                (_, series), (_, compare) = props["series"], props["compare"]
                assert all(a > b for a, b in zip(series, compare, strict=True)), (
                    f"{page.slug}:{example.__name__} says {props['description']!r}"
                )
                checked += 1
    assert checked
