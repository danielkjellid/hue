from __future__ import annotations

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.base import ChainableComponent
from hue.utils import classnames


class ScrollArea(ChainableComponent):
    """
    A box that scrolls, with a scrollbar that belongs to the page.

    The scrolling itself is the browser's: only the bar is themed. max_height()
    is how far the content grows before it starts, and fade() softens the cut
    edge instead of drawing a line under it. label() names the region, and is
    required - a box a keyboard reaches has to say what it is.
    """

    category = "Layout"

    def label(self, value: str) -> Self:
        """
        What the region is, announced when the keyboard reaches it.
        """
        self._props["label"] = value
        return self

    def max_height(self, value: str) -> Self:
        """
        How tall it grows before it scrolls, as a Tailwind class, e.g.
        "max-h-64". Leave it out where the parent already sets a height.
        """
        self._props["max_height"] = value
        return self

    def fade(self, value: bool = True) -> Self:
        """
        Soften the top and bottom edges, each only while there is more that
        way. Worth it for prose, where a hard cut mid-sentence reads as the
        end; a list of rows already says it continues by cutting one in half.
        The fade keeps an Alpine scope of its own, so x_data() raises here
        and belongs on an element around the area.
        """
        self._props["fade"] = value
        return self

    def _render(self, context: Context) -> Component:
        # A blank label names nothing, so it is no label at all.
        label: str | None = (self._get_prop("label") or "").strip() or None
        fade: bool = self._get_prop("fade", False)

        if label is None:
            raise ValueError(
                "ScrollArea needs a label(): it is focusable, because a "
                "keyboard has no other way to scroll it, and a stop on the "
                "way through a page that announces nothing is a stop nobody "
                "can account for."
            )

        # tabindex so the keyboard can scroll it at all (WCAG 2.1.1), and
        # role="region" so what it lands on is announced as somewhere rather
        # than as an unnamed group.
        attrs = {
            "role": "region",
            "aria_label": label,
            "tabindex": "0",
            **self._get_base_html_attrs(),
        }

        if fade:
            self._refuse_x_data()
            attrs |= {
                "x-data": "hueScrollArea()",
                "x-on:scroll": "edges()",
                ":data-scroll-above": "above || null",
                ":data-scroll-below": "below || null",
            }

        return html.div(
            *self._children,
            class_=classnames(
                "overflow-auto overscroll-contain scrollbar-thin",
                "scroll-fade" if fade else None,
                FOCUS_RING,
                self._get_prop("max_height"),
                self._get_prop("class_"),
            ),
            **attrs,
        )
