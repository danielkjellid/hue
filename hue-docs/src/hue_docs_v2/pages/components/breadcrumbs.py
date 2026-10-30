from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Breadcrumbs, Sidebar, Tabs

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# The links go to anchors, so following one leaves the preview where it is.

# Live


def invoice_trail() -> Breadcrumbs:
    return Breadcrumbs().items(
        [
            ("#home", "Home"),
            ("#billing", "Billing"),
            ("#invoices", "Invoices"),
            (None, "INV-2048"),
        ]
    )


# Anatomy


def two_steps() -> Breadcrumbs:
    return Breadcrumbs().items([("#settings", "Settings"), (None, "Billing")])


# Collapsed


def folded_middle() -> Breadcrumbs:
    return (
        Breadcrumbs()
        .items(
            [
                ("#home", "Home"),
                ("#acme", "Acme Inc."),
                ("#projects", "Projects"),
                ("#website", "Website"),
                ("#pages", "Pages"),
                (None, "Pricing"),
            ]
        )
        .collapse_after(3)
    )


def short_enough() -> Breadcrumbs:
    return (
        Breadcrumbs()
        .items([("#home", "Home"), ("#projects", "Projects"), (None, "Website")])
        .collapse_after(2)
    )


# Width


def wraps() -> Breadcrumbs:
    return Breadcrumbs().items(
        [
            ("#home", "Home"),
            ("#organisation", "Northwind Traders"),
            ("#warehouses", "Warehouses"),
            ("#oslo", "Oslo central"),
            ("#shelves", "Shelves"),
            (None, "Aisle 14, shelf C"),
        ]
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Building a Breadcrumbs trail"),
        pr.p(
            "`items()` takes the trail root first, as `(href, label)` pairs. The "
            "step with `None` for its `href` is the page you are on. `Breadcrumbs` "
            'renders it as text with `aria-current="page"` rather than as a link. '
            "Put it last."
        ),
        pr.code(
            "Breadcrumbs().items(\n"
            "    [\n"
            '        ("/", "Home"),\n'
            '        ("/billing/", "Billing"),\n'
            '        (None, "INV-2048"),\n'
            "    ]\n"
            ")"
        ),
        pr.p(
            "The pairs unpack into `Crumb`, a named tuple with `href` and `label` "
            "fields. `Crumb` lives in `hue.ui.molecules.breadcrumbs` and is not "
            "exported from `hue.ui`."
        ),
        pr.h2("Folding a long Breadcrumbs trail"),
        pr.p(
            "`collapse_after(n)` folds the middle of the trail once it has more "
            "than `n` steps. The first step and the last two stay in the row. "
            "The steps between them move into a popover behind an ellipsis "
            "button, which opens below it as a list of links."
        ),
        pr.p(
            "A trail of three steps or fewer never folds, whatever `n` is, "
            "because there is no middle to fold."
        ),
        pr.code(
            "Breadcrumbs().items(trail).collapse_after(3)",
        ),
        pr.h2("Breadcrumbs on a narrow screen"),
        pr.p(
            "The steps sit in a row that wraps. A trail too long for its "
            "container continues on a second line, and `collapse_after()` is "
            "how you keep it on one."
        ),
    )


PAGE = ComponentPage(
    Breadcrumbs,
    lede=(
        "Breadcrumbs show the path from the root of a hierarchy down to the "
        "page you are on, with a link to each step above it. `collapse_after()` "
        "folds the middle of a deep trail behind an ellipsis."
    ),
    usage=_usage,
    panels=[
        panel("Live", invoice_trail, layout="center"),
        panel("Anatomy", invoice_trail, two_steps, layout="stack"),
        panel(
            "Collapsed",
            folded_middle,
            short_enough,
            layout="stack",
            min_height=260,
            hint="Open the ellipsis to see the folded steps",
        ),
        panel("Width", wraps, layout="stack", hint="The row wraps when it runs out"),
    ],
    notes=[
        Note(
            "a11y",
            'The trail is a `nav` labelled "Breadcrumb" around an ordered list, '
            "so a screen reader announces it as a landmark and counts the steps.",
        ),
        Note(
            "a11y",
            'The page you are on is text with `aria-current="page"`, not a link.',
        ),
        Note(
            "a11y",
            "The chevrons between steps are `aria-hidden`, so they are not read "
            "out between every pair of steps.",
        ),
        Note(
            "a11y",
            'The ellipsis is a button named "Show n hidden levels". It opens a '
            "popover holding a plain list of links rather than a menu, so the "
            "links are announced and navigated as links.",
        ),
        Note(
            "warn",
            "A step with an `href` of `None` anywhere but last still renders as "
            "the current page. `Breadcrumbs` does not check the order.",
        ),
    ],
    related=[Tabs, Sidebar],
)
