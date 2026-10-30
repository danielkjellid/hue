from __future__ import annotations

from htmy import Context, html
from typing_extensions import Self

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
    "h-10 bg-canvas-subtle px-4 text-start font-ui text-base font-medium "
    "leading-none "
    "text-fg hover:bg-surface-hover"
)

_CHEVRON = (
    "ms-auto size-4 flex-none text-fg-subtle transition-transform "
    "duration-150 [[aria-expanded=true]>&]:rotate-180"
)


# Opens the section for something inside it that has to be seen: an invalid
# field the browser is about to focus, which it gives up on while the panel
# is display: none, or a heading the contents is going to. The panel is
# shown there and then, since x-show only gets to it after the browser has
# looked. Capturing, because invalid does not bubble.
#
# Only on a submit, which is when the browser reports a field: a form that
# calls checkValidity() as the reader types fires invalid too, and opening a
# section then would move the page under them. A submit is a click on a
# submit control, which Enter in a field makes as well, or Enter in a field
# of a form with none; it validates in the same task. A script calling
# requestSubmit() or reportValidity() opens nothing.
#
# Every key hue puts in this x-data, and in the Accordion's, starts with hue:
# the section holds the caller's markup, and a key of ours named like one of
# theirs, such as a form's own submitting flag, would shadow it in there.
SUBMIT_STATE = (
    "hueSubmitting: false, "
    "hueNoteSubmit() { this.hueSubmitting = true; "
    "setTimeout(() => { this.hueSubmitting = false }) }"
)
SUBMIT_LISTENERS = {
    "x-on:click.capture.document": (
        "if ($event.target.closest?.('button:not([type]), button[type=submit], "
        "input[type=submit], input[type=image]')?.form) hueNoteSubmit()"
    ),
    "x-on:keydown.capture.document": (
        "if ($event.key === 'Enter' && $event.target.form "
        "&& $event.target.matches('input')) hueNoteSubmit()"
    ),
}
_OPEN_NOW = unsafe(
    "if ($event.type === 'invalid' && !hueSubmitting) return; "
    "hueOpen = true; $el.style.removeProperty('display')"
)
_REVEAL = {"x-on:invalid.capture": _OPEN_NOW, "x-on:hue-reveal": _OPEN_NOW}


class Disclosure(ChainableComponent):
    """
    A section of a page that can be folded away.

    The title sits in an h3, which is how a screen reader finds the section.

    One heading and what it opens, answering to nothing else on the page -
    where an Accordion is a set of these that agree on how many stay open.
    Reach for this to group a long form; reach for that when the point is
    that only one section is open at a time.

        Disclosure().title("General").content(fields)
    """

    category = "Layout"

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def closed(self, value: bool = True) -> Self:
        """
        Start it folded away.

        Open is the default: a section of a form is there to be filled in,
        and one that hides its fields until asked is one the reader has to
        open before they can see what the page even wants.
        """
        self._props["closed"] = value
        return self

    def _render(self, context: Context) -> Component:
        self._refuse_x_data()
        starts_open = not self._get_prop("closed", False)

        trigger = html.button(
            render_if(self._get_prop("title"), lambda text: text),
            HueIcon("chevron-down").class_(_CHEVRON),
            type="button",
            class_=classnames(_HEADER, FOCUS_RING),
            **{
                ":id": "$id('hue-disclosure-title')",
                ":aria-expanded": unsafe("hueOpen"),
                ":aria-controls": "$id('hue-disclosure-panel')",
                "x-on:click": unsafe("hueOpen = !hueOpen"),
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
                    "x-show": unsafe("hueOpen"),
                    "x-cloak": True,
                    **_REVEAL,
                },
            ),
            # A section spans its column: the header is a band across the
            # content it folds, not a chip the width of its own title. The
            # band carries its own height; on the wrapper it would clamp the
            # section and leave the panel hanging over whatever follows.
            class_=classnames("w-full", self._get_prop("class_")),
            **{
                "x-data": f"{{ hueOpen: {str(starts_open).lower()}, {SUBMIT_STATE} }}",
                **SUBMIT_LISTENERS,
                "x-id": "['hue-disclosure-title', 'hue-disclosure-panel']",
                **self._get_base_html_attrs(),
            },
        )
