"""
The search dialog: Pagefind's index, behind a combobox the docs draw themselves.

hue's Command filters items the server rendered, and these results arrive from
the index as the reader types, so the docs build their own list on the WAI-ARIA
combobox pattern: focus stays in the input, arrow keys move an active option
named by aria-activedescendant, Enter follows it.
"""

from __future__ import annotations

import json

from htmy import html as h
from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import Dialog, Kbd

from hue_docs_v2.icons import Icon
from hue_docs_v2.site import url

_LISTBOX = "docs-search-results"


def _result_row() -> ComponentType:
    # One option per result, stamped out by x-for, which hue's template does
    # not have. The link is htmy too, for its tabindex: focus stays in the
    # input, and the option is reached through aria-activedescendant.
    option = (
        html.li(
            h.a(
                html.span()
                .class_("block truncate font-ui text-sm font-semibold text-fg")
                .x_text(unsafe("row.title")),
                html.span()
                .class_(
                    "block truncate text-2xs uppercase tracking-wide text-fg-subtle"
                )
                .x_text(unsafe("row.page"))
                .x_show(unsafe("row.page")),
                # Pagefind encodes the text before it adds <mark>, so the
                # excerpt is safe to set as markup.
                html.span()
                .class_("docs-excerpt mt-1 line-clamp-2 block text-xs text-fg-muted")
                .x_html(unsafe("row.excerpt")),
                **{":href": "row.url", "tabindex": "-1"},
                class_="block rounded-md px-3 py-2",
            )
        )
        .role("option")
        .class_("cursor-pointer rounded-md")
        .x_bind("id", unsafe("`docs-search-${index}`"))
        .x_bind("aria-selected", unsafe("String(index === active)"))
        .x_bind("class", unsafe("index === active ? 'bg-surface-active' : ''"))
        .x_on("mousemove", unsafe("active = index"))
    )
    return h.template(option, **{"x-for": "(row, index) in results", ":key": "row.url"})


def search_dialog() -> ComponentType:
    # htmy for the attributes a combobox needs that hue's input has no
    # modifier for: aria-autocomplete, aria-activedescendant, spellcheck.
    box = h.input_(
        type="search",
        placeholder="Search components and guides",
        autocomplete="off",
        spellcheck="false",
        class_=(
            "h-11 min-w-0 flex-1 bg-transparent text-md text-fg outline-none "
            "placeholder:text-fg-subtle"
        ),
        **{
            "role": "combobox",
            "aria-label": "Search the docs",
            "aria-autocomplete": "list",
            "aria-controls": _LISTBOX,
            ":aria-expanded": "String(results.length > 0)",
            ":aria-activedescendant": "active >= 0 ? `docs-search-${active}` : null",
            "x-model": "query",
            "x-ref": "input",
            "x-on:input": "search()",
            "x-on:keydown.arrow-down.prevent": "move(1)",
            "x-on:keydown.arrow-up.prevent": "move(-1)",
            "x-on:keydown.enter.prevent": "go()",
        },
    )
    field = html.div(
        Icon("search").class_("size-4 flex-none text-fg-subtle"), box
    ).class_("flex items-center gap-3 border-b border-border px-4")
    listbox = (
        html.ul(_result_row())
        .id(_LISTBOX)
        .role("listbox")
        .aria_label("Results")
        .class_("max-h-[min(60vh,28rem)] overflow-y-auto p-2")
        .x_show(unsafe("results.length > 0"))
    )
    empty = (
        html.p()
        .class_("px-4 py-8 text-center text-sm text-fg-muted")
        .x_show(unsafe("searched && !results.length && query.trim()"))
        .x_text(unsafe('`Nothing matches "${query.trim()}".`'))
        .x_cloak()
    )
    footer = html.div(
        html.span(Kbd("up"), Kbd("down"), " to move").class_(
            "inline-flex items-center gap-1"
        ),
        html.span(Kbd("enter"), " to open").class_("inline-flex items-center gap-1"),
        html.span(Kbd("esc"), " to close").class_("inline-flex items-center gap-1"),
    ).class_(
        "flex gap-4 border-t border-border px-4 py-2 text-2xs text-fg-subtle "
        "max-sm:hidden"
    )
    return (
        Dialog()
        .label("Search the docs")
        .size("lg")
        .x_on("docs-search.window", unsafe("open = true"))
        .content(
            html.div(
                field,
                listbox,
                empty,
                html.p().class_("sr-only").aria_live("polite").x_text(unsafe("status")),
                footer,
            )
            .class_("-m-5 flex flex-col")
            .x_data(f"docsSearch({json.dumps(url('/'))})")
            # Reset when it opens, so the reader starts from an empty box, and
            # focused by hand: the dialog's trap would otherwise land on its
            # close button, which comes first. -m-5 and open lean on Dialog's
            # body padding and its state's name.
            .x_effect(
                unsafe("if (open) { reset(); $nextTick(() => $refs.input.focus()) }")
            )
        )
    )
