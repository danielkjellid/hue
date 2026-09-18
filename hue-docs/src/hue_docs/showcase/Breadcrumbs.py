"""
Curated showcases for the Breadcrumbs molecule.

The auto-grid has nothing to toggle here - what matters is a real trail and
what happens to a long one.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_TRAIL = (
    '[("/", "Home"), ("/billing", "Billing"), '
    '("/billing/invoices", "Invoices"), (None, "INV-2048")]'
)

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "A nav around an ordered list, with aria-current on the last "
            "step. The page you are on is not a link: making it one teaches "
            "people that breadcrumb items do nothing. Separators are "
            'decoration - "greater than" read four times is noise. Only '
            "worth the row it costs where the hierarchy is real and deeper "
            "than two levels."
        ),
        variants=[
            variant("A trail", f"Breadcrumbs().items({_TRAIL})"),
            variant(
                "Folded in the middle",
                f"Breadcrumbs().items({_TRAIL}).collapse_after(3)",
            ),
        ],
    ),
]
