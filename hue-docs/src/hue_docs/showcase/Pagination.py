"""
Curated showcases for the Pagination molecule.

The auto-grid has nothing to toggle; what matters is what the control does
at the ends of the range and when there is only one page.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            'Always paired with a record count: "page 3 of 7" without "148 '
            'records" leaves nobody able to tell whether their filter did '
            "anything. A step with nowhere to go stays in the row and stays "
            "announced, because a control that disappears at the ends teaches "
            "nobody where the ends are."
        ),
        variants=[
            variant(
                "In the middle",
                "Pagination().page(8).total_pages(15).total_records(148)",
            ),
            variant(
                "At the start",
                "Pagination().page(1).total_pages(15).total_records(148)",
            ),
            variant(
                "As links",
                "(\n"
                "    Pagination()\n"
                "    .page(3)\n"
                "    .total_pages(7)\n"
                "    .total_records(68)\n"
                '    .href(lambda page: f"?page={page}")\n'
                ")",
            ),
            variant(
                "One page",
                "Pagination().page(1).total_pages(1).total_records(10)",
            ),
        ],
    ),
]
