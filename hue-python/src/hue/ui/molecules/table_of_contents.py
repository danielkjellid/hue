from __future__ import annotations

import json

from htmy import SafeStr, html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames

_LINK = (
    "flex min-h-9 items-center rounded-md py-1.5 pe-2 font-ui text-sm "
    "font-medium text-fg-muted no-underline hover:text-fg "
    "aria-[current=location]:font-semibold aria-[current=location]:text-fg"
)

# The fill grows by uncovering more of a dash; the dot moves by travelling
# further along the path. Both are the same 300ms, so they arrive together.
_FILL_MOTION = "transition-[stroke-dashoffset] duration-300 ease-out"
_DOT_MOTION = "transition-[offset-distance] duration-300 ease-out"


class TableOfContents(ChainableComponent):
    """
    The headings on this page, with the reading position marked on a rail.

    It reads the page rather than being told about it: every heading inside
    of() becomes an entry, nested by its own level, and one without an id is
    given one from its text so the link has somewhere to go. Nothing to keep
    in step with the page, and content swapped in by a fragment rebuilds the
    list rather than leaving it stale.

    The rail bends to follow the nesting and fills in as far as the heading
    being read, which follows the page as it scrolls.
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return cls().of("main").title("On this page")

    def of(self, value: str, *, headings: str = "h2, h3") -> Self:
        """
        Where the content is, as a CSS selector - "main" by default.

        headings says which of them count, as a selector of its own. h2 and
        h3 by default: an h1 is the page's own title rather than a section of
        it, and a fourth level is more shape than a list down a side can
        carry. Being a selector, it is also how a page keeps a heading out of
        its own contents - headings="h2:not([data-toc-skip]), h3". Levels
        nest by their own number, so a page whose headings start at h3 is not
        a page indented by one.

        A heading too long to read down a side can say what it would rather
        be called with data-toc on the heading itself, which renames it here
        without renaming it on the page.
        """
        self._props["of"] = value
        self._props["headings"] = headings
        return self

    def title(self, value: str) -> Self:
        """
        What the list is called. It names the navigation too, so a page with
        more than one set of links says which is which.
        """
        self._props["title"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        title: str = self._get_prop("title", "On this page")
        title_id = "$id('hue-toc-title')"
        options = json.dumps(
            {
                "of": self._get_prop("of", "main"),
                "headings": self._get_prop("headings", "h2, h3"),
            }
        )

        return html.nav(
            html.div(
                HueIcon("file-text").class_("size-3.5 flex-none text-fg-subtle"),
                html.span(title),
                class_=(
                    "mb-1 flex items-center gap-2 font-ui text-2xs font-bold "
                    "uppercase tracking-[0.05em] text-fg-subtle"
                ),
                **{":id": title_id},
            ),
            html.div(
                _rail(),
                html.ol(class_="m-0 list-none p-0", **{"x-ref": "list"}),
                # One entry, for the browser to copy per heading. A template
                # rather than markup built in JavaScript, because Tailwind
                # reads the source for its class names and never sees a
                # string put together at runtime.
                html.template(
                    html.li(
                        html.a(html.span(), class_=classnames(_LINK, FOCUS_RING)),
                        class_="m-0",
                    ),
                    **{"x-ref": "row"},
                ),
                class_="relative",
            ),
            class_=classnames("w-full", self._get_prop("class_")),
            **{
                ":aria-labelledby": title_id,
                "x-id": "['hue-toc-title']",
                "x-data": f"hueToc({options})",
                # Nothing until the headings have been read, so a page that
                # turns out to have none never shows a title over an empty
                # list.
                "x-cloak": True,
                **self._get_base_html_attrs(),
            },
        )


def _rail() -> ComponentType:
    """
    The line, the fill up to where the reader is, and the three dots on it -
    one at each end and one where they are.

    Empty, because every number in it is measured from the rows once they
    exist: a heading long enough to wrap still gets its node beside the line
    the eye starts on. The fill is a second copy of the line, dashed so that
    exactly the first n pixels of it show, which is how a stroke is animated
    along a curve. The dot rides the same path with offset-path, which is
    what keeps it on the line through a bend rather than cutting the corner.
    """
    markup = (
        "<path x-ref='track' fill='none' class='stroke-border'></path>"
        f"<path x-ref='fill' fill='none' class='stroke-accent {_FILL_MOTION}'></path>"
        "<circle x-ref='first' class='fill-accent'></circle>"
        "<circle x-ref='last' class='fill-border'></circle>"
        f"<circle x-ref='dot' class='fill-accent {_DOT_MOTION}'></circle>"
    )
    return html.svg(
        SafeStr(markup),
        aria_hidden="true",
        class_="pointer-events-none absolute start-0 top-0",
        **{"x-ref": "rail"},
    )
