from __future__ import annotations

from fastapi import Request
from hue import html
from hue.context import HueContext
from hue.types.core import ComponentType
from hue.ui import DataTable, Pagination, Stack, Table, Tabs
from hue_fastapi import HueFragmentsView, Page, Router

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# The demo's list: 18 orders, five to a page.
_ORDERS = 18
_PAGE_SIZE = 5
_PAGES = 4


class PaginationDemo(HueFragmentsView):
    """
    The pages behind the live example. A page route rather than a fragment, so
    a reload of the URL the swap pushed still answers with the whole page.
    """

    router = Router[Request]()

    @router.page("{number}/")
    async def orders_page(
        self, request: Request, context: HueContext[Request], number: str
    ) -> ComponentType:
        # Taken as text and clamped here, so a hand-edited URL still gets a
        # page rather than a 422.
        page = min(max(int(number), 1), _PAGES) if number.isdecimal() else 1
        first = (page - 1) * _PAGE_SIZE + 1
        last = min(page * _PAGE_SIZE, _ORDERS)
        return Page(
            title=f"Orders, page {page}",
            body=Stack()
            .class_("p-6")
            .content(
                html.ul(
                    *[html.li(f"Order #{1000 + n}") for n in range(first, last + 1)]
                )
                .id("orders")
                .class_("text-base"),
                Pagination()
                .id("orders-pages")
                .target("orders")
                .page(page)
                .total_pages(_PAGES)
                .total_records(_ORDERS)
                .page_size(_PAGE_SIZE)
                .href(lambda step: f"/demos/pagination/{step}/"),
            ),
        )


# Live


def swapping_a_list() -> ComponentType:
    return Stack().content(
        html.ul(*[html.li(f"Order #{1000 + n}") for n in range(1, 6)])
        .id("orders")
        .class_("text-base"),
        Pagination()
        .id("orders-pages")
        .target("orders")
        .page(1)
        .total_pages(4)
        .total_records(18)
        .page_size(5)
        .href(lambda page: f"/demos/pagination/{page}/"),
    )


# States


def first_page() -> Pagination:
    return (
        Pagination()
        .page(1)
        .total_pages(15)
        .total_records(148)
        .href(lambda page: f"#page-{page}")
    )


def middle_page() -> Pagination:
    return (
        Pagination()
        .page(8)
        .total_pages(15)
        .total_records(148)
        .href(lambda page: f"#page-{page}")
    )


def last_page() -> Pagination:
    return (
        Pagination()
        .page(15)
        .total_pages(15)
        .total_records(148)
        .href(lambda page: f"#page-{page}")
    )


def single_page() -> Pagination:
    return Pagination().page(1).total_pages(1).total_records(7)


# Empty


def no_records() -> Pagination:
    return Pagination().page(1).total_pages(1).total_records(0)


# Anatomy


def wider_window() -> Pagination:
    return (
        Pagination()
        .page(8)
        .total_pages(15)
        .total_records(148)
        .sibling_count(2)
        .href(lambda page: f"#page-{page}")
    )


def without_a_count() -> Pagination:
    return Pagination().page(3).total_pages(7).href(lambda page: f"#page-{page}")


def rows_per_page() -> Pagination:
    return (
        Pagination()
        .id("invoices-pages")
        .page(2)
        .total_pages(10)
        .total_records(248)
        .page_size(25)
        .page_sizes([10, 25, 50, 100])
        .href(lambda page: f"#page-{page}")
    )


