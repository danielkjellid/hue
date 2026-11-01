from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules.disclosure import SUBMIT_LISTENERS, SUBMIT_STATE
from hue.utils import classnames, render_if

type HeadingLevel = Literal["h2", "h3", "h4", "h5", "h6"]

# Ruled off from each other, or each in a box of its own.
_PLAIN = "border-t border-border [&>*]:border-b [&>*]:border-border"
_BOXED = (
    "flex flex-col gap-2 "
    "[&>*]:rounded-md [&>*]:border [&>*]:border-border "
    "[&>*]:bg-surface [&>*]:px-4"
)

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

    def boxed(self, value: bool = True) -> Self:
        """
        Put each section in a bordered, rounded box of its own, with a gap
        between them, rather than ruling them off from each other.
        """
        self._props["boxed"] = value
        return self

    def multiple(self, value: bool = True) -> Self:
        """
        Let any number of sections stay open at once, rather than the one
        most recently opened.
        """
        self._props["multiple"] = value
        return self

    def _render(self, context: Context) -> Component:
        self._refuse_x_data()
        boxed: bool = self._get_prop("boxed", False)
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
            f"{{ hueOpen: {opened}, hueSingle: {single}, "
            "hueShown(index) { return this.hueOpen.includes(index) }, "
            "hueToggle(index) { this.hueOpen = this.hueShown(index) "
            "? this.hueOpen.filter((each) => each !== index) "
            ": (this.hueSingle ? [index] : [...this.hueOpen, index]) }, "
            f"{_REVEAL_METHOD} }}"
        )

        return html.div(
            *self._children,
            # w-full, or the accordion is as wide as whichever panel happens
            # to be open and the whole thing jumps every time one is. The
            # panel keeps its own reading width instead.
            class_=classnames(
                "w-full",
                _BOXED if boxed else _PLAIN,
                self._get_prop("class_"),
            ),
            **{
                "x-data": state,
                "x-on:invalid.capture.document": "hueNoteInvalid($event.target)",
                **SUBMIT_LISTENERS,
                **self._get_base_html_attrs(),
            },
        )


# Opens a section for something inside it that has to be seen, as a
# Disclosure does: an invalid field the browser is about to focus, which it
# gives up on while the panel is display: none, or a heading the contents is
# going to. The panel is shown there and then, since x-show only gets to it
# after the browser has looked.
#
# One at a time, a field the browser does not report opens its section only
# while none is open, since opening it would close the section the reader is
# in, or the one just opened for the field that is reported. The browser
# reports the first field it fires invalid at in a task: a submit fires at
# every invalid field at once, in order, and reportValidity() on one field
# at that field alone. hueNoteInvalid hears every one of them, on the
# document, before any panel does. Those left closed are also left
# unreported, rather than logged as fields it could not focus. All of it on
# a submit only, as for a Disclosure.
_REPORTED = "($event.type !== 'invalid' || hueReportedField === $event.target)"
_REVEAL_METHOD = (
    "hueReportedField: null, "
    f"{SUBMIT_STATE}, "
    "hueNoteInvalid(field) { "
    "if (!this.hueSubmitting || this.hueReportedField) return; "
    "this.hueReportedField = field; "
    "setTimeout(() => { this.hueReportedField = null }) }, "
    "hueRevealSection(index, panel, event, reported) { "
    "if (event.type === 'invalid' && !this.hueSubmitting) return; "
    "if (this.hueSingle && !reported && this.hueOpen.length "
    "&& !this.hueShown(index)) return event.preventDefault(); "
    "if (!this.hueShown(index)) this.hueToggle(index); "
    "panel.style.removeProperty('display') }"
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

    def _render(self, context: Context) -> Component:
        index: int = self._get_prop("index", 0)
        heading: HeadingLevel = self._get_prop("heading", "h3")
        shown = unsafe(f"hueShown({index})")
        reveal = unsafe(f"hueRevealSection({index}, $el, $event, {_REPORTED})")

        trigger = html.button(
            render_if(self._get_prop("title"), lambda text: text),
            HueIcon("chevron-down").class_(_CHEVRON),
            type="button",
            class_=classnames(_TRIGGER, FOCUS_RING),
            **{
                ":id": "$id('hue-accordion-trigger')",
                ":aria-expanded": shown,
                ":aria-controls": "$id('hue-accordion-panel')",
                "x-on:click": unsafe(f"hueToggle({index})"),
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
                    "x-on:invalid.capture": reveal,
                    "x-on:hue-reveal": reveal,
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
