from __future__ import annotations

from collections.abc import Callable

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

_ITEM = (
    "inline-flex h-control-sm min-w-[var(--spacing-control-sm)] items-center "
    "justify-center rounded-md border border-transparent px-2 font-ui "
    "text-sm font-medium tabular-nums text-fg-muted no-underline "
    "hover:bg-surface-hover hover:text-fg cursor-pointer"
)

_CURRENT = "bg-accent-subtle border-accent-border text-accent-text"

# A step with nowhere to go stays in the row and stays announced: a control
# that disappears at the ends teaches nobody where the ends are.
_SPENT = "text-fg-disabled cursor-not-allowed pointer-events-none"


class Pagination(ChainableComponent):
    """
    Which page you are on, out of how many, over how many records.

    The count is not decoration: "page 3 of 7" without "148 records" leaves
    nobody able to tell whether their filter did anything. href() makes the
    steps links; without it they are buttons for a handler to catch.

        Pagination().page(3).total_pages(7).total_records(148)
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return cls().page(3).total_pages(15).total_records(148)

    def page(self, value: int) -> Self:
        self._props["page"] = value
        return self

    def total_pages(self, value: int) -> Self:
        self._props["total_pages"] = value
        return self

    def total_records(self, value: int) -> Self:
        self._props["total_records"] = value
        return self

    def page_size(self, value: int) -> Self:
        """
        How many rows a page holds, which is what turns a page number into
        "showing 21-30".
        """
        self._props["page_size"] = value
        return self

    def sibling_count(self, value: int) -> Self:
        """
        How many pages to show either side of the current one before the rest
        fold into an ellipsis.
        """
        self._props["sibling_count"] = value
        return self

    def href(self, value: Callable[[int], str]) -> Self:
        """
        Where page n lives. Given one, the steps are links, which can be
        opened in a new tab and read by a crawler; without one they are
        buttons for your own handler.
        """
        self._props["href"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        page: int = self._get_prop("page", 1)
        total_pages: int = self._get_prop("total_pages", 1)
        total_records: int | None = self._get_prop("total_records")
        size: int = self._get_prop("page_size", 10)

        status = render_if(
            total_records,
            lambda count: html.span(
                *_status(page, size, count),
                class_="text-sm tabular-nums text-fg-muted",
            ),
        )

        # One page is not a control. Rendering the whole row for a list that
        # cannot move is worse than rendering the count alone.
        if total_pages <= 1:
            return html.div(
                status,
                class_=classnames(
                    "flex flex-wrap items-center justify-between gap-4",
                    self._get_prop("class_"),
                ),
                **self._get_base_html_attrs(),
            )

        return html.div(
            status,
            html.nav(
                self._step(page - 1, "Previous page", "chevron-left", page > 1),
                *self._numbers(page, total_pages),
                self._step(page + 1, "Next page", "chevron-right", page < total_pages),
                aria_label="Pagination",
                class_="flex items-center gap-1",
            ),
            class_=classnames(
                "flex flex-wrap items-center justify-between gap-4",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )

    def _numbers(self, page: int, total_pages: int) -> list[ComponentType]:
        siblings: int = self._get_prop("sibling_count", 1)
        # The first and the last are always reachable; the window walks.
        window = range(max(2, page - siblings), min(total_pages, page + siblings) + 1)
        shown = sorted({1, *window, total_pages})

        items: list[ComponentType] = []
        previous = 0
        for number in shown:
            if number - previous > 1:
                items.append(_ellipsis())
            items.append(self._number(number, current=number == page))
            previous = number
        return items

    def _number(self, number: int, *, current: bool) -> ComponentType:
        classes = classnames(_ITEM, _CURRENT if current else "", FOCUS_RING)
        href = self._get_prop("href")
        if href is None:
            return html.button(
                str(number),
                type="button",
                aria_current="page" if current else None,
                class_=classes,
            )
        return html.a(
            str(number),
            href=href(number),
            aria_current="page" if current else None,
            class_=classes,
        )

    def _step(self, number: int, label: str, icon: str, enabled: bool) -> ComponentType:
        glyph = HueIcon(icon).class_("size-3.5")
        href = self._get_prop("href")

        if not enabled:
            # A span, so there is nothing to activate - but still in the row,
            # still named, so the end of the range is something you can hear.
            return html.span(
                glyph,
                aria_label=label,
                aria_disabled="true",
                class_=classnames(_ITEM, _SPENT),
            )
        if href is None:
            return html.button(
                glyph,
                type="button",
                aria_label=label,
                class_=classnames(_ITEM, FOCUS_RING),
            )
        return html.a(
            glyph,
            href=href(number),
            aria_label=label,
            class_=classnames(_ITEM, FOCUS_RING),
        )


#: The range separator. An en dash, which is what a range takes.
_RANGE = "\u2013"


def _status(page: int, size: int, total: int) -> list[ComponentType]:
    first = (page - 1) * size + 1
    last = min(page * size, total)
    return [
        "Showing ",
        html.strong(f"{first:,}{_RANGE}{last:,}"),
        " of ",
        html.strong(f"{total:,}"),
        " records",
    ]


def _ellipsis() -> ComponentType:
    """
    The pages nobody is asking about. Decoration, so it is not announced.
    """
    return html.span(
        "…",
        aria_hidden="true",
        class_="inline-flex h-control-sm min-w-7 items-center justify-center "
        "text-fg-disabled",
    )
