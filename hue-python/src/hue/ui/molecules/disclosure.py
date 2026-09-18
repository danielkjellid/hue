from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.js import unsafe
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

# A band rather than a row: the header is a tinted strip and what it opens
# sits under it at full width, which is what makes this a section of a page
# rather than an item in a list.
_HEADER = (
    "flex w-full cursor-pointer items-center gap-2 rounded-md border-none "
    "bg-canvas-subtle px-4 py-1.5 text-start font-ui text-base font-medium "
    "text-fg hover:bg-surface-hover"
)

_CHEVRON = (
    "ms-auto size-3 flex-none text-fg-subtle transition-transform "
    "duration-150 [[aria-expanded=true]>&]:rotate-180"
)


class Disclosure(ChainableComponent):
    """
    A section of a page that can be folded away.

    The title sits in an h3, which is how a screen reader finds the section.

    One heading and what it opens, answering to nothing else on the page -
    where an Accordion is a set of these that agree on how many stay open.
    Reach for this to group a long form; reach for that when the point is
    that only one section is open at a time.

        Disclosure().title("General").open().content(fields)
    """

    category = "Layout"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .title("General")
            .open()
            .content("Everything about the product itself.")
        )

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def open(self, value: bool = True) -> Self:
        """
        Start it open.
        """
        self._props["open"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        starts_open: bool = self._get_prop("open", False)

        trigger = html.button(
            render_if(self._get_prop("title"), lambda text: text),
            HueIcon("chevron-down").class_(_CHEVRON),
            type="button",
            class_=classnames(_HEADER, FOCUS_RING),
            **{
                ":id": "$id('hue-disclosure-title')",
                ":aria-expanded": unsafe("open"),
                ":aria-controls": "$id('hue-disclosure-panel')",
                "x-on:click": unsafe("open = !open"),
            },
        )

        return html.div(
            html.h3(trigger),
            html.div(
                *self._children,
                # Named by the heading that opens it, so a screen reader
                # landing in the section knows which one it is in.
                role="region",
                # The same inset as the header, so what the section holds
                # starts under the word that names it.
                class_="px-4 pt-4",
                **{
                    ":id": "$id('hue-disclosure-panel')",
                    ":aria-labelledby": "$id('hue-disclosure-title')",
                    "x-show": unsafe("open"),
                    "x-cloak": True,
                },
            ),
            # A section spans its column: the header is a band across the
            # content it folds, not a chip the width of its own title.
            class_=classnames("w-full", self._get_prop("class_")),
            **{
                "x-data": f"{{ open: {str(starts_open).lower()} }}",
                "x-id": "['hue-disclosure-title', 'hue-disclosure-panel']",
                **self._get_base_html_attrs(),
            },
        )
