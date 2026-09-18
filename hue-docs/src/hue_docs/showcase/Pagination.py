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
            "nobody where the ends are. A single page keeps the control and "
            "makes all of it inert, because a row that vanishes when a filter "
            "narrows the list reads as something breaking. A list too long or "
            "too live to count pages through steps by cursor instead: the "
            "same bar, two steps, and no claim about how many pages there are."
        ),
        variants=[
            variant(
                "Numbered",
                "(\n"
                "    Pagination()\n"
                "    .page(8)\n"
                "    .total_pages(15)\n"
                "    .total_records(148)\n"
                '    .href(lambda page: f"#page-{page}")\n'
                ")",
            ),
            variant(
                "At the first page",
                "Pagination().page(1).total_pages(15).total_records(148)",
            ),
            variant(
                "A single page",
                "Pagination().page(1).total_pages(1).total_records(10)",
            ),
            variant(
                "By cursor",
                "(\n"
                "    Pagination()\n"
                "    .total_records(2481)\n"
                "    .page_size(25)\n"
                "    .page_sizes([10, 25, 50, 100])\n"
                "    .cursor(previous=False, next=True)\n"
                ")",
            ),
        ],
    ),
]