def by_cursor() -> Pagination:
    return Pagination().total_records(2481).cursor(previous=False, next=True)


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Building a Pagination"),
        pr.p(
            "`page()` is the page you are on and `total_pages()` how many there "
            "are. `total_records()` adds the count on the left, and `page_size()`, "
            "`10` by default, turns the page number into the range of records "
            "it shows."
        ),
        pr.code(
            "(\n"
            "    Pagination()\n"
            "    .page(3)\n"
            "    .total_pages(15)\n"
            "    .total_records(148)\n"
            '    .href(lambda page: f"/invoices/?page={page}")\n'
            ")"
        ),
        pr.p(
            "A `page()` below `1` or above `total_pages()` is clamped to the nearest "
            "end, so a stale or hand-edited URL still renders a real page."
        ),
        pr.h3("Links or buttons"),
        pr.p(
            "`href()` takes a function from a page number to its URL, and the "
            "steps become links. Without `href()` the steps are buttons with no "
            "handler, and the number in each is the only thing that says "
            "which page it leads to."
        ),
        pr.h2("Swapping a list with Pagination"),
        pr.p(
            "`target()` names the id of the element a page lands in. Every link "
            "then fetches its page with Alpine AJAX, swaps that element and "
            "pushes the URL, so the back button and a reload still work. The "
            "`Pagination` sits outside the element it swaps, so it needs an `id()` "
            "of its own, because it carries `x-sync` and refreshes itself from "
            "the same response. A `target()` without an `id()` raises an error."
        ),
        pr.code(
            "Stack().content(\n"
            '    html.ul(*rows).id("orders"),\n'
            "    Pagination()\n"
            '    .id("orders-pages")\n'
            '    .target("orders")\n'
            "    .page(page)\n"
            "    .total_pages(4)\n"
            '    .href(lambda n: f"/orders/{n}/"),\n'
            ")"
        ),
        pr.p(
            "The route behind each link returns the whole page. Alpine AJAX "
            "takes the elements with the two ids out of it and leaves the "
            "rest of the page alone."
        ),
        pr.h2("The window of Pagination numbers"),
        pr.p(
            "The first and last pages always show. `sibling_count()`, `1` by "
            "default, sets how many pages show either side of the current one. "
            "The gaps between them become an ellipsis. In a container narrower "
            "than 28rem the neighbours fold away as well, so the steps stay on one "
            "line on a phone."
        ),
        pr.h2("Rows per page in Pagination"),
        pr.p(
            "`page_sizes()` renders a `select` of row counts beside the steps, "
            "named `page_size` and preset to `page_size()`. Its id is built from "
            "the `Pagination`'s own, so `page_sizes()` also needs an `id()`. The "
            "`Pagination` adds nothing that sends the select's value, so put it "
            "in a form or attach a handler to it."
        ),
        pr.h2("Stepping by cursor"),
        pr.p(
            "`cursor(previous=..., next=...)` replaces the numbers with Previous "
            "and Next buttons, for a list too long or too live to count. Each "
            "argument says whether there is anything in that direction, and a "
            "`False` disables its button. The count shows the total records "
            "without a range."
        ),
        pr.h2("One page or no records"),
        pr.p(
            "With a single page, `Pagination` still draws its row, with every "
            "step inert, so the control does not vanish when a filter narrows "
            'the list. With `total_records(0)` the count reads "No records".'
        ),
    )


PAGE = ComponentPage(
    Pagination,
    lede=(
        "`Pagination` moves through a long list one page at a time and says "
        "which records are showing out of how many. The steps are links to "
        "real URLs, and with `target()` they swap the list in place."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            swapping_a_list,
            layout="stack",
            min_height=220,
            hint="Each step fetches its page and swaps the list",
        ),
        panel(
            "States",
            first_page,
            middle_page,
            last_page,
            single_page,
            layout="stack",
        ),
        panel("Empty", no_records, layout="stack"),
        panel(
            "Anatomy",
            wider_window,
            without_a_count,
            rows_per_page,
            by_cursor,
            layout="stack",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The steps sit in a `nav` labelled "Pagination", or "Pagination, '
            'single page" when there is only one, and the current page carries '
            '`aria-current="page"`.',
        ),
        Note(
            "a11y",
            "The previous and next steps hold only a chevron, so they are "
            'named "Previous page" and "Next page" with `aria-label`.',
        ),
        Note(
            "a11y",
            "At either end the spent step stays in the row as a `span` with "
            "`aria-disabled`, so it is announced but has nothing to activate.",
        ),
        Note(
            "a11y",
            "The ellipses are `aria-hidden`. The rows-per-page select has a "
            "visually hidden label, and the visible words beside it are "
            "`aria-hidden`, so the control is announced once.",
        ),
        Note(
            "warn",
            "`page_sizes()` and `target()` both need an `id()` on the `Pagination`, "
            "and raise an error without one.",
        ),
    ],
    related=[Table, DataTable, Tabs],
    views=[PaginationDemo],
)
