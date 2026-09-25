from __future__ import annotations

from collections.abc import Callable

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.native_select import NativeSelect
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

# What every step is, minus anything its state decides. The three states
# below each name a border colour, a text colour and a cursor, so no two
# classes are left competing for the same property.
_BAR = "flex w-full flex-wrap items-center justify-between gap-4"

_ITEM = (
    "inline-flex h-control-sm min-w-[var(--spacing-control-sm)] items-center "
    "justify-center rounded-md border px-2 font-ui text-sm font-medium "
    "tabular-nums no-underline"
)

_IDLE = (
    "border-transparent text-fg-muted cursor-pointer "
    "hover:bg-surface-hover hover:text-fg"
)

_CURRENT = "bg-accent-subtle border-accent-border text-accent-text cursor-pointer"

# A step with nowhere to go stays in the row and stays announced: a control
# that disappears at the ends teaches nobody where the ends are.
_SPENT = "border-transparent text-fg-disabled cursor-not-allowed pointer-events-none"


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

    def cursor(self, *, previous: bool, next: bool) -> Self:
        """
        Step by cursor rather than by number, for a list too long or too
        live to count pages through. Each argument says whether there is
        anything that way.
        """
        self._props["cursor"] = (previous, next)
        return self

    def page_sizes(self, value: list[int]) -> Self:
        """
        The rows-per-page choices, rendered as a select beside the steps.
        """
        self._props["page_sizes"] = value
        return self

    def href(self, value: Callable[[int], str]) -> Self:
        """
        Where page n lives. Given one, the steps are links, which can be
        opened in a new tab and read by a crawler; without one they are
        buttons for your own handler.
        """
        self._props["href"] = value
        return self

    def target(self, value: str) -> Self:
        """
        The id a page lands in. Given one, the browser fetches the page and
        swaps that element; without one every step is a plain navigation.
        """
        self._props["target"] = value
        return self

    def _render(self, context: Context) -> Component:
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

        if cursor := self._get_prop("cursor"):
            return html.div(
                render_if(
                    total_records,
                    lambda count: html.span(
                        f"{count:,} records",
                        class_="text-sm tabular-nums text-fg-muted",
                    ),
                ),
                html.div(
                    render_if(self._get_prop("page_sizes"), self._sizes),
                    html.nav(
                        _cursor_step("Previous", cursor[0]),
                        _cursor_step("Next", cursor[1]),
                        aria_label="Pagination",
                        class_="flex items-center gap-2",
                    ),
                    class_="flex flex-wrap items-center gap-3",
                ),
                class_=classnames(_BAR, self._get_prop("class_")),
                **self._get_base_html_attrs(),
            )

        # One page still draws the control, inert: a row that disappears when
        # a filter narrows the list to one page reads as something breaking.
        if total_pages <= 1:
            return html.div(
                status,
                html.nav(
                    self._step(0, "Previous page", "chevron-left", False),
                    self._number(1, current=True, inert=True),
                    self._step(2, "Next page", "chevron-right", False),
                    aria_label="Pagination, single page",
                    class_="flex items-center gap-1",
                ),
                class_=classnames(_BAR, self._get_prop("class_")),
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
            class_=classnames(_BAR, self._get_prop("class_")),
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

    def _number(
        self, number: int, *, current: bool, inert: bool = False
    ) -> ComponentType:
        classes = classnames(_ITEM, _CURRENT if current else _IDLE, FOCUS_RING)
        href = self._get_prop("href")
        if inert:
            return html.span(str(number), aria_current="page", class_=classes)
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
            **self._target_attr(),
        )

    def _sizes(self, options: list[int]) -> ComponentType:
        """
        Rows per page. The select carries the name, hidden; the words beside
        it are the same words and are marked as decoration, so the control is
        announced once and reads the way it looks.
        """
        return html.div(
            html.span(
                "Rows per page",
                aria_hidden="true",
                class_="text-sm text-fg-muted",
            ),
            NativeSelect()
            .name("page_size")
            .label("Rows per page")
            .hidden_label()
            .size("sm")
            .value(str(self._get_prop("page_size", 10)))
            .options([(str(option), str(option)) for option in options]),
            # The select fills its box, so the box is what sets the width - a
            # w-auto on the control itself would just fight its own w-full.
            class_="flex items-center gap-2 [&_select]:w-20",
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
                class_=classnames(_ITEM, _IDLE, FOCUS_RING),
            )
        return html.a(
            glyph,
            href=href(number),
            aria_label=label,
            class_=classnames(_ITEM, _IDLE, FOCUS_RING),
            **self._target_attr(),
        )

    def _target_attr(self) -> dict[str, str]:
        target: str | None = self._get_prop("target")
        # push, so a page is a place: the URL says which one, the back
        # button goes to the last, and the link can be sent to somebody.
        return {"x-target.push": target} if target else {}


#: The range separator. An en dash, which is what a range takes.
_RANGE = "\u2013"


def _cursor_step(label: str, enabled: bool) -> ComponentType:
    """
    One of the two steps a cursor knows about. Spent, it stays and says so.
    """
    button = Button().variant("outline").size("sm").content(label)
    if not enabled:
        button.disabled()
    return button


def _status(page: int, size: int, total: int) -> list[ComponentType]:
    if total == 0:
        # There is no range of nothing, and "showing 1-0" reads as a bug.
        return ["No records"]
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
