from __future__ import annotations

from typing import NamedTuple

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules.popover import Popover
from hue.utils import classnames, render_when


class Crumb(NamedTuple):
    """
    A step and where it goes. No href is the page you are on, which is not a
    link - and the fields have names, so a trail reads as a trail rather than
    as a list of pairs.
    """

    href: str | None
    label: str


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

    def items(self, value: list[Crumb] | list[tuple[str | None, str]]) -> Self:
        """
        The trail, root first. A step with no href is the current page.

        Crumb(href, label), or the plain pair it unpacks from.
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
        items = [Crumb(*item) for item in self._get_prop("items", [])]
        limit: int | None = self._get_prop("collapse_after")
        hidden: list[Crumb] = []

        if limit is not None and len(items) > limit:
            # Keep the root and the tail; the middle is what gets folded.
            hidden = items[1:-2]
            items = [items[0], *items[-2:]]

        steps: list[ComponentType] = []
        for index, crumb in enumerate(items):
            if index == 1 and hidden:
                steps.append(self._ellipsis(hidden))
            steps.append(
                self._step(crumb.href, crumb.label, last=index == len(items) - 1)
            )

        return html.nav(
            html.ol(
                *steps,
                class_="flex flex-wrap items-center gap-0.5 p-0 m-0 list-none",
            ),
            aria_label="Breadcrumb",
            class_=classnames("text-sm", self._get_prop("class_")),
            **self._get_base_html_attrs(),
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
        The folded middle, behind a popover rather than a menu.

        A list of links is navigation: role="menu" would announce them as
        commands and change what the arrow keys are expected to do. Opening a
        panel also leaves the trail one line, where expanding in place pushes
        the page around while the reader is looking at it.
        """
        count = len(hidden)
        levels = "level" if count == 1 else "levels"
        return html.li(
            Popover()
            .fit()
            .placement("bottom-start")
            .trigger(
                Button()
                .variant("ghost")
                .size("xs")
                .icon_only(f"Show {count} hidden {levels}")
                .content("…")
            )
            .content(
                html.ul(
                    *(
                        html.li(
                            html.a(
                                crumb.label,
                                href=crumb.href or "#",
                                class_=classnames(
                                    "block rounded-sm px-2 py-[7px] text-base "
                                    "text-fg no-underline hover:bg-surface-hover",
                                    FOCUS_RING,
                                ),
                            )
                        )
                        for crumb in hidden
                    ),
                    class_="flex min-w-40 flex-col list-none p-0 m-0",
                )
            ),
            _separator(),
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
