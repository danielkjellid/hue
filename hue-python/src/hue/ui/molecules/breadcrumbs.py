from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_when

# A step and where it goes. None is the page you are on, which is not a link.
type Crumb = tuple[str | None, str]

_LINK = (
    "rounded-xs px-1.5 py-[3px] text-fg-muted no-underline "
    "hover:bg-surface-hover hover:text-fg"
)

_CURRENT = "px-1.5 py-[3px] font-medium text-fg"


class Breadcrumbs(ChainableComponent):
    """
    The trail back up from the page you are on.

    Worth the row it costs only where the hierarchy is real and deeper than
    two levels. collapse_after() folds the middle of a long trail behind an
    ellipsis that expands in place.

        Breadcrumbs().items([("/", "Home"), (None, "INV-2048")])
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return cls().items([("/", "Home"), ("/billing", "Billing"), (None, "INV-2048")])

    def items(self, value: list[Crumb]) -> Self:
        """
        The trail, root first. A step with no href is the current page.
        """
        self._props["items"] = value
        return self

    def collapse_after(self, value: int) -> Self:
        """
        Fold the middle away once the trail is longer than this many steps.

        The first and the last two always show: where you started, where you
        are, and the one step back that most people actually want.
        """
        self._props["collapse_after"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        items: list[Crumb] = self._get_prop("items", [])
        limit: int | None = self._get_prop("collapse_after")
        hidden: list[Crumb] = []

        if limit is not None and len(items) > limit:
            # Keep the root and the tail; the middle is what gets folded.
            hidden = items[1:-2]
            items = [items[0], *items[-2:]]

        steps: list[ComponentType] = []
        for index, (href, label) in enumerate(items):
            if index == 1 and hidden:
                steps.append(self._ellipsis(hidden))
            steps.append(self._step(href, label, last=index == len(items) - 1))

        return html.nav(
            html.ol(
                *steps,
                class_="flex flex-wrap items-center gap-0.5 p-0 m-0 list-none",
            ),
            aria_label="Breadcrumb",
            class_=classnames("text-sm", self._get_prop("class_")),
            **{
                "x-data": "{ expanded: false }",
                **self._get_base_html_attrs(),
            },
        )

    def _step(self, href: str | None, label: str, *, last: bool) -> ComponentType:
        # The page you are on is not a link: making it one teaches people that
        # breadcrumbs do nothing.
        crumb = (
            html.span(label, aria_current="page", class_=_CURRENT)
            if href is None
            else html.a(label, href=href, class_=classnames(_LINK, FOCUS_RING))
        )
        return html.li(
            crumb,
            render_when(not last, _separator()),
            class_="flex items-center gap-0.5",
        )

    def _ellipsis(self, hidden: list[Crumb]) -> ComponentType:
        """
        The folded middle: a button that swaps itself for the steps it hides,
        rather than a link to nowhere or a menu to open.
        """
        count = len(hidden)
        return html.li(
            html.button(
                "…",
                type="button",
                aria_label=f"Show {count} hidden {'level' if count == 1 else 'levels'}",
                class_=classnames(
                    "rounded-xs px-1.5 py-[3px] text-fg-muted "
                    "hover:bg-surface-hover hover:text-fg cursor-pointer",
                    FOCUS_RING,
                ),
                **{
                    "x-show": unsafe("!expanded"),
                    "x-on:click": unsafe("expanded = true"),
                },
            ),
            *(
                html.span(
                    html.a(label, href=href, class_=classnames(_LINK, FOCUS_RING))
                    if href is not None
                    else label,
                    _separator(),
                    class_="flex items-center gap-0.5",
                    **{"x-show": unsafe("expanded"), "x-cloak": True},
                )
                for href, label in hidden
            ),
            render_when(bool(hidden), _separator()),
            class_="flex items-center gap-0.5",
        )


def _separator() -> ComponentType:
    """
    Decoration: "greater than" read four times is noise.
    """
    return html.span(
        HueIcon("chevron-right").class_("size-3.5"),
        aria_hidden="true",
        class_="flex text-fg-disabled",
    )
