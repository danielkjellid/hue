from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.js import unsafe
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type AccordionVariant = Literal["plain", "boxed"]
type HeadingLevel = Literal["h2", "h3", "h4", "h5", "h6"]

_VARIANTS: dict[AccordionVariant, str] = {
    "plain": "border-t border-border [&>*]:border-b [&>*]:border-border",
    "boxed": (
        "flex flex-col gap-2 "
        "[&>*]:rounded-md [&>*]:border [&>*]:border-border "
        "[&>*]:bg-surface [&>*]:px-4"
    ),
}

_TRIGGER = (
    "flex w-full cursor-pointer items-center justify-between gap-4 rounded-sm "
    "border-none bg-transparent px-0.5 py-4 text-start font-ui text-base "
    "font-medium text-fg hover:text-accent-text"
)

# The label tints rather than the row: the row's fill is already carrying the
# open and closed distinction.
_CHEVRON = (
    "size-4 flex-none text-fg-subtle transition-transform duration-150 "
    "[[aria-expanded=true]>&]:rotate-180"
)

_PANEL = "px-0.5 pb-4 text-base leading-[1.6] text-fg-muted max-w-[72ch]"


class Accordion(ChainableComponent):
    """
    Sections that open one at a time, for content nobody needs all of.

    Opening one closes the last, unless multiple() says otherwise. If every
    panel has to be opened to finish the task, the content wants a page
    rather than an accordion.
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return cls().content(
            AccordionItem()
            .title("How is usage calculated?")
            .open()
            .content("Metered per API call, aggregated hourly, billed monthly."),
            AccordionItem()
            .title("Can I change plans mid-cycle?")
            .content("Upgrades take effect immediately and are prorated."),
        )

    def variant(self, value: AccordionVariant) -> Self:
        self._props["variant"] = value
        return self

    def multiple(self, value: bool = True) -> Self:
        """
        Let any number of sections stay open at once, rather than the one
        most recently opened.
        """
        self._props["multiple"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: AccordionVariant = self._get_prop("variant", "plain")
        multiple: bool = self._get_prop("multiple", False)

        # The items are numbered here rather than numbering themselves, since
        # what a section has to know about is the ones beside it.
        opened: list[int] = []
        for index, item in enumerate(self._children):
            if not isinstance(item, AccordionItem):
                continue
            item._props["index"] = index
            if item._get_prop("open", False):
                opened.append(index)

        # One at a time keeps at most one, whatever the items asked for.
        if not multiple:
            opened = opened[:1]

        single = str(not multiple).lower()
        state = (
            f"{{ open: {opened}, single: {single}, "
            "shown(index) { return this.open.includes(index) }, "
            "toggle(index) { this.open = this.shown(index) "
            "? this.open.filter((each) => each !== index) "
            ": (this.single ? [index] : [...this.open, index]) } }"
        )

        return html.div(
            *self._children,
            # w-full, or the accordion is as wide as whichever panel happens
            # to be open and the whole thing jumps every time one is. The
            # panel keeps its own reading width instead.
            class_=classnames("w-full", _VARIANTS[variant], self._get_prop("class_")),
            **{"x-data": state, **self._get_base_html_attrs()},
        )


class AccordionItem(ChainableComponent):
    """
    One section: a heading that opens it and the panel it opens.
    """

    category = None

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def heading(self, value: HeadingLevel) -> Self:
        """
        The heading level the trigger sits in, which is how a screen reader
        jumps between sections. h3 by default, since an accordion usually
        follows an h2.
        """
        self._props["heading"] = value
        return self

    def open(self, value: bool = True) -> Self:
        """
        Start this section open. In single mode the first one asking wins.
        """
        self._props["open"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        index: int = self._get_prop("index", 0)
        heading: HeadingLevel = self._get_prop("heading", "h3")
        shown = unsafe(f"shown({index})")

        trigger = html.button(
            render_if(self._get_prop("title"), lambda text: text),
            HueIcon("chevron-down").class_(_CHEVRON),
            type="button",
            class_=classnames(_TRIGGER, FOCUS_RING),
            **{
                ":id": "$id('hue-accordion-trigger')",
                ":aria-expanded": shown,
                ":aria-controls": "$id('hue-accordion-panel')",
                "x-on:click": unsafe(f"toggle({index})"),
            },
        )

        return html.div(
            getattr(html, heading)(trigger),
            html.div(
                *self._children,
                # Named by the heading that opens it, so a screen reader
                # landing in the panel knows which section it is in.
                role="region",
                class_=_PANEL,
                **{
                    ":id": "$id('hue-accordion-panel')",
                    ":aria-labelledby": "$id('hue-accordion-trigger')",
                    "x-show": shown,
                    "x-cloak": True,
                },
            ),
            class_=self._get_prop("class_"),
            **{
                # Minted per item, so two accordions on a page - or two
                # sections in one - cannot point at each other's panels.
                "x-id": "['hue-accordion-trigger', 'hue-accordion-panel']",
                **self._get_base_html_attrs(),
            },
        )
